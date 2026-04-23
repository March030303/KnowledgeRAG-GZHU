import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hermes")

_HERMES_ROOT = Path(r"C:\Users\ASUS\.hermes")
_HERMES_AVAILABLE = _HERMES_ROOT.is_dir()

_skills_cache: Optional[List[Dict]] = None
_config_cache: Optional[Dict] = None


def _parse_frontmatter(content: str) -> Dict[str, Any]:
    fm = {}
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if match:
        for line in match.group(1).strip().split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                val = val.strip()
                if val.startswith("[") and val.endswith("]"):
                    try:
                        val = json.loads(val.replace("'", '"'))
                    except Exception:
                        val = [v.strip().strip("'\"") for v in val[1:-1].split(",")]
                fm[key.strip()] = val
    return fm


def _load_skills() -> List[Dict]:
    global _skills_cache
    if _skills_cache is not None:
        return _skills_cache
    skills = []
    if not _HERMES_AVAILABLE:
        _skills_cache = skills
        return skills
    skills_dir = _HERMES_ROOT / "skills"
    if not skills_dir.is_dir():
        _skills_cache = skills
        return skills
    for skill_path in sorted(skills_dir.rglob("SKILL.md")):
        try:
            content = skill_path.read_text(encoding="utf-8")
            fm = _parse_frontmatter(content)
            rel = skill_path.relative_to(skills_dir)
            parts = rel.parts
            category = parts[0] if len(parts) > 1 else "uncategorized"
            name = fm.get("name", skill_path.parent.name)
            skills.append({
                "name": name,
                "category": category,
                "version": fm.get("version", "1.0.0"),
                "description": fm.get("description", ""),
                "tags": fm.get("tags", []),
                "path": str(rel).replace("\\", "/"),
                "content_length": len(content),
                "frontmatter": fm,
            })
        except Exception as e:
            logger.warning(f"加载Hermes Skill失败: {e}")
    _skills_cache = skills
    return skills


def _load_config() -> Dict:
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    config = {}
    if not _HERMES_AVAILABLE:
        _config_cache = config
        return config
    config_path = _HERMES_ROOT / "config.yaml"
    if config_path.is_file():
        try:
            content = config_path.read_text(encoding="utf-8")
            current_section = None
            for line in content.split("\n"):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if line.startswith("  ") or line.startswith("\t"):
                    if current_section:
                        if ":" in stripped:
                            k, v = stripped.split(":", 1)
                            k = k.strip()
                            v = v.strip()
                            if v.startswith('"') and v.endswith('"'):
                                v = v[1:-1]
                            elif v.lower() == "true":
                                v = True
                            elif v.lower() == "false":
                                v = False
                            elif v.isdigit():
                                v = int(v)
                            if isinstance(config.get(current_section), dict):
                                config[current_section][k] = v
                            else:
                                config[current_section] = {k: v}
                elif ":" in stripped and not stripped.startswith(" "):
                    k, v = stripped.split(":", 1)
                    k = k.strip()
                    v = v.strip()
                    if not v:
                        current_section = k
                        config[k] = {}
                    else:
                        if v.startswith('"') and v.endswith('"'):
                            v = v[1:-1]
                        elif v.lower() == "true":
                            v = True
                        elif v.lower() == "false":
                            v = False
                        config[k] = v
                        current_section = None
        except Exception as e:
            logger.warning(f"加载Hermes配置失败: {e}")
    _config_cache = config
    return config


def _load_soul() -> str:
    if not _HERMES_AVAILABLE:
        return ""
    soul_path = _HERMES_ROOT / "SOUL.md"
    if soul_path.is_file():
        return soul_path.read_text(encoding="utf-8")
    return ""


def _load_sessions() -> List[Dict]:
    sessions = []
    if not _HERMES_AVAILABLE:
        return sessions
    sessions_dir = _HERMES_ROOT / "sessions"
    if not sessions_dir.is_dir():
        return sessions
    for f in sorted(sessions_dir.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sessions.append({
                "filename": f.name,
                "message_count": len(data.get("messages", [])),
                "created_at": data.get("created_at", ""),
                "model": data.get("model", ""),
            })
        except Exception:
            pass
    return sessions


# ==================== API Endpoints ====================

@router.get("/status", summary="获取Hermes Agent集成状态")
async def hermes_status():
    skills = _load_skills()
    config = _load_config()
    categories = sorted(set(s["category"] for s in skills))
    return {
        "available": _HERMES_AVAILABLE,
        "root": str(_HERMES_ROOT),
        "soul_loaded": bool(_load_soul()),
        "skills_count": len(skills),
        "skill_categories": categories,
        "model": config.get("model", {}),
        "tools_enabled": config.get("tools", {}),
    }


@router.get("/soul", summary="获取Hermes Agent SOUL.md")
async def get_soul():
    content = _load_soul()
    if not content:
        raise HTTPException(status_code=404, detail="SOUL.md 不存在")
    return {"content": content, "length": len(content)}


@router.get("/config", summary="获取Hermes Agent配置")
async def get_config():
    config = _load_config()
    safe_config = {k: v for k, v in config.items() if k not in ("api_key",)}
    if "custom_providers" in safe_config:
        for provider in safe_config["custom_providers"]:
            if isinstance(provider, dict) and "api_key" in provider:
                provider["api_key"] = "***REDACTED***"
    return {"config": safe_config}


@router.get("/skills", summary="获取Hermes Agent技能列表")
async def list_skills(
    category: Optional[str] = Query(None, description="按分类过滤"),
    keyword: Optional[str] = Query(None, description="按关键词搜索"),
):
    skills = _load_skills()
    if category:
        skills = [s for s in skills if s["category"] == category]
    if keyword:
        kw = keyword.lower()
        skills = [
            s for s in skills
            if kw in s["name"].lower()
            or kw in s["description"].lower()
            or any(kw in str(t).lower() for t in s.get("tags", []))
        ]
    return {"skills": skills, "total": len(skills)}


@router.get("/skills/categories", summary="获取技能分类列表")
async def list_skill_categories():
    skills = _load_skills()
    categories = {}
    for s in skills:
        cat = s["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "name": s["name"],
            "description": s["description"],
            "tags": s.get("tags", []),
        })
    return {"categories": categories}


