import json
import logging
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/darwin")

_DARWIN_ROOT = Path(__file__).resolve().parent.parent / "external_resources" / "darwin-skill"
_SKILLS_ROOT = Path(__file__).resolve().parent.parent / "skills"
_RESULTS_DIR = Path(__file__).resolve().parent.parent / "darwin_results"
_DARWIN_AVAILABLE = _DARWIN_ROOT.is_dir()

_SKILLS_ROOT.mkdir(parents=True, exist_ok=True)
_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

RUBRIC = {
    "frontmatter_quality": {"weight": 8, "category": "structure", "name": "Frontmatter质量"},
    "workflow_clarity": {"weight": 15, "category": "structure", "name": "工作流清晰度"},
    "boundary_conditions": {"weight": 10, "category": "structure", "name": "边界条件覆盖"},
    "checkpoint_design": {"weight": 7, "category": "structure", "name": "检查点设计"},
    "instruction_specificity": {"weight": 15, "category": "structure", "name": "指令具体性"},
    "resource_integration": {"weight": 5, "category": "structure", "name": "资源整合度"},
    "overall_architecture": {"weight": 15, "category": "effectiveness", "name": "整体架构"},
    "actual_performance": {"weight": 25, "category": "effectiveness", "name": "实测表现"},
}

OPTIMIZATION_STRATEGIES = {
    "P0": [
        {"issue": "测试输出偏离用户意图", "action": "检查skill是否有误导性指令"},
        {"issue": "带skill比不带还差", "action": "skill可能过度约束，考虑精简"},
        {"issue": "输出格式不符合预期", "action": "补充明确的输出模板"},
    ],
    "P1": [
        {"issue": "Frontmatter缺少触发词", "action": "补充中英文触发词"},
        {"issue": "缺少Phase/Step结构", "action": "重组为线性流程"},
        {"issue": "缺少用户确认检查点", "action": "在关键决策处插入"},
    ],
    "P2": [
        {"issue": "步骤模糊", "action": "改为具体操作和参数"},
        {"issue": "缺少输入/输出规格", "action": "补充格式、路径、示例"},
        {"issue": "缺少异常处理", "action": "补充'如果X失败，则Y'"},
    ],
    "P3": [
        {"issue": "段落过长", "action": "拆分+用表格"},
        {"issue": "重复描述", "action": "合并去重"},
        {"issue": "缺少速查", "action": "添加TL;DR或决策树"},
    ],
}


class SkillScore(BaseModel):
    frontmatter_quality: float = 0
    workflow_clarity: float = 0
    boundary_conditions: float = 0
    checkpoint_design: float = 0
    instruction_specificity: float = 0
    resource_integration: float = 0
    overall_architecture: float = 0
    actual_performance: float = 0

    @property
    def total(self) -> float:
        s = 0
        for dim, info in RUBRIC.items():
            s += getattr(self, dim) * info["weight"] / 10
        return round(s, 1)

    @property
    def structure_score(self) -> float:
        s = 0
        for dim, info in RUBRIC.items():
            if info["category"] == "structure":
                s += getattr(self, dim) * info["weight"] / 10
        return round(s, 1)

    @property
    def effectiveness_score(self) -> float:
        s = 0
        for dim, info in RUBRIC.items():
            if info["category"] == "effectiveness":
                s += getattr(self, dim) * info["weight"] / 10
        return round(s, 1)

    @property
    def weakest_dimension(self) -> Tuple[str, float]:
        worst_dim = ""
        worst_val = 11
        for dim, info in RUBRIC.items():
            val = getattr(self, dim)
            weighted = val * info["weight"] / 10
            if weighted < worst_val:
                worst_val = weighted
                worst_dim = dim
        return worst_dim, round(worst_val, 1)

    def to_dict(self) -> Dict[str, Any]:
        d = {}
        for dim, info in RUBRIC.items():
            d[dim] = {
                "name": info["name"],
                "score": getattr(self, dim),
                "weight": info["weight"],
                "weighted_score": round(getattr(self, dim) * info["weight"] / 10, 1),
                "category": info["category"],
            }
        d["total"] = self.total
        d["structure_score"] = self.structure_score
        d["effectiveness_score"] = self.effectiveness_score
        return d


class EvolutionRecord(BaseModel):
    timestamp: str
    skill_name: str
    old_score: float
    new_score: float
    status: str
    dimension: str
    note: str
    eval_mode: str = "dry_run"
    commit: str = "-"


