import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ui-resources")

_EXTERNAL_ROOT = Path(__file__).resolve().parent.parent / "external_resources"
_GALAXY_ROOT = _EXTERNAL_ROOT / "galaxy"
_ART_DESIGN_PRO_ROOT = _EXTERNAL_ROOT / "art-design-pro"

_GALAXY_AVAILABLE = _GALAXY_ROOT.is_dir()
_ART_DESIGN_PRO_AVAILABLE = _ART_DESIGN_PRO_ROOT.is_dir()

_GALAXY_INDEX: Optional[Dict[str, List[str]]] = None
_ART_COMPONENT_INDEX: Optional[List[Dict]] = None
_ART_STYLE_INDEX: Optional[List[Dict]] = None
_ART_HOOK_INDEX: Optional[List[Dict]] = None
_ART_CONFIG_INDEX: Optional[List[Dict]] = None


def _build_galaxy_index() -> Dict[str, List[str]]:
    global _GALAXY_INDEX
    if _GALAXY_INDEX is not None:
        return _GALAXY_INDEX
    index: Dict[str, List[str]] = {}
    if not _GALAXY_AVAILABLE:
        logger.warning("Galaxy 资源目录不存在")
        _GALAXY_INDEX = index
        return index
    for category_dir in sorted(_GALAXY_ROOT.iterdir()):
        if not category_dir.is_dir():
            continue
        files = sorted(
            f.name for f in category_dir.iterdir() if f.is_file() and f.suffix == ".html"
        )
        if files:
            index[category_dir.name] = files
    _GALAXY_INDEX = index
    logger.info(f"Galaxy 索引构建完成: {len(index)} 个分类, {sum(len(v) for v in index.values())} 个组件")
    return index


def _build_art_component_index() -> List[Dict]:
    global _ART_COMPONENT_INDEX
    if _ART_COMPONENT_INDEX is not None:
        return _ART_COMPONENT_INDEX
    components: List[Dict] = []
    if not _ART_DESIGN_PRO_AVAILABLE:
        logger.warning("Art Design Pro 资源目录不存在")
        _ART_COMPONENT_INDEX = components
        return components
    comp_root = _ART_DESIGN_PRO_ROOT / "src" / "components"
    if not comp_root.is_dir():
        _ART_COMPONENT_INDEX = components
        return components
    for group_dir in sorted(comp_root.iterdir()):
        if not group_dir.is_dir():
            continue
        group_name = group_dir.name
        for comp_dir in sorted(group_dir.iterdir()):
            if not comp_dir.is_dir():
                continue
            comp_name = comp_dir.name
            rel_path = comp_dir.relative_to(_ART_DESIGN_PRO_ROOT / "src")
            vue_files = list(comp_dir.rglob("*.vue"))
            ts_files = list(comp_dir.rglob("*.ts"))
            scss_files = list(comp_dir.rglob("*.scss"))
            components.append({
                "name": comp_name,
                "group": group_name,
                "path": str(rel_path).replace("\\", "/"),
                "vue_files": [str(f.relative_to(comp_dir)).replace("\\", "/") for f in vue_files],
                "ts_files": [str(f.relative_to(comp_dir)).replace("\\", "/") for f in ts_files],
                "scss_files": [str(f.relative_to(comp_dir)).replace("\\", "/") for f in scss_files],
            })
    _ART_COMPONENT_INDEX = components
    logger.info(f"Art Design Pro 组件索引构建完成: {len(components)} 个组件")
    return components


def _build_art_style_index() -> List[Dict]:
    global _ART_STYLE_INDEX
    if _ART_STYLE_INDEX is not None:
        return _ART_STYLE_INDEX
    styles: List[Dict] = []
    if not _ART_DESIGN_PRO_AVAILABLE:
        _ART_STYLE_INDEX = styles
        return styles
    style_root = _ART_DESIGN_PRO_ROOT / "src" / "assets" / "styles"
    if not style_root.is_dir():
        _ART_STYLE_INDEX = styles
        return styles
    for f in sorted(style_root.rglob("*")):
        if f.is_file() and f.suffix in (".scss", ".css"):
            rel_path = f.relative_to(_ART_DESIGN_PRO_ROOT / "src")
            styles.append({
                "name": f.name,
                "path": str(rel_path).replace("\\", "/"),
                "size": f.stat().st_size,
            })
    _ART_STYLE_INDEX = styles
    logger.info(f"Art Design Pro 样式索引构建完成: {len(styles)} 个文件")
    return styles


