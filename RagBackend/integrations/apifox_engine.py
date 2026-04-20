import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/apifox")

_APIFOX_ROOT = Path(r"C:\Users\ASUS\WorkBuddy\20260324003945\KnowledgeRAG-GZHU\apifox")
_APIFOX_AVAILABLE = _APIFOX_ROOT.is_dir()

_collections_cache: Optional[List[Dict]] = None
_endpoints_cache: Optional[List[Dict]] = None


def _load_collections() -> List[Dict]:
    global _collections_cache
    if _collections_cache is not None:
        return _collections_cache
    collections = []
    if not _APIFOX_AVAILABLE:
        _collections_cache = collections
        return collections
    col_dir = _APIFOX_ROOT / "collections"
    if col_dir.is_dir():
        for f in sorted(col_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                data["_source_file"] = f.name
                collections.append(data)
            except Exception as e:
                logger.warning(f"加载Apifox集合失败 {f.name}: {e}")
    _collections_cache = collections
    return collections


def _extract_endpoints_from_collection(collection: Dict) -> List[Dict]:
    endpoints = []
    items = collection.get("item", collection.get("items", []))
    for item in items:
        if "request" in item:
            req = item["request"]
            method = req.get("method", "GET")
            url_raw = req.get("url", {})
            if isinstance(url_raw, str):
                url = url_raw
                path = url_raw
            else:
                url = url_raw.get("raw", "")
                path = "/".join(url_raw.get("path", [])) if isinstance(url_raw, dict) else str(url_raw)
            headers = []
            for h in req.get("header", []):
                headers.append({"key": h.get("key", ""), "value": h.get("value", "")})
            body = req.get("body", {})
            responses = []
            for r in item.get("response", []):
                responses.append({
                    "name": r.get("name", ""),
                    "status": r.get("status", ""),
                    "code": r.get("code", 0),
                })
            endpoints.append({
                "name": item.get("name", ""),
                "method": method,
                "url": url,
                "path": path,
                "headers": headers,
                "body_type": body.get("mode", "") if isinstance(body, dict) else "",
                "description": item.get("description", req.get("description", "")),
                "responses": responses,
            })
        if "item" in item:
            endpoints.extend(_extract_endpoints_from_collection(item))
    return endpoints


def _get_all_endpoints() -> List[Dict]:
    global _endpoints_cache
    if _endpoints_cache is not None:
        return _endpoints_cache
    endpoints = []
    for col in _load_collections():
        col_endpoints = _extract_endpoints_from_collection(col)
        for ep in col_endpoints:
            ep["_collection"] = col.get("info", {}).get("name", col.get("_source_file", ""))
        endpoints.extend(col_endpoints)
    _endpoints_cache = endpoints
    return endpoints


def _load_environments() -> List[Dict]:
    envs = []
    if not _APIFOX_AVAILABLE:
        return envs
    env_dir = _APIFOX_ROOT / "environments"
    if env_dir.is_dir():
        for f in sorted(env_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                data["_source_file"] = f.name
                envs.append(data)
            except Exception as e:
                logger.warning(f"加载Apifox环境失败 {f.name}: {e}")
    return envs


def _load_schemas() -> List[Dict]:
    schemas = []
    if not _APIFOX_AVAILABLE:
        return schemas
    schema_dir = _APIFOX_ROOT / "schemas"
    if schema_dir.is_dir():
        for f in sorted(schema_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                data["_source_file"] = f.name
                schemas.append(data)
            except Exception as e:
                logger.warning(f"加载Apifox Schema失败 {f.name}: {e}")
    return schemas


# ==================== API Endpoints ====================

@router.get("/status", summary="获取Apifox集成状态")
async def apifox_status():
    collections = _load_collections()
    endpoints = _get_all_endpoints()
    return {
        "available": _APIFOX_AVAILABLE,
        "root": str(_APIFOX_ROOT),
        "collections_count": len(collections),
        "endpoints_count": len(endpoints),
        "methods_distribution": {
            m: sum(1 for e in endpoints if e.get("method") == m)
            for m in sorted(set(e.get("method", "UNKNOWN") for e in endpoints))
        },
    }


@router.get("/collections", summary="获取Apifox API集合列表")
async def list_collections():
    collections = _load_collections()
    result = []
    for col in collections:
        info = col.get("info", {})
        endpoints = _extract_endpoints_from_collection(col)
        result.append({
            "name": info.get("name", col.get("_source_file", "")),
            "description": info.get("description", ""),
            "schema": info.get("schema", ""),
            "source_file": col.get("_source_file", ""),
            "endpoint_count": len(endpoints),
        })
    return {"collections": result, "total": len(result)}


@router.get("/collections/{index}/endpoints", summary="获取指定集合的API端点列表")
async def get_collection_endpoints(index: int):
    collections = _load_collections()
    if index < 0 or index >= len(collections):
        raise HTTPException(status_code=404, detail="集合索引超出范围")
    endpoints = _extract_endpoints_from_collection(collections[index])
    return {
        "collection": collections[index].get("info", {}).get("name", ""),
        "endpoints": endpoints,
        "total": len(endpoints),
    }


@router.get("/endpoints", summary="获取所有API端点列表")
async def list_all_endpoints(
    method: Optional[str] = Query(None, description="按HTTP方法过滤"),
    keyword: Optional[str] = Query(None, description="按关键词搜索"),
    limit: int = Query(100, ge=1, le=500),
):
    endpoints = _get_all_endpoints()
    if method:
        endpoints = [e for e in endpoints if e.get("method", "").upper() == method.upper()]
    if keyword:
        kw = keyword.lower()
        endpoints = [
            e for e in endpoints
            if kw in e.get("name", "").lower()
            or kw in e.get("path", "").lower()
            or kw in e.get("description", "").lower()
        ]
    return {"endpoints": endpoints[:limit], "total": len(endpoints), "filtered": len(endpoints[:limit])}


@router.get("/endpoints/search", summary="搜索API端点")
async def search_endpoints(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    search_fields: Optional[str] = Query("name,path,description", description="搜索字段（逗号分隔）"),
):
    endpoints = _get_all_endpoints()
    kw = keyword.lower()
    fields = [f.strip() for f in search_fields.split(",")]
    results = []
    for ep in endpoints:
        score = 0
        for field in fields:
            val = ep.get(field, "").lower()
            if kw in val:
                score += 10
            if val.startswith(kw):
                score += 5
        if score > 0:
            results.append({**ep, "_score": score})
    results.sort(key=lambda x: x["_score"], reverse=True)
    return {"keyword": keyword, "results": results[:50], "total": len(results)}


@router.get("/environments", summary="获取Apifox环境配置列表")
async def list_environments():
    envs = _load_environments()
    result = []
    for env in envs:
        values = env.get("values", [])
        result.append({
            "name": env.get("name", env.get("_source_file", "")),
            "source_file": env.get("_source_file", ""),
            "variable_count": len(values),
            "variables": [
                {"key": v.get("key", ""), "enabled": v.get("enabled", True)}
                for v in values
            ],
        })
    return {"environments": result}


@router.get("/schemas", summary="获取Apifox数据模型Schema列表")
async def list_schemas():
    schemas = _load_schemas()
    result = []
    for s in schemas:
        result.append({
            "source_file": s.get("_source_file", ""),
            "name": s.get("name", ""),
            "type": s.get("type", ""),
            "property_count": len(s.get("properties", {})),
        })
    return {"schemas": result}


@router.get("/stats", summary="获取Apifox API统计信息")
async def apifox_stats():
    endpoints = _get_all_endpoints()
    method_dist = {}
    for ep in endpoints:
        m = ep.get("method", "UNKNOWN")
        method_dist[m] = method_dist.get(m, 0) + 1
    collection_names = set()
    for col in _load_collections():
        collection_names.add(col.get("info", {}).get("name", ""))
    has_body = sum(1 for e in endpoints if e.get("body_type"))
    has_response = sum(1 for e in endpoints if e.get("responses"))
    return {
        "total_endpoints": len(endpoints),
        "total_collections": len(_load_collections()),
        "method_distribution": method_dist,
        "endpoints_with_body": has_body,
        "endpoints_with_response_docs": has_response,
        "collection_names": sorted(collection_names),
    }


@router.post("/reindex", summary="重建Apifox索引缓存")
async def reindex():
    global _collections_cache, _endpoints_cache
    _collections_cache = None
    _endpoints_cache = None
    _load_collections()
    _get_all_endpoints()
    return {"message": "Apifox索引重建完成"}


@router.get("/files", summary="获取Apifox目录下所有文件")
async def list_files():
    if not _APIFOX_AVAILABLE:
        raise HTTPException(status_code=404, detail="Apifox 资源未找到")
    files = []
    for f in sorted(_APIFOX_ROOT.rglob("*")):
        if f.is_file() and ".git" not in str(f):
            rel = f.relative_to(_APIFOX_ROOT)
            files.append({
                "path": str(rel).replace("\\", "/"),
                "name": f.name,
                "size": f.stat().st_size,
                "suffix": f.suffix,
            })
    return {"files": files, "total": len(files)}


@router.get("/file/{path:path}", summary="获取Apifox文件内容")
async def get_file(path: str):
    if not _APIFOX_AVAILABLE:
        raise HTTPException(status_code=404, detail="Apifox 资源未找到")
    fpath = _APIFOX_ROOT / path
    if not fpath.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not str(fpath.resolve()).startswith(str(_APIFOX_ROOT.resolve())):
        raise HTTPException(status_code=403, detail="非法路径")
    content = fpath.read_text(encoding="utf-8", errors="replace")
    return {"path": path, "content": content, "size": len(content)}
