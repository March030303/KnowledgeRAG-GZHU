"""
test_audit_log_routes.py — audit_log.py FastAPI 路由 + 缺失分支单元测试

覆盖目标（补全 audit_log.py 68% → 90%+）：
  - GET  /api/audit/logs    （分页 + 各种过滤参数）
  - GET  /api/audit/stats
  - DELETE /api/audit/logs/clean
  - AuditMiddleware：status_code 4xx/5xx detail 分支、response_trace_id 从响应头提取
  - _ensure_column：column 已存在时跳过 ALTER TABLE 分支
  - ensure_audit_table 异常处理分支
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def audit_db(tmp_path):
    """在 tmp_path 创建一个已初始化的 audit DB，并 patch 全局路径"""
    db_path = tmp_path / "audit.db"
    with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
        from audit.audit_log import ensure_audit_table
        ensure_audit_table()
        yield db_path


@pytest.fixture
def test_client(audit_db):
    """返回一个挂载了 audit router 的 TestClient，DB patch 与 audit_db 同路径"""
    with patch("audit.audit_log.AUDIT_DB_PATH", audit_db):
        from audit.audit_log import router
        app = FastAPI()
        app.include_router(router)
        with TestClient(app) as client:
            yield client, audit_db


def _insert_logs(db_path: Path, count: int = 5, **overrides):
    """向 audit DB 直接插入若干条测试数据"""
    conn = sqlite3.connect(str(db_path))
    for i in range(count):
        conn.execute(
            """INSERT INTO audit_logs
               (timestamp, user_id, user_email, action, resource_type, resource_id,
                resource_name, ip_address, user_agent, request_path, request_method,
                status_code, detail, duration_ms, trace_id, query_string)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                time.time() - i,
                overrides.get("user_id", f"uid{i}"),
                overrides.get("user_email", f"user{i}@example.com"),
                overrides.get("action", "READ"),
                overrides.get("resource_type", "knowledge_base"),
                overrides.get("resource_id", f"kb{i}"),
                None,
                "127.0.0.1",
                "TestAgent/1.0",
                overrides.get("request_path", f"/api/test/{i}"),
                "GET",
                overrides.get("status_code", 200),
                None,
                overrides.get("duration_ms", 10.0 + i),
                overrides.get("trace_id", f"trace{i:04d}"),
                None,
            ),
        )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# GET /api/audit/logs
# ---------------------------------------------------------------------------
class TestGetAuditLogs:

    def test_returns_empty_when_no_logs(self, test_client):
        client, _ = test_client
        resp = client.get("/api/audit/logs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["logs"] == []

    def test_returns_inserted_logs(self, test_client):
        client, db_path = test_client
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            _insert_logs(db_path, count=3)
        resp = client.get("/api/audit/logs")
        assert resp.status_code == 200
        assert resp.json()["total"] == 3

    def test_pagination_page_size(self, test_client):
        client, db_path = test_client
        _insert_logs(db_path, count=10)
        resp = client.get("/api/audit/logs?page_size=3")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["logs"]) == 3
        assert data["total"] == 10

    def test_pagination_page_2(self, test_client):
        client, db_path = test_client
        _insert_logs(db_path, count=10)
        resp = client.get("/api/audit/logs?page=2&page_size=4")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["logs"]) == 4
        assert data["page"] == 2

    def test_limit_param_overrides_page_size(self, test_client):
        client, db_path = test_client
        _insert_logs(db_path, count=10)
        resp = client.get("/api/audit/logs?limit=2")
        assert resp.status_code == 200
        assert len(resp.json()["logs"]) == 2

    def test_filter_by_action(self, test_client):
        client, db_path = test_client
        _insert_logs(db_path, count=3, action="QUERY")
        _insert_logs(db_path, count=2, action="DELETE")
        resp = client.get("/api/audit/logs?action=QUERY")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        for log in data["logs"]:
            assert log["action"] == "QUERY"

    def test_filter_by_user_email(self, test_client):
        client, db_path = test_client
        _insert_logs(db_path, count=2, user_email="alice@test.com")
        _insert_logs(db_path, count=3, user_email="bob@test.com")
        resp = client.get("/api/audit/logs?user_email=alice")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_filter_by_trace_id(self, test_client):
        client, db_path = test_client
        _insert_logs(db_path, count=1, trace_id="target-trace")
        _insert_logs(db_path, count=4, trace_id="other-trace")
        resp = client.get("/api/audit/logs?trace_id=target-trace")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_filter_by_status_code(self, test_client):
        client, db_path = test_client
        _insert_logs(db_path, count=2, status_code=200)
        _insert_logs(db_path, count=1, status_code=404)
        resp = client.get("/api/audit/logs?status_code=404")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_filter_by_request_path(self, test_client):
        client, db_path = test_client
        _insert_logs(db_path, count=2, request_path="/api/knowledgebase/search")
        _insert_logs(db_path, count=3, request_path="/api/user/login")
        resp = client.get("/api/audit/logs?request_path=knowledgebase")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_filter_by_resource_type(self, test_client):
        client, db_path = test_client
        _insert_logs(db_path, count=2, resource_type="document")
        _insert_logs(db_path, count=3, resource_type="chat")
        resp = client.get("/api/audit/logs?resource_type=document")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_filter_by_time_range(self, test_client):
        client, db_path = test_client
        now = time.time()
        conn = sqlite3.connect(str(db_path))
        # 插入一条 1 小时前的记录
        conn.execute(
            """INSERT INTO audit_logs (timestamp, action, request_path, request_method)
               VALUES (?, ?, ?, ?)""",
            (now - 3600, "READ", "/api/old", "GET"),
        )
        # 插入一条刚刚的记录
        conn.execute(
            """INSERT INTO audit_logs (timestamp, action, request_path, request_method)
               VALUES (?, ?, ?, ?)""",
            (now - 60, "READ", "/api/new", "GET"),
        )
        conn.commit()
        conn.close()
        # 只查过去 30 分钟内的
        resp = client.get(f"/api/audit/logs?start_time={now - 600}&end_time={now}")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_combined_filters(self, test_client):
        client, db_path = test_client
        _insert_logs(db_path, count=2, action="QUERY", status_code=200)
        _insert_logs(db_path, count=2, action="QUERY", status_code=500)
        resp = client.get("/api/audit/logs?action=QUERY&status_code=200")
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_db_failure_returns_500(self, tmp_path):
        """DB 操作失败时返回 500"""
        broken_path = tmp_path / "nodir" / "broken.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", broken_path):
            from audit.audit_log import router
            app = FastAPI()
            app.include_router(router)
            with TestClient(app, raise_server_exceptions=False) as client:
                resp = client.get("/api/audit/logs")
                assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/audit/stats