def _build_art_hook_index() -> List[Dict]:
    global _ART_HOOK_INDEX
    if _ART_HOOK_INDEX is not None:
        return _ART_HOOK_INDEX
    hooks: List[Dict] = []
    if not _ART_DESIGN_PRO_AVAILABLE:
        _ART_HOOK_INDEX = hooks
        return hooks
    hook_root = _ART_DESIGN_PRO_ROOT / "src" / "hooks"
    if not hook_root.is_dir():
        _ART_HOOK_INDEX = hooks
        return hooks
    for f in sorted(hook_root.rglob("*.ts")):
        if f.is_file():
            rel_path = f.relative_to(_ART_DESIGN_PRO_ROOT / "src")
            hooks.append({
                "name": f.name,
                "path": str(rel_path).replace("\\", "/"),
                "size": f.stat().st_size,
            })
    _ART_HOOK_INDEX = hooks
    logger.info(f"Art Design Pro Hooks 索引构建完成: {len(hooks)} 个文件")
    return hooks


def _build_art_config_index() -> List[Dict]:
    global _ART_CONFIG_INDEX
    if _ART_CONFIG_INDEX is not None:
        return _ART_CONFIG_INDEX
    configs: List[Dict] = []
    if not _ART_DESIGN_PRO_AVAILABLE:
        _ART_CONFIG_INDEX = configs
        return configs
    config_root = _ART_DESIGN_PRO_ROOT / "src" / "config"
    if not config_root.is_dir():
        _ART_CONFIG_INDEX = configs
        return configs
    for f in sorted(config_root.rglob("*")):
        if f.is_file() and f.suffix in (".ts", ".js", ".json"):
            rel_path = f.relative_to(_ART_DESIGN_PRO_ROOT / "src")
            configs.append({
                "name": f.name,
                "path": str(rel_path).replace("\\", "/"),
                "size": f.stat().st_size,
            })
    _ART_CONFIG_INDEX = configs
    logger.info(f"Art Design Pro 配置索引构建完成: {len(configs)} 个文件")
    return configs


def _safe_read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"读取文件失败 {path}: {e}")
        return ""


def _extract_galaxy_tags(html_content: str) -> List[str]:
    match = re.search(r"/\*\s*From Uiverse\.io.*?Tags:\s*(.*?)\*/", html_content)
    if match:
        return [t.strip() for t in match.group(1).split(",") if t.strip()]
    return []


def _extract_galaxy_author(html_content: str) -> str:
    match = re.search(r"From Uiverse\.io by\s+(\S+)", html_content)
    if match:
        return match.group(1)
    return ""


# ==================== Galaxy API ====================

@router.get("/galaxy/categories", summary="获取Galaxy UI组件分类列表")
async def galaxy_categories():
    if not _GALAXY_AVAILABLE:
        raise HTTPException(status_code=404, detail="Galaxy 资源未安装")
    index = _build_galaxy_index()
    result = []
    for cat, files in index.items():
        result.append({"category": cat, "count": len(files)})
    return {"categories": result, "total_components": sum(len(v) for v in index.values())}


