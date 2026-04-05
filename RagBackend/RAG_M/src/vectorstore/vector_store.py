import json
import os
import shutil
import sys
import tempfile
import warnings
from typing import List, Optional

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


from models.model_config import get_model_config

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
# 禁用 huggingface_hub 遥测，减少不必要的网络请求
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

load_dotenv()


def _reset_hf_http_client() -> None:
    """
    重置 huggingface_hub 的全局 httpx.Client。

    huggingface_hub >= 1.0 使用进程级全局 httpx.Client（_GLOBAL_CLIENT）。
    当该 client 处于 CLOSED 状态（例如 uvicorn/asyncio 在 to_thread 里关闭了它）时，
    所有通过 hf_hub 的网络请求（包括 SentenceTransformer 下载/验证）都会失败。
    在每次构建 embedding 前调用此函数，强制重建 client，避免 "client has been closed" 报错。
    """
    try:
        import huggingface_hub.utils._http as _hfhttp

        _hfhttp._GLOBAL_CLIENT = None  # get_session() 会在下次调用时重建
    except Exception:
        pass  # 若 hf_hub 版本不含该属性，静默忽略


def _resolve_hf_cache_folder() -> Optional[str]:
    """解析 HuggingFace 本地缓存目录，优先环境变量，其次回退到用户默认缓存目录。"""
    hf_home = os.environ.get("HF_HOME", "").strip()
    if hf_home:
        return hf_home

    default_cache = os.path.join(os.path.expanduser("~"), ".cache", "hf")
    return default_cache if os.path.exists(default_cache) else None


def _has_local_model_cache(model_name: str, cache_folder: Optional[str]) -> bool:
    """检测 embedding 模型是否已缓存在本地，存在则可强制 local_files_only。"""
    if not model_name:
        return False

    if os.path.isdir(model_name):
        return True

    if not cache_folder:
        return False

    model_key = model_name.replace("/", "--")
    candidate_dirs = [
        os.path.join(cache_folder, f"models--{model_key}"),
        os.path.join(cache_folder, "hub", f"models--{model_key}"),
    ]
    return any(os.path.exists(path) for path in candidate_dirs)



def _create_faiss_temp_dir(prefix: str) -> str:
    """创建尽量规避 Windows 非 ASCII 路径问题的临时目录。"""
    candidates = []
    if os.name == "nt":
        system_root = os.environ.get("SystemRoot") or os.environ.get("SYSTEMROOT")
        if system_root:
            candidates.append(os.path.join(system_root, "Temp", "knowledge-rag-faiss"))
    candidates.append(os.path.join(tempfile.gettempdir(), "knowledge-rag-faiss"))

    last_error: Optional[Exception] = None
    for base_dir in candidates:
        try:
            os.makedirs(base_dir, exist_ok=True)
            return tempfile.mkdtemp(prefix=prefix, dir=base_dir)
        except OSError as exc:
            last_error = exc

    raise RuntimeError(f"无法创建 FAISS 临时目录: {last_error}")



def _promote_saved_files(temp_dir: str, save_path: str) -> None:
    """将临时目录中的向量文件移动到最终目录。"""
    os.makedirs(save_path, exist_ok=True)
    for file_name in os.listdir(temp_dir):
        src = os.path.join(temp_dir, file_name)
        dst = os.path.join(save_path, file_name)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        elif os.path.exists(dst):
            os.remove(dst)
        shutil.move(src, dst)



# VECTORSTORE_PATH = os.getenv("VECTORSTORE_PATH")



