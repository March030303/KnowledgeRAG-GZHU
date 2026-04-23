import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orchestrator")

_INTEGRATIONS_AVAILABLE = {}
_INTEGRATION_ROUTERS = {}

try:
    from integrations.ui_resources import (
        _GALAXY_AVAILABLE, _ART_DESIGN_PRO_AVAILABLE,
        _build_galaxy_index, _build_art_component_index,
        _build_art_style_index, _build_art_hook_index,
        _safe_read_file, _GALAXY_ROOT, _ART_DESIGN_PRO_ROOT,
    )
    _INTEGRATIONS_AVAILABLE["galaxy"] = _GALAXY_AVAILABLE
    _INTEGRATIONS_AVAILABLE["art_design_pro"] = _ART_DESIGN_PRO_AVAILABLE
except ImportError:
    _INTEGRATIONS_AVAILABLE["galaxy"] = False
    _INTEGRATIONS_AVAILABLE["art_design_pro"] = False

try:
    from integrations.darwin_engine import (
        _DARWIN_AVAILABLE, _SKILLS_ROOT, evaluate_skill,
        _scan_skills, _generate_improvement_suggestion, RUBRIC,
    )
    _INTEGRATIONS_AVAILABLE["darwin"] = _DARWIN_AVAILABLE
except ImportError:
    _INTEGRATIONS_AVAILABLE["darwin"] = False

try:
    from integrations.openmythos_engine import (
        _OPENMYTHOS_AVAILABLE, _TORCH_AVAILABLE, _MYTHOS_MODULE_AVAILABLE,
        _VARIANT_FUNCS,
    )
    _INTEGRATIONS_AVAILABLE["openmythos"] = _OPENMYTHOS_AVAILABLE
except ImportError:
    _INTEGRATIONS_AVAILABLE["openmythos"] = False

try:
    from integrations.manop_engine import _MANOP_AVAILABLE, _is_macos, _has_apple_silicon
    _INTEGRATIONS_AVAILABLE["manop"] = _MANOP_AVAILABLE
except ImportError:
    _INTEGRATIONS_AVAILABLE["manop"] = False

try:
    from integrations.apifox_engine import (
        _APIFOX_AVAILABLE, _get_all_endpoints, _load_collections,
    )
    _INTEGRATIONS_AVAILABLE["apifox"] = _APIFOX_AVAILABLE
except ImportError:
    _INTEGRATIONS_AVAILABLE["apifox"] = False

try:
    from integrations.hermes_engine import (
        _HERMES_AVAILABLE, _load_skills, _load_soul, _load_config,
    )
    _INTEGRATIONS_AVAILABLE["hermes"] = _HERMES_AVAILABLE
except ImportError:
    _INTEGRATIONS_AVAILABLE["hermes"] = False

_OBSIDIAN_DIR = Path(__file__).resolve().parent.parent / "local-KLB-files" / "obsidian-sync"
_INTEGRATIONS_AVAILABLE["obsidian"] = _OBSIDIAN_DIR.is_dir()

_TASK_LOG_DIR = Path(__file__).resolve().parent.parent / "orchestrator_logs"
_TASK_LOG_DIR.mkdir(parents=True, exist_ok=True)


class TaskAugmentRequest(BaseModel):
    task_description: str
    task_type: str = "general"
    context: Optional[Dict[str, Any]] = None


class SkillRegisterRequest(BaseModel):
    name: str
    content: str
    category: str = "auto-generated"


