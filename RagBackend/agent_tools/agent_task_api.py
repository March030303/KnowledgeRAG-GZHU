"""
agent_task_api.py
Agent 任务执行 SSE 端点
- 接受自然语言任务描述，自动拆解步骤并流式执行
- 支持文件上传（多模态输入）
- 复用 multi_model 的流式生成能力
"""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import AsyncGenerator, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["Agent 任务执行"])

# sys.path
_backend_root = str(Path(__file__).resolve().parent.parent)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)


def _get_provider(model_id: str) -> tuple[str, str]:
    """根据 model_id 判断 provider"""
    if model_id.startswith("cloud:"):
        parts = model_id.split(":", 2)
        provider = parts[1] if len(parts) > 1 else "ollama"
        real_model = parts[2] if len(parts) > 2 else "deepseek-chat"
        return real_model, provider

    cloud_prefixes = {
        "deepseek": "deepseek",
        "gpt": "openai",
        "o1": "openai",
        "o3": "openai",
        "hunyuan": "hunyuan",
        "claude": "openai",
    }
    lower = model_id.lower()
    for prefix, provider in cloud_prefixes.items():
        if lower.startswith(prefix):
            return model_id, provider
    return model_id, "ollama"


def _get_default_model() -> str:
    try:
        from models.user_model_config import get_effective_config
        cfg = get_effective_config()
        return cfg.llm_model or "deepseek-chat"
    except Exception:
        return os.getenv("MODEL", "deepseek-chat")


async def _stream_llm(
    model: str, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096
) -> AsyncGenerator[str, None]:
    """统一调用 LLM 流式输出，复用 model_router 的能力"""
    real_model, provider = _get_provider(model)

    try:
        if provider == "ollama":
            async for chunk in _stream_ollama(real_model, messages, temperature, max_tokens):
                yield chunk
        else:
            from multi_model.model_router import _stream_deepseek, _stream_hunyuan, _stream_openai

            stream_fn = {
                "deepseek": _stream_deepseek,
                "openai": _stream_openai,
                "hunyuan": _stream_hunyuan,
            }.get(provider, _stream_deepseek)

            async for chunk in stream_fn(real_model, messages, temperature, max_tokens):
                if chunk.startswith("data: "):
                    raw = chunk[6:].strip()
                    if not raw:
                        continue
                    try:
                        d = json.loads(raw)
                        token = d.get("content", "")
                        if token:
                            yield token
                        if d.get("done"):
                            return
                    except Exception:
                        if raw and raw != "[DONE]":
                            yield raw
    except Exception as e:
        logger.error(f"LLM 流式生成失败: {e}")
        yield f"[ERROR] {e}"


async def _stream_ollama(
    model: str, messages: list[dict], temperature: float, max_tokens: int
) -> AsyncGenerator[str, None]:
    """直连 Ollama /api/chat 流式输出"""
    import httpx

    host = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    timeout = 120
    try:
        from models.user_model_config import get_effective_config
        cfg = get_effective_config()
        host = cfg.ollama_base_url or host
        model = cfg.llm_model or model
        timeout = cfg.timeout or timeout
    except Exception:
        pass

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", f"{host}/api/chat", json=payload) as resp:
                if resp.status_code != 200:
                    yield f"data: [ERROR] Ollama 返回 {resp.status_code}\n\n"
                    return
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        token = data.get("message", {}).get("content", "")
                        if token:
                            yield token
                        if data.get("done"):
                            return
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        yield f"[ERROR] Ollama 连接失败: {e}"


def _extract_file_content(file_path: str, filename: str) -> str:
    """从上传文件中提取文本内容（复用 OCR 模块）"""
    try:
        from knowledge.ocr_parser import extract_content

        with open(file_path, "rb") as f:
            content = f.read()
        text = extract_content(content, filename, "")
        return text if not text.startswith("[") else ""
    except Exception as e:
        logger.warning(f"文件内容提取失败: {e}")
        return ""


@router.post("/task")
async def agent_task(
    query: str = Form(...),
    model: str = Form(default=""),
    kb_id: Optional[str] = Form(default=None),
    temperature: float = Form(default=0.7),
    max_tokens: int = Form(default=4096),
    files: List[UploadFile] = File(default=[]),
):
    """
    Agent 任务执行端点（SSE 流式）
    - 接受任务描述 + 可选文件
    - 自动拆解步骤并流式返回
    """
    model = model or _get_default_model()

    # 提取文件内容
    file_contents: list[dict] = []
    for f in files:
        if not f.filename:
            continue
        suffix = Path(f.filename).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content = await f.read()
            tmp.write(content)
            tmp_path = tmp.name
        try:
            text = _extract_file_content(tmp_path, f.filename)
            file_contents.append({"filename": f.filename, "content": text[:8000]})
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    task_id = uuid.uuid4().hex[:8]

    async def generate() -> AsyncGenerator[str, None]:
        # Step 0: 理解任务
        yield f"data: {json.dumps({'event': 'step', 'index': 0, 'name': '理解任务目标', 'detail': query[:60]}, ensure_ascii=False)}\n\n"

        # 构建上下文
        file_ctx = ""
        if file_contents:
            file_parts = []
            for fc in file_contents:
                if fc["content"]:
                    file_parts.append(f"【文件: {fc['filename']}】\n{fc['content'][:4000]}")
                else:
                    file_parts.append(f"【文件: {fc['filename']}】（无法提取文本内容）")
            file_ctx = "\n\n".join(file_parts)

        # Step 1: 规划/检索
        step1_name = "检索知识库" if kb_id else "规划执行流程"
        step1_detail = f"知识库 {kb_id}" if kb_id else "基于模型知识推理"
        yield f"data: {json.dumps({'event': 'step', 'index': 1, 'name': step1_name, 'detail': step1_detail}, ensure_ascii=False)}\n\n"

        # Step 2: 生成草稿
        yield f"data: {json.dumps({'event': 'step', 'index': 2, 'name': '生成结构化草稿', 'detail': f'使用 {model}'}, ensure_ascii=False)}\n\n"

        # Step 3: 润色优化
        yield f"data: {json.dumps({'event': 'step', 'index': 3, 'name': '润色与优化', 'detail': '流式生成输出'}, ensure_ascii=False)}\n\n"

        # 构建系统提示
        system_prompt = """你是一个智能任务执行助手。请根据用户的任务描述，生成高质量、结构化的输出。

要求：
- 内容准确、逻辑清晰
- 使用 Markdown 格式输出
- 如果有文件内容作为参考，请基于文件内容回答
- 适当使用标题、列表、表格等格式增强可读性"""

        if kb_id:
            system_prompt += f"\n\n当前任务需要参考知识库 {kb_id} 的内容。"

        user_content = query
        if file_ctx:
            user_content += f"\n\n参考文件内容：\n{file_ctx}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        # 流式生成
        try:
            async for token in _stream_llm(model, messages, temperature, max_tokens):
                if token.startswith("[ERROR]"):
                    yield f"data: {json.dumps({'event': 'error', 'message': token}, ensure_ascii=False)}\n\n"
                    return
                yield f"data: {json.dumps({'content': token, 'done': False}, ensure_ascii=False)}\n\n"

            # 完成
            yield f"data: {json.dumps({'content': '', 'done': True}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'event': 'done'}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"Agent 任务执行失败: {e}", exc_info=True)
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