# ---------------------------------------------------------------------------
class TestAuditStats:

    def test_returns_stats_structure(self, test_client):
        client, db_path = test_client
        _insert_logs(db_path, count=5)
        resp = client.get("/api/audit/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_logs" in data
        assert "today_logs" in data
        assert "error_logs_24h" in data
        assert "slow_requests_over_1s_24h" in data
        assert "top_actions" in data
        assert "top_users" in data
        assert "top_status_codes" in data

    def test_total_count_matches_insertions(self, test_client):
        client, db_path = test_client
        _insert_logs(db_path, count=7)
        resp = client.get("/api/audit/stats")
        assert resp.status_code == 200
        assert resp.json()["total_logs"] == 7

    def test_error_count_counts_500s(self, test_client):
        client, db_path = test_client
        _insert_logs(db_path, count=3, status_code=500)
        _insert_logs(db_path, count=2, status_code=200)
        resp = client.get("/api/audit/stats")
        assert resp.status_code == 200
        assert resp.json()["error_logs_24h"] == 3

    def test_slow_requests_counted(self, test_client):
        client, db_path = test_client
        # 插入一条超 1000ms 的记录
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            """INSERT INTO audit_logs (timestamp, action, request_path, request_method, duration_ms)
               VALUES (?, ?, ?, ?, ?)""",
            (time.time(), "READ", "/api/slow", "GET", 2000.0),
        )
        conn.commit()
        conn.close()
        resp = client.get("/api/audit/stats")
        assert resp.status_code == 200
        assert resp.json()["slow_requests_over_1s_24h"] >= 1

    def test_empty_db_returns_zeros(self, test_client):
        client, _ = test_client
        resp = client.get("/api/audit/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_logs"] == 0
        assert data["error_logs_24h"] == 0

    def test_db_failure_returns_500(self, tmp_path):
        broken_path = tmp_path / "nodir" / "broken.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", broken_path):
            from audit.audit_log import router
            app = FastAPI()
            app.include_router(router)
            with TestClient(app, raise_server_exceptions=False) as client:
                resp = client.get("/api/audit/stats")
                assert resp.status_code == 500