def _detect_task_domains(task_description: str) -> List[str]:
    domains = []
    desc_lower = task_description.lower()
    frontend_kws = [
        "前端", "页面", "组件", "ui", "vue", "css", "样式", "按钮", "表单", "布局",
        "frontend", "component", "style", "button", "form", "layout", "sidebar",
        "导航", "卡片", "对话框", "模态", "动画", "交互", "主题", "暗色", "黑金",
    ]
    backend_kws = [
        "后端", "api", "接口", "数据库", "模型", "路由", "fastapi", "python",
        "backend", "endpoint", "database", "model", "router", "crud", "auth",
    ]
    rag_kws = [
        "rag", "检索", "向量", "嵌入", "知识库", "分块", "重排", "rerank",
        "retrieval", "embedding", "vector", "chunk", "knowledge", "hybrid",
    ]
    devops_kws = [
        "部署", "docker", "容器", "监控", "运维", "健康检查", "日志",
        "deploy", "container", "monitoring", "devops", "redis", "mysql",
    ]
    design_kws = [
        "设计", "风格", "配色", "主题", "视觉", "动画", "交互", "用户体验",
        "design", "theme", "color", "animation", "ux", "dark mode", "gold",
    ]
    agent_kws = [
        "agent", "智能体", "自动化", "gui", "截图", "点击", "操作",
        "automation", "click", "screenshot", "workflow",
    ]
    if any(kw in desc_lower for kw in frontend_kws):
        domains.append("frontend")
    if any(kw in desc_lower for kw in backend_kws):
        domains.append("backend")
    if any(kw in desc_lower for kw in rag_kws):
        domains.append("rag")
    if any(kw in desc_lower for kw in devops_kws):
        domains.append("devops")
    if any(kw in desc_lower for kw in design_kws):
        domains.append("design")
    if any(kw in desc_lower for kw in agent_kws):
        domains.append("agent")
    if not domains:
        domains.append("general")
    return domains


def _gather_ui_resources(task_description: str, domains: List[str]) -> Dict[str, Any]:
    result = {"available": False, "galaxy_suggestions": [], "art_component_suggestions": [], "art_style_suggestions": []}
    if "frontend" not in domains and "design" not in domains:
        return result
    result["available"] = True
    if _INTEGRATIONS_AVAILABLE.get("galaxy"):
        try:
            index = _build_galaxy_index()
            desc_lower = task_description.lower()
            relevant_cats = []
            cat_keywords = {
                "Buttons": ["按钮", "button", "点击", "click", "提交", "submit"],
                "Cards": ["卡片", "card", "信息卡", "展示", "profile"],
                "Inputs": ["输入", "input", "表单", "form", "搜索", "search"],
                "Forms": ["表单", "form", "登录", "注册", "login"],
                "Loaders": ["加载", "loader", "loading", "进度", "spinner"],
                "Toggle-switches": ["开关", "toggle", "切换", "switch"],
                "Checkboxes": ["复选", "checkbox", "选择", "check"],
                "Tooltips": ["提示", "tooltip", "悬浮", "hint"],
                "Notifications": ["通知", "notification", "消息", "alert", "toast"],
                "Patterns": ["背景", "pattern", "纹理", "texture", "装饰"],
                "Radio-buttons": ["单选", "radio", "选项"],
            }
            for cat, kws in cat_keywords.items():
                if any(kw in desc_lower for kw in kws):
                    if cat in index:
                        relevant_cats.append(cat)
            if not relevant_cats:
                for cat in ["Buttons", "Cards", "Inputs", "Loaders"]:
                    if cat in index:
                        relevant_cats.append(cat)
            for cat in relevant_cats[:3]:
                files = index[cat]
                sample = files[:3]
                result["galaxy_suggestions"].append({
                    "category": cat,
                    "total_count": len(files),
                    "sample_files": sample,
                    "access_endpoint": f"/api/ui-resources/galaxy/component/{cat}",
                })
        except Exception as e:
            result["galaxy_suggestions"] = [{"error": str(e)}]
    if _INTEGRATIONS_AVAILABLE.get("art_design_pro"):
        try:
            components = _build_art_component_index()
            styles = _build_art_style_index()
            hooks = _build_art_hook_index()
            desc_lower = task_description.lower()
            relevant_comps = []
            comp_keywords = {
                "cards": ["卡片", "card"],
                "charts": ["图表", "chart", "数据可视化"],
                "forms": ["表单", "form"],
                "layouts": ["布局", "layout"],
                "tables": ["表格", "table"],
            }
            for comp in components:
                group = comp["group"].lower()
                for cat, kws in comp_keywords.items():
                    if any(kw in desc_lower for kw in kws) and cat in group:
                        relevant_comps.append(comp)
                        break
            if not relevant_comps:
                relevant_comps = components[:5]
            result["art_component_suggestions"] = [
                {"name": c["name"], "group": c["group"], "path": c["path"]}
                for c in relevant_comps[:5]
            ]
            result["art_style_suggestions"] = [
                {"name": s["name"], "path": s["path"]}
                for s in styles[:5]
            ]
        except Exception as e:
            result["art_component_suggestions"] = [{"error": str(e)}]
    return result