def _parse_frontmatter(content: str) -> Dict[str, str]:
    fm = {}
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if match:
        for line in match.group(1).strip().split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def _score_frontmatter_quality(content: str) -> Tuple[float, str]:
    fm = _parse_frontmatter(content)
    score = 5.0
    notes = []
    if not fm.get("name"):
        score -= 2
        notes.append("缺少name字段")
    if not fm.get("description"):
        score -= 2
        notes.append("缺少description字段")
    else:
        desc = fm["description"]
        if len(desc) > 1024:
            score -= 1
            notes.append("description超过1024字符")
        if not any(kw in desc for kw in ["Use when", "何时用", "触发"]):
            score -= 1
            notes.append("description缺少触发词/使用场景")
        if len(desc) < 20:
            score -= 1
            notes.append("description过短")
    if score < 1:
        score = 1
    return min(score, 10), "; ".join(notes) if notes else "Frontmatter规范"


def _score_workflow_clarity(content: str) -> Tuple[float, str]:
    score = 5.0
    notes = []
    body = re.sub(r"^---.*?---", "", content, count=1, flags=re.DOTALL).strip()
    phase_count = len(re.findall(r"Phase\s*\d", body, re.IGNORECASE))
    step_count = len(re.findall(r"Step\s*\d|步骤\s*\d|^\s*\d+\.", body, re.MULTILINE))
    if phase_count == 0 and step_count == 0:
        score -= 3
        notes.append("缺少Phase/Step结构")
    elif phase_count < 2:
        score -= 1
        notes.append("Phase结构不完整")
    has_io = bool(re.search(r"输入[：/:]|输出[：/:]|Input[：/:]|Output[：/:]", body, re.IGNORECASE))
    if not has_io:
        score -= 1
        notes.append("缺少输入/输出说明")
    ordered = bool(re.search(r"^\s*1[\.\)]|^\s*Step\s*1|^\s*Phase\s*0", body, re.MULTILINE | re.IGNORECASE))
    if not ordered:
        score -= 1
        notes.append("步骤缺少序号")
    if score < 1:
        score = 1
    return min(score, 10), "; ".join(notes) if notes else "工作流清晰"


def _score_boundary_conditions(content: str) -> Tuple[float, str]:
    score = 4.0
    notes = []
    body = re.sub(r"^---.*?---", "", content, count=1, flags=re.DOTALL).strip()
    if not re.search(r"异常|错误|失败|fallback|回退|边界|Error|Exception|Fail|Fallback", body, re.IGNORECASE):
        score -= 2
        notes.append("缺少异常处理说明")
    if not re.search(r"如果.*则|If.*then|当.*时", body, re.IGNORECASE):
        score -= 1
        notes.append("缺少条件分支")
    if not re.search(r"否则|else|备选|替代", body, re.IGNORECASE):
        score -= 1
        notes.append("缺少备选路径")
    if score < 1:
        score = 1
    return min(score, 10), "; ".join(notes) if notes else "边界条件充分"


def _score_checkpoint_design(content: str) -> Tuple[float, str]:
    score = 4.0
    notes = []
    body = re.sub(r"^---.*?---", "", content, count=1, flags=re.DOTALL).strip()
    if not re.search(r"确认|暂停|等用户|Human|检查点|Checkpoint|Confirm", body, re.IGNORECASE):
        score -= 2
        notes.append("缺少用户确认检查点")
    if not re.search(r"同意|批准|OK|确认后", body, re.IGNORECASE):
        score -= 1
        notes.append("缺少用户批准流程")
    if not re.search(r"回滚|撤销|revert|rollback", body, re.IGNORECASE):
        score -= 1
        notes.append("缺少回滚机制")
    if score < 1:
        score = 1
    return min(score, 10), "; ".join(notes) if notes else "检查点设计合理"


def _score_instruction_specificity(content: str) -> Tuple[float, str]:
    score = 5.0
    notes = []
    body = re.sub(r"^---.*?---", "", content, count=1, flags=re.DOTALL).strip()
    has_example = bool(re.search(r"示例|Example|例如|比如|```", body, re.IGNORECASE))
    if not has_example:
        score -= 2
        notes.append("缺少示例")
    has_format = bool(re.search(r"格式|Format|模板|Template|```json|```yaml|```python", body, re.IGNORECASE))
    if not has_format:
        score -= 1
        notes.append("缺少格式/模板说明")
    has_param = bool(re.search(r"参数|Parameter|配置|Config|字段|Field", body, re.IGNORECASE))
    if not has_param:
        score -= 1
        notes.append("缺少参数/配置说明")
    vague_words = len(re.findall(r"处理|操作|执行|适当|合理|相关", body))
    if vague_words > 10:
        score -= 1
        notes.append(f"模糊词汇较多({vague_words}个)")
    if score < 1:
        score = 1
    return min(score, 10), "; ".join(notes) if notes else "指令具体明确"


def _score_resource_integration(content: str) -> Tuple[float, str]:
    score = 5.0
    notes = []
    body = re.sub(r"^---.*?---", "", content, count=1, flags=re.DOTALL).strip()
    has_ref = bool(re.search(r"references|scripts|assets|资源|引用|路径", body, re.IGNORECASE))
    if not has_ref:
        score -= 1
        notes.append("缺少资源引用")
    has_path = bool(re.search(r"[./\w]+\.\w{1,5}", body))
    if not has_path:
        score -= 1
        notes.append("缺少文件路径引用")
    if score < 1:
        score = 1
    return min(score, 10), "; ".join(notes) if notes else "资源整合良好"