# ---------------------------------------------------------------------------
# DELETE /api/audit/logs/clean
# ---------------------------------------------------------------------------
class TestCleanOldLogs:

    def test_clean_old_logs_deletes_expired(self, test_client):
        client, db_path = test_client
        # 插入一条超过 365 天的旧记录
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            """INSERT INTO audit_logs (timestamp, action, request_path, request_method)
               VALUES (?, ?, ?, ?)""",
            (time.time() - 400 * 86400, "READ", "/api/old", "GET"),
        )
        conn.commit()
        conn.close()
        resp = client.delete("/api/audit/logs/clean?days=90")
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted_count"] >= 1
        assert data["days"] == 90

    def test_clean_does_not_delete_recent_logs(self, test_client):
        client, db_path = test_client
        _insert_logs(db_path, count=3)  # 新记录，timestamp ≈ now
        resp = client.delete("/api/audit/logs/clean?days=90")
        assert resp.status_code == 200
        assert resp.json()["deleted_count"] == 0

    def test_clean_default_days_is_90(self, test_client):
        client, _ = test_client
        resp = client.delete("/api/audit/logs/clean")
        assert resp.status_code == 200
        assert resp.json()["days"] == 90

    def test_db_failure_returns_500(self, tmp_path):
        broken_path = tmp_path / "nodir" / "broken.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", broken_path):
            from audit.audit_log import router
            app = FastAPI()
            app.include_router(router)
            with TestClient(app, raise_server_exceptions=False) as client:
                resp = client.delete("/api/audit/logs/clean")
                assert resp.status_code == 500


# ---------------------------------------------------------------------------
# AuditMiddleware — 缺失分支补充
# ---------------------------------------------------------------------------
class TestAuditMiddlewareExtraBranches:
    """补充 AuditMiddleware 的 4xx/5xx detail、response trace_id 提取等分支"""

    def _make_scope(self, path: str = "/api/test", method: str = "GET",
                    headers: list | None = None) -> dict:
        return {
            "type": "http",
            "method": method,
            "path": path,
            "query_string": b"page=1",
            "headers": headers or [],
            "client": ("10.0.0.1", 9999),
        }

    async def test_5xx_sets_detail_server_error(self, tmp_path):
        """HTTP 5xx 响应时 detail 应为 server_error"""
        db_path = tmp_path / "audit.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table, AuditMiddleware
            ensure_audit_table()

            async def mock_app(scope, receive, send):
                await send({
                    "type": "http.response.start",
                    "status": 503,
                    "headers": [],
                })
                await send({"type": "http.response.body", "body": b""})

            middleware = AuditMiddleware(mock_app)
            scope = self._make_scope("/api/something")
            await middleware(scope, AsyncMock(), AsyncMock())

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM audit_logs LIMIT 1").fetchone()
        conn.close()
        assert row["detail"] == "server_error"
        assert row["status_code"] == 503

    async def test_4xx_sets_detail_client_error(self, tmp_path):
        """HTTP 4xx 响应时 detail 应为 client_error"""
        db_path = tmp_path / "audit.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table, AuditMiddleware
            ensure_audit_table()

            async def mock_app(scope, receive, send):
                await send({
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [],
                })
                await send({"type": "http.response.body", "body": b""})

            middleware = AuditMiddleware(mock_app)
            await middleware(self._make_scope(), AsyncMock(), AsyncMock())

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM audit_logs LIMIT 1").fetchone()
        conn.close()
        assert row["detail"] == "client_error"
        assert row["status_code"] == 404

    async def test_200_has_no_detail(self, tmp_path):
        """HTTP 2xx 时 detail 为 None"""
        db_path = tmp_path / "audit.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table, AuditMiddleware
            ensure_audit_table()

            async def mock_app(scope, receive, send):
                await send({"type": "http.response.start", "status": 200, "headers": []})
                await send({"type": "http.response.body", "body": b""})

            middleware = AuditMiddleware(mock_app)
            await middleware(self._make_scope(), AsyncMock(), AsyncMock())

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM audit_logs LIMIT 1").fetchone()
        conn.close()
        assert row["detail"] is None

    async def test_response_trace_id_extracted_from_header(self, tmp_path):
        """响应头中的 X-Trace-Id 应被写入审计记录"""
        db_path = tmp_path / "audit.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table, AuditMiddleware
            ensure_audit_table()

            async def mock_app(scope, receive, send):
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [(b"x-trace-id", b"resp-trace-xyz")],
                })
                await send({"type": "http.response.body", "body": b""})

            middleware = AuditMiddleware(mock_app)
            await middleware(self._make_scope(), AsyncMock(), AsyncMock())

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM audit_logs LIMIT 1").fetchone()
        conn.close()
        assert row["trace_id"] == "resp-trace-xyz"

    async def test_incoming_trace_id_used_when_no_response_header(self, tmp_path):
        """请求头带 X-Trace-Id 但响应头无时，应使用请求头的 trace_id"""
        db_path = tmp_path / "audit.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table, AuditMiddleware
            ensure_audit_table()

            async def mock_app(scope, receive, send):
                await send({"type": "http.response.start", "status": 200, "headers": []})
                await send({"type": "http.response.body", "body": b""})

            middleware = AuditMiddleware(mock_app)
            headers = [(b"x-trace-id", b"incoming-trace-001")]
            await middleware(
                self._make_scope(headers=headers), AsyncMock(), AsyncMock()
            )

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM audit_logs LIMIT 1").fetchone()
        conn.close()
        assert row["trace_id"] == "incoming-trace-001"

    async def test_user_agent_truncated_to_200(self, tmp_path):
        """超长 User-Agent 应被截断到 200 字符"""
        db_path = tmp_path / "audit.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table, AuditMiddleware
            ensure_audit_table()

            async def mock_app(scope, receive, send):
                await send({"type": "http.response.start", "status": 200, "headers": []})
                await send({"type": "http.response.body", "body": b""})

            middleware = AuditMiddleware(mock_app)
            long_ua = b"A" * 500
            headers = [(b"user-agent", long_ua)]
            await middleware(self._make_scope(headers=headers), AsyncMock(), AsyncMock())

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM audit_logs LIMIT 1").fetchone()
        conn.close()
        assert len(row["user_agent"]) == 200

    async def test_no_client_ip_returns_unknown(self, tmp_path):
        """scope 中无 client 字段时，ip_address 应为 unknown"""
        db_path = tmp_path / "audit.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table, AuditMiddleware
            ensure_audit_table()

            async def mock_app(scope, receive, send):
                await send({"type": "http.response.start", "status": 200, "headers": []})
                await send({"type": "http.response.body", "body": b""})

            middleware = AuditMiddleware(mock_app)
            scope = {
                "type": "http", "method": "GET", "path": "/api/test",
                "query_string": b"", "headers": [], "client": None,
            }
            await middleware(scope, AsyncMock(), AsyncMock())

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM audit_logs LIMIT 1").fetchone()
        conn.close()
        assert row["ip_address"] == "unknown"

    async def test_query_string_written(self, tmp_path):
        """query_string 应被写入审计记录"""
        db_path = tmp_path / "audit.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table, AuditMiddleware
            ensure_audit_table()

            async def mock_app(scope, receive, send):
                await send({"type": "http.response.start", "status": 200, "headers": []})
                await send({"type": "http.response.body", "body": b""})

            middleware = AuditMiddleware(mock_app)
            scope = {
                "type": "http", "method": "GET", "path": "/api/test",
                "query_string": b"page=2&size=10",
                "headers": [], "client": ("127.0.0.1", 1234),
            }
            await middleware(scope, AsyncMock(), AsyncMock())

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM audit_logs LIMIT 1").fetchone()
        conn.close()
        assert row["query_string"] == "page=2&size=10"


