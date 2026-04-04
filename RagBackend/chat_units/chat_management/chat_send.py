"""
chat_send.py — 对话消息发送接口（多模型统一路由版）

支持：
  - Ollama 本地模型（默认，兼容旧行为）
  - DeepSeek / OpenAI / 腾讯混元 等云端模型（通过 model_router 路由）
  - RAG 知识库问答（支持检索策略透传与来源返回）
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, List, Optional

import requests as sync_requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

_backend_root = str(Path(__file__).resolve().parent.parent.parent)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


class ChatMessage(BaseModel):
    role: str
    content: str


class OllamaSettings(BaseModel):
    serverUrl: Optional[str] = None
    timeout: Optional[int] = 60


class SendMessageRequest(BaseModel):
    message: str
    sessionId: Optional[str] = None
    history: Optional[List[dict]] = []
    model: Optional[str] = None
    ollamaSettings: Optional[OllamaSettings] = None
    rag_mode: bool = False
    kb_id: Optional[str] = None
    retrieval_config: Optional[dict] = None


def _get_default_model() -> str:
    try:
        from multi_model.model_router import _resolve_default_model

        return str(_resolve_default_model() or "").strip()
    except Exception:
        try:
            from models.user_model_config import get_effective_config

            return str(get_effective_config().llm_model or "").strip()
        except Exception:
            return str(os.getenv("MODEL", "")).strip()


def _resolve_model(raw_model: Optional[str]) -> tuple[str, str]:
    """解析 model 字段，返回 (real_model_id, provider)。"""
    fallback_model = _get_default_model()
    normalized = str(raw_model or "").strip()
    if not normalized:
        return fallback_model, "ollama"

    if normalized.startswith("cloud:"):
        parts = normalized.split(":", 2)
        provider = parts[1] if len(parts) > 1 else "ollama"
        model_id = parts[2] if len(parts) > 2 else fallback_model
        return model_id, provider

    try:
        from multi_model.model_router import _build_model_list

        for item in _build_model_list():
            if item["id"] == normalized:
                return normalized, item.get("provider", "ollama")
    except Exception:
        pass

    return normalized, "ollama"


async def _call_cloud_model(
    model_id: str, provider: str, messages: list, timeout: int = 60
) -> str:
    """调用云端模型（复用 model_router 的流式函数，收集完整回复）。"""
    try:
        from multi_model.model_router import (
            _collect_stream,
            _stream_deepseek,
            _stream_hunyuan,
            _stream_openai,
        )
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"无法加载 model_router: {e}")

    stream_map = {
        "deepseek": _stream_deepseek,
        "openai": _stream_openai,
        "hunyuan": _stream_hunyuan,
    }
    stream_fn = stream_map.get(provider)
    if not stream_fn:
        raise HTTPException(status_code=400, detail=f"不支持的云端 provider: {provider}")

    try:
        reply = await _collect_stream(
            stream_fn(model_id, messages, temperature=0.7, max_tokens=2048)
        )
        if not reply:
            raise HTTPException(status_code=500, detail="云端模型返回空回复")
        return reply
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"云端模型调用失败: {e}")


def _call_ollama_model(
    model_id: str, messages: list[dict[str, Any]], server_url: str, timeout: int
) -> str:
    response = sync_requests.post(
        f"{server_url.rstrip('/')}/api/chat",
        json={"model": model_id, "messages": messages, "stream": False},
        timeout=timeout,
    )

    if response.status_code != 200:
        err_text = response.text or ""
        if "more system memory" in err_text or "memory" in err_text.lower():
            detail = (
                f"模型 [{model_id}] 所需内存不足，请关闭其他程序或换用更小的模型"
            )
        elif "model" in err_text.lower() and "not found" in err_text.lower():
            detail = f"模型 [{model_id}] 未安装，请先执行: ollama pull {model_id}"
        else:
            detail = f"Ollama 服务错误（状态码 {response.status_code}）: {err_text[:200]}"
        raise HTTPException(status_code=500, detail=detail)

    data = response.json()
    reply = data.get("message", {}).get("content", "")
    return reply or data.get("response", "（模型无回复）")


async def _call_model(
    model_id: str,
    provider: str,
    messages: list[dict[str, Any]],
    ollama_settings: Optional[OllamaSettings] = None,
) -> str:
    if provider in ("deepseek", "openai", "hunyuan"):
        return await _call_cloud_model(model_id, provider, messages)

    server_url = (
        ollama_settings.serverUrl.rstrip("/")
        if ollama_settings and ollama_settings.serverUrl
        else OLLAMA_BASE_URL
    )
    timeout = (
        ollama_settings.timeout if ollama_settings and ollama_settings.timeout else 60
    )
    return _call_ollama_model(model_id, messages, server_url, timeout)


def _normalize_sources(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sources = []
    for item in results:
        src = item.get("source_info", {})
        sources.append(
            {
                "filename": src.get("file_name") or "未知来源",
                "content": item.get("content_preview")
                or item.get("document").page_content[:200],
                "score": src.get("score", src.get("rrf_score")),
                "page": src.get("page"),
                "source_path": src.get("source_path", ""),
            }
        )
    return sources


async def _build_rag_reply(
    req: SendMessageRequest,
    model_id: str,
    provider: str,
) -> dict[str, Any]:
    try:
        from RAG_M.RAG_app import _load_vectorstore_and_docs
        from document_processing.retrieval_strategy import (
            RetrievalConfig,
            RetrievalStrategyExecutor,
        )
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"无法加载 RAG 依赖: {e}")

    kb_dir = Path(_backend_root) / "local-KLB-files" / str(req.kb_id)
    if not kb_dir.exists():
        raise HTTPException(status_code=404, detail=f"知识库不存在: {req.kb_id}")

    vectorstore, documents, _ = _load_vectorstore_and_docs(str(kb_dir))
    retrieval_cfg = RetrievalConfig.from_dict(req.retrieval_config or {})
    executor = RetrievalStrategyExecutor(vectorstore=vectorstore, documents=documents)
    results = executor.retrieve(req.message, retrieval_cfg)
    sources = _normalize_sources(results)

    if not results:
        return {
            "reply": "未在当前知识库中检索到相关内容，暂时无法给出可靠回答。",
            "model": model_id,
            "provider": provider,
            "sources": [],
            "retrieval_mode": retrieval_cfg.strategy,
        }

    context_blocks = []
    for item in results:
        src = item["source_info"]
        context_blocks.append(
            f"【来源：{src.get('file_name', '未知来源')}】\n{item['document'].page_content.strip()}"
        )
    context = "\n\n---\n\n".join(context_blocks)

    history_messages = []
    for msg in req.history or []:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            history_messages.append({"role": role, "content": content})
    history_messages = history_messages[-6:]

    messages = [
        {
            "role": "system",
            "content": (
                "你是知识库问答助手。必须优先依据提供的知识库片段回答，"
                "不要编造未出现在资料中的事实；如果资料不足，请明确说明。"
            ),
        },
        *history_messages,
        {
            "role": "user",
            "content": (
                f"请基于以下知识库检索结果回答问题。\n\n{context}\n\n"
                f"---\n\n用户问题：{req.message}"
            ),
        },
    ]
    reply = await _call_model(model_id, provider, messages, req.ollamaSettings)
    return {
        "reply": reply,
        "model": model_id,
        "provider": provider,
        "sources": sources,
        "retrieval_mode": retrieval_cfg.strategy,
    }


@router.post("/send-message")
async def send_message(req: SendMessageRequest):
    """
    发送消息到 AI 模型，返回回复。
    自动识别本地 Ollama 模型和云端模型（DeepSeek / OpenAI / 混元）。
    当 rag_mode=true 且 kb_id 存在时，走知识库检索增强链路并返回引用来源。
    """
    raw_model = req.model or _get_default_model()
    model_id, provider = _resolve_model(raw_model)

    if req.rag_mode and req.kb_id:
        logger.info(
            "[chat_send] RAG 对话: provider=%s, model=%s, kb_id=%s, strategy=%s",
            provider,
            model_id,
            req.kb_id,
            (req.retrieval_config or {}).get("strategy", "rrf"),
        )
        return await _build_rag_reply(req, model_id, provider)

    messages = []
    if req.history:
        for msg in req.history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    if not messages or messages[-1].get("content") != req.message:
        messages.append({"role": "user", "content": req.message})

    try:
        logger.info(
            "[chat_send] 普通对话: provider=%s, model=%s, 消息数=%s",
            provider,
            model_id,
            len(messages),
        )
        reply = await _call_model(model_id, provider, messages, req.ollamaSettings)
        return {"reply": reply, "model": model_id, "provider": provider, "sources": []}
    except sync_requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=500,
            detail=(
                f"连接 Ollama 失败，请检查服务是否在运行: "
                f"{req.ollamaSettings.serverUrl if req.ollamaSettings and req.ollamaSettings.serverUrl else OLLAMA_BASE_URL}"
            ),
        )
    except sync_requests.exceptions.Timeout:
        raise HTTPException(
            status_code=500,
            detail="Ollama 响应超时，请尝试更换更小的模型或增加超时时间",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("send_message 未知错误: %s", e)
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")
