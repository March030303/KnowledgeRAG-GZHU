"""
审计日志模块
记录用户操作行为（API 调用、文件上传、查询、删除等），写入 SQLite 文件。

增强点：
- 与 trace_id 关联，便于把 Apifox 请求、控制台日志、审计记录串起来
- 保留 query_string，便于程序员/运维回放与排障
- 支持更细粒度的查询参数，方便运维筛查
"""

from __future__ import annotations

import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)
router = APIRouter()

AUDIT_DB_PATH = Path(__file__).parent.parent / "metadata" / "audit_log.db"
_AUDIT_COLUMNS = {
    "trace_id": "TEXT",
    "query_string": "TEXT",
}


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(AUDIT_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _get_existing_columns(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("PRAGMA table_info(audit_logs)").fetchall()
    return {row[1] for row in rows}


def _ensure_column(
    conn: sqlite3.Connection, column_name: str, column_type: str
) -> None:
    existing_columns = _get_existing_columns(conn)
    if column_name not in existing_columns:
        conn.execute(f"ALTER TABLE audit_logs ADD COLUMN {column_name} {column_type}")
        logger.info("审计日志表新增列: %s (%s)", column_name, column_type)


def ensure_audit_table() -> None:
    """确保审计日志表存在，并自动补齐运维增强列。"""
    try:
        with _get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    user_id TEXT,
                    user_email TEXT,
                    action TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    resource_name TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    request_path TEXT,
                    request_method TEXT,
                    status_code INTEGER,
                    detail TEXT,
                    duration_ms REAL,
                    trace_id TEXT,
                    query_string TEXT
                )
                """
            )
            for column_name, column_type in _AUDIT_COLUMNS.items():
                _ensure_column(conn, column_name, column_type)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_trace ON audit_logs(trace_id)"
            )
            conn.commit()
        logger.info("审计日志表初始化完成")
    except Exception as exc:
        logger.warning("审计日志表初始化失败: %s", exc)


def write_audit_log(
    action: str,
    user_id: str | None = None,
    user_email: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    resource_name: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_path: str | None = None,
    request_method: str | None = None,
    status_code: int | None = None,
    detail: str | None = None,
    duration_ms: float | None = None,
    trace_id: str | None = None,
    query_string: str | None = None,
) -> None:
    """写入一条审计记录（非阻塞，失败不抛出）。"""
    try:
        with _get_conn() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs (
                    timestamp, user_id, user_email, action, resource_type, resource_id,
                    resource_name, ip_address, user_agent, request_path, request_method,
                    status_code, detail, duration_ms, trace_id, query_string
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    time.time(),
                    user_id,
                    user_email,
                    action,
                    resource_type,
                    resource_id,
                    resource_name,
                    ip_address,
                    user_agent,
                    request_path,
                    request_method,
                    status_code,
                    detail,
                    duration_ms,
                    trace_id,
                    query_string,
                ),
            )
            conn.commit()
    except Exception as exc:
        logger.debug("写入审计日志失败（不影响业务）: %s", exc)


def _decode_query_string(raw_query: bytes) -> str | None:
    if not raw_query:
        return None
    try:
        return raw_query.decode("utf-8", errors="ignore")[:500]
    except Exception:
        return None


def _extract_user_from_auth_header(auth_header: str) -> dict[str, str | None]:
    """从 Authorization header 的 JWT 中提取用户信息。"""
    user: dict[str, str | None] = {"user_id": None, "user_email": None}

    try:
        if auth_header.startswith("Bearer "):
            import jwt as jwt_lib

            token = auth_header[7:]
            secret = (
                os.getenv("JWT_SECRET")
                or os.getenv("JWT_SECRET_KEY")
                or "default_secret"
            )
            payload = jwt_lib.decode(token, secret, algorithms=["HS256"])
            user["user_id"] = str(payload.get("user_id") or payload.get("sub", ""))
            user["user_email"] = payload.get("email", "")
    except Exception:
        pass
    return user


class AuditMiddleware:
    """ASGI 中间件，自动记录 API 调用审计日志。"""

    def __init__(self, app, skip_paths: list | None = None):
        self.app = app
        self.skip_paths = skip_paths or ["/static", "/docs", "/openapi.json", "/redoc"]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if any(path.startswith(prefix) for prefix in self.skip_paths):
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        method = scope.get("method", "")
        client = scope.get("client")
        ip_address = client[0] if client else "unknown"
        headers = dict(scope.get("headers", []))
        user_agent = headers.get(b"user-agent", b"").decode("utf-8", errors="ignore")
        auth_header = headers.get(b"authorization", b"").decode(
            "utf-8", errors="ignore"
        )
        incoming_trace_id = (
            headers.get(b"x-trace-id", b"").decode("utf-8", errors="ignore") or None
        )
        query_string = _decode_query_string(scope.get("query_string", b""))
        user_info = _extract_user_from_auth_header(auth_header)

        status_code = 500
        response_trace_id = incoming_trace_id

        async def send_wrapper(message):
            nonlocal status_code, response_trace_id
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_headers = dict(message.get("headers", []))
                response_trace_id = (
                    response_headers.get(b"x-trace-id", b"").decode(
                        "utf-8", errors="ignore"
                    )
                    or response_trace_id
                )
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            action = _infer_action(method, path)
            resource_type, resource_id = _infer_resource(path)
            detail = None
            if status_code >= 500:
                detail = "server_error"
            elif status_code >= 400:
                detail = "client_error"

            write_audit_log(
                action=action,
                user_id=user_info["user_id"],
                user_email=user_info["user_email"],
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent[:200] if user_agent else None,
                request_path=path,
                request_method=method,
                status_code=status_code,
                detail=detail,
                duration_ms=duration_ms,
                trace_id=response_trace_id,
                query_string=query_string,
            )


def _infer_action(method: str, path: str) -> str:
    """根据 HTTP 方法和路径推断操作名称。"""
    method = method.upper()
    if "/login" in path or "/register" in path:
        return "AUTH"
    if "/upload" in path or method == "POST" and "/documents" in path:
        return "FILE_UPLOAD"
    if method == "DELETE":
        return "DELETE"
    if method == "POST" and ("/query" in path or "/RAG" in path or "/chat" in path):
        return "QUERY"
    if method == "POST":
        return "CREATE"
    if method in ("PUT", "PATCH"):
        return "UPDATE"
    if method == "GET":
        return "READ"
    return method


def _infer_resource(path: str) -> tuple[str | None, str | None]:
    """从路径推断资源类型和 ID。"""
    parts = [part for part in path.split("/") if part]
    resource_type = None
    resource_id = None
    if "knowledge" in path or "klb" in path.lower():
        resource_type = "knowledge_base"
    elif "document" in path or "file" in path:
        resource_type = "document"
    elif "chat" in path:
        resource_type = "chat"
    elif "user" in path:
        resource_type = "user"
    elif "RAG" in path:
        resource_type = "rag_query"

    for part in reversed(parts):
        if len(part) > 4 and part.replace("-", "").isalnum():
            resource_id = part
            break
    return resource_type, resource_id


@router.get("/api/audit/logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    limit: Optional[int] = Query(
        None, ge=1, le=500, description="兼容旧版 Apifox，等价于 page_size"
    ),
    user_email: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    trace_id: Optional[str] = None,
    request_path: Optional[str] = None,
    status_code: Optional[int] = Query(None, ge=100, le=599),
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
):
    """查询审计日志（分页 + 运维筛选）。"""
    try:
        if limit is not None:
            page_size = limit

        conditions: list[str] = []
        params: list[object] = []

        if user_email:
            conditions.append("user_email LIKE ?")
            params.append(f"%{user_email}%")
        if action:
            conditions.append("action = ?")
            params.append(action)
        if resource_type:
            conditions.append("resource_type = ?")
            params.append(resource_type)
        if trace_id:
            conditions.append("trace_id = ?")
            params.append(trace_id)
        if request_path:
            conditions.append("request_path LIKE ?")
            params.append(f"%{request_path}%")
        if status_code is not None:
            conditions.append("status_code = ?")
            params.append(status_code)
        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time)
        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        offset = (page - 1) * page_size

        with _get_conn() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) FROM audit_logs {where}", params
            ).fetchone()[0]
            rows = conn.execute(
                f"SELECT * FROM audit_logs {where} ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                params + [page_size, offset],
            ).fetchall()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "logs": [dict(row) for row in rows],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"查询审计日志失败: {exc}")


@router.get("/api/audit/stats")
async def audit_stats():
    """审计日志统计摘要，面向程序员/运维快速排查。"""
    try:
        with _get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]
            today_start = time.time() - 86400
            today = conn.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE timestamp >= ?",
                (today_start,),
            ).fetchone()[0]
            error_logs_24h = conn.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE timestamp >= ? AND status_code >= 500",
                (today_start,),
            ).fetchone()[0]
            slow_requests_over_1s_24h = conn.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE timestamp >= ? AND duration_ms >= 1000",
                (today_start,),
            ).fetchone()[0]
            top_actions = conn.execute(
                "SELECT action, COUNT(*) as cnt FROM audit_logs GROUP BY action ORDER BY cnt DESC LIMIT 10"
            ).fetchall()
            top_users = conn.execute(
                "SELECT user_email, COUNT(*) as cnt FROM audit_logs WHERE user_email IS NOT NULL GROUP BY user_email ORDER BY cnt DESC LIMIT 10"
            ).fetchall()
            top_status_codes = conn.execute(
                "SELECT status_code, COUNT(*) as cnt FROM audit_logs WHERE status_code IS NOT NULL GROUP BY status_code ORDER BY cnt DESC LIMIT 10"
            ).fetchall()

        return {
            "total_logs": total,
            "today_logs": today,
            "error_logs_24h": error_logs_24h,
            "slow_requests_over_1s_24h": slow_requests_over_1s_24h,
            "top_actions": [dict(row) for row in top_actions],
            "top_users": [dict(row) for row in top_users],
            "top_status_codes": [dict(row) for row in top_status_codes],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取审计统计失败: {exc}")


@router.delete("/api/audit/logs/clean")
async def clean_old_logs(days: int = Query(90, ge=7, le=365)):
    """清理超过指定天数的审计日志。"""
    cutoff = time.time() - days * 86400
    try:
        with _get_conn() as conn:
            result = conn.execute(
                "DELETE FROM audit_logs WHERE timestamp < ?", (cutoff,)
            )
            conn.commit()
        return {"deleted_count": result.rowcount, "days": days}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"清理审计日志失败: {exc}")
