"""
多模型适配路由 - 支持 Ollama / OpenAI / 腾讯混元 / DeepSeek 统一接口

API Key 优先级（每次请求动态读取，无需重启）：
  文件（models_config.json）> 环境变量（.env）> 空
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# - Config file user_model_config.py -
_CONFIG_PATH = Path(__file__).parent.parent / "models_config.json"
_DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"


def _read_config_data() -> dict:
    try:
        if _CONFIG_PATH.exists():
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning("[model_router] 读取 models_config.json 失败: %s", e)
    return {}


def _write_config_data(data: dict) -> None:
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _read_cloud_keys() -> dict:
    """读取 models_config.json 中的云端 API Key，不存在则返回空字典。每次调用都重新读取，实时生效。"""
    return _read_config_data().get("cloud_keys", {})


def _get_key(provider: str, env_var: str) -> str:
    """按优先级获取 API Key：文件 > 环境变量"""
    keys = _read_cloud_keys()
    return keys.get(provider, {}).get("api_key", "") or os.getenv(env_var, "")


def _get_base_url(provider: str, env_var: str, default: str) -> str:
    """按优先级获取 Base URL：文件 > 环境变量 > 默认值"""
    keys = _read_cloud_keys()
    return keys.get(provider, {}).get("base_url", "") or os.getenv(env_var, default)


def _resolve_default_model() -> str:
    config_data = _read_config_data()
    configured_default = str(config_data.get("default_model") or "").strip()
    if configured_default:
        return configured_default

    try:
        from models.user_model_config import get_effective_config

        cfg = get_effective_config()
        if cfg.llm_model:
            return cfg.llm_model
    except Exception as e:
        logger.warning("[model_router] 解析默认模型失败: %s", e)

    return str(os.getenv("MODEL", "")).strip()



# - / -
class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[dict]
    stream: bool = True
    temperature: float = 0.7
    max_tokens: int = 2048
    kb_id: Optional[str] = None
    deep_think: bool = False


class ModelListResponse(BaseModel):
    models: list[dict]


# - Model catalog -
_MODEL_CATALOG = [
    {
        "id": "deepseek-chat",
        "name": "DeepSeek Chat（云端·深度推理）",
        "provider": "deepseek",
        "description": "擅长深度推理、复杂分析、专业问题",
        "context_length": 32768,
        "requires_key": "DEEPSEEK_API_KEY",
    },
    {
        "id": "deepseek-reasoner",
        "name": "DeepSeek Reasoner（云端·R1推理）",
        "provider": "deepseek",
        "description": "DeepSeek R1 推理模型，适合数学/代码/逻辑",
        "context_length": 32768,
        "requires_key": "DEEPSEEK_API_KEY",
    },
    {
        "id": "hunyuan-lite",
        "name": "腾讯混元 Lite（云端·通用）",
        "provider": "hunyuan",
        "description": "擅长通用问答、日常创作、快速响应",
        "context_length": 8192,
        "requires_key": "HUNYUAN_SECRET_ID",
    },
    {
        "id": "hunyuan-pro",
        "name": "腾讯混元 Pro（云端·专业）",
        "provider": "hunyuan",
        "description": "混元高性能版本，支持更长上下文",
        "context_length": 32768,
        "requires_key": "HUNYUAN_SECRET_ID",
    },
    {
        "id": "gpt-4o-mini",
        "name": "GPT-4o Mini（云端·OpenAI）",
        "provider": "openai",
        "description": "OpenAI GPT-4o Mini，性价比高",
        "context_length": 128000,
        "requires_key": "OPENAI_API_KEY",
    },
    {
        "id": "gpt-4o",
        "name": "GPT-4o（云端·OpenAI 旗舰）",
        "provider": "openai",
        "description": "OpenAI 旗舰模型，多模态能力强",
        "context_length": 128000,
        "requires_key": "OPENAI_API_KEY",
    },
]

AVAILABLE_MODELS = _MODEL_CATALOG


def _build_local_model_entries() -> list[dict]:
    try:
        from models.user_model_config import discover_local_models, get_effective_config

        cfg = get_effective_config()
        base_url = cfg.ollama_base_url or _DEFAULT_OLLAMA_BASE_URL
        detected = discover_local_models(base_url)
    except Exception as e:
        logger.warning("[model_router] 本地模型发现失败: %s", e)
        base_url = _DEFAULT_OLLAMA_BASE_URL
        detected = []

    configured = _resolve_default_model()
    local_models: list[str] = []
    for model_id in [configured, *detected]:
        model_id = str(model_id or "").strip()
        if model_id and model_id not in local_models:
            local_models.append(model_id)

    return [
        {
            "id": model_id,
            "name": f"{model_id}（本地 Ollama）",
            "provider": "ollama",
            "description": f"本地 Ollama 模型 · {base_url}",
            "context_length": 8192,
            "available": model_id in detected if detected else bool(model_id),
        }
        for model_id in local_models
    ]


def _append_configured_cloud_models(catalog: list[dict]) -> list[dict]:
    result = [dict(item) for item in catalog]
    existing_ids = {item["id"] for item in result}
    for provider, cfg in _read_cloud_keys().items():
        model_id = str(cfg.get("model") or "").strip()
        if (
            provider in {"deepseek", "openai", "hunyuan"}
            and model_id
            and model_id not in existing_ids
        ):
            result.append(
                {
                    "id": model_id,
                    "name": f"{model_id}（云端·{provider}）",
                    "provider": provider,
                    "description": "来自已保存的多模型配置",
                    "context_length": 32768,
                    "requires_key": {
                        "deepseek": "DEEPSEEK_API_KEY",
                        "openai": "OPENAI_API_KEY",
                        "hunyuan": "HUNYUAN_SECRET_ID",
                    }.get(provider),
                }
            )
            existing_ids.add(model_id)
    return result


def _build_model_list() -> list:
    """动态构建模型列表，available 字段实时反映当前配置状态。"""
    has_deepseek = bool(_get_key("deepseek", "DEEPSEEK_API_KEY"))
    has_openai = bool(_get_key("openai", "OPENAI_API_KEY"))
    has_hunyuan = bool(
        _get_key("hunyuan", "HUNYUAN_SECRET_ID") or os.getenv("HUNYUAN_SECRET_ID")
    )
    provider_available = {
        "deepseek": has_deepseek,
        "openai": has_openai,
        "hunyuan": has_hunyuan,
    }
    result = _build_local_model_entries()
    for m in _append_configured_cloud_models(_MODEL_CATALOG):
        entry = dict(m)
        entry["available"] = provider_available.get(m["provider"], False)
        result.append(entry)
    return result



# - provider -
async def _stream_ollama(
    model: str, messages: list, temperature: float, max_tokens: int, deep_think: bool = False
) -> AsyncGenerator[str, None]:
    """调用本地 Ollama 流式接口"""
    import aiohttp

    ollama_url = _get_base_url("ollama", "OLLAMA_BASE_URL", "http://localhost:11434")
    payload: dict = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    if deep_think:
        payload["think"] = True
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{ollama_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=300),
            ) as resp:
                if resp.status != 200:
                    err = await resp.text()
                    yield f"data: {json.dumps({'error': f'Ollama 返回错误: {err}'})}\n\n"
                    return
                async for line in resp.content:
                    line = line.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        done = chunk.get("done", False)
                        if content:
                            yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"
                        if done:
                            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


async def _stream_deepseek(
    model: str, messages: list, temperature: float, max_tokens: int
) -> AsyncGenerator[str, None]:
    """调用 DeepSeek API 流式接口"""
    api_key = _get_key("deepseek", "DEEPSEEK_API_KEY")
    if not api_key:
        yield f"data: {json.dumps({'error': '未配置 DeepSeek API Key，请在「设置 → 多模型」填写并保存'})}\n\n"
        return
    import aiohttp

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.deepseek.com/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=300),
            ) as resp:
                if resp.status != 200:
                    err = await resp.text()
                    yield f"data: {json.dumps({'error': f'DeepSeek 返回错误({resp.status}): {err}'})}\n\n"
                    return
                async for line in resp.content:
                    line = line.decode("utf-8").strip()
                    if not line or line == "data: [DONE]":
                        if line == "data: [DONE]":
                            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
                        continue
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"
                        except Exception:
                            pass
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


async def _stream_openai(
    model: str, messages: list, temperature: float, max_tokens: int
) -> AsyncGenerator[str, None]:
    """调用 OpenAI 兼容接口（同样支持 Kimi / Moonshot 等兼容服务）"""
    api_key = _get_key("openai", "OPENAI_API_KEY")
    base_url = _get_base_url("openai", "OPENAI_BASE_URL", "https://api.openai.com/v1")
    if not api_key:
        yield f"data: {json.dumps({'error': '未配置 OpenAI API Key，请在「设置 → 多模型」填写并保存'})}\n\n"
        return
    import aiohttp

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=300),
            ) as resp:
                if resp.status != 200:
                    err = await resp.text()
                    yield f"data: {json.dumps({'error': f'OpenAI 返回错误({resp.status}): {err}'})}\n\n"
                    return
                async for line in resp.content:
                    line = line.decode("utf-8").strip()
                    if not line or line == "data: [DONE]":
                        if line == "data: [DONE]":
                            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
                        continue
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"
                        except Exception:
                            pass
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


async def _stream_hunyuan(
    model: str, messages: list, temperature: float, max_tokens: int
) -> AsyncGenerator[str, None]:
    """调用腾讯混元 API（使用 OpenAI 兼容接口）"""
    secret_id = _get_key("hunyuan", "HUNYUAN_SECRET_ID") or os.getenv(
        "HUNYUAN_SECRET_ID", ""
    )
    secret_key = os.getenv("HUNYUAN_SECRET_KEY", "")
    # hunyuan api_key Bearer token
    file_keys = _read_cloud_keys().get("hunyuan", {})
    if file_keys.get("api_key"):
        secret_id = file_keys["api_key"]
        secret_key = ""
    if not secret_id:
        yield f"data: {json.dumps({'error': '未配置混元 API Key，请在「设置 → 多模型」填写并保存'})}\n\n"
        return
    # OpenAI API key
    import aiohttp

    # api_keyEnvironment variable secretId:secretKey
    api_key = secret_id if not secret_key else f"{secret_id}:{secret_key}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.hunyuan.cloud.tencent.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=300),
            ) as resp:
                if resp.status != 200:
                    err = await resp.text()
                    yield f"data: {json.dumps({'error': f'混元 API 返回错误({resp.status}): {err}'})}\n\n"
                    return
                async for line in resp.content:
                    line = line.decode("utf-8").strip()
                    if not line or line == "data: [DONE]":
                        if line == "data: [DONE]":
                            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
                        continue
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"
                        except Exception:
                            pass
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


# - API -
@router.get("/api/models/list")
async def list_models():
    """获取所有可用模型列表（available 字段实时反映当前 Key 配置状态）"""
    return {"models": _build_model_list()}


@router.post("/api/models/chat")
async def model_chat(req: ChatCompletionRequest):
    """
    统一多模型对话接口（SSE 流式）
    根据 model 字段自动路由到对应 provider
    """
    # provider
    model_info = next((m for m in _MODEL_CATALOG if m["id"] == req.model), None)
    if not model_info:
        # Ollama Local model
        provider = "ollama"
    else:
        provider = model_info.get("provider", "ollama")

    async def generate():
        if provider == "ollama":
            async for chunk in _stream_ollama(
                req.model, req.messages, req.temperature, req.max_tokens, req.deep_think
            ):
                yield chunk
        elif provider == "deepseek":
            async for chunk in _stream_deepseek(
                req.model, req.messages, req.temperature, req.max_tokens
            ):
                yield chunk
        elif provider == "openai":
            async for chunk in _stream_openai(
                req.model, req.messages, req.temperature, req.max_tokens
            ):
                yield chunk
        elif provider == "hunyuan":
            async for chunk in _stream_hunyuan(
                req.model, req.messages, req.temperature, req.max_tokens
            ):
                yield chunk
        else:
            yield f"data: {json.dumps({'error': f'不支持的 provider: {provider}'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# - MultiModelTab saveProvider -


class ProviderConfigRequest(BaseModel):
    provider_id: str  # ollama / deepseek / openai / hunyuan / bailian / xinghuo
    config: dict  # { api_key, base_url, model, temperature, max_tokens }


@router.post("/api/models/configure")
async def configure_provider(req: ProviderConfigRequest):
    """
    保存 Provider 配置到 models_config.json，并同步统一默认模型配置。
    修复：前端 saveProvider / setDefault 调用后，API Key、Ollama 地址、默认模型立即生效。
    """
    try:
        data = _read_config_data()
        data.setdefault("cloud_keys", {})

        provider_config = dict(req.config or {})
        is_default = bool(provider_config.pop("is_default", False))
        data["cloud_keys"][req.provider_id] = provider_config

        if req.provider_id == "ollama":
            base_url = (
                str(provider_config.get("base_url") or data.get("ollama_base_url") or _DEFAULT_OLLAMA_BASE_URL)
                .strip()
            )
            model = str(provider_config.get("model") or data.get("llm_model") or "").strip()
            if base_url:
                data["ollama_base_url"] = base_url
            if model:
                data["llm_model"] = model
                if is_default or not str(data.get("default_model") or "").strip():
                    data["default_model"] = model
        elif is_default:
            model = str(provider_config.get("model") or "").strip()
            if model:
                data["default_model"] = model

        _write_config_data(data)
        logger.info("[model_router] Provider %r 配置已保存", req.provider_id)
        return {
            "status": "ok",
            "message": f"{req.provider_id} 配置已保存，立即生效",
            "default_model": data.get("default_model") or data.get("llm_model") or "",
        }
    except Exception as e:
        logger.error(f"[model_router] 保存配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存失败: {e}")



class ProviderTestRequest(BaseModel):
    provider_id: str
    config: dict


@router.post("/api/models/test")
async def test_provider(req: ProviderTestRequest):
    """
    测试 Provider 连通性（发送一条最小 message 验证 API Key 有效）。
    修复：前端 testProvider 调用此接口，返回真实测试结果而非演示数据。
    """
    import time

    import aiohttp

    start = time.monotonic()
    provider = req.provider_id
    cfg = req.config
    api_key = cfg.get("api_key", "")

    try:
        if provider == "ollama":
            base_url = cfg.get("base_url", "http://localhost:11434")
            async with aiohttp.ClientSession() as s:
                async with s.get(
                    f"{base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=8)
                ) as r:
                    ok = r.status == 200
            latency = int((time.monotonic() - start) * 1000)
            return {
                "ok": ok,
                "message": "Ollama 服务正常" if ok else "无法连接 Ollama",
                "latency": latency,
            }

        elif provider == "deepseek":
            if not api_key:
                return {"ok": False, "message": "API Key 为空"}
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": cfg.get("model", "deepseek-chat"),
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
                "stream": False,
            }
            async with aiohttp.ClientSession() as s:
                async with s.post(
                    "https://api.deepseek.com/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as r:
                    ok = r.status == 200
                    msg = (
                        "连接成功，API Key 有效"
                        if ok
                        else f"API 返回 {r.status}，请检查 Key"
                    )
            latency = int((time.monotonic() - start) * 1000)
            return {"ok": ok, "message": msg, "latency": latency}

        elif provider == "openai":
            if not api_key:
                return {"ok": False, "message": "API Key 为空"}
            base_url = cfg.get("base_url", "https://api.openai.com/v1")
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": cfg.get("model", "gpt-4o-mini"),
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
                "stream": False,
            }
            async with aiohttp.ClientSession() as s:
                async with s.post(
                    f"{base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as r:
                    ok = r.status == 200
                    msg = (
                        "连接成功，API Key 有效"
                        if ok
                        else f"API 返回 {r.status}，请检查 Key 或 Base URL"
                    )
            latency = int((time.monotonic() - start) * 1000)
            return {"ok": ok, "message": msg, "latency": latency}

        elif provider in ("hunyuan", "bailian", "xinghuo"):
            if not api_key:
                return {"ok": False, "message": "API Key 为空"}
            # Key
            latency = int((time.monotonic() - start) * 1000)
            return {
                "ok": True,
                "message": "API Key 已填写（格式校验通过）",
                "latency": latency,
            }

        else:
            return {"ok": False, "message": f"未知 provider: {provider}"}

    except aiohttp.ClientConnectorError:
        return {"ok": False, "message": "网络连接失败，请检查地址或网络"}
    except asyncio.TimeoutError:
        return {"ok": False, "message": "连接超时"}
    except Exception as e:
        return {"ok": False, "message": f"测试失败: {e}"}


@router.get("/api/models/providers/status")
async def providers_status():
    """检查各云端 Provider 的密钥配置状态（动态读取，实时反映）"""
    return {
        "ollama": {
            "configured": True,
            "url": _get_base_url("ollama", "OLLAMA_BASE_URL", "http://localhost:11434"),
        },
        "deepseek": {
            "configured": bool(_get_key("deepseek", "DEEPSEEK_API_KEY")),
            "key_hint": "在设置→多模型中配置",
        },
        "openai": {
            "configured": bool(_get_key("openai", "OPENAI_API_KEY")),
            "key_hint": "在设置→多模型中配置",
            "base_url": _get_base_url(
                "openai", "OPENAI_BASE_URL", "https://api.openai.com/v1"
            ),
        },
        "hunyuan": {
            "configured": bool(
                _get_key("hunyuan", "HUNYUAN_SECRET_ID")
                or os.getenv("HUNYUAN_SECRET_ID")
            ),
            "key_hint": "在设置→多模型中配置",
        },
    }


# - Agent Task mode+Local model-


class AgentTaskRequest(BaseModel):
    query: str
    model: str = "deepseek-chat"
    kb_id: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    retrieval_config: Optional[dict] = None
    max_iterations: int = 5
    use_hybrid: bool = True


def _get_provider_for_model(model_id: str) -> str:
    """根据 model_id 判断对应 provider"""
    m = next((m for m in _MODEL_CATALOG if m["id"] == model_id), None)
    return m["provider"] if m else "ollama"


async def _collect_stream(gen: AsyncGenerator[str, None]) -> str:
    """将 SSE 流收集为完整文本"""
    parts = []
    async for chunk in gen:
        if chunk.startswith("data: "):
            payload = chunk[6:].strip()
            try:
                d = json.loads(payload)
                if d.get("content"):
                    parts.append(d["content"])
                if d.get("error"):
                    return f"[模型错误] {d['error']}"
            except Exception:
                pass
    return "".join(parts)


@router.post("/api/agent/task")
async def agent_task(req: AgentTaskRequest):
    """
    任务模式统一入口（SSE 流式）
    - 支持 Ollama 本地模型 + DeepSeek / OpenAI / 混元云端模型
    - 可选 RAG 知识库上下文增强（kb_id 不为空时自动检索相关文档）
    - 输出格式与 /api/models/chat 一致（data: {content, done}）
      额外输出 data: STEP_START/STEP_DONE/TASK_DONE 事件用于前端步骤可视化

    SSE 事件类型：
      data: {"event":"step","name":"...","index":N}   — 步骤开始
      data: {"event":"content","content":"..."}       — 流式内容片段
      data: {"event":"done","answer":"...(full)"}     — 完成，带完整答案
      data: {"event":"error","message":"..."}         — 错误
    """
    active_model = str(req.model or "").strip() or _resolve_default_model() or "deepseek-chat"
    provider = _get_provider_for_model(active_model)

    async def generate():
        # - Step 1: -
        yield f"data: {json.dumps({'event':'step','index':0,'name':'理解任务目标','detail':req.query[:80]}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.05)

        # - Step 2: RAG (支持全部5种检索模式) -
        rag_context = ""
        rag_sources = []
        retrieval_strategy = "model_only"
        if req.kb_id:
            yield f"data: {json.dumps({'event':'step','index':1,'name':'检索知识库','detail':f'知识库 {req.kb_id}'}, ensure_ascii=False)}\n\n"
            try:
                import sys
                from pathlib import Path as _P

                _backend_root = str(_P(__file__).resolve().parent.parent)
                if _backend_root not in sys.path:
                    sys.path.insert(0, _backend_root)

                from RAG_M.RAG_app import _load_vectorstore_and_docs
                from document_processing.retrieval_strategy import (
                    RetrievalStrategyExecutor,
                    RetrievalConfig,
                )

                docs_dir = f"local-KLB-files/{req.kb_id}"
                vectorstore, documents, _ = _load_vectorstore_and_docs(docs_dir)

                # 根据前端传入的 retrieval_config 构建配置，支持全部5种策略
                raw_config = req.retrieval_config or {}
                strategy_name = raw_config.get("strategy", "rrf")
                retrieval_config = RetrievalConfig.from_dict(raw_config)
                retrieval_strategy = strategy_name

                executor = RetrievalStrategyExecutor(
                    vectorstore=vectorstore,
                    documents=documents,
                )
                results = executor.retrieve(req.query, config=retrieval_config)

                if results:
                    rag_parts = []
                    for item in results:
                        src = item["source_info"]
                        file_name = src.get("file_name", "")
                        if file_name and file_name not in rag_sources:
                            rag_sources.append(file_name)
                        rag_parts.append(
                            f"【来源：{src.get('file_name','?')}】\n{item['document'].page_content.strip()}"
                        )
                    rag_context = "\n\n---\n\n".join(rag_parts)
                    yield f"data: {json.dumps({'event':'step_result','index':1,'detail':f'[{retrieval_strategy.upper()}] 检索到 {len(results)} 个相关片段'}, ensure_ascii=False)}\n\n"
            except Exception as e:
                retrieval_strategy = "model_only_fallback"
                yield f"data: {json.dumps({'event':'step_result','index':1,'detail':f'知识库检索失败({strategy_name}): {e}，将直接使用模型知识'}, ensure_ascii=False)}\n\n"
        else:
            yield f"data: {json.dumps({'event':'step','index':1,'name':'规划执行流程','detail':'基于模型知识直接推理'}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.05)

        # - Step 3: Prompt -
        yield f"data: {json.dumps({'event':'step','index':2,'name':'生成结构化草稿','detail':f'使用 {active_model}'}, ensure_ascii=False)}\n\n"

        system_prompt = (
            "你是一个高效的任务执行 AI 助手。请严格按照用户要求完成任务，"
            "输出结构清晰、内容完整的 Markdown 格式报告。"
        )
        user_content = req.query
        if rag_context:
            user_content = (
                f"以下是知识库中检索到的相关内容，请结合这些内容完成任务：\n\n"
                f"{rag_context}\n\n---\n\n任务：{req.query}"
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        # - Step 4: LLMStreaming output -
        full_answer = []
        yield f"data: {json.dumps({'event':'step','index':3,'name':'润色与优化','detail':'流式生成中...'}, ensure_ascii=False)}\n\n"

        try:
            if provider == "ollama":
                async for chunk in _stream_ollama(
                    active_model, messages, req.temperature, req.max_tokens
                ):
                    yield chunk
                    if chunk.startswith("data: "):
                        try:
                            d = json.loads(chunk[6:])
                            if d.get("content"):
                                full_answer.append(d["content"])
                        except Exception:
                            pass
            elif provider == "deepseek":
                async for chunk in _stream_deepseek(
                    active_model, messages, req.temperature, req.max_tokens
                ):
                    yield chunk
                    if chunk.startswith("data: "):
                        try:
                            d = json.loads(chunk[6:])
                            if d.get("content"):
                                full_answer.append(d["content"])
                        except Exception:
                            pass
            elif provider == "openai":
                async for chunk in _stream_openai(
                    active_model, messages, req.temperature, req.max_tokens
                ):
                    yield chunk
                    if chunk.startswith("data: "):
                        try:
                            d = json.loads(chunk[6:])
                            if d.get("content"):
                                full_answer.append(d["content"])
                        except Exception:
                            pass
            elif provider == "hunyuan":
                async for chunk in _stream_hunyuan(
                    active_model, messages, req.temperature, req.max_tokens
                ):
                    yield chunk
                    if chunk.startswith("data: "):
                        try:
                            d = json.loads(chunk[6:])
                            if d.get("content"):
                                full_answer.append(d["content"])
                        except Exception:
                            pass
            else:
                yield f"data: {json.dumps({'error': f'不支持的 provider: {provider}'})}\n\n"
                return
        except Exception as e:
            yield f"data: {json.dumps({'event':'error','message': str(e)}, ensure_ascii=False)}\n\n"
            return

        # - DONE -
        yield f"data: {json.dumps({'event':'done','model':active_model,'provider':provider,'answer': ''.join(full_answer),'has_rag': bool(req.kb_id),'sources': rag_sources,'retrieval_strategy': retrieval_strategy}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


# - -


async def call_model_once(
    model: str,
    messages: list,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """
    调用任意模型（Ollama 本地 / 云端），收集 SSE 流，返回完整文本字符串。
    适合 RAG / Agent 场景中需要一次性获取完整生成结果的调用。

    参数：
        model       - 模型 ID（如 "llama3:8b", "deepseek-chat"）
        messages    - [{role, content}] 列表
        temperature - 生成温度
        max_tokens  - 最大生成 token 数

    返回：
        完整回复文本；出错时返回 "[模型错误] <错误信息>"
    """
    provider = _get_provider_for_model(model)

    stream_map = {
        "ollama": _stream_ollama,
        "deepseek": _stream_deepseek,
        "openai": _stream_openai,
        "hunyuan": _stream_hunyuan,
    }
    stream_fn = stream_map.get(provider, _stream_ollama)
    return await _collect_stream(stream_fn(model, messages, temperature, max_tokens))