def _gather_hermes_context(domains: List[str]) -> Dict[str, Any]:
    result = {"available": False, "skills": [], "relevant_context": []}
    if not _INTEGRATIONS_AVAILABLE.get("hermes"):
        return result
    result["available"] = True
    try:
        skills = _load_skills()
        result["skills"] = [
            {"name": s["name"], "category": s["category"], "description": s["description"]}
            for s in skills
        ]
        domain_to_category = {
            "rag": "rag",
            "frontend": "fullstack",
            "backend": "fullstack",
            "devops": "devops",
        }
        for domain in domains:
            cat = domain_to_category.get(domain)
            if cat:
                matching = [s for s in skills if s["category"] == cat]
                for s in matching:
                    skill_path = Path(r"C:\Users\ASUS\.hermes") / "skills" / s["path"]
                    if skill_path.is_file():
                        content = skill_path.read_text(encoding="utf-8")
                        result["relevant_context"].append({
                            "skill_name": s["name"],
                            "category": s["category"],
                            "content_preview": content[:2000],
                            "full_access_endpoint": f"/api/hermes/skills/{s['category']}/{s['name']}",
                        })
    except Exception as e:
        result["skills"] = [{"error": str(e)}]
    return result


def _gather_apifox_context(domains: List[str]) -> Dict[str, Any]:
    result = {"available": False, "relevant_endpoints": [], "total_endpoints": 0}
    if not _INTEGRATIONS_AVAILABLE.get("apifox"):
        return result
    if "backend" not in domains and "rag" not in domains:
        return result
    result["available"] = True
    try:
        endpoints = _get_all_endpoints()
        result["total_endpoints"] = len(endpoints)
        desc_keywords = set()
        for d in domains:
            desc_keywords.add(d)
        relevant = []
        for ep in endpoints:
            path = ep.get("path", "").lower()
            name = ep.get("name", "").lower()
            for kw in desc_keywords:
                if kw in path or kw in name:
                    relevant.append(ep)
                    break
        if not relevant:
            relevant = endpoints[:10]
        result["relevant_endpoints"] = [
            {
                "name": ep.get("name", ""),
                "method": ep.get("method", ""),
                "path": ep.get("path", ""),
                "description": ep.get("description", ""),
            }
            for ep in relevant[:15]
        ]
    except Exception as e:
        result["relevant_endpoints"] = [{"error": str(e)}]
    return result


def _gather_darwin_context() -> Dict[str, Any]:
    result = {"available": False, "registered_skills": [], "rubric_dimensions": []}
    if not _INTEGRATIONS_AVAILABLE.get("darwin"):
        return result
    result["available"] = True
    try:
        skills = _scan_skills()
        result["registered_skills"] = [
            {"name": s["name"], "has_skill_md": s["has_skill_md"]}
            for s in skills
        ]
        result["rubric_dimensions"] = [
            {"id": dim, "name": info["name"], "weight": info["weight"], "category": info["category"]}
            for dim, info in RUBRIC.items()
        ]
    except Exception as e:
        result["registered_skills"] = [{"error": str(e)}]
    return result


def _gather_obsidian_context() -> Dict[str, Any]:
    result = {"available": False, "notes_count": 0, "sample_notes": []}
    if not _INTEGRATIONS_AVAILABLE.get("obsidian"):
        return result
    result["available"] = True
    try:
        md_files = list(_OBSIDIAN_DIR.rglob("*.md"))
        result["notes_count"] = len(md_files)
        for f in md_files[:5]:
            content = f.read_text(encoding="utf-8", errors="replace")
            result["sample_notes"].append({
                "name": f.name,
                "preview": content[:300],
            })
    except Exception as e:
        result["sample_notes"] = [{"error": str(e)}]
    return result


