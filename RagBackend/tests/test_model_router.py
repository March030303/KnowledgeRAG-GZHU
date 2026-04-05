from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import multi_model.model_router as mr


async def collect_chunks(gen):
    return [chunk async for chunk in gen]


class FakeContent:
    def __init__(self, lines):
        self._lines = [line if isinstance(line, bytes) else line.encode("utf-8") for line in lines]

    def __aiter__(self):
        self._iter = iter(self._lines)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class FakeResponse:
    def __init__(self, status=200, lines=None, text_value=""):
        self.status = status
        self.content = FakeContent(lines or [])
        self._text_value = text_value

    async def text(self):
        return self._text_value

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    def __init__(self, response=None, exc=None, capture=None):
        self.response = response
        self.exc = exc
        self.capture = capture if capture is not None else {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def post(self, url, **kwargs):
        self.capture["url"] = url
        self.capture["kwargs"] = kwargs
        if self.exc is not None:
            raise self.exc
        return self.response

    def get(self, url, **kwargs):
        self.capture["url"] = url
        self.capture["kwargs"] = kwargs
        if self.exc is not None:
            raise self.exc
        return self.response


def install_fake_aiohttp(monkeypatch, response=None, exc=None, capture=None):
    connector_error = type("FakeConnectorError", (Exception,), {})

    class FakeAiohttpModule:
        ClientConnectorError = connector_error

        @staticmethod
        def ClientTimeout(total):
            return {"total": total}

        @staticmethod
        def ClientSession():
            return FakeSession(response=response, exc=exc, capture=capture)

    monkeypatch.setitem(sys.modules, "aiohttp", FakeAiohttpModule)
    return connector_error


@pytest.fixture
def client():

    app = FastAPI()
    app.include_router(mr.router)
    with TestClient(app) as c:
        yield c


class TestModelRouterConfigHelpers:
    def test_read_cloud_keys_invalid_json_returns_empty(self, tmp_path, monkeypatch, caplog):
        config_path = tmp_path / "models_config.json"
        config_path.write_text("{not-json", encoding="utf-8")
        monkeypatch.setattr(mr, "_CONFIG_PATH", config_path)

        with caplog.at_level("WARNING"):
            result = mr._read_cloud_keys()

        assert result == {}
        assert any("读取 models_config.json 失败" in record.message for record in caplog.records)

    def test_get_key_prefers_file_over_env(self, tmp_path, monkeypatch):
        config_path = tmp_path / "models_config.json"
        config_path.write_text(
            json.dumps({"cloud_keys": {"openai": {"api_key": "file-key"}}}, ensure_ascii=False),
            encoding="utf-8",
        )
        monkeypatch.setattr(mr, "_CONFIG_PATH", config_path)
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")

        assert mr._get_key("openai", "OPENAI_API_KEY") == "file-key"

    def test_get_base_url_falls_back_to_env_then_default(self, tmp_path, monkeypatch):
        config_path = tmp_path / "models_config.json"
        monkeypatch.setattr(mr, "_CONFIG_PATH", config_path)
        monkeypatch.setenv("OPENAI_BASE_URL", "https://env.example/v1")

        assert (
            mr._get_base_url("openai", "OPENAI_BASE_URL", "https://default.example/v1")
            == "https://env.example/v1"
        )

    def test_build_model_list_marks_provider_availability(self, monkeypatch):
        def fake_get_key(provider, _env_var):
            return {
                "deepseek": "deepseek-key",
                "openai": "",
                "hunyuan": "hunyuan-key",
            }.get(provider, "")

        monkeypatch.setattr(mr, "_get_key", fake_get_key)
        monkeypatch.setenv("HUNYUAN_SECRET_ID", "env-hunyuan")
        # 本地模型列表由 Ollama 动态发现，测试中 mock 为空列表避免网络依赖
        monkeypatch.setattr(mr, "_build_local_model_entries", lambda: [])

        result = mr._build_model_list()
        lookup = {item["id"]: item for item in result}

        # 云端模型可用性由 API Key 决定
        assert lookup["deepseek-chat"]["available"] is True
        assert lookup["gpt-4o"]["available"] is False
        assert lookup["hunyuan-pro"]["available"] is True


class TestModelRouterStreamHelpers:
    def test_collect_stream_concatenates_content_and_stops_on_error(self):
        async def fake_stream():
            yield 'data: {"content":"Hello ","done":false}\n\n'
            yield 'data: {"content":"World","done":false}\n\n'
            yield 'data: {"error":"boom"}\n\n'
            yield 'data: {"content":"ignored","done":false}\n\n'

        result = asyncio.run(mr._collect_stream(fake_stream()))

        assert result == "[模型错误] boom"

    def test_call_model_once_uses_provider_specific_stream(self, monkeypatch):
        async def fake_openai(model, messages, temperature, max_tokens):
            assert model == "gpt-4o"
            assert messages == [{"role": "user", "content": "hi"}]
            assert temperature == 0.2
            assert max_tokens == 12
            yield 'data: {"content":"A","done":false}\n\n'
            yield 'data: {"content":"B","done":false}\n\n'

        monkeypatch.setattr(mr, "_get_provider_for_model", lambda _model: "openai")
        monkeypatch.setattr(mr, "_stream_openai", fake_openai)

        result = asyncio.run(
            mr.call_model_once(
                model="gpt-4o",
                messages=[{"role": "user", "content": "hi"}],
                temperature=0.2,
                max_tokens=12,
            )
        )

        assert result == "AB"

    def test_stream_ollama_success_parses_content_and_done(self, monkeypatch):
        capture = {}
        response = FakeResponse(
            status=200,
            lines=[
                '{"message":{"content":"Hi"},"done":false}',
                '',
                'not-json',
                '{"done":true}',
            ],
        )
        install_fake_aiohttp(monkeypatch, response=response, capture=capture)
        monkeypatch.setattr(mr, "_get_base_url", lambda provider, env, default: "http://ollama.local")

        chunks = asyncio.run(
            collect_chunks(
                mr._stream_ollama("llama3:8b", [{"role": "user", "content": "hi"}], 0.5, 16)
            )
        )

        assert chunks == [
            'data: {"content": "Hi", "done": false}\n\n',
            'data: {"content": "", "done": true}\n\n',
        ]
        assert capture["url"] == "http://ollama.local/api/chat"
        assert capture["kwargs"]["json"]["options"] == {"temperature": 0.5, "num_predict": 16}

    def test_stream_ollama_returns_error_on_non_200(self, monkeypatch):
        response = FakeResponse(status=500, text_value="backend failed")
        install_fake_aiohttp(monkeypatch, response=response)
        monkeypatch.setattr(mr, "_get_base_url", lambda provider, env, default: "http://ollama.local")

        chunks = asyncio.run(
            collect_chunks(mr._stream_ollama("llama3:8b", [], 0.7, 32))
        )

        assert len(chunks) == 1
        payload = json.loads(chunks[0][6:].strip())
        assert payload["error"] == "Ollama 返回错误: backend failed"


    def test_stream_deepseek_missing_key_returns_error(self, monkeypatch):
        monkeypatch.setattr(mr, "_get_key", lambda provider, env: "")

        chunks = asyncio.run(
            collect_chunks(mr._stream_deepseek("deepseek-chat", [], 0.7, 32))
        )

        assert len(chunks) == 1
        payload = json.loads(chunks[0][6:].strip())
        assert payload["error"] == "未配置 DeepSeek API Key，请在「设置 → 多模型」填写并保存"


    def test_stream_deepseek_success_handles_done_marker(self, monkeypatch):
        response = FakeResponse(
            status=200,
            lines=[
                'data: {"choices":[{"delta":{"content":"你好"}}]}',
                'data: [DONE]',
            ],
        )
        install_fake_aiohttp(monkeypatch, response=response)
        monkeypatch.setattr(mr, "_get_key", lambda provider, env: "deepseek-key")

        chunks = asyncio.run(
            collect_chunks(mr._stream_deepseek("deepseek-chat", [], 0.7, 32))
        )

        assert chunks == [
            'data: {"content": "\\u4f60\\u597d", "done": false}\n\n',
            'data: {"content": "", "done": true}\n\n',
        ]

    def test_stream_openai_returns_error_on_non_200(self, monkeypatch):
        response = FakeResponse(status=401, text_value="bad key")
        install_fake_aiohttp(monkeypatch, response=response)
        monkeypatch.setattr(mr, "_get_key", lambda provider, env: "openai-key")
        monkeypatch.setattr(mr, "_get_base_url", lambda provider, env, default: "https://openai.local/v1")

        chunks = asyncio.run(
            collect_chunks(mr._stream_openai("gpt-4o", [], 0.7, 32))
        )

        assert len(chunks) == 1
        payload = json.loads(chunks[0][6:].strip())
        assert payload["error"] == "OpenAI 返回错误(401): bad key"


    def test_stream_hunyuan_uses_file_api_key_override(self, monkeypatch):
        capture = {}
        response = FakeResponse(
            status=200,
            lines=[
                'data: {"choices":[{"delta":{"content":"混元"}}]}',
                'data: [DONE]',
            ],
        )
        install_fake_aiohttp(monkeypatch, response=response, capture=capture)
        monkeypatch.setattr(mr, "_get_key", lambda provider, env: "")
        monkeypatch.setattr(mr, "_read_cloud_keys", lambda: {"hunyuan": {"api_key": "file-hy-key"}})
        monkeypatch.delenv("HUNYUAN_SECRET_ID", raising=False)
        monkeypatch.delenv("HUNYUAN_SECRET_KEY", raising=False)

        chunks = asyncio.run(
            collect_chunks(mr._stream_hunyuan("hunyuan-pro", [], 0.7, 32))
        )

        assert chunks == [
            'data: {"content": "\\u6df7\\u5143", "done": false}\n\n',
            'data: {"content": "", "done": true}\n\n',
        ]
        assert capture["kwargs"]["headers"]["Authorization"] == "Bearer file-hy-key"




class TestModelRouterRoutes:
    def test_list_models_route_returns_dynamic_models(self, client, monkeypatch):
        monkeypatch.setattr(mr, "_build_model_list", lambda: [{"id": "demo", "available": True}])

        resp = client.get("/api/models/list")

        assert resp.status_code == 200
        assert resp.json() == {"models": [{"id": "demo", "available": True}]}

    def test_model_chat_unknown_model_uses_ollama_stream(self, client, monkeypatch):
        called = {}

        async def fake_stream(model, messages, temperature, max_tokens):
            called["args"] = (model, messages, temperature, max_tokens)
            yield 'data: {"content":"from-ollama","done":false}\n\n'
            yield 'data: {"content":"","done":true}\n\n'

        monkeypatch.setattr(mr, "_stream_ollama", fake_stream)

        resp = client.post(
            "/api/models/chat",
            json={
                "model": "unknown-local-model",
                "messages": [{"role": "user", "content": "hi"}],
                "temperature": 0.6,
                "max_tokens": 22,
                "stream": True,
            },
        )

        assert resp.status_code == 200
        assert "from-ollama" in resp.text
        assert called["args"] == (
            "unknown-local-model",
            [{"role": "user", "content": "hi"}],
            0.6,
            22,
        )

    def test_model_chat_catalog_model_routes_to_deepseek(self, client, monkeypatch):
        async def fake_stream(model, messages, temperature, max_tokens):
            assert model == "deepseek-chat"
            yield 'data: {"content":"from-deepseek","done":false}\n\n'

        monkeypatch.setattr(mr, "_stream_deepseek", fake_stream)

        resp = client.post(
            "/api/models/chat",
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "hello"}],
                "stream": True,
            },
        )

        assert resp.status_code == 200
        assert "from-deepseek" in resp.text

    def test_configure_provider_writes_json_file(self, client, tmp_path, monkeypatch):
        config_path = tmp_path / "models_config.json"
        monkeypatch.setattr(mr, "_CONFIG_PATH", config_path)

        resp = client.post(
            "/api/models/configure",
            json={
                "provider_id": "openai",
                "config": {"api_key": "abc", "base_url": "https://demo/v1"},
            },
        )

        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        saved = json.loads(config_path.read_text(encoding="utf-8"))
        assert saved == {
            "cloud_keys": {
                "openai": {"api_key": "abc", "base_url": "https://demo/v1"}
            }
        }

    def test_test_provider_returns_early_when_api_key_missing(self, client):
        resp = client.post(
            "/api/models/test",
            json={"provider_id": "openai", "config": {"base_url": "https://demo/v1"}},
        )

        assert resp.status_code == 200
        assert resp.json() == {"ok": False, "message": "API Key 为空"}

    def test_test_provider_unknown_provider(self, client):
        resp = client.post(
            "/api/models/test",
            json={"provider_id": "mystery", "config": {"api_key": "abc"}},
        )

        assert resp.status_code == 200
        assert resp.json() == {"ok": False, "message": "未知 provider: mystery"}

    def test_providers_status_uses_helper_values(self, client, monkeypatch):
        monkeypatch.setattr(mr, "_get_key", lambda provider, _env: "key" if provider in {"deepseek", "openai"} else "")
        monkeypatch.setattr(
            mr,
            "_get_base_url",
            lambda provider, _env, default: "http://ollama.local" if provider == "ollama" else "https://openai.local/v1",
        )
        monkeypatch.setenv("HUNYUAN_SECRET_ID", "env-hy")

        resp = client.get("/api/models/providers/status")

        assert resp.status_code == 200
        data = resp.json()
        assert data["ollama"] == {"configured": True, "url": "http://ollama.local"}
        assert data["deepseek"]["configured"] is True
        assert data["openai"]["configured"] is True
        assert data["openai"]["base_url"] == "https://openai.local/v1"
        assert data["hunyuan"]["configured"] is True

    def test_configure_provider_returns_500_on_write_failure(self, client, tmp_path, monkeypatch):
        config_path = tmp_path / "models_config.json"
        monkeypatch.setattr(mr, "_CONFIG_PATH", config_path)
        monkeypatch.setattr(mr.json, "dump", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("disk full")))

        resp = client.post(
            "/api/models/configure",
            json={"provider_id": "openai", "config": {"api_key": "abc"}},
        )

        assert resp.status_code == 500
        assert "保存失败: disk full" in resp.json()["detail"]

    def test_test_provider_accepts_hunyuan_format_check(self, client):
        resp = client.post(
            "/api/models/test",
            json={"provider_id": "hunyuan", "config": {"api_key": "abc"}},
        )

        assert resp.status_code == 200
        assert resp.json()["ok"] is True
        assert "格式校验通过" in resp.json()["message"]

    def test_agent_task_without_kb_streams_steps_and_content(self, client, monkeypatch):
        async def fake_stream(model, messages, temperature, max_tokens):
            yield 'data: {"content":"task-body","done":false}\n\n'

        monkeypatch.setattr(mr, "_get_provider_for_model", lambda model: "openai")
        monkeypatch.setattr(mr, "_stream_openai", fake_stream)

        resp = client.post(
            "/api/agent/task",
            json={"query": "写个总结", "model": "gpt-4o", "temperature": 0.3, "max_tokens": 50},
        )

        assert resp.status_code == 200
        text = resp.text
        assert '"event": "step"' in text
        assert '"name": "规划执行流程"' in text
        assert 'task-body' in text
        assert '"event": "done"' in text

    def test_agent_task_stream_exception_yields_error_event(self, client, monkeypatch):
        async def broken_stream(model, messages, temperature, max_tokens):
            raise RuntimeError("stream failed")
            yield 'data: {"content":"never"}\n\n'

        monkeypatch.setattr(mr, "_get_provider_for_model", lambda model: "openai")
        monkeypatch.setattr(mr, "_stream_openai", broken_stream)

        resp = client.post(
            "/api/agent/task",
            json={"query": "写个总结", "model": "gpt-4o"},
        )

        assert resp.status_code == 200
        assert '"event": "error"' in resp.text
        assert 'stream failed' in resp.text

    def test_get_provider_for_model_defaults_to_ollama_for_unknown_model(self):
        assert mr._get_provider_for_model("totally-unknown") == "ollama"

