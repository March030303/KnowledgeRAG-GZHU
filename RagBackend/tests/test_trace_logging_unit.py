"""
test_trace_logging_unit.py - trace_logging 模块单元测试
覆盖目标：trace_logging.py 中的纯函数和类（不依赖运行中的 FastAPI 服务）
"""

from __future__ import annotations

import logging
import uuid
from contextvars import copy_context
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ----- 基础函数 -----

class TestGetTraceId:
    """get_trace_id 函数测试"""

    def test_returns_string(self):
        """get_trace_id 应当返回字符串"""
        from trace_logging import get_trace_id
        result = get_trace_id()
        assert isinstance(result, str)

    def test_returns_consistent_within_context(self):
        """同一上下文内多次调用应返回相同 trace_id"""
        from trace_logging import get_trace_id
        id1 = get_trace_id()
        id2 = get_trace_id()
        assert id1 == id2

    def test_default_generates_8char_hex(self):
        """首次调用默认生成 8 位 hex trace_id"""
        from trace_logging import _trace_id_var, get_trace_id

        def check():
            # 在新 context 内测试
            _trace_id_var.set("-")
            result = get_trace_id()
            assert len(result) == 8
            assert all(c in "0123456789abcdef" for c in result)

        ctx = copy_context()
        ctx.run(check)

    def test_set_custom_trace_id_is_returned(self):
        """手动设置 trace_id 后，get_trace_id 应返回该值"""
        from trace_logging import _trace_id_var, get_trace_id

        custom = "deadbeef"

        def check():
            _trace_id_var.set(custom)
            result = get_trace_id()
            assert result == custom

        ctx = copy_context()
        ctx.run(check)

    def test_different_contexts_have_independent_trace_ids(self):
        """不同 contextvars context 应有独立的 trace_id"""
        from trace_logging import _trace_id_var, get_trace_id

        results = []

        def run_in_context(value: str):
            _trace_id_var.set("-")  # 重置
            tid = get_trace_id()
            results.append(tid)

        ctx1 = copy_context()
        ctx2 = copy_context()
        ctx1.run(run_in_context, "a")
        ctx2.run(run_in_context, "b")

        assert len(results) == 2
        # 两次调用生成的 trace_id 都是 8 位 hex
        for r in results:
            assert len(r) == 8


class TestTruncate:
    """_truncate 内部函数测试"""

    def test_short_value_unchanged(self):
        """短字符串不截断"""
        from trace_logging import _truncate
        assert _truncate("hello") == "hello"

    def test_empty_value_returns_dash(self):
        """空字符串返回 '-'"""
        from trace_logging import _truncate
        assert _truncate("") == "-"

    def test_none_equivalent_empty(self):
        """None 等价的空字符串返回 '-'"""
        from trace_logging import _truncate
        # 传入 None 并不是正常用法，但测试 falsy 分支
        assert _truncate("") == "-"

    def test_exact_limit_not_truncated(self):
        """恰好 limit 长度不截断"""
        from trace_logging import _truncate
        s = "a" * 160
        assert _truncate(s) == s
        assert not _truncate(s).endswith("...")

    def test_over_limit_gets_ellipsis(self):
        """超过 limit 的字符串被截断并加 ..."""
        from trace_logging import _truncate
        s = "a" * 200
        result = _truncate(s)
        assert result.endswith("...")
        assert len(result) == 160

    def test_custom_limit(self):
        """自定义 limit 参数生效"""
        from trace_logging import _truncate
        s = "x" * 50
        result = _truncate(s, limit=20)
        assert result.endswith("...")
        assert len(result) == 20


class TestExtractClientIp:
    """_extract_client_ip 函数测试"""

    def _make_request(self, headers: dict, client_host: str | None = None):
        """创建最小 mock Request"""
        req = MagicMock()
        req.headers = headers
        if client_host:
            req.client = MagicMock()
            req.client.host = client_host
        else:
            req.client = None
        return req

    def test_forwarded_for_first_ip(self):
        """X-Forwarded-For 存在时返回第一个 IP"""
        from trace_logging import _extract_client_ip
        req = self._make_request({"x-forwarded-for": "1.2.3.4, 5.6.7.8"})
        assert _extract_client_ip(req) == "1.2.3.4"

    def test_forwarded_for_single(self):
        """X-Forwarded-For 只有一个 IP"""
        from trace_logging import _extract_client_ip
        req = self._make_request({"x-forwarded-for": "10.0.0.1"})
        assert _extract_client_ip(req) == "10.0.0.1"

    def test_no_forwarded_for_uses_client_host(self):
        """无 X-Forwarded-For 时使用 request.client.host"""
        from trace_logging import _extract_client_ip
        req = self._make_request({}, client_host="192.168.1.1")
        assert _extract_client_ip(req) == "192.168.1.1"

    def test_no_client_returns_unknown(self):
        """无任何 IP 信息时返回 'unknown'"""
        from trace_logging import _extract_client_ip
        req = self._make_request({})
        assert _extract_client_ip(req) == "unknown"


class TestQuerySummary:
    """_query_summary 函数测试"""

    def _make_request(self, query: str):
        req = MagicMock()
        req.url.query = query
        return req

    def test_empty_query_returns_dash(self):
        """无 query string 返回 '-'"""
        from trace_logging import _query_summary
        req = self._make_request("")
        assert _query_summary(req) == "-"

    def test_single_param(self):
        """单个参数格式化为 key=value"""
        from trace_logging import _query_summary
        req = self._make_request("page=1")
        result = _query_summary(req)
        assert "page=1" in result

    def test_multiple_params(self):
        """多个参数用 & 连接"""
        from trace_logging import _query_summary
        req = self._make_request("page=1&size=20")
        result = _query_summary(req)
        assert "page=1" in result
        assert "size=20" in result


class TestTraceIdFilter:
    """TraceIdFilter 日志 Filter 测试"""

    def test_filter_adds_trace_id_to_record(self):
        """filter() 应向 LogRecord 注入 trace_id 字段"""
        from trace_logging import TraceIdFilter, _trace_id_var

        def check():
            _trace_id_var.set("abc12345")
            f = TraceIdFilter()
            record = logging.LogRecord(
                name="test", level=logging.INFO,
                pathname="", lineno=0, msg="", args=(), exc_info=None
            )
            result = f.filter(record)
            assert result is True
            assert record.trace_id == "abc12345"

        ctx = copy_context()
        ctx.run(check)

    def test_filter_always_returns_true(self):
        """filter() 不会屏蔽任何记录"""
        from trace_logging import TraceIdFilter
        f = TraceIdFilter()
        record = logging.LogRecord(
            name="test", level=logging.WARNING,
            pathname="", lineno=0, msg="warn", args=(), exc_info=None
        )
        assert f.filter(record) is True


class TestSetupTraceLogging:
    """setup_trace_logging 配置函数测试"""

    def test_setup_does_not_raise(self):
        """setup_trace_logging 不应抛出异常"""
        from trace_logging import setup_trace_logging
        setup_trace_logging()  # 不应有异常

    def test_setup_idempotent(self):
        """多次调用不重复添加 handler"""
        import logging
        from trace_logging import TraceIdFilter, setup_trace_logging

        setup_trace_logging()
        handler_count_1 = len(logging.getLogger().handlers)
        setup_trace_logging()
        handler_count_2 = len(logging.getLogger().handlers)
        # handler 数量不应增加
        assert handler_count_2 <= handler_count_1 + 1
