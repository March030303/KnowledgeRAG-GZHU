from __future__ import annotations

import os
import pathlib
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent
VECTOR_STORE_PATH = BACKEND_ROOT / "RAG_M" / "src" / "vectorstore" / "vector_store.py"
NATIVE_RAG_PATH = BACKEND_ROOT / "RAG_M" / "src" / "rag" / "native_rag.py"
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
HF_HOME = "C:/Users/ASUS/.cache/hf"
CACHED_MODEL_DIR = f"models--{DEFAULT_MODEL.replace('/', '--')}"


class FakeEmbeddings:
    last_args = None
    last_kwargs = None

    def __init__(self, *args, **kwargs):
        type(self).last_args = args
        type(self).last_kwargs = kwargs


class FakeSentenceTransformer:
    last_args = None
    last_kwargs = None

    def __init__(self, *args, **kwargs):
        type(self).last_args = args
        type(self).last_kwargs = kwargs

    def encode(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]


class TestLocalCacheBootstrap(unittest.TestCase):
    def setUp(self):
        FakeEmbeddings.last_args = None
        FakeEmbeddings.last_kwargs = None
        FakeSentenceTransformer.last_args = None
        FakeSentenceTransformer.last_kwargs = None

    def test_vector_store_uses_local_files_only_when_cache_exists(self):
        source = VECTOR_STORE_PATH.read_text(encoding="utf-8")

        fake_dotenv = types.ModuleType("dotenv")
        fake_dotenv.load_dotenv = lambda: None

        fake_vectorstores = types.ModuleType("langchain_community.vectorstores")
        fake_vectorstores.FAISS = object

        fake_documents = types.ModuleType("langchain_core.documents")
        fake_documents.Document = object

        fake_hf_embeddings = types.ModuleType("langchain_huggingface")
        fake_hf_embeddings.HuggingFaceEmbeddings = FakeEmbeddings

        fake_models_pkg = types.ModuleType("models")
        fake_model_config = types.ModuleType("models.model_config")
        fake_model_config.get_model_config = lambda: types.SimpleNamespace(
            embedding_model=DEFAULT_MODEL
        )

        fake_hf_root = types.ModuleType("huggingface_hub")
        fake_hf_utils = types.ModuleType("huggingface_hub.utils")
        fake_hf_http = types.ModuleType("huggingface_hub.utils._http")
        fake_hf_http._GLOBAL_CLIENT = "closed-client"

        injected_modules = {
            "dotenv": fake_dotenv,
            "langchain_community.vectorstores": fake_vectorstores,
            "langchain_core.documents": fake_documents,
            "langchain_huggingface": fake_hf_embeddings,
            "models": fake_models_pkg,
            "models.model_config": fake_model_config,
            "huggingface_hub": fake_hf_root,
            "huggingface_hub.utils": fake_hf_utils,
            "huggingface_hub.utils._http": fake_hf_http,
        }

        namespace = {"__name__": "vector_store_test", "__file__": str(VECTOR_STORE_PATH)}

        with patch.dict(sys.modules, injected_modules, clear=False), patch.dict(
            os.environ, {"HF_HOME": HF_HOME}, clear=False
        ):
            exec(compile(source, str(VECTOR_STORE_PATH), "exec"), namespace)
            with patch.object(namespace["os"].path, "isdir", return_value=False), patch.object(
                namespace["os"].path,
                "exists",
                side_effect=lambda path: CACHED_MODEL_DIR in str(path),
            ):
                manager = namespace["VectorStoreManager"]()
                manager.embeddings

        self.assertIsNotNone(FakeEmbeddings.last_kwargs)
        self.assertEqual(FakeEmbeddings.last_kwargs["cache_folder"], HF_HOME)
        self.assertEqual(
            FakeEmbeddings.last_kwargs["model_kwargs"],
            {"local_files_only": True},
        )
        self.assertIsNone(fake_hf_http._GLOBAL_CLIENT)

    def test_native_vector_store_uses_local_files_only_when_cache_exists(self):
        source = NATIVE_RAG_PATH.read_text(encoding="utf-8")

        fake_sentence_transformers = types.ModuleType("sentence_transformers")
        fake_sentence_transformers.SentenceTransformer = FakeSentenceTransformer

        namespace = {"__name__": "native_rag_test", "__file__": str(NATIVE_RAG_PATH)}

        with patch.dict(
            sys.modules,
            {"sentence_transformers": fake_sentence_transformers},
            clear=False,
        ), patch.dict(os.environ, {"HF_HOME": HF_HOME}, clear=False):
            exec(compile(source, str(NATIVE_RAG_PATH), "exec"), namespace)
            with patch.object(namespace["os"].path, "isdir", return_value=False), patch.object(
                namespace["os"].path,
                "exists",
                side_effect=lambda path: CACHED_MODEL_DIR in str(path),
            ):
                vector_store = namespace["NativeVectorStore"]()
                vector_store._get_model()

        self.assertEqual(FakeSentenceTransformer.last_args[0], DEFAULT_MODEL)
        self.assertEqual(FakeSentenceTransformer.last_kwargs["cache_folder"], HF_HOME)
        self.assertTrue(FakeSentenceTransformer.last_kwargs["local_files_only"])

    def test_vector_store_saves_via_ascii_temp_dir_for_unicode_target(self):
        source = VECTOR_STORE_PATH.read_text(encoding="utf-8")

        fake_dotenv = types.ModuleType("dotenv")
        fake_dotenv.load_dotenv = lambda: None

        class FakeSavedVectorStore:
            saved_paths = []

            def save_local(self, path):
                type(self).saved_paths.append(path)
                if "全站第一知识库" in str(path):
                    raise RuntimeError("unicode path is not supported by fake faiss")
                path_obj = pathlib.Path(path)
                path_obj.mkdir(parents=True, exist_ok=True)
                (path_obj / "index.faiss").write_text("faiss", encoding="utf-8")
                (path_obj / "index.pkl").write_text("pickle", encoding="utf-8")

        class FakeFAISS:
            @staticmethod
            def from_documents(_documents, _embeddings):
                return FakeSavedVectorStore()

        fake_vectorstores = types.ModuleType("langchain_community.vectorstores")
        fake_vectorstores.FAISS = FakeFAISS

        fake_documents = types.ModuleType("langchain_core.documents")
        fake_documents.Document = object

        fake_hf_embeddings = types.ModuleType("langchain_huggingface")
        fake_hf_embeddings.HuggingFaceEmbeddings = FakeEmbeddings

        fake_models_pkg = types.ModuleType("models")
        fake_model_config = types.ModuleType("models.model_config")
        fake_model_config.get_model_config = lambda: types.SimpleNamespace(
            embedding_model=DEFAULT_MODEL
        )

        namespace = {"__name__": "vector_store_test", "__file__": str(VECTOR_STORE_PATH)}

        with patch.dict(
            sys.modules,
            {
                "dotenv": fake_dotenv,
                "langchain_community.vectorstores": fake_vectorstores,
                "langchain_core.documents": fake_documents,
                "langchain_huggingface": fake_hf_embeddings,
                "models": fake_models_pkg,
                "models.model_config": fake_model_config,
            },
            clear=False,
        ):
            exec(compile(source, str(VECTOR_STORE_PATH), "exec"), namespace)
            manager = namespace["VectorStoreManager"]()
            with tempfile.TemporaryDirectory() as temp_dir:
                save_path = os.path.join(temp_dir, "全站第一知识库", "vectorstore")
                manager.create_vectorstore([object()], save_path)

                self.assertTrue(os.path.exists(os.path.join(save_path, "index.faiss")))
                self.assertTrue(os.path.exists(os.path.join(save_path, "index.pkl")))

        self.assertTrue(FakeSavedVectorStore.saved_paths)
        self.assertTrue(
            all("全站第一知识库" not in path for path in FakeSavedVectorStore.saved_paths)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