@router.get("/skills/{category}/{name}", summary="获取指定技能详情")
async def get_skill_detail(category: str, name: str):
    skills = _load_skills()
    for s in skills:
        if s["category"] == category and s["name"] == name:
            skill_path = _HERMES_ROOT / "skills" / s["path"]
            content = ""
            if skill_path.is_file():
                content = skill_path.read_text(encoding="utf-8")
            return {
                "name": s["name"],
                "category": s["category"],
                "version": s["version"],
                "description": s["description"],
                "tags": s.get("tags", []),
                "frontmatter": s["frontmatter"],
                "content": content,
            }
    raise HTTPException(status_code=404, detail=f"技能 '{category}/{name}' 不存在")


@router.get("/sessions", summary="获取Hermes Agent会话列表")
async def list_sessions():
    sessions = _load_sessions()
    return {"sessions": sessions, "total": len(sessions)}


@router.get("/sessions/{filename}", summary="获取指定会话详情")
async def get_session(filename: str):
    if not _HERMES_AVAILABLE:
        raise HTTPException(status_code=404, detail="Hermes 资源未找到")
    fpath = _HERMES_ROOT / "sessions" / filename
    if not fpath.is_file():
        raise HTTPException(status_code=404, detail="会话不存在")
    if not str(fpath.resolve()).startswith(str(_HERMES_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    content = fpath.read_text(encoding="utf-8")
    data = json.loads(content)
    return {"filename": filename, "data": data}


@router.get("/files", summary="获取Hermes Agent目录下所有文件")
async def list_files():
    if not _HERMES_AVAILABLE:
        raise HTTPException(status_code=404, detail="Hermes 资源未找到")
    files = []
    skip_dirs = {".git", "__pycache__", "node_modules", ".cache"}
    for f in sorted(_HERMES_ROOT.rglob("*")):
        if f.is_file() and not any(d in str(f) for d in skip_dirs):
            rel = f.relative_to(_HERMES_ROOT)
            files.append({
                "path": str(rel).replace("\\", "/"),
                "name": f.name,
                "size": f.stat().st_size,
                "suffix": f.suffix,
            })
    return {"files": files, "total": len(files)}


@router.get("/file/{path:path}", summary="获取Hermes Agent文件内容")
async def get_file(path: str):
    if not _HERMES_AVAILABLE:
        raise HTTPException(status_code=404, detail="Hermes 资源未找到")
    fpath = _HERMES_ROOT / path
    if not fpath.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not str(fpath.resolve()).startswith(str(_HERMES_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    content = fpath.read_text(encoding="utf-8", errors="replace")
    return {"path": path, "content": content, "size": len(content)}


@router.post("/reindex", summary="重建Hermes技能索引缓存")
async def reindex():
    global _skills_cache, _config_cache
    _skills_cache = None
    _config_cache = None
    _load_skills()
    _load_config()
    return {"message": "Hermes索引重建完成"}


@router.get("/rag-context", summary="获取Hermes RAG技能上下文（供RAG检索增强使用）")
async def get_rag_context():
    skills = _load_skills()
    rag_skills = [s for s in skills if s["category"] == "rag"]
    context_parts = []
    for s in rag_skills:
        skill_path = _HERMES_ROOT / "skills" / s["path"]
        if skill_path.is_file():
            content = skill_path.read_text(encoding="utf-8")
            context_parts.append({
                "skill_name": s["name"],
                "category": s["category"],
                "content": content,
                "tags": s.get("tags", []),
            })
    return {"rag_skills": context_parts, "total": len(context_parts)}


@router.get("/fullstack-context", summary="获取Hermes全栈开发技能上下文")
async def get_fullstack_context():
    skills = _load_skills()
    fs_skills = [s for s in skills if s["category"] == "fullstack"]
    context_parts = []
    for s in fs_skills:
        skill_path = _HERMES_ROOT / "skills" / s["path"]
        if skill_path.is_file():
            content = skill_path.read_text(encoding="utf-8")
            context_parts.append({
                "skill_name": s["name"],
                "category": s["category"],
                "content": content,
                "tags": s.get("tags", []),
            })
    return {"fullstack_skills": context_parts, "total": len(context_parts)}


@router.get("/devops-context", summary="获取Hermes DevOps技能上下文")
async def get_devops_context():
    skills = _load_skills()
    devops_skills = [s for s in skills if s["category"] == "devops"]
    context_parts = []
    for s in devops_skills:
        skill_path = _HERMES_ROOT / "skills" / s["path"]
        if skill_path.is_file():
            content = skill_path.read_text(encoding="utf-8")
            context_parts.append({
                "skill_name": s["name"],
                "category": s["category"],
                "content": content,
                "tags": s.get("tags", []),
            })
    return {"devops_skills": context_parts, "total": len(context_parts)}