# ---------------------------------------------------------------------------
# _ensure_column — already-exists 分支
# ---------------------------------------------------------------------------
class TestEnsureColumn:

    def test_column_already_exists_no_alter(self, tmp_path):
        """如果列已存在，不应执行 ALTER TABLE"""
        db_path = tmp_path / "col_test.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table, _ensure_column
            ensure_audit_table()
            # trace_id 已经在 CREATE TABLE 中定义
            conn = sqlite3.connect(str(db_path))
            # 应不抛出，也不重复添加
            _ensure_column(conn, "trace_id", "TEXT")
            conn.close()

    def test_column_new_gets_added(self, tmp_path):
        """如果列不存在，应通过 ALTER TABLE 添加"""
        db_path = tmp_path / "col_test2.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", db_path):
            from audit.audit_log import ensure_audit_table, _ensure_column
            ensure_audit_table()
            conn = sqlite3.connect(str(db_path))
            _ensure_column(conn, "new_custom_col", "TEXT")
            conn.commit()
            # 验证新列存在
            cols = {row[1] for row in conn.execute("PRAGMA table_info(audit_logs)").fetchall()}
            conn.close()
            assert "new_custom_col" in cols


# ---------------------------------------------------------------------------
# ensure_audit_table 异常分支
# ---------------------------------------------------------------------------
class TestEnsureAuditTableException:

    def test_exception_logged_not_raised(self, tmp_path):
        """ensure_audit_table 遇到 DB 错误时应 log warning 而不是抛出"""
        broken_path = tmp_path / "no_such_dir" / "audit.db"
        with patch("audit.audit_log.AUDIT_DB_PATH", broken_path):
            from audit.audit_log import ensure_audit_table
            # 不应抛出任何异常
            ensure_audit_table()


# ---------------------------------------------------------------------------
# _decode_query_string — 异常分支（decode 本身抛出）
# ---------------------------------------------------------------------------
class TestDecodeQueryStringExceptionBranch:

    def test_decode_exception_returns_none(self):
        """即使 bytes.decode 本身抛出，也应返回 None"""
        from audit.audit_log import _decode_query_string
        # 使用一个自定义对象模拟 decode 抛出的场景
        class BrokenBytes:
            def __bool__(self):
                return True
            def decode(self, *args, **kwargs):
                raise RuntimeError("forced decode error")

        result = _decode_query_string(BrokenBytes())  # type: ignore
        assert result is None