@router.get("/galaxy/components", summary="获取Galaxy指定分类的组件列表")
async def galaxy_components(
    category: str = Query(..., description="组件分类名称"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
):
    if not _GALAXY_AVAILABLE:
        raise HTTPException(status_code=404, detail="Galaxy 资源未安装")
    index = _build_galaxy_index()
    if category not in index:
        raise HTTPException(status_code=404, detail=f"分类 '{category}' 不存在")
    files = index[category]
    total = len(files)
    start = (page - 1) * page_size
    end = start + page_size
    page_files = files[start:end]
    items = []
    for fname in page_files:
        fpath = _GALAXY_ROOT / category / fname
        content = _safe_read_file(fpath)
        author = _extract_galaxy_author(content)
        tags = _extract_galaxy_tags(content)
        items.append({
            "name": fname,
            "author": author,
            "tags": tags,
        })
    return {
        "category": category,
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.get("/galaxy/component/{category}/{name}", summary="获取Galaxy组件源代码")
async def galaxy_component_detail(category: str, name: str):
    if not _GALAXY_AVAILABLE:
        raise HTTPException(status_code=404, detail="Galaxy 资源未安装")
    fpath = _GALAXY_ROOT / category / name
    if not fpath.is_file():
        raise HTTPException(status_code=404, detail="组件文件不存在")
    if not str(fpath.resolve()).startswith(str(_GALAXY_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    content = _safe_read_file(fpath)
    author = _extract_galaxy_author(content)
    tags = _extract_galaxy_tags(content)
    html_match = re.search(r"(<[^/!][^>]*>.*?</[^>]+>|<[^/!][^>]*/?>)", content, re.DOTALL)
    html_part = html_match.group(0).strip() if html_match else ""
    style_match = re.search(r"<style[^>]*>(.*?)</style>", content, re.DOTALL)
    style_part = style_match.group(1).strip() if style_match else ""
    return {
        "category": category,
        "name": name,
        "author": author,
        "tags": tags,
        "html": html_part,
        "css": style_part,
        "raw": content,
    }


@router.get("/galaxy/search", summary="搜索Galaxy组件")
async def galaxy_search(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    category: Optional[str] = Query(None, description="限定分类"),
    limit: int = Query(50, ge=1, le=200, description="最大返回数量"),
):
    if not _GALAXY_AVAILABLE:
        raise HTTPException(status_code=404, detail="Galaxy 资源未安装")
    index = _build_galaxy_index()
    results = []
    kw_lower = keyword.lower()
    categories_to_search = [category] if category else list(index.keys())
    for cat in categories_to_search:
        if cat not in index:
            continue
        for fname in index[cat]:
            if kw_lower in fname.lower():
                fpath = _GALAXY_ROOT / cat / fname
                content = _safe_read_file(fpath)
                author = _extract_galaxy_author(content)
                tags = _extract_galaxy_tags(content)
                tag_match = any(kw_lower in t.lower() for t in tags)
                results.append({
                    "category": cat,
                    "name": fname,
                    "author": author,
                    "tags": tags,
                    "match_type": "filename" if not tag_match else "tag",
                })
                if len(results) >= limit:
                    break
        if len(results) >= limit:
            break
    return {"keyword": keyword, "total": len(results), "items": results}


@router.get("/galaxy/random", summary="随机获取Galaxy组件")
async def galaxy_random(
    category: Optional[str] = Query(None, description="限定分类"),
    count: int = Query(10, ge=1, le=50, description="获取数量"),
):
    import random
    if not _GALAXY_AVAILABLE:
        raise HTTPException(status_code=404, detail="Galaxy 资源未安装")
    index = _build_galaxy_index()
    candidates = []
    categories = [category] if category and category in index else list(index.keys())
    for cat in categories:
        for fname in index.get(cat, []):
            candidates.append((cat, fname))
    if not candidates:
        return {"items": []}
    sampled = random.sample(candidates, min(count, len(candidates)))
    items = []
    for cat, fname in sampled:
        fpath = _GALAXY_ROOT / cat / fname
        content = _safe_read_file(fpath)
        items.append({
            "category": cat,
            "name": fname,
            "author": _extract_galaxy_author(content),
            "tags": _extract_galaxy_tags(content),
            "html": re.search(r"(<[^/!][^>]*>.*?</[^>]+>|<[^/!][^>]*/?>)", content, re.DOTALL).group(0).strip() if re.search(r"(<[^/!][^>]*>.*?</[^>]+>|<[^/!][^>]*/?>)", content, re.DOTALL) else "",
            "css": re.search(r"<style[^>]*>(.*?)</style>", content, re.DOTALL).group(1).strip() if re.search(r"<style[^>]*>(.*?)</style>", content, re.DOTALL) else "",
        })
    return {"items": items}


# ==================== Art Design Pro API ====================

@router.get("/art-design-pro/overview", summary="获取Art Design Pro项目概览")
async def art_design_pro_overview():
    if not _ART_DESIGN_PRO_AVAILABLE:
        raise HTTPException(status_code=404, detail="Art Design Pro 资源未安装")
    components = _build_art_component_index()
    styles = _build_art_style_index()
    hooks = _build_art_hook_index()
    configs = _build_art_config_index()
    groups = {}
    for c in components:
        g = c["group"]
        if g not in groups:
            groups[g] = 0
        groups[g] += 1
    return {
        "components": {"total": len(components), "groups": groups},
        "styles": {"total": len(styles)},
        "hooks": {"total": len(hooks)},
        "configs": {"total": len(configs)},
    }


@router.get("/art-design-pro/components", summary="获取Art Design Pro组件列表")
async def art_design_pro_components(
    group: Optional[str] = Query(None, description="组件分组过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
):
    if not _ART_DESIGN_PRO_AVAILABLE:
        raise HTTPException(status_code=404, detail="Art Design Pro 资源未安装")
    components = _build_art_component_index()
    if group:
        components = [c for c in components if c["group"] == group]
    total = len(components)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = components[start:end]
    return {"total": total, "page": page, "page_size": page_size, "items": page_items}


@router.get("/art-design-pro/component/{path:path}", summary="获取Art Design Pro组件源代码")
async def art_design_pro_component_detail(path: str):
    if not _ART_DESIGN_PRO_AVAILABLE:
        raise HTTPException(status_code=404, detail="Art Design Pro 资源未安装")
    full_path = _ART_DESIGN_PRO_ROOT / "src" / path
    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not str(full_path.resolve()).startswith(str(_ART_DESIGN_PRO_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    content = _safe_read_file(full_path)
    return {
        "path": path,
        "name": full_path.name,
        "suffix": full_path.suffix,
        "content": content,
    }


@router.get("/art-design-pro/styles", summary="获取Art Design Pro样式文件列表")
async def art_design_pro_styles():
    if not _ART_DESIGN_PRO_AVAILABLE:
        raise HTTPException(status_code=404, detail="Art Design Pro 资源未安装")
    return {"items": _build_art_style_index()}


@router.get("/art-design-pro/style/{path:path}", summary="获取Art Design Pro样式文件源代码")
async def art_design_pro_style_detail(path: str):
    if not _ART_DESIGN_PRO_AVAILABLE:
        raise HTTPException(status_code=404, detail="Art Design Pro 资源未安装")
    full_path = _ART_DESIGN_PRO_ROOT / "src" / path
    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not str(full_path.resolve()).startswith(str(_ART_DESIGN_PRO_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    content = _safe_read_file(full_path)
    return {"path": path, "name": full_path.name, "content": content}


@router.get("/art-design-pro/hooks", summary="获取Art Design Pro Hooks列表")
async def art_design_pro_hooks():
    if not _ART_DESIGN_PRO_AVAILABLE:
        raise HTTPException(status_code=404, detail="Art Design Pro 资源未安装")
    return {"items": _build_art_hook_index()}


@router.get("/art-design-pro/hook/{path:path}", summary="获取Art Design Pro Hook源代码")
async def art_design_pro_hook_detail(path: str):
    if not _ART_DESIGN_PRO_AVAILABLE:
        raise HTTPException(status_code=404, detail="Art Design Pro 资源未安装")
    full_path = _ART_DESIGN_PRO_ROOT / "src" / path
    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not str(full_path.resolve()).startswith(str(_ART_DESIGN_PRO_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    content = _safe_read_file(full_path)
    return {"path": path, "name": full_path.name, "content": content}


@router.get("/art-design-pro/configs", summary="获取Art Design Pro配置文件列表")
async def art_design_pro_configs():
    if not _ART_DESIGN_PRO_AVAILABLE:
        raise HTTPException(status_code=404, detail="Art Design Pro 资源未安装")
    return {"items": _build_art_config_index()}


@router.get("/art-design-pro/config/{path:path}", summary="获取Art Design Pro配置文件源代码")
async def art_design_pro_config_detail(path: str):
    if not _ART_DESIGN_PRO_AVAILABLE:
        raise HTTPException(status_code=404, detail="Art Design Pro 资源未安装")
    full_path = _ART_DESIGN_PRO_ROOT / "src" / path
    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not str(full_path.resolve()).startswith(str(_ART_DESIGN_PRO_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    content = _safe_read_file(full_path)
    return {"path": path, "name": full_path.name, "content": content}


@router.get("/art-design-pro/locales", summary="获取Art Design Pro国际化文件列表")
async def art_design_pro_locales():
    if not _ART_DESIGN_PRO_AVAILABLE:
        raise HTTPException(status_code=404, detail="Art Design Pro 资源未安装")
    locale_root = _ART_DESIGN_PRO_ROOT / "src" / "locales"
    items = []
    if locale_root.is_dir():
        for f in sorted(locale_root.rglob("*")):
            if f.is_file():
                rel_path = f.relative_to(_ART_DESIGN_PRO_ROOT / "src")
                items.append({
                    "name": f.name,
                    "path": str(rel_path).replace("\\", "/"),
                    "size": f.stat().st_size,
                })
    return {"items": items}


@router.get("/art-design-pro/locale/{path:path}", summary="获取Art Design Pro国际化文件内容")
async def art_design_pro_locale_detail(path: str):
    if not _ART_DESIGN_PRO_AVAILABLE:
        raise HTTPException(status_code=404, detail="Art Design Pro 资源未安装")
    full_path = _ART_DESIGN_PRO_ROOT / "src" / path
    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not str(full_path.resolve()).startswith(str(_ART_DESIGN_PRO_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    content = _safe_read_file(full_path)
    return {"path": path, "name": full_path.name, "content": content}


@router.get("/art-design-pro/types", summary="获取Art Design Pro类型定义文件列表")
async def art_design_pro_types():
    if not _ART_DESIGN_PRO_AVAILABLE:
        raise HTTPException(status_code=404, detail="Art Design Pro 资源未安装")
    type_root = _ART_DESIGN_PRO_ROOT / "src" / "types"
    items = []
    if type_root.is_dir():
        for f in sorted(type_root.rglob("*")):
            if f.is_file():
                rel_path = f.relative_to(_ART_DESIGN_PRO_ROOT / "src")
                items.append({
                    "name": f.name,
                    "path": str(rel_path).replace("\\", "/"),
                    "size": f.stat().st_size,
                })
    return {"items": items}


@router.get("/art-design-pro/type/{path:path}", summary="获取Art Design Pro类型定义文件内容")
async def art_design_pro_type_detail(path: str):
    if not _ART_DESIGN_PRO_AVAILABLE:
        raise HTTPException(status_code=404, detail="Art Design Pro 资源未安装")
    full_path = _ART_DESIGN_PRO_ROOT / "src" / path
    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not str(full_path.resolve()).startswith(str(_ART_DESIGN_PRO_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    content = _safe_read_file(full_path)
    return {"path": path, "name": full_path.name, "content": content}


@router.get("/art-design-pro/store", summary="获取Art Design Pro状态管理文件列表")
async def art_design_pro_store():
    if not _ART_DESIGN_PRO_AVAILABLE:
        raise HTTPException(status_code=404, detail="Art Design Pro 资源未安装")
    store_root = _ART_DESIGN_PRO_ROOT / "src" / "store"
    items = []
    if store_root.is_dir():
        for f in sorted(store_root.rglob("*")):
            if f.is_file():
                rel_path = f.relative_to(_ART_DESIGN_PRO_ROOT / "src")
                items.append({
                    "name": f.name,
                    "path": str(rel_path).replace("\\", "/"),
                    "size": f.stat().st_size,
                })
    return {"items": items}


@router.get("/art-design-pro/store-file/{path:path}", summary="获取Art Design Pro状态管理文件内容")
async def art_design_pro_store_detail(path: str):
    if not _ART_DESIGN_PRO_AVAILABLE:
        raise HTTPException(status_code=404, detail="Art Design Pro 资源未安装")
    full_path = _ART_DESIGN_PRO_ROOT / "src" / path
    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not str(full_path.resolve()).startswith(str(_ART_DESIGN_PRO_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    content = _safe_read_file(full_path)
    return {"path": path, "name": full_path.name, "content": content}


@router.get("/art-design-pro/router", summary="获取Art Design Pro路由文件列表")
async def art_design_pro_router():
    if not _ART_DESIGN_PRO_AVAILABLE:
        raise HTTPException(status_code=404, detail="Art Design Pro 资源未安装")
    router_root = _ART_DESIGN_PRO_ROOT / "src" / "router"
    items = []
    if router_root.is_dir():
        for f in sorted(router_root.rglob("*")):
            if f.is_file():
                rel_path = f.relative_to(_ART_DESIGN_PRO_ROOT / "src")
                items.append({
                    "name": f.name,
                    "path": str(rel_path).replace("\\", "/"),
                    "size": f.stat().st_size,
                })
    return {"items": items}


@router.get("/art-design-pro/router-file/{path:path}", summary="获取Art Design Pro路由文件内容")
async def art_design_pro_router_detail(path: str):
    if not _ART_DESIGN_PRO_AVAILABLE:
        raise HTTPException(status_code=404, detail="Art Design Pro 资源未安装")
    full_path = _ART_DESIGN_PRO_ROOT / "src" / path
    if not full_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not str(full_path.resolve()).startswith(str(_ART_DESIGN_PRO_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    content = _safe_read_file(full_path)
    return {"path": path, "name": full_path.name, "content": content}


# ==================== Global Search API ====================

@router.get("/search", summary="全局搜索UI资源")
async def global_search(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    source: Optional[str] = Query(None, description="限定来源: galaxy / art-design-pro"),
    limit: int = Query(30, ge=1, le=100, description="最大返回数量"),
):
    results = []
    kw_lower = keyword.lower()
    if (source is None or source == "galaxy") and _GALAXY_AVAILABLE:
        index = _build_galaxy_index()
        for cat, files in index.items():
            for fname in files:
                if kw_lower in fname.lower():
                    results.append({
                        "source": "galaxy",
                        "category": cat,
                        "name": fname,
                        "type": "ui-component",
                    })
                    if len(results) >= limit:
                        break
            if len(results) >= limit:
                break
    if (source is None or source == "art-design-pro") and _ART_DESIGN_PRO_AVAILABLE:
        for c in _build_art_component_index():
            if kw_lower in c["name"].lower() or kw_lower in c["group"].lower():
                results.append({
                    "source": "art-design-pro",
                    "category": c["group"],
                    "name": c["name"],
                    "path": c["path"],
                    "type": "vue-component",
                })
                if len(results) >= limit:
                    break
        for s in _build_art_style_index():
            if kw_lower in s["name"].lower():
                results.append({
                    "source": "art-design-pro",
                    "category": "styles",
                    "name": s["name"],
                    "path": s["path"],
                    "type": "style",
                })
                if len(results) >= limit:
                    break
        for h in _build_art_hook_index():
            if kw_lower in h["name"].lower():
                results.append({
                    "source": "art-design-pro",
                    "category": "hooks",
                    "name": h["name"],
                    "path": h["path"],
                    "type": "hook",
                })
                if len(results) >= limit:
                    break
    return {"keyword": keyword, "total": len(results), "items": results}


@router.get("/status", summary="获取UI资源服务状态")
async def ui_resources_status():
    galaxy_info = {}
    if _GALAXY_AVAILABLE:
        index = _build_galaxy_index()
        galaxy_info = {
            "available": True,
            "categories": len(index),
            "total_components": sum(len(v) for v in index.values()),
        }
    else:
        galaxy_info = {"available": False}

    art_info = {}
    if _ART_DESIGN_PRO_AVAILABLE:
        components = _build_art_component_index()
        styles = _build_art_style_index()
        hooks = _build_art_hook_index()
        art_info = {
            "available": True,
            "components": len(components),
            "styles": len(styles),
            "hooks": len(hooks),
        }
    else:
        art_info = {"available": False}

    return {
        "galaxy": galaxy_info,
        "art_design_pro": art_info,
    }


@router.post("/reindex", summary="重建UI资源索引")
async def reindex():
    global _GALAXY_INDEX, _ART_COMPONENT_INDEX, _ART_STYLE_INDEX, _ART_HOOK_INDEX, _ART_CONFIG_INDEX
    _GALAXY_INDEX = None
    _ART_COMPONENT_INDEX = None
    _ART_STYLE_INDEX = None
    _ART_HOOK_INDEX = None
    _ART_CONFIG_INDEX = None
    _build_galaxy_index()
    _build_art_component_index()
    _build_art_style_index()
    _build_art_hook_index()
    _build_art_config_index()
    return {"message": "索引重建完成"}
