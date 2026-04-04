from __future__ import annotations

from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

DB_UNAVAILABLE_DETAIL = (
    "Cannot connect to the database. "
    "Make sure MySQL is running and the .env file has the correct DB_PASSWORD."
)


class DummyCursor:
    def __init__(
        self,
        *,
        fetchone_results: list[Any] | None = None,
        fetchall_result: list[Any] | None = None,
        rowcount: int = 0,
    ) -> None:
        self._fetchone_results = list(fetchone_results or [])
        self._fetchall_result = list(fetchall_result or [])
        self.rowcount = rowcount

    def execute(self, _query: str, _params: tuple[Any, ...] | None = None) -> None:
        return None

    def fetchone(self) -> Any:
        if self._fetchone_results:
            return self._fetchone_results.pop(0)
        return None

    def fetchall(self) -> list[Any]:
        return self._fetchall_result


@contextmanager
def db_unavailable_cursor():
    raise HTTPException(status_code=503, detail=DB_UNAVAILABLE_DETAIL)
    yield None


def make_cursor_context(cursor: DummyCursor):
    @contextmanager
    def _cursor_context():
        yield cursor

    return _cursor_context


@pytest.fixture
def auth_client():
    from RAGF_User_Management.LogonAndLogin import router as auth_router

    app = FastAPI()
    app.include_router(auth_router)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
def reset_client():
    from RAGF_User_Management.Reset_Password import router as reset_router

    app = FastAPI()
    app.include_router(reset_router)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def test_register_returns_503_when_database_unavailable(auth_client):
    with patch("RAGF_User_Management.LogonAndLogin.db_cursor", db_unavailable_cursor):
        response = auth_client.post(
            "/api/register",
            json={"email": "tester@example.com", "password": "Passw0rd!"},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == DB_UNAVAILABLE_DETAIL


def test_register_keeps_duplicate_email_business_error(auth_client):
    cursor = DummyCursor(fetchone_results=[(1,)])

    with patch(
        "RAGF_User_Management.LogonAndLogin.db_cursor", make_cursor_context(cursor)
    ):
        response = auth_client.post(
            "/api/register",
            json={"email": "tester@example.com", "password": "Passw0rd!"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "用户注册失败（可能邮箱已存在）"


def test_login_returns_503_when_database_unavailable(auth_client):
    with patch("RAGF_User_Management.LogonAndLogin.db_cursor", db_unavailable_cursor):
        response = auth_client.post(
            "/api/login/json",
            json={"email": "tester@example.com", "password": "Passw0rd!"},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == DB_UNAVAILABLE_DETAIL


def test_login_keeps_invalid_credentials_business_error(auth_client):
    cursor = DummyCursor(fetchone_results=[None])

    with patch(
        "RAGF_User_Management.LogonAndLogin.db_cursor", make_cursor_context(cursor)
    ):
        response = auth_client.post(
            "/api/login/json",
            json={"email": "tester@example.com", "password": "Passw0rd!"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "用户名或密码错误"


def test_reset_check_email_returns_503_when_database_unavailable(reset_client):
    with patch("RAGF_User_Management.Reset_Password.db_cursor", db_unavailable_cursor):
        response = reset_client.get("/api/reset/check-email?email=tester@example.com")

    assert response.status_code == 503
    assert response.json()["detail"] == DB_UNAVAILABLE_DETAIL


def test_send_email_code_keeps_not_registered_business_error(reset_client):
    cursor = DummyCursor(fetchone_results=[None])

    with patch(
        "RAGF_User_Management.Reset_Password.db_cursor", make_cursor_context(cursor)
    ):
        response = reset_client.post(
            "/api/reset/send-email-code",
            json={"email": "tester@example.com"},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "该邮箱未注册"
