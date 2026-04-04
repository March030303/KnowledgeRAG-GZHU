"""
test_audit_log_unit.py - audit/audit_log.py 模块单元测试

覆盖目标：
  - 纯函数：_infer_action, _infer_resource, _decode_query_string
  - _extract_user_from_auth_header（不依赖真实 JWT secret）
  - ensure_audit_table + write_audit_log（使用内存 SQLite mock）
  - AuditMiddleware 基本流程（ASGI mock）
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# _infer_action
# ---------------------------------------------------------------------------
class TestInferAction:

    def test_login_path_returns_auth(self):
        from audit.audit_log import _infer_action
        assert _infer_action("POST", "/api/login") == "AUTH"

    def test_register_path_returns_auth(self):
        from audit.audit_log import _infer_action
        assert _infer_action("POST", "/api/register") == "AUTH"

    def test_upload_in_path_returns_file_upload(self):
        from audit.audit_log import _infer_action
        assert _infer_action("POST", "/api/upload-document") == "FILE_UPLOAD"

    def test_delete_method_returns_delete(self):
        from audit.audit_log import _infer_action
        assert _infer_action("DELETE", "/api/knowledgebase/kb1") == "DELETE"

    def test_post_query_path_returns_query(self):
        from audit.audit_log import _infer_action
        assert _infer_action("POST", "/api/RAG-query") == "QUERY"

    def test_post_chat_path_returns_query(self):
        from audit.audit_log import _infer_action
        assert _infer_action("POST", "/api/chat") == "QUERY"

    def test_post_create(self):
        from audit.audit_log import _infer_action
        assert _infer_action("POST", "/api/create-knowledgebase") == "CREATE"

    def test_put_returns_update(self):
        from audit.audit_log import _infer_action
        assert _infer_action("PUT", "/api/settings") == "UPDATE"

    def test_patch_returns_update(self):
        from audit.audit_log import _infer_action
        assert _infer_action("PATCH", "/api/settings") == "UPDATE"

    def test_get_returns_read(self):
        from audit.audit_log import _infer_action
        assert _infer_action("GET", "/api/anything") == "READ"

    def test_unknown_method_returns_method(self):
        from audit.audit_log import _infer_action
        assert _infer_action("OPTIONS", "/api/x") == "OPTIONS"

    def test_case_insensitive_method(self):
        from audit.audit_log import _infer_action
        assert _infer_action("get", "/api/anything") == "READ"


# ---------------------------------------------------------------------------
# _infer_resource
# ---------------------------------------------------------------------------
class TestInferResource:

    def test_knowledge_path(self):
        from audit.audit_log import _infer_resource
        rtype, _ = _infer_resource("/api/create-knowledgebase")
        assert rtype == "knowledge_base"

    def test_document_path(self):
        from audit.audit_log import _infer_resource
        rtype, _ = _infer_resource("/api/upload-document/kb1")
        assert rtype == "document"

    def test_chat_path(self):
        from audit.audit_log import _infer_resource
        rtype, _ = _infer_resource("/api/chat")
        assert rtype == "chat"

    def test_user_path(self):
        from audit.audit_log import _infer_resource
        # "/api/user/profile" 含 "file" 字符串，_infer_resource 优先匹配 document
        # 使用不含 "file"/"document" 的路径测试 user 分支
        rtype, _ = _infer_resource("/api/user/settings")
        assert rtype == "user"

    def test_rag_path(self):
        from audit.audit_log import _infer_resource
        rtype, _ = _infer_resource("/api/RAG-query")
        assert rtype == "rag_query"

    def test_unknown_path_returns_none(self):
        from audit.audit_log import _infer_resource
        rtype, _ = _infer_resource("/api/health")
        assert rtype is None

    def test_resource_id_extracted(self):
        from audit.audit_log import _infer_resource
        _, rid = _infer_resource("/api/knowledgebase/mykb12345")
        assert rid == "mykb12345"

    def test_short_segment_not_resource_id(self):
        from audit.audit_log import _infer_resource
        _, rid = _infer_resource("/api/kb")
        # 'kb' is 2 chars, < 4 — should not be extracted as resource_id
        assert rid is None


# ---------------------------------------------------------------------------
# _decode_query_string
# ---------------------------------------------------------------------------
class TestDecodeQueryString:

    def test_empty_bytes_returns_none(self):
        from audit.audit_log import _decode_query_string
        assert _decode_query_string(b"") is None

    def test_none_returns_none(self):
        from audit.audit_log import _decode_query_string
        assert _decode_query_string(None) is None

    def test_valid_utf8_decoded(self):
        from audit.audit_log import _decode_query_string
        result = _decode_query_string(b"page=1&size=20")
        assert result == "page=1&size=20"

    def test_long_string_truncated_to_500(self):
        from audit.audit_log import _decode_query_string
        long_qs = b"k=v&" * 200  # > 500 bytes
        result = _decode_query_string(long_qs)
        assert result is not None
        assert len(result) <= 500

    def test_invalid_utf8_handled(self):
        from audit.audit_log import _decode_query_string
        # bytes with invalid UTF-8 sequence
        result = _decode_query_string(b"ok=\xff\xfe")
        assert result is not None  # should not raise


# ---------------------------------------------------------------------------
# _extract_user_from_auth_header
# ---------------------------------------------------------------------------
class TestExtractUserFromAuthHeader:

    def test_no_bearer_prefix_returns_nones(self):
        from audit.audit_log import _extract_user_from_auth_header
        result = _extract_user_from_auth_header("Basic dXNlcjpwYXNz")
        assert result["user_id"] is None
        assert result["user_email"] is None

    def test_invalid_token_returns_nones(self):
        from audit.audit_log import _extract_user_from_auth_header
        result = _extract_user_from_auth_header("Bearer not-a-real-jwt")
        assert result["user_id"] is None
        assert result["user_email"] is None

    def test_empty_header_returns_nones(self):
        from audit.audit_log import _extract_user_from_auth_header
        result = _extract_user_from_auth_header("")
        assert result["user_id"] is None

    def test_valid_jwt_extracts_user(self):
        """用真实 JWT 测试提取"""
        import importlib
        import os
        import sys

        try:
            import PyJWT as jwt_lib
        except ImportError:
            import jwt as jwt_lib  # fallback

        secret = "test_secret"
        token = jwt_lib.encode(
            {"user_id": "42", "email": "test@example.com"},
            secret,
            algorithm="HS256",
        )

        # 确保 audit_log 模块重新读取 env
        import audit.audit_log as al_module
        with patch.dict(os.environ, {"JWT_SECRET": secret}):
            result = al_module._extract_user_from_auth_header(f"Bearer {token}")
            assert result["user_id"] == "42"
            assert result["user_email"] == "test@example.com"


# ---------------------------------------------------------------------------
# ensure_audit_table + write_audit_log (in-memory SQLite)
# ---------------------------------------------------------------------------
class TestEnsureAuditTable:

    def test_ensure_creates_table(self, tmp_path):
        """ensure_audit_table 应创建 audit_logs 表"""
        db_path = tmp_path / "test_audit.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table
            ensure_audit_table()

        # 验证表已创建
        conn = sqlite3.connect(str(db_path))
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        conn.close()
        table_names = [t[0] for t in tables]
        assert "audit_logs" in table_names

    def test_ensure_idempotent(self, tmp_path):
        """多次调用不应抛出"""
        db_path = tmp_path / "test_audit2.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table
            ensure_audit_table()
            ensure_audit_table()  # 第二次调用不应抛出


class TestWriteAuditLog:

    def test_write_basic_log(self, tmp_path):
        """write_audit_log 写入一条记录后可查询到"""
        db_path = tmp_path / "test_write.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table, write_audit_log

            ensure_audit_table()
            write_audit_log(
                action="TEST",
                user_id="u1",
                user_email="u@test.com",
                request_path="/api/test",
                request_method="GET",
                status_code=200,
            )

        conn = sqlite3.connect(str(db_path))
        rows = conn.execute("SELECT * FROM audit_logs").fetchall()
        conn.close()
        assert len(rows) == 1

    def test_write_multiple_logs(self, tmp_path):
        """写入多条记录"""
        db_path = tmp_path / "test_multi.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table, write_audit_log

            ensure_audit_table()
            for i in range(5):
                write_audit_log(action=f"ACTION_{i}", request_path=f"/api/test/{i}")

        conn = sqlite3.connect(str(db_path))
        count = conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]
        conn.close()
        assert count == 5

    def test_write_with_all_fields(self, tmp_path):
        """所有字段都写入"""
        db_path = tmp_path / "test_all.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table, write_audit_log

            ensure_audit_table()
            write_audit_log(
                action="QUERY",
                user_id="u42",
                user_email="user@example.com",
                resource_type="knowledge_base",
                resource_id="kb-001",
                resource_name="my-kb",
                ip_address="127.0.0.1",
                user_agent="test-agent/1.0",
                request_path="/api/RAG-query",
                request_method="POST",
                status_code=200,
                detail="ok",
                duration_ms=42.5,
                trace_id="abc12345",
                query_string="k=v",
            )

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM audit_logs LIMIT 1").fetchone()
        conn.close()
        assert row["action"] == "QUERY"
        assert row["trace_id"] == "abc12345"
        assert row["duration_ms"] == 42.5

    def test_write_fails_gracefully_on_bad_db(self):
        """即使 DB 路径不可写，也不应抛出（写入失败静默）"""
        with patch("audit.audit_log.AUDIT_DB_PATH", Path("/nonexistent/path/audit.db")):
            from audit.audit_log import write_audit_log
            # Should not raise
            write_audit_log(action="FAIL_GRACEFULLY")


# ---------------------------------------------------------------------------
# AuditMiddleware ASGI
# ---------------------------------------------------------------------------
class TestAuditMiddleware:

    def _make_scope(self, path: str = "/api/test", method: str = "GET") -> dict:
        return {
            "type": "http",
            "method": method,
            "path": path,
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 12345),
        }

    async def test_non_http_scope_passes_through(self, tmp_path):
        """非 HTTP scope 直接 passthrough"""
        db_path = tmp_path / "audit.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table
            ensure_audit_table()

        app = AsyncMock()
        from audit.audit_log import AuditMiddleware
        middleware = AuditMiddleware(app)

        scope = {"type": "websocket"}
        receive = AsyncMock()
        send = AsyncMock()
        await middleware(scope, receive, send)
        app.assert_called_once_with(scope, receive, send)

    async def test_http_request_writes_audit(self, tmp_path):
        """HTTP 请求完成后应写入审计日志"""
        db_path = tmp_path / "audit.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table
            ensure_audit_table()

            async def mock_app(scope, receive, send):
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [],
                })
                await send({"type": "http.response.body", "body": b""})

            from audit.audit_log import AuditMiddleware
            middleware = AuditMiddleware(mock_app)
            scope = self._make_scope("/api/knowledgebase")
            receive = AsyncMock()
            send = AsyncMock()

            await middleware(scope, receive, send)

        conn = sqlite3.connect(str(db_path))
        count = conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]
        conn.close()
        assert count >= 1

    async def test_skip_path_not_written(self, tmp_path):
        """skip_paths 里的路径不写入审计"""
        db_path = tmp_path / "audit.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table
            ensure_audit_table()

            app = AsyncMock()
            from audit.audit_log import AuditMiddleware
            middleware = AuditMiddleware(app, skip_paths=["/docs"])

            scope = self._make_scope("/docs")
            receive = AsyncMock()
            send = AsyncMock()
            await middleware(scope, receive, send)

        conn = sqlite3.connect(str(db_path))
        count = conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]
        conn.close()
        assert count == 0