def _score_overall_architecture(content: str) -> Tuple[float, str]:
    score = 5.0
    notes = []
    body = re.sub(r"^---.*?---", "", content, count=1, flags=re.DOTALL).strip()
    sections = re.findall(r"^#{1,3}\s+", body, re.MULTILINE)
    if len(sections) < 3:
        score -= 2
        notes.append(f"章节结构过少({len(sections)}个)")
    elif len(sections) > 15:
        score -= 1
        notes.append(f"章节过多({len(sections)}个)，可能冗余")
    has_toc = bool(re.search(r"目录|TOC|Table of Contents", body, re.IGNORECASE))
    if not has_toc and len(sections) > 5:
        score -= 0.5
        notes.append("长文档缺少目录")
    lines = body.split("\n")
    non_empty = [l for l in lines if l.strip()]
    if len(non_empty) > 0:
        avg_len = sum(len(l) for l in non_empty) / len(non_empty)
        if avg_len > 120:
            score -= 1
            notes.append("段落过长，建议拆分")
    if score < 1:
        score = 1
    return min(score, 10), "; ".join(notes) if notes else "架构清晰"


def _score_actual_performance(content: str, test_prompts: Optional[List[Dict]] = None) -> Tuple[float, str]:
    score = 5.0
    notes = []
    fm = _parse_frontmatter(content)
    desc = fm.get("description", "")
    if not desc:
        score -= 2
        notes.append("无法评估：缺少description")
    body = re.sub(r"^---.*?---", "", content, count=1, flags=re.DOTALL).strip()
    if len(body) < 100:
        score -= 2
        notes.append("内容过短，难以产生有效输出")
    if len(body) > 10000:
        score -= 1
        notes.append("内容过长，可能引入噪音")
    has_workflow = bool(re.search(r"Phase|Step|步骤|流程", body, re.IGNORECASE))
    if not has_workflow:
        score -= 1
        notes.append("缺少可执行工作流")
    if test_prompts:
        notes.append(f"已设计{len(test_prompts)}个测试prompt")
    else:
        notes.append("dry_run模式：未执行实测")
    if score < 1:
        score = 1
    return min(score, 10), "; ".join(notes) if notes else "效果评估完成"


def evaluate_skill(content: str, test_prompts: Optional[List[Dict]] = None) -> Tuple[SkillScore, Dict[str, str]]:
    scores = SkillScore()
    notes = {}
    dim_funcs = {
        "frontmatter_quality": _score_frontmatter_quality,
        "workflow_clarity": _score_workflow_clarity,
        "boundary_conditions": _score_boundary_conditions,
        "checkpoint_design": _score_checkpoint_design,
        "instruction_specificity": _score_instruction_specificity,
        "resource_integration": _score_resource_integration,
        "overall_architecture": _score_overall_architecture,
    }
    for dim, func in dim_funcs.items():
        s, n = func(content)
        setattr(scores, dim, s)
        notes[dim] = n
    s, n = _score_actual_performance(content, test_prompts)
    scores.actual_performance = s
    notes["actual_performance"] = n
    return scores, notes