def _generate_task_strategy(task_description: str, domains: List[str], augmented: Dict) -> Dict[str, Any]:
    strategy = {
        "recommended_approach": [],
        "resource_priorities": [],
        "estimated_complexity": "medium",
        "key_references": [],
    }
    if "frontend" in domains or "design" in domains:
        strategy["recommended_approach"].extend([
            "1. 从Galaxy检索匹配的UI组件（按钮/卡片/输入框等）",
            "2. 从Art Design Pro获取Vue3组件模板和样式系统",
            "3. 使用Darwin引擎评估并优化生成的SKILL",
            "4. 参考Hermes全栈开发技能中的前端架构指南",
        ])
        strategy["resource_priorities"].extend(["galaxy", "art_design_pro", "hermes", "darwin"])
    if "backend" in domains:
        strategy["recommended_approach"].extend([
            "1. 从Apifox获取现有API端点定义作为参考",
            "2. 参考Hermes全栈开发技能中的后端架构指南",
            "3. 使用Darwin引擎优化后端处理SKILL",
        ])
        strategy["resource_priorities"].extend(["apifox", "hermes", "darwin"])
    if "rag" in domains:
        strategy["recommended_approach"].extend([
            "1. 从Hermes RAG技能获取管线架构指南",
            "2. 参考Obsidian记忆中的相关笔记",
            "3. 从Apifox获取RAG相关API端点",
        ])
        strategy["resource_priorities"].extend(["hermes", "obsidian", "apifox"])
    if "devops" in domains:
        strategy["recommended_approach"].extend([
            "1. 从Hermes DevOps技能获取部署指南",
            "2. 使用Mano-P进行GUI自动化验证",
        ])
        strategy["resource_priorities"].extend(["hermes", "manop"])
    if "agent" in domains:
        strategy["recommended_approach"].extend([
            "1. 使用Mano-P的CUA技能进行GUI自动化",
            "2. 使用OpenMythos进行高级推理（如可用）",
        ])
        strategy["resource_priorities"].extend(["manop", "openmythos"])
    if not strategy["recommended_approach"]:
        strategy["recommended_approach"] = [
            "1. 从Hermes获取相关领域技能上下文",
            "2. 从Galaxy/Art Design Pro获取UI资源",
            "3. 从Apifox获取API参考",
            "4. 使用Darwin引擎优化工作流SKILL",
        ]
        strategy["resource_priorities"] = ["hermes", "galaxy", "apifox", "darwin"]
    desc_len = len(task_description)
    if desc_len < 50:
        strategy["estimated_complexity"] = "low"
    elif desc_len > 200 or len(domains) > 3:
        strategy["estimated_complexity"] = "high"
    for source, data in augmented.get("sources", {}).items():
        if isinstance(data, dict) and data.get("available"):
            strategy["key_references"].append(source)
    return strategy


# ==================== API Endpoints ====================

@router.get("/status", summary="获取任务编排引擎状态")
async def orchestrator_status():
    return {
        "integrations": _INTEGRATIONS_AVAILABLE,
        "total_integrations": len(_INTEGRATIONS_AVAILABLE),
        "active_integrations": sum(1 for v in _INTEGRATIONS_AVAILABLE.values() if v),
        "orchestrator_version": "1.0.0",
    }


@router.post("/augment", summary="任务增强：根据任务描述自动聚合所有集成资源")
async def augment_task(req: TaskAugmentRequest):
    domains = _detect_task_domains(req.task_description)
    ui_resources = _gather_ui_resources(req.task_description, domains)
    hermes_context = _gather_hermes_context(domains)
    apifox_context = _gather_apifox_context(domains)
    darwin_context = _gather_darwin_context()
    obsidian_context = _gather_obsidian_context()
    augmented = {
        "task_description": req.task_description,
        "detected_domains": domains,
        "task_type": req.task_type,
        "timestamp": datetime.now().isoformat(),
        "sources": {
            "galaxy_art_design_pro": ui_resources,
            "hermes": hermes_context,
            "apifox": apifox_context,
            "darwin": darwin_context,
            "obsidian": obsidian_context,
            "openmythos": {"available": _INTEGRATIONS_AVAILABLE.get("openmythos", False)},
            "manop": {"available": _INTEGRATIONS_AVAILABLE.get("manop", False)},
        },
    }
    strategy = _generate_task_strategy(req.task_description, domains, augmented)
    augmented["strategy"] = strategy
    log_path = _TASK_LOG_DIR / f"augment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path.write_text(json.dumps(augmented, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return augmented


