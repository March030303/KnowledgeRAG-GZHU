"""
trace_logging.py — 结构化日志 TraceID 中间件

每个 HTTP 请求自动生成唯一 trace_id，贯穿整个请求生命周期：
  - 请求进入时写入 contextvars.ContextVar
  - 所有日志自动携带 trace_id
  - 响应头返回 X-Trace-Id，方便前端/排查关联
  - 响应头返回 X-Process-Time-Ms，方便 Apifox/运维快速查看耗时
"""

from __future__ import annotations

import logging
import time
import uuid
from contextvars import ContextVar
from typing import Callable, cast
from urllib.parse import parse_qsl

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# - ContextVar / trace_id -
_trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")


def get_trace_id() -> str:
    """获取当前请求的 trace_id（在任意代码中均可调用）"""
    trace_id = _trace_id_var.get()
    if trace_id == "-":
        trace_id = uuid.uuid4().hex[:8]
        _trace_id_var.set(trace_id)
    return trace_id


class TraceIdFilter(logging.Filter):
    """为所有日志记录自动补充 trace_id 字段。"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id()
        return True


def setup_trace_logging(level: int = logging.INFO) -> None:
    """
    配置全局结构化日志格式（含 trace_id）。
    在 main.py 顶部调用一次即可。
    """
    fmt = (
        "%(asctime)s | %(levelname)-8s | trace=%(trace_id)s | "
        "%(name)s:%(lineno)d | %(message)s"
    )
    handler = logging.StreamHandler()
    handler.addFilter(TraceIdFilter())
    handler.setFormatter(logging.Formatter(fmt))

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    has_trace_handler = any(
        isinstance(existing_handler, logging.StreamHandler)
        and any(
            isinstance(filter_item, TraceIdFilter)
            for filter_item in existing_handler.filters
        )
        for existing_handler in root_logger.handlers
    )
    if not has_trace_handler:
        root_logger.handlers.clear()
        root_logger.addHandler(handler)


def _truncate(value: str, limit: int = 160) -> str:
    """限制日志字段长度，避免 access log 被超长请求污染。"""
    if not value:
        return "-"
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3]}..."


def _extract_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _query_summary(request: Request) -> str:
    if not request.url.query:
        return "-"
    parts = [
        f"{key}={value}"
        for key, value in parse_qsl(request.url.query, keep_blank_values=True)
    ]
    return _truncate("&".join(parts), 200)


class TraceMiddleware(BaseHTTPMiddleware):
    """
    每个请求注入唯一 trace_id，并在响应头中返回，方便前端/日志关联。

    日志格式示例：
        2026-03-27 17:30:01 | INFO     | trace=a3f8c1d2 | access:110 | access method=GET path=/api/audit/stats status=200 duration_ms=12.4 client_ip=127.0.0.1 query="page=1&page_size=20" ua="Apifox/2.x"
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        trace_id = request.headers.get("X-Trace-Id") or uuid.uuid4().hex[:8]
        token = _trace_id_var.set(trace_id)

        access_logger = logging.getLogger("access")
        client_ip = _extract_client_ip(request)
        query_summary = _query_summary(request)
        user_agent = _truncate(request.headers.get("user-agent", "-"), 120)
        start = time.perf_counter()

        try:
            response = cast(Response, await call_next(request))

            elapsed_ms = (time.perf_counter() - start) * 1000
            response.headers["X-Trace-Id"] = trace_id
            response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"
            access_logger.info(
                'access method=%s path=%s status=%s duration_ms=%.1f client_ip=%s query="%s" ua="%s"',
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
                client_ip,
                query_summary,
                user_agent,
            )
            return response
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            access_logger.exception(
                'access method=%s path=%s status=ERROR duration_ms=%.1f client_ip=%s query="%s" ua="%s"',
                request.method,
                request.url.path,
                elapsed_ms,
                client_ip,
                query_summary,
                user_agent,
            )
            raise
        finally:
            _trace_id_var.reset(token)
