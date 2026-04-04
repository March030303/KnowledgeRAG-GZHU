from __future__ import annotations

import builtins
import sys
import types
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import rag_enhancement.reranker as reranker


@pytest.fixture(autouse=True)
def reset_reranker_globals():
    reranker._rerank_model = None
    reranker._rerank_model_name = ""
    yield
    reranker._rerank_model = None
    reranker._rerank_model_name = ""


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(reranker.router)
    with TestClient(app) as c:
        yield c


class TestGetReranker:
    def test_get_reranker_returns_cached_instance(self):
        cached = object()
        reranker._rerank_model = cached
        reranker._rerank_model_name = "demo/model"

        model = reranker._get_reranker("demo/model")

        assert model is cached

    def test_get_reranker_loads_cross_encoder_and_caches(self):
        class FakeCrossEncoder:
            def __init__(self, model_name, max_length):
                self.model_name = model_name
                self.max_length = max_length

        fake_module = types.SimpleNamespace(CrossEncoder=FakeCrossEncoder)
        original = sys.modules.get("sentence_transformers")

        try:
            sys.modules["sentence_transformers"] = fake_module
            model = reranker._get_reranker("fake/model")
        finally:
            if original is None:
                sys.modules.pop("sentence_transformers", None)
            else:
                sys.modules["sentence_transformers"] = original

        assert isinstance(model, FakeCrossEncoder)
        assert model.model_name == "fake/model"
        assert model.max_length == 512
        assert reranker._rerank_model is model
        assert reranker._rerank_model_name == "fake/model"

    def test_get_reranker_returns_none_when_import_fails(self, caplog, monkeypatch):
        original_import = builtins.__import__
        original_module = sys.modules.pop("sentence_transformers", None)

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "sentence_transformers":
                raise RuntimeError("missing dependency")
            return original_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        try:
            with caplog.at_level("WARNING"):
                model = reranker._get_reranker("broken/model")
        finally:
            if original_module is not None:
                sys.modules["sentence_transformers"] = original_module

        assert model is None
        assert any("无法加载 cross-encoder" in record.message for record in caplog.records)


class TestRerankDocuments:
    def test_rerank_documents_returns_empty_for_empty_candidates(self):
        assert reranker.rerank_documents("query", []) == []

    def test_rerank_documents_uses_cross_encoder_scores(self, monkeypatch):
        captured = {}

        class FakeModel:
            def predict(self, pairs):
                captured["pairs"] = pairs
                return [0.1, 0.9, 0.4]

        monkeypatch.setattr(reranker, "_get_reranker", lambda _name: FakeModel())
        candidates = [
            {"content": "alpha content", "score": 0.2},
            {"text": "beta text", "score": 0.3},
            {"page_content": "gamma page", "score": 0.4},
        ]

        results = reranker.rerank_documents("who wins", candidates, top_k=2, model_name="demo")

        assert captured["pairs"] == [
            ("who wins", "alpha content"),
            ("who wins", "beta text"),
            ("who wins", "gamma page"),
        ]
        assert [item.get("text") or item.get("content") or item.get("page_content") for item in results] == [
            "beta text",
            "gamma page",
        ]
        assert results[0]["rerank_score"] == 0.9
        assert "rerank_score" not in candidates[0]

    def test_rerank_documents_falls_back_when_predict_raises(self, monkeypatch):
        class BrokenModel:
            def predict(self, _pairs):
                raise RuntimeError("predict failed")

        monkeypatch.setattr(reranker, "_get_reranker", lambda _name: BrokenModel())
        candidates = [
            {"text": "low", "score": 0.1},
            {"text": "high", "score": 0.8},
            {"text": "mid", "score": 0.5},
        ]

        results = reranker.rerank_documents("query", candidates, top_k=2)

        assert [item["text"] for item in results] == ["high", "mid"]
        assert results[0]["rerank_score"] == 0.8
        assert results[1]["rerank_score"] == 0.5

    def test_rerank_documents_falls_back_when_model_is_missing(self, monkeypatch):
        monkeypatch.setattr(reranker, "_get_reranker", lambda _name: None)
        candidates = [
            {"text": "a", "score": 0.3},
            {"text": "b", "score": 0.9},
        ]

        results = reranker.rerank_documents("query", candidates, top_k=1)

        assert results == [{"text": "b", "score": 0.9, "rerank_score": 0.9}]


class TestRerankerRoutes:
    def test_rerank_api_returns_standard_payload(self, client, monkeypatch):
        monkeypatch.setattr(
            reranker,
            "rerank_documents",
            lambda query, candidates, top_k, model_name: [
                {"text": "top answer", "rerank_score": 0.99}
            ],
        )

        resp = client.post(
            "/api/rerank",
            json={
                "query": "hello",
                "candidates": [{"text": "a"}, {"text": "b"}],
                "top_k": 1,
                "model_name": "demo/model",
            },
        )

        assert resp.status_code == 200
        assert resp.json() == {
            "query": "hello",
            "total_candidates": 2,
            "reranked": [{"text": "top answer", "rerank_score": 0.99}],
            "model": "demo/model",
        }

    def test_list_rerank_models_contains_recommended_models(self, client):
        resp = client.get("/api/rerank/models")

        assert resp.status_code == 200
        data = resp.json()
        names = [item["name"] for item in data["recommended"]]
        assert "cross-encoder/ms-marco-MiniLM-L-6-v2" in names
        assert "BAAI/bge-reranker-base" in names