@router.post("/augment/quick", summary="快速任务增强：仅返回关键资源摘要")
async def quick_augment(task_description: str):
    domains = _detect_task_domains(task_description)
    result = {
        "domains": domains,
        "ui_resources_available": _INTEGRATIONS_AVAILABLE.get("galaxy", False) or _INTEGRATIONS_AVAILABLE.get("art_design_pro", False),
        "hermes_skills_available": _INTEGRATIONS_AVAILABLE.get("hermes", False),
        "apifox_docs_available": _INTEGRATIONS_AVAILABLE.get("apifox", False),
        "darwin_engine_available": _INTEGRATIONS_AVAILABLE.get("darwin", False),
        "obsidian_memory_available": _INTEGRATIONS_AVAILABLE.get("obsidian", False),
        "recommended_endpoints": [],
    }
    if _INTEGRATIONS_AVAILABLE.get("hermes"):
        try:
            skills = _load_skills()
            domain_map = {"rag": "rag", "frontend": "fullstack", "backend": "fullstack", "devops": "devops"}
            for d in domains:
                cat = domain_map.get(d)
                if cat:
                    matching = [s for s in skills if s["category"] == cat]
                    for s in matching[:2]:
                        result["recommended_endpoints"].append(
                            f"/api/hermes/skills/{s['category']}/{s['name']}"
                        )
        except Exception:
            pass
    if _INTEGRATIONS_AVAILABLE.get("apifox") and ("backend" in domains or "rag" in domains):
        result["recommended_endpoints"].append("/api/apifox/endpoints")
    if ("frontend" in domains or "design" in domains):
        result["recommended_endpoints"].extend([
            "/api/ui-resources/galaxy/categories",
            "/api/ui-resources/art-design-pro/components",
        ])
    return result


@router.get("/domains", summary="获取任务域检测关键词映射")
async def get_domain_keywords():
    return {
        "frontend": ["前端", "页面", "组件", "ui", "vue", "css", "样式", "按钮", "表单", "布局", "sidebar", "card", "button"],
        "backend": ["后端", "api", "接口", "数据库", "模型", "路由", "fastapi", "python", "crud"],
        "rag": ["rag", "检索", "向量", "嵌入", "知识库", "分块", "重排", "rerank", "retrieval", "embedding"],
        "devops": ["部署", "docker", "容器", "监控", "运维", "健康检查", "deploy", "devops"],
        "design": ["设计", "风格", "配色", "主题", "视觉", "动画", "交互", "design", "theme", "dark mode"],
        "agent": ["agent", "智能体", "自动化", "gui", "截图", "automation", "workflow"],
    }


@router.post("/skill/auto-register", summary="自动将任务经验注册为Darwin Skill")
async def auto_register_skill(req: SkillRegisterRequest):
    if not _INTEGRATIONS_AVAILABLE.get("darwin"):
        raise HTTPException(status_code=503, detail="Darwin引擎不可用")
    try:
        from integrations.darwin_engine import _save_skill_content, _ensure_git_repo, _git_run, evaluate_skill, EvolutionRecord, _append_results_tsv
        safe_name = re.sub(r"[^\w\-]", "_", req.name)
        skill_dir = _SKILLS_ROOT / safe_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            content = req.content
            if not content.startswith("---"):
                fm = f"""---
name: {safe_name}
version: 1.0.0
description: Auto-generated skill for {req.category}
tags: [{req.category}, auto-generated]
---

"""
                content = fm + content
            skill_md.write_text(content, encoding="utf-8")
            scores, notes = evaluate_skill(content)
            _ensure_git_repo()
            _git_run(["add", f"{safe_name}/SKILL.md"], str(_SKILLS_ROOT))
            _git_run(["commit", "-m", f"auto-register skill: {safe_name}"], str(_SKILLS_ROOT))
            record = EvolutionRecord(
                timestamp=datetime.now().isoformat(timespec="seconds"),
                skill_name=safe_name,
                old_score=0,
                new_score=scores.total,
                status="register",
                dimension="-",
                note=f"自动注册 via orchestrator ({req.category})",
                eval_mode="auto",
                commit="-",
            )
            _append_results_tsv(record)
            return {
                "name": safe_name,
                "scores": scores.to_dict(),
                "message": f"Skill '{safe_name}' 自动注册成功，评分: {scores.total}",
            }
        return {"name": safe_name, "message": "Skill已存在，跳过注册"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"自动注册失败: {str(e)}")