def _scan_skills() -> List[Dict[str, Any]]:
    skills = []
    if not _SKILLS_ROOT.is_dir():
        return skills
    for skill_dir in sorted(_SKILLS_ROOT.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if skill_md.is_file():
            content = skill_md.read_text(encoding="utf-8")
            fm = _parse_frontmatter(content)
            skills.append({
                "name": skill_dir.name,
                "path": str(skill_dir),
                "has_skill_md": True,
                "frontmatter": fm,
                "content_length": len(content),
            })
        else:
            skills.append({
                "name": skill_dir.name,
                "path": str(skill_dir),
                "has_skill_md": False,
                "frontmatter": {},
                "content_length": 0,
            })
    return skills


def _read_results_tsv() -> List[Dict[str, str]]:
    tsv_path = _RESULTS_DIR / "results.tsv"
    if not tsv_path.is_file():
        return []
    records = []
    with open(tsv_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            parts = line.strip().split("\t")
            if len(parts) >= 9:
                records.append({
                    "timestamp": parts[0],
                    "commit": parts[1],
                    "skill_name": parts[2],
                    "old_score": parts[3],
                    "new_score": parts[4],
                    "status": parts[5],
                    "dimension": parts[6],
                    "note": parts[7],
                    "eval_mode": parts[8],
                })
    return records


def _append_results_tsv(record: EvolutionRecord):
    tsv_path = _RESULTS_DIR / "results.tsv"
    header_needed = not tsv_path.is_file()
    with open(tsv_path, "a", encoding="utf-8") as f:
        if header_needed:
            f.write("timestamp\tcommit\tskill_name\told_score\tnew_score\tstatus\tdimension\tnote\teval_mode\n")
        f.write(f"{record.timestamp}\t{record.commit}\t{record.skill_name}\t{record.old_score}\t{record.new_score}\t{record.status}\t{record.dimension}\t{record.note}\t{record.eval_mode}\n")


def _git_run(args: List[str], cwd: Optional[str] = None) -> Tuple[int, str]:
    work_dir = cwd or str(_SKILLS_ROOT)
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode, result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        return 1, str(e)


def _ensure_git_repo():
    if not (_SKILLS_ROOT / ".git").is_dir():
        _git_run(["init"], str(_SKILLS_ROOT))
        _git_run(["config", "user.email", "darwin@rag-gzhu.local"], str(_SKILLS_ROOT))
        _git_run(["config", "user.name", "Darwin Engine"], str(_SKILLS_ROOT))


def _save_skill_content(skill_name: str, content: str) -> bool:
    skill_dir = _SKILLS_ROOT / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(content, encoding="utf-8")
    return True


def _read_skill_content(skill_name: str) -> Optional[str]:
    skill_md = _SKILLS_ROOT / skill_name / "SKILL.md"
    if not skill_md.is_file():
        return None
    return skill_md.read_text(encoding="utf-8")


def _generate_improvement_suggestion(scores: SkillScore, notes: Dict[str, str]) -> Dict[str, Any]:
    weakest_dim, weakest_val = scores.weakest_dimension
    dim_info = RUBRIC.get(weakest_dim, {})
    category = dim_info.get("category", "structure")
    priority = "P0" if category == "effectiveness" else "P1"
    if scores.instruction_specificity < 5:
        priority = "P2"
    if weakest_val > 6:
        priority = "P3"
    strategies = OPTIMIZATION_STRATEGIES.get(priority, OPTIMIZATION_STRATEGIES["P3"])
    matching_strategy = None
    for s in strategies:
        if any(kw in notes.get(weakest_dim, "") for kw in s["issue"].split()):
            matching_strategy = s
            break
    if not matching_strategy:
        matching_strategy = strategies[0]
    return {
        "weakest_dimension": weakest_dim,
        "weakest_dimension_name": dim_info.get("name", weakest_dim),
        "weakest_score": weakest_val,
        "priority": priority,
        "suggested_action": matching_strategy["action"],
        "issue": matching_strategy["issue"],
        "category": category,
    }


# ==================== API Endpoints ====================

class SkillUploadRequest(BaseModel):
    name: str
    content: str


class EvaluateRequest(BaseModel):
    content: str
    test_prompts: Optional[List[Dict[str, str]]] = None


class OptimizeRequest(BaseModel):
    skill_name: str
    max_rounds: int = 3
    dry_run: bool = True


@router.get("/status", summary="获取达尔文引擎状态")
async def darwin_status():
    skills = _scan_skills()
    results = _read_results_tsv()
    return {
        "available": _DARWIN_AVAILABLE,
        "darwin_root": str(_DARWIN_ROOT),
        "skills_root": str(_SKILLS_ROOT),
        "registered_skills": len(skills),
        "evolution_history_count": len(results),
        "rubric_dimensions": len(RUBRIC),
        "skills": [{"name": s["name"], "has_skill_md": s["has_skill_md"]} for s in skills],
    }


@router.get("/rubric", summary="获取8维度评分标准")
async def get_rubric():
    dims = []
    for dim, info in RUBRIC.items():
        dims.append({
            "id": dim,
            "name": info["name"],
            "weight": info["weight"],
            "category": info["category"],
        })
    return {"dimensions": dims, "total_weight": sum(i["weight"] for i in RUBRIC.values())}


@router.get("/strategies", summary="获取优化策略库")
async def get_strategies():
    return {"strategies": OPTIMIZATION_STRATEGIES}


@router.post("/evaluate", summary="评估SKILL.md内容质量")
async def evaluate_skill_api(req: EvaluateRequest):
    scores, notes = evaluate_skill(req.content, req.test_prompts)
    suggestion = _generate_improvement_suggestion(scores, notes)
    return {
        "scores": scores.to_dict(),
        "notes": notes,
        "suggestion": suggestion,
    }


@router.get("/skills", summary="获取已注册的Skill列表")
async def list_skills():
    skills = _scan_skills()
    return {"skills": skills, "total": len(skills)}


@router.post("/skills/register", summary="注册新Skill到进化引擎")
async def register_skill(req: SkillUploadRequest):
    safe_name = re.sub(r"[^\w\-]", "_", req.name)
    if not safe_name:
        raise HTTPException(status_code=400, detail="Skill名称无效")
    _save_skill_content(safe_name, req.content)
    scores, notes = evaluate_skill(req.content)
    _ensure_git_repo()
    _git_run(["add", f"{safe_name}/SKILL.md"], str(_SKILLS_ROOT))
    _git_run(["commit", "-m", f"register skill: {safe_name}"], str(_SKILLS_ROOT))
    record = EvolutionRecord(
        timestamp=datetime.now().isoformat(timespec="seconds"),
        skill_name=safe_name,
        old_score=0,
        new_score=scores.total,
        status="register",
        dimension="-",
        note="初始注册评估",
        eval_mode="dry_run",
        commit="-",
    )
    _append_results_tsv(record)
    return {
        "name": safe_name,
        "scores": scores.to_dict(),
        "notes": notes,
        "message": f"Skill '{safe_name}' 注册成功，初始评分: {scores.total}",
    }


@router.get("/skills/{skill_name}", summary="获取指定Skill详情")
async def get_skill_detail(skill_name: str):
    content = _read_skill_content(skill_name)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' 不存在")
    scores, notes = evaluate_skill(content)
    test_prompts_path = _SKILLS_ROOT / skill_name / "test-prompts.json"
    test_prompts = None
    if test_prompts_path.is_file():
        try:
            test_prompts = json.loads(test_prompts_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    suggestion = _generate_improvement_suggestion(scores, notes)
    return {
        "name": skill_name,
        "content": content,
        "scores": scores.to_dict(),
        "notes": notes,
        "suggestion": suggestion,
        "test_prompts": test_prompts,
    }


@router.put("/skills/{skill_name}", summary="更新Skill内容")
async def update_skill(skill_name: str, req: SkillUploadRequest):
    old_content = _read_skill_content(skill_name)
    if old_content is None:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' 不存在")
    old_scores, _ = evaluate_skill(old_content)
    _save_skill_content(skill_name, req.content)
    new_scores, new_notes = evaluate_skill(req.content)
    _ensure_git_repo()
    _git_run(["add", f"{skill_name}/SKILL.md"], str(_SKILLS_ROOT))
    rc, commit_hash = _git_run(["commit", "-m", f"update skill: {skill_name}"], str(_SKILLS_ROOT))
    short_hash = commit_hash[:7] if commit_hash else "-"
    if new_scores.total > old_scores.total:
        status = "keep"
        msg = f"更新后分数提升: {old_scores.total} → {new_scores.total}"
    elif new_scores.total < old_scores.total:
        status = "revert"
        msg = f"更新后分数下降: {old_scores.total} → {new_scores.total}，建议回滚"
    else:
        status = "neutral"
        msg = f"更新后分数不变: {new_scores.total}"
    record = EvolutionRecord(
        timestamp=datetime.now().isoformat(timespec="seconds"),
        skill_name=skill_name,
        old_score=old_scores.total,
        new_score=new_scores.total,
        status=status,
        dimension="-",
        note=msg,
        eval_mode="dry_run",
        commit=short_hash,
    )
    _append_results_tsv(record)
    return {
        "name": skill_name,
        "old_scores": old_scores.to_dict(),
        "new_scores": new_scores.to_dict(),
        "new_notes": new_notes,
        "status": status,
        "message": msg,
    }


@router.delete("/skills/{skill_name}", summary="删除Skill")
async def delete_skill(skill_name: str):
    skill_dir = _SKILLS_ROOT / skill_name
    if not skill_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' 不存在")
    shutil.rmtree(skill_dir)
    _ensure_git_repo()
    _git_run(["add", "-A"], str(_SKILLS_ROOT))
    _git_run(["commit", "-m", f"remove skill: {skill_name}"], str(_SKILLS_ROOT))
    return {"message": f"Skill '{skill_name}' 已删除"}


@router.post("/skills/{skill_name}/test-prompts", summary="为Skill设计测试Prompt")
async def design_test_prompts(skill_name: str, prompts: List[Dict[str, str]]):
    skill_dir = _SKILLS_ROOT / skill_name
    if not skill_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' 不存在")
    tp_path = skill_dir / "test-prompts.json"
    tp_path.write_text(json.dumps(prompts, ensure_ascii=False, indent=2), encoding="utf-8")
    content = _read_skill_content(skill_name)
    scores, notes = evaluate_skill(content, prompts)
    return {
        "skill_name": skill_name,
        "test_prompts": prompts,
        "updated_scores": scores.to_dict(),
        "message": f"已保存{len(prompts)}个测试Prompt",
    }


@router.post("/skills/{skill_name}/revert", summary="回滚Skill到上一个版本")
async def revert_skill(skill_name: str):
    _ensure_git_repo()
    rc, output = _git_run(["log", "--oneline", "-5", "--", f"{skill_name}/SKILL.md"], str(_SKILLS_ROOT))
    if rc != 0:
        raise HTTPException(status_code=500, detail=f"无法获取git历史: {output}")
    rc2, output2 = _git_run(["revert", "HEAD", "--no-edit"], str(_SKILLS_ROOT))
    if rc2 != 0:
        raise HTTPException(status_code=500, detail=f"回滚失败: {output2}")
    record = EvolutionRecord(
        timestamp=datetime.now().isoformat(timespec="seconds"),
        skill_name=skill_name,
        old_score=0,
        new_score=0,
        status="revert",
        dimension="-",
        note="手动回滚",
        eval_mode="manual",
        commit="-",
    )
    _append_results_tsv(record)
    return {"message": f"Skill '{skill_name}' 已回滚到上一版本"}


@router.post("/evolve", summary="执行进化循环")
async def evolve_skill(req: OptimizeRequest):
    content = _read_skill_content(req.skill_name)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Skill '{req.skill_name}' 不存在")
    baseline_scores, baseline_notes = evaluate_skill(content)
    _ensure_git_repo()
    evolution_log = []
    current_scores = baseline_scores
    current_content = content
    for round_num in range(1, req.max_rounds + 1):
        suggestion = _generate_improvement_suggestion(current_scores, baseline_notes)
        weakest_dim = suggestion["weakest_dimension"]
        weakest_name = suggestion["weakest_dimension_name"]
        action = suggestion["suggested_action"]
        priority = suggestion["priority"]
        improvement_patch = _apply_improvement(current_content, suggestion)
        new_scores, new_notes = evaluate_skill(improvement_patch)
        if new_scores.total > current_scores.total:
            _save_skill_content(req.skill_name, improvement_patch)
            _git_run(["add", f"{req.skill_name}/SKILL.md"], str(_SKILLS_ROOT))
            rc, commit_hash = _git_run(
                ["commit", "-m", f"evolve {req.skill_name}: {action} ({weakest_name})"],
                str(_SKILLS_ROOT),
            )
            short_hash = commit_hash[:7] if commit_hash else "-"
            status = "keep"
            current_scores = new_scores
            current_content = improvement_patch
            record = EvolutionRecord(
                timestamp=datetime.now().isoformat(timespec="seconds"),
                skill_name=req.skill_name,
                old_score=current_scores.total if round_num > 1 else baseline_scores.total,
                new_score=new_scores.total,
                status=status,
                dimension=weakest_dim,
                note=f"R{round_num}: {action}",
                eval_mode="dry_run" if req.dry_run else "full_test",
                commit=short_hash,
            )
            _append_results_tsv(record)
            evolution_log.append({
                "round": round_num,
                "status": "keep",
                "dimension": weakest_dim,
                "action": action,
                "old_score": record.old_score,
                "new_score": new_scores.total,
                "priority": priority,
            })
        else:
            rc, commit_hash = _git_run(
                ["commit", "--allow-empty", "-m", f"evolve {req.skill_name}: FAILED {action}"],
                str(_SKILLS_ROOT),
            )
            record = EvolutionRecord(
                timestamp=datetime.now().isoformat(timespec="seconds"),
                skill_name=req.skill_name,
                old_score=current_scores.total,
                new_score=new_scores.total,
                status="revert",
                dimension=weakest_dim,
                note=f"R{round_num}: 分数未提升，跳过",
                eval_mode="dry_run" if req.dry_run else "full_test",
                commit="-",
            )
            _append_results_tsv(record)
            evolution_log.append({
                "round": round_num,
                "status": "revert",
                "dimension": weakest_dim,
                "action": action,
                "old_score": current_scores.total,
                "new_score": new_scores.total,
                "priority": priority,
            })
            break
    return {
        "skill_name": req.skill_name,
        "baseline_score": baseline_scores.total,
        "final_score": current_scores.total,
        "delta": round(current_scores.total - baseline_scores.total, 1),
        "rounds_completed": len(evolution_log),
        "evolution_log": evolution_log,
        "final_scores": current_scores.to_dict(),
        "final_notes": baseline_notes,
    }


def _apply_improvement(content: str, suggestion: Dict[str, Any]) -> str:
    dim = suggestion["weakest_dimension"]
    action = suggestion["suggested_action"]
    category = suggestion["category"]
    body = re.sub(r"^---.*?---", "", content, count=1, flags=re.DOTALL).strip()
    fm = _parse_frontmatter(content)
    fm_str = ""
    for k, v in fm.items():
        fm_str += f"{k}: {v}\n"
    if not fm_str:
        fm_str = "name: unnamed-skill\ndescription: A skill for optimization\n"
    improvements = {
        "frontmatter_quality": f"""
## 优化说明
> 自动优化：{action}

### 使用场景
当用户提到相关关键词时自动触发此Skill。

### 触发词
- 中文：优化、评估、改进、检查
- English: optimize, evaluate, improve, check
""",
        "workflow_clarity": f"""
## 工作流程

### Phase 1: 初始化
1. 读取并理解用户需求
2. 确认执行范围和目标
   - 输入：用户请求
   - 输出：确认的执行计划

### Phase 2: 执行
1. 按步骤执行核心逻辑
2. 记录中间结果
   - 输入：执行计划
   - 输出：执行结果

### Phase 3: 验证
1. 检查执行结果是否符合预期
2. 输出最终结果
   - 输入：执行结果
   - 输出：验证后的最终输出

> 自动优化：{action}
""",
        "boundary_conditions": f"""
## 异常处理与边界条件

### 常见异常
- **输入无效**：如果输入为空或格式错误，提示用户重新输入
- **执行失败**：如果核心步骤执行失败，回退到安全状态并告知用户
- **超时处理**：如果操作超时，保存当前进度并允许用户恢复

### Fallback路径
- 如果方案A失败 → 尝试方案B
- 如果方案B失败 → 提示用户手动干预

> 自动优化：{action}
""",
        "checkpoint_design": f"""
## 检查点

### 用户确认点
- ⚠️ **关键决策前**：在执行不可逆操作前，暂停并等待用户确认
- ⚠️ **资源消耗操作前**：在执行高资源消耗操作前，提示用户确认
- ⚠️ **结果确认**：执行完成后，展示结果等待用户确认

### 回滚机制
- 所有改动通过git版本控制
- 使用 `git revert` 回滚，不使用 `reset --hard`

> 自动优化：{action}
""",
        "instruction_specificity": f"""
## 参数与配置

### 输入参数
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| input | string | 是 | - | 用户输入内容 |
| mode | string | 否 | "auto" | 执行模式 |

### 输出格式
```json
{{
  "status": "success|error",
  "result": "执行结果",
  "message": "状态说明"
}}
```

### 示例
输入: "优化这个skill"
输出: 执行优化流程并返回改进建议

> 自动优化：{action}
""",
        "resource_integration": f"""
## 资源引用

### 相关文件
- `scripts/` - 辅助脚本
- `assets/` - 资源文件
- `templates/` - 模板文件

### 外部依赖
- 无额外依赖

> 自动优化：{action}
""",
        "overall_architecture": f"""
## 目录

1. 概述
2. 工作流程
3. 参数与配置
4. 异常处理
5. 检查点
6. 资源引用

## 概述
本Skill用于特定任务的自动化执行。

> 自动优化：{action}
""",
        "actual_performance": f"""
## 效果验证

### 测试场景
1. 典型使用场景：用户按常规方式调用
2. 边界场景：输入不完整或异常
3. 性能场景：大量输入或复杂请求

### 预期效果
- 输出应准确完成用户意图
- 相比无Skill的baseline应有明显质量提升
- 不应引入过度冗余或跑偏

> 自动优化：{action}
""",
    }
    patch = improvements.get(dim, f"\n> 自动优化：{action}\n")
    if len(body) > 100 and not body.endswith("\n"):
        body += "\n"
    new_body = body + patch
    size_ratio = len(new_body) / max(len(body), 1)
    if size_ratio > 1.5:
        patch = f"\n> 自动优化：{action}\n"
        new_body = body + patch
    return f"---\n{fm_str}---\n\n{new_body}"


@router.post("/evolve-all", summary="全量进化所有Skill")
async def evolve_all(max_rounds: int = Query(3, ge=1, le=10)):
    skills = _scan_skills()
    eligible = [s for s in skills if s["has_skill_md"]]
    if not eligible:
        return {"message": "没有可进化的Skill", "results": []}
    results = []
    for skill_info in eligible:
        name = skill_info["name"]
        content = _read_skill_content(name)
        if content is None:
            continue
        scores, _ = evaluate_skill(content)
        req = OptimizeRequest(skill_name=name, max_rounds=max_rounds, dry_run=True)
        result = await evolve_skill(req)
        results.append(result)
    return {
        "total_skills": len(eligible),
        "evolved": len(results),
        "results": results,
    }


@router.get("/history", summary="获取进化历史")
async def evolution_history(
    skill_name: Optional[str] = Query(None, description="过滤指定Skill"),
    limit: int = Query(100, ge=1, le=500),
):
    records = _read_results_tsv()
    if skill_name:
        records = [r for r in records if r["skill_name"] == skill_name]
    records = records[-limit:]
    return {"total": len(records), "records": records}


@router.get("/history/summary", summary="获取进化历史汇总")
async def evolution_summary():
    records = _read_results_tsv()
    if not records:
        return {"total_experiments": 0, "kept": 0, "reverted": 0, "skills_affected": []}
    kept = sum(1 for r in records if r["status"] == "keep")
    reverted = sum(1 for r in records if r["status"] == "revert")
    skills = set(r["skill_name"] for r in records)
    skill_stats = {}
    for s in skills:
        s_records = [r for r in records if r["skill_name"] == s]
        first_score = None
        last_score = None
        for r in s_records:
            try:
                score = float(r["new_score"])
                if first_score is None:
                    first_score = score
                last_score = score
            except (ValueError, TypeError):
                pass
        skill_stats[s] = {
            "experiments": len(s_records),
            "first_score": first_score,
            "last_score": last_score,
            "delta": round(last_score - first_score, 1) if first_score is not None and last_score is not None else 0,
        }
    return {
        "total_experiments": len(records),
        "kept": kept,
        "reverted": reverted,
        "keep_rate": round(kept / max(len(records), 1) * 100, 1),
        "skills_affected": list(skills),
        "skill_stats": skill_stats,
    }


@router.post("/skills/{skill_name}/rewrite", summary="探索性重写Skill")
async def rewrite_skill(skill_name: str):
    content = _read_skill_content(skill_name)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' 不存在")
    old_scores, _ = evaluate_skill(content)
    _ensure_git_repo()
    _git_run(["stash", "-m", f"pre-rewrite-{skill_name}"], str(_SKILLS_ROOT))
    fm = _parse_frontmatter(content)
    fm_str = ""
    for k, v in fm.items():
        fm_str += f"{k}: {v}\n"
    if not fm_str:
        fm_str = f"name: {skill_name}\ndescription: Optimized skill\n"
    rewritten = f"""---
{fm_str}---

# {skill_name}

## 概述
本Skill经过达尔文引擎探索性重写，重新组织了结构和表达方式。

## 工作流程

### Phase 1: 初始化
1. 读取用户需求
2. 确认执行范围
   - 输入：用户请求
   - 输出：确认的执行计划

### Phase 2: 执行
1. 按步骤执行核心逻辑
2. 记录中间结果
   - 输入：执行计划
   - 输出：执行结果

### Phase 3: 验证与输出
1. 验证结果完整性
2. 输出最终结果
   - 输入：执行结果
   - 输出：最终输出

## 参数与配置

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input | string | 是 | - | 用户输入 |

## 异常处理
- 输入无效 → 提示用户重新输入
- 执行失败 → 回退到安全状态
- 超时 → 保存进度，允许恢复

## 检查点
- ⚠️ 关键决策前暂停确认
- ⚠️ 结果确认后再结束

## 资源引用
- 无额外依赖
"""
    new_scores, new_notes = evaluate_skill(rewritten)
    if new_scores.total > old_scores.total:
        _save_skill_content(skill_name, rewritten)
        _git_run(["add", f"{skill_name}/SKILL.md"], str(_SKILLS_ROOT))
        _git_run(["commit", "-m", f"rewrite skill: {skill_name}"], str(_SKILLS_ROOT))
        record = EvolutionRecord(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            skill_name=skill_name,
            old_score=old_scores.total,
            new_score=new_scores.total,
            status="keep",
            dimension="rewrite",
            note="探索性重写，分数提升",
            eval_mode="dry_run",
            commit="-",
        )
        _append_results_tsv(record)
        return {
            "skill_name": skill_name,
            "status": "keep",
            "old_score": old_scores.total,
            "new_score": new_scores.total,
            "delta": round(new_scores.total - old_scores.total, 1),
            "message": f"重写成功，分数提升 {old_scores.total} → {new_scores.total}",
        }
    else:
        rc, output = _git_run(["stash", "pop"], str(_SKILLS_ROOT))
        record = EvolutionRecord(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            skill_name=skill_name,
            old_score=old_scores.total,
            new_score=new_scores.total,
            status="revert",
            dimension="rewrite",
            note="探索性重写，分数未提升，已恢复",
            eval_mode="dry_run",
            commit="-",
        )
        _append_results_tsv(record)
        return {
            "skill_name": skill_name,
            "status": "revert",
            "old_score": old_scores.total,
            "new_score": new_scores.total,
            "delta": round(new_scores.total - old_scores.total, 1),
            "message": f"重写未提升分数，已恢复原版本",
        }


@router.get("/darwin-skill/source", summary="获取达尔文Skill原始SKILL.md")
async def get_darwin_skill_source():
    skill_md = _DARWIN_ROOT / "SKILL.md"
    if not skill_md.is_file():
        raise HTTPException(status_code=404, detail="达尔文Skill源文件不存在")
    content = skill_md.read_text(encoding="utf-8")
    return {"content": content, "length": len(content)}


@router.get("/darwin-skill/templates", summary="获取达尔文成果卡片模板列表")
async def get_darwin_templates():
    templates_dir = _DARWIN_ROOT / "templates"
    if not templates_dir.is_dir():
        return {"templates": []}
    templates = []
    for f in sorted(templates_dir.iterdir()):
        if f.is_file():
            templates.append({
                "name": f.name,
                "size": f.stat().st_size,
            })
    return {"templates": templates}


@router.get("/darwin-skill/template/{name}", summary="获取达尔文成果卡片模板内容")
async def get_darwin_template(name: str):
    fpath = _DARWIN_ROOT / "templates" / name
    if not fpath.is_file():
        raise HTTPException(status_code=404, detail="模板文件不存在")
    if not str(fpath.resolve()).startswith(str(_DARWIN_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    content = fpath.read_text(encoding="utf-8")
    return {"name": name, "content": content}
