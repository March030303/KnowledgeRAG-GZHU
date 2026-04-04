from __future__ import annotations

import importlib.util
import json
import sys
import types
import uuid
from pathlib import Path
from unittest.mock import MagicMock


from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.documents import Document

RAG_APP_PATH = Path(__file__).resolve().parent.parent / "RAG_M" / "RAG_app.py"


def load_rag_app_module():
    module_name = f"rag_app_test_{uuid.uuid4().hex}"

    src_pkg = types.ModuleType("src")
    src_pkg.__path__ = []
    rag_pkg = types.ModuleType("src.rag")
    rag_pkg.__path__ = []
    vector_pkg = types.ModuleType("src.vectorstore")
    vector_pkg.__path__ = []
    agent_pkg = types.ModuleType("src.agent")
    agent_pkg.__path__ = []
    scripts_pkg = types.ModuleType("src.scripts")
    scripts_pkg.__path__ = []

    rag_pipeline_mod = types.ModuleType("src.rag.rag_pipeline")
    vector_store_mod = types.ModuleType("src.vectorstore.vector_store")
    react_agent_mod = types.ModuleType("src.agent.react_agent")
    init_project_mod = types.ModuleType("src.scripts.init_project")

    class FakeRAGPipeline:
        init_calls = []

        def __init__(self, **kwargs):
            self.kwargs = kwargs
            type(self).init_calls.append(kwargs)

        def process_query(self, query):
            return {"answer": f"processed:{query}", "sources": []}

        def stream_query(self, query):
            yield f"data: {query}\n\n"

    class FakeVectorStoreManager:
        init_calls = []

        def __init__(self, docs_dir):
            self.docs_dir = docs_dir
            type(self).init_calls.append(docs_dir)

        def load_vectorstore(self, path, trust_source=True):
            return MagicMock(docstore=MagicMock(_dict={}))

    class FakeReActRAGAgent:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def stream_query(self, query):
            yield f"data: agent:{query}\n\n"

    def fake_init_project():
        return None

    rag_pipeline_mod.RAGPipeline = FakeRAGPipeline
    vector_store_mod.VectorStoreManager = FakeVectorStoreManager
    react_agent_mod.ReActRAGAgent = FakeReActRAGAgent
    init_project_mod.init_project = fake_init_project

    src_pkg.rag = rag_pkg
    src_pkg.vectorstore = vector_pkg
    src_pkg.agent = agent_pkg
    src_pkg.scripts = scripts_pkg
    rag_pkg.rag_pipeline = rag_pipeline_mod
    vector_pkg.vector_store = vector_store_mod
    agent_pkg.react_agent = react_agent_mod
    scripts_pkg.init_project = init_project_mod

    injected_modules = {
        "src": src_pkg,
        "src.rag": rag_pkg,
        "src.rag.rag_pipeline": rag_pipeline_mod,
        "src.vectorstore": vector_pkg,
        "src.vectorstore.vector_store": vector_store_mod,
        "src.agent": agent_pkg,
        "src.agent.react_agent": react_agent_mod,
        "src.scripts": scripts_pkg,
        "src.scripts.init_project": init_project_mod,
    }

    previous_modules = {name: sys.modules.get(name) for name in injected_modules}
    sys.modules.update(injected_modules)
    try:
        spec = importlib.util.spec_from_file_location(module_name, RAG_APP_PATH)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
    finally:
        for name, previous in previous_modules.items():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous

    return module, FakeRAGPipeline, FakeVectorStoreManager


def make_client(module):
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


class TestRagAppHelpers:
    def test_resolve_rag_model_supports_cloud_prefix(self):
        module, _, _ = load_rag_app_module()

        assert module._resolve_rag_model("cloud:deepseek:deepseek-chat") == (
            "deepseek-chat",
            "deepseek",
            True,
        )

    def test_resolve_rag_model_reads_provider_from_catalog(self):
        module, _, _ = load_rag_app_module()

        assert module._resolve_rag_model("deepseek-chat") == (
            "deepseek-chat",
            "deepseek",
            True,
        )
        assert module._resolve_rag_model("qwen2:0.5b") == (
            "qwen2:0.5b",
            "ollama",
            False,
        )

    def test_get_or_create_vsm_caches_instances(self):
        module, _, fake_vsm = load_rag_app_module()
        module._vsm_cache.clear()
        fake_vsm.init_calls.clear()

        a = module._get_or_create_vsm("kb/demo")
        b = module._get_or_create_vsm("kb/demo")
        c = module._get_or_create_vsm("kb/other")

        assert a is b
        assert a is not c
        assert fake_vsm.init_calls == ["kb/demo", "kb/other"]

    def test_load_vectorstore_and_docs_reads_docstore_documents(self, monkeypatch):
        module, _, _ = load_rag_app_module()
        doc1 = Document(page_content="alpha", metadata={"source": "a.txt"})
        doc2 = Document(page_content="beta", metadata={"source": "b.txt"})
        fake_vectorstore = MagicMock(docstore=MagicMock(_dict={"1": doc1, "2": doc2}))
        fake_manager = MagicMock()
        fake_manager.load_vectorstore.return_value = fake_vectorstore
        monkeypatch.setattr(module, "_get_or_create_vsm", lambda docs_dir: fake_manager)
        monkeypatch.setattr(module.os.path, "exists", lambda path: True)

        vectorstore, documents, manager = module._load_vectorstore_and_docs("kb/demo")

        assert vectorstore is fake_vectorstore
        assert documents == [doc1, doc2]
        assert manager is fake_manager
        fake_manager.load_vectorstore.assert_called_once()
        called_path = fake_manager.load_vectorstore.call_args.args[0]
        assert Path(called_path).as_posix().endswith("kb/demo/vectorstore")
        assert fake_manager.load_vectorstore.call_args.kwargs == {"trust_source": True}



    def test_load_vectorstore_and_docs_raises_when_vectorstore_missing(self, monkeypatch):
        module, _, _ = load_rag_app_module()
        monkeypatch.setattr(module, "_get_or_create_vsm", lambda docs_dir: MagicMock())
        monkeypatch.setattr(module.os.path, "exists", lambda path: False)

        try:
            module._load_vectorstore_and_docs("kb/missing")
            assert False, "应抛出 FileNotFoundError"
        except FileNotFoundError as exc:
            assert "向量存储路径不存在" in str(exc)