@router.get("/context/{domain}", summary="获取指定域的完整增强上下文")
async def get_domain_context(domain: str):
    domain_map = {
        "rag": ["rag"],
        "frontend": ["frontend", "design"],
        "backend": ["backend"],
        "devops": ["devops"],
        "design": ["design", "frontend"],
        "agent": ["agent"],
    }
    domains = domain_map.get(domain, [domain])
    context = {
        "domain": domain,
        "hermes": _gather_hermes_context(domains),
        "apifox": _gather_apifox_context(domains),
        "ui_resources": _gather_ui_resources(f"task about {domain}", domains),
        "darwin": _gather_darwin_context(),
        "obsidian": _gather_obsidian_context(),
    }
    return context


@router.get("/logs", summary="获取编排引擎任务日志")
async def list_logs(limit: int = Query(20, ge=1, le=100)):
    logs = []
    for f in sorted(_TASK_LOG_DIR.glob("*.json"), reverse=True)[:limit]:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            logs.append({
                "filename": f.name,
                "task_description": data.get("task_description", "")[:100],
                "domains": data.get("detected_domains", []),
                "timestamp": data.get("timestamp", ""),
            })
        except Exception:
            pass
    return {"logs": logs, "total": len(logs)}


@router.get("/integration-matrix", summary="获取集成资源矩阵")
async def get_integration_matrix():
    matrix = {
        "galaxy": {
            "available": _INTEGRATIONS_AVAILABLE.get("galaxy", False),
            "type": "UI组件库",
            "scope": "前端",
            "resources": "4802个HTML/CSS组件",
            "best_for": ["按钮", "卡片", "加载器", "输入框", "表单", "开关"],
        },
        "art_design_pro": {
            "available": _INTEGRATIONS_AVAILABLE.get("art_design_pro", False),
            "type": "Vue3设计系统",
            "scope": "前端",
            "resources": "Vue3组件 + SCSS样式 + Hooks",
            "best_for": ["管理后台", "数据可视化", "表单", "布局", "主题"],
        },
        "darwin": {
            "available": _INTEGRATIONS_AVAILABLE.get("darwin", False),
            "type": "Skill进化引擎",
            "scope": "全栈",
            "resources": "8维度评分 + 棘轮机制 + 自动优化",
            "best_for": ["Skill质量评估", "工作流优化", "自动改进"],
        },
        "openmythos": {
            "available": _INTEGRATIONS_AVAILABLE.get("openmythos", False),
            "type": "RDT模型引擎",
            "scope": "AI推理",
            "resources": "1B-1T参数变体 + 循环深度Transformer",
            "best_for": ["高级推理", "自适应计算", "长上下文"],
        },
        "manop": {
            "available": _INTEGRATIONS_AVAILABLE.get("manop", False),
            "type": "GUI智能体",
            "scope": "自动化",
            "resources": "CUA技能 + 截图 + 鼠标键盘操作",
            "best_for": ["GUI自动化", "数据采集", "流程自动化"],
        },
        "apifox": {
            "available": _INTEGRATIONS_AVAILABLE.get("apifox", False),
            "type": "API文档引擎",
            "scope": "后端",
            "resources": "API集合 + 端点定义 + 环境配置",
            "best_for": ["API参考", "接口设计", "端点查询"],
        },
        "hermes": {
            "available": _INTEGRATIONS_AVAILABLE.get("hermes", False),
            "type": "Agent技能引擎",
            "scope": "全栈",
            "resources": "RAG/全栈/DevOps技能 + SOUL人格 + 配置",
            "best_for": ["领域知识", "开发指南", "部署参考"],
        },
        "obsidian": {
            "available": _INTEGRATIONS_AVAILABLE.get("obsidian", False),
            "type": "无限记忆",
            "scope": "知识管理",
            "resources": "Obsidian笔记 + 自动同步",
            "best_for": ["上下文记忆", "笔记检索", "知识关联"],
        },
    }
    return {"matrix": matrix, "total": len(matrix)}