class VectorStoreManager:
    """Manager for creating and loading FAISS vector stores"""

    def __init__(self, docs_dir: str = None):
        """Initialize vector store manager with embedding model from config file"""
        self._embeddings: Optional[HuggingFaceEmbeddings] = None
        # Config file
        self._embedding_model = self._load_embedding_config(docs_dir)
        if not self._embedding_model:
            model_config = get_model_config()
            self._embedding_model = model_config.embedding_model

    def _load_embedding_config(self, docs_dir: str) -> str:
        """从knowledge_data.json加载embedding模型配置"""
        if not docs_dir:
            print("使用默认的 embedding 模型: sentence-transformers/all-MiniLM-L6-v2")
            return "sentence-transformers/all-MiniLM-L6-v2"

        # knowledge_data.json
        config_path = os.path.join(docs_dir, "knowledge_data.json")

        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    print(
                        f"加载embedding配置成功，使用模型: {config.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')}"
                    )
                    return config.get(
                        "embedding_model", "sentence-transformers/all-MiniLM-L6-v2"
                    )
            return "sentence-transformers/all-MiniLM-L6-v2"
        except Exception as e:
            print(f"加载embedding配置失败: {e}")
            return "sentence-transformers/all-MiniLM-L6-v2"

    @property
    def embeddings(self) -> HuggingFaceEmbeddings:
        """Lazy load and cache embeddings model（单例，只初始化一次）

        在初始化前重置 huggingface_hub 全局 httpx.Client，防止
        "Cannot send a request, as the client has been closed" 错误。
        该错误在 uvicorn/asyncio + asyncio.to_thread 场景下必现，
        原因是 hf_hub >= 1.0 的全局 client 会被 event loop 关闭。
        同时传入 cache_folder，确保在 HF_HUB_OFFLINE=1 时也能从本地缓存加载。
        """
        if self._embeddings is None:
            _reset_hf_http_client()
            cache_folder = _resolve_hf_cache_folder()
            local_files_only = _has_local_model_cache(
                self._embedding_model, cache_folder
            )

            model_kwargs = {"local_files_only": True} if local_files_only else {}
            self._embeddings = HuggingFaceEmbeddings(
                model_name=self._embedding_model,
                cache_folder=cache_folder,
                model_kwargs=model_kwargs,
            )
        return self._embeddings


    def create_vectorstore(self, documents: List[Document], save_path: str) -> FAISS:
        """Create and save a FAISS vector store from documents"""
        if not documents:
            raise ValueError("No documents provided to create vector store")

        save_path = os.path.abspath(os.path.normpath(save_path))
        print(f"Attempting to create vector store at: {save_path}")
        temp_dir: Optional[str] = None

        try:
            print(f"Creating FAISS vector store with {len(documents)} documents...")
            vectorstore = FAISS.from_documents(documents, self.embeddings)

            print(f"Ensuring save directory exists: {save_path}")
            os.makedirs(save_path, exist_ok=True)

            temp_dir = _create_faiss_temp_dir("langchain-faiss-")
            test_file = os.path.join(temp_dir, ".write_test")
            try:
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write("test")
                os.remove(test_file)
                print("Temporary directory write permissions verified")
            except Exception as exc:
                raise RuntimeError(
                    f"Cannot write to temporary directory: {str(exc)}"
                ) from exc

            print(f"Saving vector store to temporary directory: {temp_dir}")
            vectorstore.save_local(temp_dir)
            _promote_saved_files(temp_dir, save_path)

            print(f"Vector store successfully created and saved to {save_path}")

            required_files = ["index.faiss", "index.pkl"]
            for file in required_files:
                file_path = os.path.join(save_path, file)
                if not os.path.exists(file_path):
                    raise RuntimeError(
                        f"Expected file not found after save: {file_path}"
                    )
                print(f"Verified file exists: {file_path}")

            return vectorstore

        except Exception as e:
            print(f"Error creating vector store: {str(e)}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Save path exists: {os.path.exists(save_path)}")
            if os.path.exists(save_path):
                print(f"Save path is writable: {os.access(save_path, os.W_OK)}")
                print(f"Contents of save directory: {os.listdir(save_path)}")
            raise
        finally:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)


    def initialize_vectorstore(self, save_path: str):
        """Initialize an empty vector store with required files"""
        save_path = os.path.abspath(os.path.normpath(save_path))
        temp_dir: Optional[str] = None

        try:
            os.makedirs(save_path, exist_ok=True)

            if not os.path.exists(save_path):
                raise RuntimeError(f"Failed to create directory: {save_path}")

            test_file = os.path.join(save_path, ".write_test")
            try:
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write("test")
                os.remove(test_file)
            except Exception as exc:
                raise RuntimeError(
                    f"Cannot write to vector store directory: {str(exc)}"
                ) from exc

        except Exception as exc:
            raise RuntimeError(f"Cannot create vector store directory: {str(exc)}") from exc

        try:
            empty_docs = [Document(page_content="")]
            vectorstore = FAISS.from_documents(empty_docs, self.embeddings)

            temp_dir = _create_faiss_temp_dir("langchain-faiss-init-")
            vectorstore.save_local(temp_dir)
            _promote_saved_files(temp_dir, save_path)
            print(f"Successfully initialized vector store at {save_path}")
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize vector store: {str(exc)}") from exc
        finally:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)


    def load_vectorstore(self, load_path: str, trust_source: bool = False) -> FAISS:
        """
        Load a FAISS vector store from disk

        Args:
            load_path: Path to the vector store
            trust_source: If True, allows deserialization of the vector store.
                        WARNING: Only set to True if you trust the source.

        Returns:
            FAISS vector store instance

        Raises:
            SecurityError: If trust_source is False
            RuntimeError: If loading fails
        """
        load_path = os.path.abspath(load_path)

        if not os.path.exists(load_path):
            raise FileNotFoundError(f"Vector store not found at {load_path}")

        if not trust_source:
            warnings.warn(
                "Loading vector stores requires deserializing pickle files, which can be unsafe. "
                "If you trust the source of this vector store (e.g., you created it), "
                "set trust_source=True. Never set trust_source=True with files from untrusted sources.",
                UserWarning,
            )
            raise SecurityError(
                "Refusing to load vector store without explicit trust_source=True"
            )

        try:
            return FAISS.load_local(
                load_path, self.embeddings, allow_dangerous_deserialization=True
            )
        except RuntimeError as e:
            raise RuntimeError(
                f"Failed to load vector store from {load_path}. Error: {str(e)}"
            )


class SecurityError(Exception):
    """Raised when attempting unsafe operations without explicit permission"""

    pass
