"""
user_model_config.py
用户自定义模型配置 API
- GET  /api/user-model-config       获取当前模型配置（优先读用户配置，回落到环境变量/自动发现）
- POST /api/user-model-config       保存用户模型配置
- GET  /api/user-model-config/local-models  获取本地 Ollama 已安装模型列表
- POST /api/user-model-config/test  测试当前配置是否可连通
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

import requests
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

# Config file models_config.json
_CONFIG_PATH = Path(__file__).parent.parent / "models_config.json"
_DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
_DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class UserModelConfig(BaseModel):
    llm_model: str = ""
    ollama_base_url: str = _DEFAULT_OLLAMA_BASE_URL
    timeout: int = 120
    embedding_model: str = _DEFAULT_EMBEDDING_MODEL
    kg_model: Optional[str] = None


class TestConfigRequest(BaseModel):
    ollama_base_url: str = _DEFAULT_OLLAMA_BASE_URL
    llm_model: str = ""
    timeout: int = 10


def _read_config_file() -> dict:
    """读取 models_config.json，不存在则返回空字典"""
    try:
        if _CONFIG_PATH.exists():
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning("[UserModelConfig] 读取配置文件失败: %s", e)
    return {}


def _write_config_file(data: dict) -> None:
    """写入 models_config.json"""
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _parse_ollama_list_output(output: str) -> list[str]:
    models: list[str] = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("name"):
            continue
        parts = re.split(r"\s{2,}", line)
        candidate = (parts[0] if parts else line).strip()
        if candidate and candidate not in models:
            models.append(candidate)
    return models


def _fetch_ollama_models_via_http(base_url: str) -> list[str]:
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=8)
        resp.raise_for_status()
        data = resp.json()
        models = []
        for model in data.get("models", []):
            name = str(model.get("name", "")).strip()
            if name and name not in models:
                models.append(name)
        return models
    except Exception as e:
        logger.warning("[UserModelConfig] 通过 HTTP 获取 Ollama 模型失败: %s", e)
        return []


def discover_local_models(base_url: Optional[str] = None) -> list[str]:
    """优先通过 `ollama list` 发现本地模型，失败时回退到 /api/tags。"""
    try:
        completed = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=10,
            check=False,
        )
        if completed.returncode == 0:
            models = _parse_ollama_list_output(completed.stdout)
            if models:
                return models
    except Exception as e:
        logger.warning("[UserModelConfig] 执行 ollama list 失败: %s", e)

    return _fetch_ollama_models_via_http(base_url or _DEFAULT_OLLAMA_BASE_URL)


def _resolve_default_model(file_cfg: Optional[dict] = None) -> str:
    file_cfg = file_cfg or _read_config_file()
    configured_model = str(file_cfg.get("llm_model") or "").strip()
    if configured_model:
        return configured_model

    env_model = str(os.getenv("MODEL", "")).strip()
    if env_model:
        return env_model

    base_url = (
        str(file_cfg.get("ollama_base_url") or "").strip() or _DEFAULT_OLLAMA_BASE_URL
    )
    local_models = discover_local_models(base_url)
    return local_models[0] if local_models else ""


def get_effective_config() -> UserModelConfig:
    """获取生效的模型配置（优先级：文件 > 环境变量 > 自动发现）"""
    file_cfg = _read_config_file()
    resolved_model = _resolve_default_model(file_cfg)
    return UserModelConfig(
        llm_model=resolved_model,
        ollama_base_url=str(file_cfg.get("ollama_base_url") or "").strip()
        or os.getenv("OLLAMA_BASE_URL", _DEFAULT_OLLAMA_BASE_URL),
        timeout=int(file_cfg.get("timeout") or os.getenv("OLLAMA_TIMEOUT", "120")),
        embedding_model=str(file_cfg.get("embedding_model") or "").strip()
        or os.getenv("EMBEDDING_MODEL", _DEFAULT_EMBEDDING_MODEL),
        kg_model=file_cfg.get("kg_model") or os.getenv("KG_MODEL") or None,
    )


@router.get("/api/user-model-config")
async def get_user_model_config():
    """获取当前生效的模型配置"""
    cfg = get_effective_config()
    return {
        "status": "ok",
        "config": cfg.dict(),
        "source": "file" if _read_config_file() else "env_or_auto_detect",
    }


@router.post("/api/user-model-config")
async def save_user_model_config(cfg: UserModelConfig):
    """保存用户模型配置到 models_config.json，并同步 Ollama provider 配置。"""
    try:
        current = _read_config_file()
        payload = cfg.dict()
        current.update(payload)

        current.setdefault("cloud_keys", {})
        ollama_cfg = current["cloud_keys"].get("ollama", {})
        ollama_cfg.update(
            {
                "base_url": payload.get("ollama_base_url") or current.get("ollama_base_url"),
                "model": payload.get("llm_model") or _resolve_default_model(current),
            }
        )
        current["cloud_keys"]["ollama"] = ollama_cfg

        if not current.get("llm_model"):
            current["llm_model"] = _resolve_default_model(current)

        _write_config_file(current)
        return {"status": "ok", "message": "配置已保存", "config": current}
    except Exception as e:
        logger.exception("[UserModelConfig] 保存失败: %s", e)
        return {"status": "error", "message": f"保存失败: {e}"}


@router.get("/api/user-model-config/local-models")
async def get_local_models(base_url: str = _DEFAULT_OLLAMA_BASE_URL):
    """查询本地 Ollama 已安装的模型列表。"""
    try:
        models = discover_local_models(base_url)
        if models:
            return {"status": "ok", "models": models, "base_url": base_url}
        return {
            "status": "error",
            "message": "未检测到本地模型，请先执行 ollama pull <model>",
            "models": [],
            "base_url": base_url,
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "models": [], "base_url": base_url}


@router.post("/api/user-model-config/test")
async def test_model_config(req: TestConfigRequest):
    """测试模型配置连通性。"""
    result = {"ollama_reachable": False, "model_installed": False, "message": ""}

    try:
        tags_resp = requests.get(f"{req.ollama_base_url.rstrip('/')}/api/tags", timeout=req.timeout)
        tags_resp.raise_for_status()
        result["ollama_reachable"] = True

        installed = discover_local_models(req.ollama_base_url)
        requested = req.llm_model.strip()
        result["model_installed"] = (not requested) or requested in installed or any(
            m.startswith(requested.split(":")[0]) for m in installed
        )
        result["installed_models"] = installed

        if requested and not result["model_installed"]:
            result["message"] = (
                f"模型 {requested!r} 未安装。"
                f"已安装: {', '.join(installed) or '（无）'}。"
                f"请运行: ollama pull {requested}"
            )
        else:
            resolved = requested or (installed[0] if installed else "")
            result["message"] = (
                f"连接正常，模型 {resolved!r} 已就绪" if resolved else "连接正常，但暂未检测到本地模型"
            )

    except requests.exceptions.ConnectionError:
        result["message"] = f"无法连接 Ollama（{req.ollama_base_url}），请确认服务已启动"
    except requests.exceptions.Timeout:
        result["message"] = f"连接超时（{req.timeout}s），请检查 Ollama 地址"
    except Exception as e:
        result["message"] = f"测试失败: {e}"

    return result