class TestRagAppRoutes:
    def test_rag_query_sync_returns_success_payload(self, monkeypatch):
        module, fake_pipeline, _ = load_rag_app_module()
        fake_pipeline.init_calls.clear()
        monkeypatch.setattr(module.os.path, "exists", lambda path: True)
        monkeypatch.setattr(
            module,
            "_load_vectorstore_and_docs",
            lambda docs_dir: (MagicMock(name="vectorstore"), [Document(page_content="ctx", metadata={})], None),
        )
        monkeypatch.setattr(
            module,
            "_resolve_rag_model",
            lambda raw_model: ("deepseek-chat", "deepseek", True),
        )

        with make_client(module) as client:
            resp = client.post(
                "/RAG_query_sync",
                json={"query": "hello", "docs_dir": "kb/demo", "use_hybrid": True},
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "status": "success",
            "model": "deepseek-chat",
            "provider": "deepseek",
            "answer": "processed:hello",
            "sources": [],
        }
        assert fake_pipeline.init_calls[0]["use_hybrid"] is True
        assert fake_pipeline.init_calls[0]["documents"] is not None

    def test_rag_query_sync_rejects_missing_docs_dir(self, monkeypatch):
        module, _, _ = load_rag_app_module()
        monkeypatch.setattr(module.os.path, "exists", lambda path: False)

        with make_client(module) as client:
            resp = client.post(
                "/RAG_query_sync",
                json={"query": "hello", "docs_dir": "kb/missing", "use_hybrid": True},
            )

        assert resp.status_code == 400
        assert resp.json()["detail"] == "文档目录未指定或不存在"

    def test_rag_query_sync_wraps_internal_error_as_500(self, monkeypatch):
        module, _, _ = load_rag_app_module()
        monkeypatch.setattr(module.os.path, "exists", lambda path: True)
        monkeypatch.setattr(
            module,
            "_load_vectorstore_and_docs",
            lambda docs_dir: (_ for _ in ()).throw(RuntimeError("load failed")),
        )

        with make_client(module) as client:
            resp = client.post(
                "/RAG_query_sync",
                json={"query": "hello", "docs_dir": "kb/demo", "use_hybrid": True},
            )

        assert resp.status_code == 500
        assert "查询失败: load failed" in resp.json()["detail"]

    def test_agent_query_returns_503_when_react_agent_is_unavailable(self):
        module, _, _ = load_rag_app_module()
        module.ReActRAGAgent = None
        module._REACT_AGENT_IMPORT_ERROR = RuntimeError("agent unavailable")

        with make_client(module) as client:
            resp = client.post(
                "/agent_query",
                json={"query": "hello", "docs_dir": "kb/demo", "use_hybrid": True},
            )

        assert resp.status_code == 503
        assert "ReAct Agent 当前不可用" in resp.json()["detail"]

    def test_health_endpoint_reports_features_and_vectorstore_state(self, monkeypatch):
        module, _, _ = load_rag_app_module()
        monkeypatch.setenv("MODEL", "qwen2:0.5b")
        monkeypatch.setenv("VECTORSTORE_PATH", "kb/demo/vectorstore")
        monkeypatch.setattr(module.os.path, "exists", lambda path: path == "kb/demo/vectorstore")

        with make_client(module) as client:
            resp = client.get("/health")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["model"] == "qwen2:0.5b"
        assert data["vectorstore_exists"] is True
        assert "react_agent" in data["features"]

    def test_init_project_returns_success(self):
        module, _, _ = load_rag_app_module()

        with make_client(module) as client:
            resp = client.post("/init")

        assert resp.status_code == 200
        assert resp.json() == {"message": "Project initialized successfully"}

    def test_capture_stdout_collects_text_and_restores_stdout(self):
        module, _, _ = load_rag_app_module()
        original_stdout = module.sys.stdout

        with module.capture_stdout() as buffer:
            print("hello stdout", end="")

        assert "hello stdout" in buffer.getvalue()
        assert module.sys.stdout is original_stdout

    def test_rag_query_cloud_mode_streams_sources_and_complete(self, monkeypatch):
        module, _, _ = load_rag_app_module()
        docs = [Document(page_content="知识库内容", metadata={"source": "doc.pdf", "page": 2})]
        vectorstore = MagicMock(name="vectorstore")
        monkeypatch.setattr(module.os.path, "exists", lambda path: True)
        monkeypatch.setattr(module, "_load_vectorstore_and_docs", lambda docs_dir: (vectorstore, docs, None))
        monkeypatch.setattr(module, "_resolve_rag_model", lambda raw_model: ("deepseek-chat", "deepseek", True))

        class FakeHybridRetriever:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def retrieve_with_scores(self, query):
                return [
                    {
                        "document": docs[0],
                        "source_info": {"rank": 1, "file_name": "doc.pdf", "page": 2},
                    }
                ]

        fake_hybrid_module = types.ModuleType("src.rag.hybrid_retriever")
        fake_hybrid_module.HybridRetriever = FakeHybridRetriever

        async def fake_stream(model_id, messages, temperature, max_tokens):
            assert model_id == "deepseek-chat"
            assert any(msg["role"] == "user" for msg in messages)
            yield f'data: {json.dumps({"content": "云端回答", "done": False}, ensure_ascii=False)}\n\n'

        fake_model_router_module = types.ModuleType("multi_model.model_router")
        fake_model_router_module._stream_deepseek = fake_stream
        fake_model_router_module._stream_openai = fake_stream
        fake_model_router_module._stream_hunyuan = fake_stream
        fake_model_router_module._stream_ollama = fake_stream

        monkeypatch.setitem(sys.modules, "src.rag.hybrid_retriever", fake_hybrid_module)
        monkeypatch.setitem(sys.modules, "multi_model.model_router", fake_model_router_module)

        with make_client(module) as client:
            resp = client.post(
                "/RAG_query",
                json={"query": "帮我总结", "docs_dir": "kb/demo", "use_hybrid": True},
            )

        assert resp.status_code == 200
        text = resp.text
        assert "SOURCES:" in text
        assert "云端回答" in text
        assert "COMPLETE" in text

    def test_rag_query_local_mode_streams_pipeline_chunks(self, monkeypatch):
        module, _, _ = load_rag_app_module()
        docs = [Document(page_content="本地上下文", metadata={})]
        monkeypatch.setattr(module.os.path, "exists", lambda path: True)
        monkeypatch.setattr(module, "_load_vectorstore_and_docs", lambda docs_dir: (MagicMock(name="vectorstore"), docs, None))
        monkeypatch.setattr(module, "_resolve_rag_model", lambda raw_model: ("qwen2:0.5b", "ollama", False))

        with make_client(module) as client:
            resp = client.post(
                "/RAG_query",
                json={"query": "本地问题", "docs_dir": "kb/demo", "use_hybrid": True},
            )

        assert resp.status_code == 200
        assert "检索模式: 混合检索(BM25+向量)" in resp.text
        assert "data: 本地问题" in resp.text

    def test_agent_query_success_streams_agent_chunks(self, monkeypatch):
        module, _, _ = load_rag_app_module()
        docs = [Document(page_content="agent ctx", metadata={})]
        monkeypatch.setattr(module.os.path, "exists", lambda path: True)
        monkeypatch.setattr(module, "_load_vectorstore_and_docs", lambda docs_dir: (MagicMock(name="vectorstore"), docs, None))
        monkeypatch.setattr(module, "_resolve_rag_model", lambda raw_model: ("qwen2:0.5b", "ollama", False))

        with make_client(module) as client:
            resp = client.post(
                "/agent_query",
                json={"query": "agent 问题", "docs_dir": "kb/demo", "use_hybrid": True},
            )

        assert resp.status_code == 200
        assert "启动 ReAct Agent 模式" in resp.text
        assert "agent:agent 问题" in resp.text

    def test_init_project_failure_returns_500(self, monkeypatch):
        module, _, _ = load_rag_app_module()
        scripts_pkg = types.ModuleType("src.scripts")
        scripts_pkg.__path__ = []
        failing_init_module = types.ModuleType("src.scripts.init_project")

        def fail_init():
            raise RuntimeError("boom")

        failing_init_module.init_project = fail_init
        scripts_pkg.init_project = failing_init_module
        monkeypatch.setitem(sys.modules, "src.scripts", scripts_pkg)
        monkeypatch.setitem(sys.modules, "src.scripts.init_project", failing_init_module)

        with make_client(module) as client:
            resp = client.post("/init")

        assert resp.status_code == 500
        assert resp.json()["detail"] == "Project initialization failed: boom"

