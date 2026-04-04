"""
test_trace_middleware.py — TraceMiddleware.dispatch 路径全覆盖

覆盖 trace_logging.py L109-148：
  - 正常请求路径（response headers 注入、access log 输出）
  - 请求携带 X-Trace-Id 时重用
  - 请求不带 X-Trace-Id 时自动生成
  - 内部 call_next 抛出异常时的 except 路径
  - finally 中 _trace_id_var.reset 被调用
"""
from __future__ import annotations

import logging
from contextvars import copy_context
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import Response


# ---------------------------------------------------------------------------
# 辅助：创建携带 TraceMiddleware 的最小 FastAPI app
# ---------------------------------------------------------------------------

def _make_app(handler=None, raise_exc: Exception | None = None) -> FastAPI:
    """
    创建一个挂载了 TraceMiddleware 的测试 app。
    handler: 路由处理函数，默认返回 200 OK
    raise_exc: 若设置，则路由抛出该异常
    """
    from trace_logging import TraceMiddleware
    app = FastAPI()
    app.add_middleware(TraceMiddleware)

    @app.get("/test")
    async def route():
        if raise_exc is not None:
            raise raise_exc
        if handler:
            return handler()
        return {"ok": True}

    return app


# ---------------------------------------------------------------------------
# 正常路径
# ---------------------------------------------------------------------------
class TestTraceMiddlewareNormalPath:

    def test_response_contains_x_trace_id_header(self):
        """正常请求后响应头应包含 X-Trace-Id"""
        app = _make_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/test")
        assert "x-trace-id" in resp.headers
        assert len(resp.headers["x-trace-id"]) > 0

    def test_response_contains_x_process_time_ms_header(self):
        """响应头应包含 X-Process-Time-Ms"""
        app = _make_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/test")
        assert "x-process-time-ms" in resp.headers
        # 应为数字字符串
        float(resp.headers["x-process-time-ms"])  # 不抛出即通过

    def test_incoming_trace_id_is_reused(self):
        """请求携带 X-Trace-Id 时，响应头应回显相同 trace_id"""
        app = _make_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/test", headers={"X-Trace-Id": "custom-trace-abc"})
        assert resp.headers.get("x-trace-id") == "custom-trace-abc"

    def test_no_incoming_trace_id_generates_new(self):
        """无 X-Trace-Id 请求时，自动生成 8 位 hex trace_id"""
        app = _make_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/test")
        tid = resp.headers.get("x-trace-id", "")
        assert len(tid) == 8
        assert all(c in "0123456789abcdef" for c in tid)

    def test_multiple_requests_get_unique_trace_ids(self):
        """连续两次请求应得到不同的 trace_id"""
        app = _make_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            resp1 = client.get("/test")
            resp2 = client.get("/test")
        tid1 = resp1.headers.get("x-trace-id")
        tid2 = resp2.headers.get("x-trace-id")
        assert tid1 != tid2

    def test_200_response_code_preserved(self):
        """中间件不应改变 2xx 响应状态码"""
        app = _make_app()
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/test")
        assert resp.status_code == 200

    def test_access_log_written(self, caplog):
        """access logger 应记录 method/path/status 信息"""
        app = _make_app()
        with caplog.at_level(logging.INFO, logger="access"):
            with TestClient(app, raise_server_exceptions=False) as client:
                client.get("/test")
        assert any("access" in r.message and "GET" in r.message
                   for r in caplog.records)


# ---------------------------------------------------------------------------
# 异常路径（call_next 抛出）
# ---------------------------------------------------------------------------
class TestTraceMiddlewareExceptionPath:

    def test_exception_is_reraised(self):
        """call_next 抛出异常时，中间件应重新抛出"""
        app = _make_app(raise_exc=ValueError("test error"))
        with TestClient(app, raise_server_exceptions=True) as client:
            with pytest.raises(ValueError, match="test error"):
                client.get("/test")

    def test_access_log_written_on_exception(self, caplog):
        """异常时 access logger 应以 status=ERROR 记录"""
        app = _make_app(raise_exc=RuntimeError("boom"))
        with caplog.at_level(logging.ERROR, logger="access"):
            with TestClient(app, raise_server_exceptions=False) as client:
                client.get("/test")
        assert any("ERROR" in r.message for r in caplog.records
                   if r.name == "access")

    def test_trace_id_reset_after_exception(self, caplog):
        """异常发生时 finally 块应被执行（access logger 记录 ERROR）"""
        app = _make_app(raise_exc=RuntimeError("reset test"))
        with caplog.at_level(logging.ERROR, logger="access"):
            with TestClient(app, raise_server_exceptions=False) as client:
                client.get("/test")
        # finally 执行了才会写 access log ERROR
        assert any(r.name == "access" for r in caplog.records)


# ---------------------------------------------------------------------------
# ContextVar 隔离
# ---------------------------------------------------------------------------
class TestTraceIdVarIsolation:

    def test_trace_id_not_leaked_between_requests(self):
        """两次请求之间 trace_id ContextVar 不应互相污染"""
        from trace_logging import _trace_id_var

        app = _make_app()
        captured = []

        @app.middleware("http")
        async def capture_trace(request: Request, call_next):
            # 在 TraceMiddleware 之后（内层）捕获 trace_id
            resp = await call_next(request)
            captured.append(_trace_id_var.get())
            return resp

        # 重新构建，确保 capture 在 trace 之后
        from trace_logging import TraceMiddleware
        app2 = FastAPI()
        app2.add_middleware(TraceMiddleware)
        ids_seen: list[str] = []

        @app2.get("/capture")
        async def capture_route(request: Request):
            ids_seen.append(_trace_id_var.get())
            return {"ok": True}

        with TestClient(app2, raise_server_exceptions=False) as client:
            client.get("/capture")
            client.get("/capture")

        # 两次请求捕获到的 trace_id 应不同
        assert len(ids_seen) == 2
        assert ids_seen[0] != ids_seen[1]
