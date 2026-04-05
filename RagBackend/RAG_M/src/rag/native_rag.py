"""
native_rag.py
原生 RAG 流水线（不依赖 LangChain）
使用：
  - 原生 FAISS 向量检索（通过 faiss-cpu）
  - 内置 BM25 关键词检索 + RRF 融合（复用 hybrid_retriever.BM25）
  - 直接调用 Ollama HTTP API 生成回答
  - 自行实现 Prompt 拼装、文本分块、文档加载

与 LangChain 版本对比：
  - LangChain 版：通过 langchain_ollama / langchain_community 等封装层
  - 原生版：直接调用 ollama REST API (http://host:port/api/generate)，
            向量存储用 faiss-cpu 原生接口，文档加载用 pypdf/docx2txt 等原始库
"""

from __future__ import annotations

import json
import logging
import math
import os
import pathlib
import pickle
import re
import shutil
import tempfile
from typing import Any, Dict, Generator, List, Optional, Tuple


import requests

logger = logging.getLogger(__name__)


def _resolve_hf_cache_folder() -> Optional[str]:
    """解析 HuggingFace 本地缓存目录，优先环境变量，其次回退到用户默认缓存目录。"""
    hf_home = os.environ.get("HF_HOME", "").strip()
    if hf_home:
        return hf_home

    default_cache = os.path.join(os.path.expanduser("~"), ".cache", "hf")
    return default_cache if os.path.exists(default_cache) else None


def _has_local_model_cache(model_name: str, cache_folder: Optional[str]) -> bool:
    """检测 sentence-transformers 模型是否已缓存在本地。"""
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
    """将临时目录中的索引与元数据移动到最终目录。"""
    os.makedirs(save_path, exist_ok=True)
    for file_name in os.listdir(temp_dir):
        src = os.path.join(temp_dir, file_name)
        dst = os.path.join(save_path, file_name)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        elif os.path.exists(dst):
            os.remove(dst)
        shutil.move(src, dst)



# ────────────────────────────────────────────────

# 0.
# ────────────────────────────────────────────────


class NativeDocument:
    """轻量文档对象，对应 LangChain Document"""

    def __init__(self, page_content: str, metadata: Dict[str, Any] = None):
        self.page_content = page_content
        self.metadata = metadata or {}

    def __repr__(self):
        return (
            f"NativeDocument(content={self.page_content[:60]!r}, meta={self.metadata})"
        )


# ────────────────────────────────────────────────
# 1. Document loading
# ────────────────────────────────────────────────

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
    ".docx",
    ".csv",
    ".xlsx",
    ".xls",
    ".rtf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
IGNORE_DIRS = {
    "vectorstore",
    "native_vectorstore",
    "__pycache__",
    ".git",
    "node_modules",
}
IGNORE_FILENAMES = {"knowledge_data.json", "metadata.json", "config.json"}



def _build_native_document(
    file_path: str,
    text: str,
    *,
    page: Optional[int] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Optional[NativeDocument]:
    clean_text = (text or "").strip()
    if not clean_text:
        return None

    metadata: Dict[str, Any] = {"source": file_path}
    if page is not None:
        metadata["page"] = page
    if extra_metadata:
        metadata.update(extra_metadata)
    return NativeDocument(page_content=clean_text, metadata=metadata)



def _load_txt(file_path: str) -> Tuple[List[NativeDocument], Optional[str]]:
    """加载纯文本 / Markdown。"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        document = _build_native_document(file_path, text)
        if document is None:
            return [], "文本内容为空"
        return [document], None
    except Exception as e:
        logger.error(f"[NativeRAG] 加载文本文件失败 {file_path}: {e}")
        return [], str(e)



def _load_pdf(file_path: str) -> Tuple[List[NativeDocument], Optional[str]]:
    """加载 PDF，优先 pypdf，失败后回退到 pdfplumber。"""
    errors: List[str] = []

    try:
        import pypdf

        docs: List[NativeDocument] = []
        with open(file_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for i, page in enumerate(reader.pages):
                document = _build_native_document(
                    file_path,
                    page.extract_text() or "",
                    page=i,
                )
                if document is not None:
                    docs.append(document)
        if docs:
            return docs, None
        errors.append("pypdf 未提取到有效文本")
    except ImportError:
        errors.append("pypdf 未安装")
    except Exception as e:
        logger.warning(f"[NativeRAG] pypdf 解析失败 {file_path}: {e}")
        errors.append(f"pypdf 解析失败: {e}")

    try:
        import pdfplumber

        docs = []
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                document = _build_native_document(
                    file_path,
                    page.extract_text() or "",
                    page=i,
                )
                if document is not None:
                    docs.append(document)
        if docs:
            return docs, None
        errors.append("pdfplumber 未提取到有效文本")
    except ImportError:
        errors.append("pdfplumber 未安装")
    except Exception as e:
        logger.error(f"[NativeRAG] pdfplumber 解析失败 {file_path}: {e}")
        errors.append(f"pdfplumber 解析失败: {e}")

    return [], "；".join(errors)



def _load_docx(file_path: str) -> Tuple[List[NativeDocument], Optional[str]]:
    """加载 Word 文档（使用 docx2txt）。"""
    try:
        import docx2txt

        document = _build_native_document(file_path, docx2txt.process(file_path) or "")
        if document is None:
            return [], "DOCX 内容为空"
        return [document], None
    except ImportError:
        logger.warning("[NativeRAG] docx2txt 未安装，跳过 docx 文件")
        return [], "docx2txt 未安装"
    except Exception as e:
        logger.error(f"[NativeRAG] 加载 DOCX 失败 {file_path}: {e}")
        return [], str(e)



def _load_csv(file_path: str) -> Tuple[List[NativeDocument], Optional[str]]:
    """加载 CSV。"""
    try:
        import csv

        rows = []
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(", ".join(row))
        document = _build_native_document(file_path, "\n".join(rows))
        if document is None:
            return [], "CSV 内容为空"
        return [document], None
    except Exception as e:
        logger.error(f"[NativeRAG] 加载 CSV 失败 {file_path}: {e}")
        return [], str(e)



def _load_excel(file_path: str) -> Tuple[List[NativeDocument], Optional[str]]:
    """加载 Excel，逐工作表转为文本。"""
    try:
        import pandas as pd

        sheets = pd.read_excel(file_path, sheet_name=None)
        docs: List[NativeDocument] = []
        for sheet_name, dataframe in sheets.items():
            normalized_df = dataframe.fillna("")
            text = normalized_df.to_csv(index=False)
            document = _build_native_document(
                file_path,
                text,
                extra_metadata={"sheet_name": sheet_name},
            )
            if document is not None:
                docs.append(document)
        if docs:
            return docs, None
        return [], "Excel 内容为空"
    except Exception as e:
        logger.error(f"[NativeRAG] 加载 Excel 失败 {file_path}: {e}")
        return [], str(e)



def _load_rtf(file_path: str) -> Tuple[List[NativeDocument], Optional[str]]:
    """加载 RTF，优先使用 striprtf，缺失时回退到轻量文本清洗。"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            raw_text = f.read()

        try:
            from striprtf.striprtf import rtf_to_text

            text = rtf_to_text(raw_text)
        except ImportError:
            text = raw_text
            text = re.sub(r"\\par[d]?", "\n", text)
            text = re.sub(r"\\tab", "\t", text)
            text = re.sub(r"\\'[0-9a-fA-F]{2}", " ", text)
            text = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", text)
            text = text.replace("{", "").replace("}", "")

        document = _build_native_document(file_path, text)
        if document is None:
            return [], "RTF 内容为空"
        return [document], None
    except Exception as e:
        logger.error(f"[NativeRAG] 加载 RTF 失败 {file_path}: {e}")
        return [], str(e)



def _load_image(file_path: str) -> Tuple[List[NativeDocument], Optional[str]]:
    """加载图片并执行 OCR。"""
    try:
        from knowledge.ocr_parser import extract_text_from_image

        with open(file_path, "rb") as f:
            image_bytes = f.read()
        text = extract_text_from_image(image_bytes, os.path.basename(file_path))
        if not text or text.startswith("[OCR不可用]"):
            return [], text or "图片 OCR 结果为空"
        document = _build_native_document(file_path, text)
        if document is None:
            return [], "图片 OCR 结果为空"
        return [document], None
    except Exception as e:
        logger.error(f"[NativeRAG] 加载图片失败 {file_path}: {e}")
        return [], str(e)



def _load_file(file_path: str) -> Tuple[List[NativeDocument], Optional[str]]:
    ext = pathlib.Path(file_path).suffix.lower()
    if ext in (".txt", ".md"):
        return _load_txt(file_path)
    if ext == ".pdf":
        return _load_pdf(file_path)
    if ext == ".docx":
        return _load_docx(file_path)
    if ext == ".csv":
        return _load_csv(file_path)
    if ext in (".xlsx", ".xls"):
        return _load_excel(file_path)
    if ext == ".rtf":
        return _load_rtf(file_path)
    if ext in IMAGE_EXTENSIONS:
        return _load_image(file_path)
    return [], f"原生 RAG 暂不支持该文件类型: {ext}"



def inspect_documents_from_dir(
    docs_dir: str,
) -> Tuple[List[NativeDocument], Dict[str, Any]]:
    """扫描目录，返回文档列表与加载报告。"""
    docs: List[NativeDocument] = []
    report: Dict[str, Any] = {
        "loaded_files": [],
        "failed_files": [],
        "skipped_files": [],
        "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
    }

    for root, dirs, files in os.walk(docs_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for fname in files:
            if fname in IGNORE_FILENAMES or fname.startswith("~$"):
                continue

            file_path = os.path.join(root, fname)
            ext = pathlib.Path(fname).suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                report["skipped_files"].append(

                    {
                        "path": file_path,
                        "extension": ext or "[no-extension]",
                        "reason": "原生 RAG 暂不支持该文件类型",
                    }
                )
                continue

            logger.info(f"[NativeRAG] 加载文件: {file_path}")
            loaded_docs, error = _load_file(file_path)
            if loaded_docs:
                docs.extend(loaded_docs)
                report["loaded_files"].append(
                    {
                        "path": file_path,
                        "extension": ext,
                        "documents_count": len(loaded_docs),
                    }
                )
                continue

            report["failed_files"].append(
                {
                    "path": file_path,
                    "extension": ext,
                    "reason": error or "解析结果为空",
                }
            )

    logger.info(
        "[NativeRAG] 文档加载完成："
        f"loaded={len(report['loaded_files'])}, "
        f"failed={len(report['failed_files'])}, "
        f"skipped={len(report['skipped_files'])}, "
        f"docs={len(docs)}"
    )
    return docs, report



def summarize_document_load_report(report: Dict[str, Any]) -> str:
    """将加载报告压缩成适合 SSE/日志展示的中文摘要。"""
    if not report:
        return ""

    parts: List[str] = []
    if report.get("loaded_files"):
        parts.append(f"成功加载 {len(report['loaded_files'])} 个文件")

    failed_files = report.get("failed_files", [])
    if failed_files:
        examples = "；".join(
            f"{os.path.basename(item['path'])}: {item['reason']}"
            for item in failed_files[:2]
        )
        parts.append(f"{len(failed_files)} 个文件解析失败（{examples}）")

    skipped_files = report.get("skipped_files", [])
    if skipped_files:
        skipped_exts = sorted({item["extension"] for item in skipped_files})
        parts.append(
            "跳过不支持类型 "
            + ", ".join(skipped_exts[:5])
            + (" 等" if len(skipped_exts) > 5 else "")
        )

    return "；".join(parts)



def load_documents_from_dir(docs_dir: str) -> List[NativeDocument]:
    """兼容旧调用：仅返回成功加载的文档列表。"""
    docs, _ = inspect_documents_from_dir(docs_dir)
    return docs



# ────────────────────────────────────────────────
# 2.
# ────────────────────────────────────────────────


def split_documents(
    docs: List[NativeDocument], chunk_size: int = 1000, chunk_overlap: int = 200
) -> List[NativeDocument]:
    """简单滑动窗口分块"""
    chunks = []
    for doc in docs:
        text = doc.page_content
        start = 0
        chunk_idx = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                meta = dict(doc.metadata)
                meta["chunk_index"] = chunk_idx
                chunks.append(NativeDocument(page_content=chunk_text, metadata=meta))
            chunk_idx += 1
            if end == len(text):
                break
            start = end - chunk_overlap

    logger.info(f"[NativeRAG] 分块完成，共 {len(chunks)} 个文本块")
    return chunks


# ────────────────────────────────────────────────
# 3. Vector storeFAISS
# ────────────────────────────────────────────────


class NativeVectorStore:
    """
    使用 sentence-transformers + faiss-cpu 实现的原生向量存储
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._index = None
        self._documents: List[NativeDocument] = []

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            cache_folder = _resolve_hf_cache_folder()
            local_files_only = _has_local_model_cache(self.model_name, cache_folder)

            logger.info(
                f"[NativeVectorStore] 加载 embedding 模型: {self.model_name}"
                + (f"（本地缓存: {cache_folder}）" if cache_folder else "")
                + (" [local-files-only]" if local_files_only else "")
            )
            self._model = SentenceTransformer(
                self.model_name,
                cache_folder=cache_folder,
                local_files_only=local_files_only,
            )
        return self._model


    def _encode(self, texts: List[str]):
        model = self._get_model()
        return model.encode(texts, show_progress_bar=False, normalize_embeddings=True)

    def build_index(self, documents: List[NativeDocument]) -> None:
        """构建 FAISS 索引"""
        import faiss

        self._documents = documents
        texts = [d.page_content for d in documents]
        print(f"[NativeVectorStore] 对 {len(texts)} 个文本块计算向量...")
        vectors = self._encode(texts).astype("float32")
        dim = vectors.shape[1]
        self._index = faiss.IndexFlatIP(dim)  # normalize
        self._index.add(vectors)
        print(f"[NativeVectorStore] FAISS 索引构建完成，维度={dim}")

    def save(self, save_path: str) -> None:
        """保存索引和文档到磁盘"""
        import faiss

        save_path = os.path.abspath(os.path.normpath(save_path))
        temp_dir = _create_faiss_temp_dir("native-faiss-")
        try:
            os.makedirs(save_path, exist_ok=True)
            faiss.write_index(self._index, os.path.join(temp_dir, "native.index"))
            with open(os.path.join(temp_dir, "native_docs.pkl"), "wb") as f:
                pickle.dump(self._documents, f)
            with open(
                os.path.join(temp_dir, "native_config.json"),
                "w",
                encoding="utf-8",
            ) as f:
                json.dump({"model_name": self.model_name}, f, ensure_ascii=False)
            _promote_saved_files(temp_dir, save_path)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"[NativeVectorStore] 已保存到 {save_path}")


    @classmethod
    def load(cls, load_path: str) -> "NativeVectorStore":
        """从磁盘加载"""
        import faiss

        config_path = os.path.join(load_path, "native_config.json")
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
            obj = cls(
                model_name=config.get(
                    "model_name", "sentence-transformers/all-MiniLM-L6-v2"
                )
            )
        else:
            obj = cls()
        obj._index = faiss.read_index(os.path.join(load_path, "native.index"))
        with open(os.path.join(load_path, "native_docs.pkl"), "rb") as f:
            obj._documents = pickle.load(f)
        print(
            f"[NativeVectorStore] 已从 {load_path} 加载，共 {len(obj._documents)} 个文档块"
        )
        return obj

    @classmethod
    def exists(cls, load_path: str) -> bool:
        return os.path.exists(
            os.path.join(load_path, "native.index")
        ) and os.path.exists(os.path.join(load_path, "native_docs.pkl"))

    def similarity_search(
        self, query: str, top_k: int = 5
    ) -> List[Tuple[NativeDocument, float]]:
        """向量相似度检索，返回 (doc, score) 列表

        FIX: [P0] 检查 _index 初始化状态，避免 AttributeError
        """

        # 防护：检查索引是否已构建
        if self._index is None:
            raise RuntimeError("FAISS 索引未初始化。请先调用 build_index() 构建索引。")

        q_vec = self._encode([query]).astype("float32")
        scores, indices = self._index.search(q_vec, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            results.append((self._documents[idx], float(score)))
        return results

    @property
    def documents(self) -> List[NativeDocument]:
        return self._documents


# ────────────────────────────────────────────────
# 4. BM25 NativeDocument
# ────────────────────────────────────────────────


class NativeBM25:
    """针对 NativeDocument 的内存 BM25"""

    def __init__(
        self, documents: List[NativeDocument], k1: float = 1.5, b: float = 0.75
    ):
        self.k1 = k1
        self.b = b
        self.documents = documents
        self.corpus = [self._tokenize(d.page_content) for d in documents]
        self._build()

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"[\u4e00-\u9fff]|[a-z0-9]+", text.lower())

    def _build(self):
        N = len(self.corpus)
        self.avgdl = sum(len(d) for d in self.corpus) / max(N, 1)
        df: Dict[str, int] = {}
        for tokens in self.corpus:
            for t in set(tokens):
                df[t] = df.get(t, 0) + 1
        self.idf: Dict[str, float] = {
            t: math.log((N - freq + 0.5) / (freq + 0.5) + 1) for t, freq in df.items()
        }

    def retrieve(
        self, query: str, top_k: int = 5
    ) -> List[Tuple[NativeDocument, float]]:
        q_tokens = self._tokenize(query)
        scores = []
        for doc_tokens in self.corpus:
            score = 0.0
            tf_map: Dict[str, int] = {}
            for t in doc_tokens:
                tf_map[t] = tf_map.get(t, 0) + 1
            dl = len(doc_tokens)
            for t in q_tokens:
                if t not in self.idf:
                    continue
                tf = tf_map.get(t, 0)
                score += (
                    self.idf[t]
                    * tf
                    * (self.k1 + 1)
                    / (tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
                )
            scores.append(score)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        return [(self.documents[i], s) for i, s in ranked if s > 0]


def _rrf_fusion(
    ranked_lists: List[List[Tuple[NativeDocument, float]]], k: int = 60
) -> List[Tuple[NativeDocument, float]]:
    """Reciprocal Rank Fusion"""
    rrf_scores: Dict[str, float] = {}
    doc_map: Dict[str, NativeDocument] = {}
    for ranked in ranked_lists:
        for rank, (doc, _) in enumerate(ranked, start=1):
            key = doc.page_content[:200]
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank)
            doc_map[key] = doc
    fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return [(doc_map[key], score) for key, score in fused]


# ────────────────────────────────────────────────
# 5. LLM Ollama HTTP API
# ────────────────────────────────────────────────


def _ollama_generate(
    model: str,
    prompt: str,
    host: str = "http://localhost:11434",
    stream: bool = False,
    timeout: int = 120,
) -> Generator[str, None, None]:
    """
    直接调用 Ollama /api/generate，支持流式和非流式
    stream=True 时 yield 每个 token，stream=False 时一次性 yield 完整回答
    """
    url = f"{host}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": stream}

    try:
        resp = requests.post(url, json=payload, stream=stream, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        yield f"[ERROR] 无法连接 Ollama 服务（{host}），请确认服务已启动"
        return
    except requests.exceptions.Timeout:
        yield "[ERROR] Ollama 请求超时"
        return
    except requests.exceptions.HTTPError as e:
        yield f"[ERROR] Ollama HTTP 错误: {e}"
        return

    if stream:
        for line in resp.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)
                token = data.get("response", "")
                if token:
                    yield token
                if data.get("done", False):
                    break
            except json.JSONDecodeError:
                continue
    else:
        try:
            data = resp.json()
            yield data.get("response", "")
        except Exception as e:
            yield f"[ERROR] 解析 Ollama 响应失败: {e}"


# ────────────────────────────────────────────────
# 6. RAG Pipeline
# ────────────────────────────────────────────────

_NATIVE_PROMPT_TEMPLATE = """<|im_start|>system
你是一个专业的中文知识库问答助手。你的任务是基于提供的文档片段，给出准确、简洁的中文回答。

核心规则（必须严格遵守）：
1. 【优先文档】只根据"参考文档"中的内容回答，不要编造文档中没有的信息
2. 【引用来源】回答中主动引用来源，格式：根据【来源X】，...
3. 【信息不足】如果文档完全没有相关信息，直接说"知识库中未找到相关内容"
4. 【补充通用知识】文档内容不完整时，在文档答案后追加一段通用知识，并标注"（通用知识补充）"
5. 【中文优先】始终用简体中文回答，除非问题本身用英文提问
6. 【简洁清晰】回答要结构化，重要内容用序号或要点列出，避免废话
7. 【代码/公式】涉及代码时用代码块格式展示
<|im_end|>
<|im_start|>user
参考文档（按相关度从高到低排序）：
{context}

问题：{question}
<|im_end|>
<|im_start|>assistant
"""

# 轻量提示模板（适合参数量较小的本地模型）
_NATIVE_PROMPT_TEMPLATE_LITE = """系统：你是中文知识库助手，只根据文档回答，引用来源格式为"根据【来源X】"，不确定时说"未找到相关内容"。

文档：
{context}

问题：{question}
回答："""


def _format_native_context(results: List[Dict[str, Any]]) -> str:
    parts = []
    for item in results:
        doc = item["document"]
        src = item["source_info"]
        fname = src.get("file_name", "未知来源")
        page = src.get("page")
        page_str = f"第 {page} 页" if page is not None else ""
        header = f"【来源 {src['rank']}：{fname}{' ' + page_str if page_str else ''}】"
        parts.append(f"{header}\n{doc.page_content.strip()}")
    return "\n\n---\n\n".join(parts)


def _extract_filename_native(meta: Dict[str, Any]) -> str:
    for key in ("source", "file_path", "path", "filename", "file_name"):
        val = meta.get(key, "")
        if val:
            return os.path.basename(str(val))
    return "未知来源"


class NativeRAGPipeline:
    """
    原生 RAG Pipeline（不依赖 LangChain）
    混合检索：NativeBM25 + NativeVectorStore + RRF
    生成：直接调用 Ollama HTTP API
    """

    def __init__(
        self,
        vectorstore: NativeVectorStore,
        documents: Optional[List[NativeDocument]] = None,
        llm_model: str = "deepseek-chat",
        ollama_host: str = "http://localhost:11434",
        use_hybrid: bool = True,
        bm25_top_k: int = 5,
        vector_top_k: int = 5,
        final_top_k: int = 4,
        ollama_timeout: int = 120,  # Ollama
    ):
        self.vectorstore = vectorstore
        self.llm_model = llm_model
        self.ollama_host = ollama_host
        self.use_hybrid = use_hybrid
        self.final_top_k = final_top_k
        self.bm25_top_k = bm25_top_k
        self.vector_top_k = vector_top_k
        self.ollama_timeout = ollama_timeout

        # Prompt
        # 0.5b/1b context token
        _small_models = ("0.5b", "1b", "1.5b", "tiny", "mini")
        self._prompt_template = (
            _NATIVE_PROMPT_TEMPLATE_LITE
            if any(s in llm_model.lower() for s in _small_models)
            else _NATIVE_PROMPT_TEMPLATE
        )

        # BM25
        self._bm25: Optional[NativeBM25] = None
        docs_for_bm25 = documents or (vectorstore.documents if vectorstore else None)
        if use_hybrid and docs_for_bm25:
            logger.info(
                f"[NativeRAGPipeline] 构建 BM25 索引，{len(docs_for_bm25)} 个文档块"
            )
            self._bm25 = NativeBM25(docs_for_bm25)
        else:
            self.use_hybrid = False

    def _retrieve(self, query: str) -> List[Dict[str, Any]]:
        """混合检索 or 纯向量检索，返回带 source_info 的列表"""
        vector_results = self.vectorstore.similarity_search(
            query, top_k=self.vector_top_k
        )

        if self.use_hybrid and self._bm25:
            bm25_results = self._bm25.retrieve(query, top_k=self.bm25_top_k)
            fused = _rrf_fusion([bm25_results, vector_results])
        else:
            fused = vector_results

        results = []
        for rank, (doc, score) in enumerate(fused[: self.final_top_k], start=1):
            meta = doc.metadata or {}
            results.append(
                {
                    "document": doc,
                    "source_info": {
                        "rank": rank,
                        "rrf_score": round(score, 6),
                        "file_name": _extract_filename_native(meta),
                        "page": meta.get("page"),
                        "chunk_index": meta.get("chunk_index"),
                        "source_path": meta.get("source", ""),
                    },
                    "content_preview": doc.page_content[:200],
                }
            )
        return results

    def stream_query(self, query: str) -> Generator[str, None, None]:
        """
        流式查询（SSE 格式）
        yield 格式与 LangChain 版一致，前端可复用同一解析逻辑
        """
        yield f"data: [原生RAG] 正在执行{'混合' if self.use_hybrid else '向量'}检索...\n\n"

        docs_with_sources = self._retrieve(query)

        if not docs_with_sources:
            yield "data: 未找到相关文档\n\n"
            yield "data: COMPLETE\n\n"
            return

        yield f"data: [原生RAG] 检索完成，获取到 {len(docs_with_sources)} 个相关文档块\n\n"

        sources = [
            {
                "rank": item["source_info"]["rank"],
                "file_name": item["source_info"]["file_name"],
                "page": item["source_info"]["page"],
                "source_path": item["source_info"]["source_path"],
                "content_preview": item["content_preview"],
            }
            for item in docs_with_sources
        ]
        yield f"data: SOURCES: {json.dumps(sources, ensure_ascii=False)}\n\n"

        context = _format_native_context(docs_with_sources)
        prompt = self._prompt_template.format(context=context, question=query)

        yield "data: [原生RAG] 正在生成回答（直接调用 Ollama API）...\n\n"

        try:
            for token in _ollama_generate(
                model=self.llm_model,
                prompt=prompt,
                host=self.ollama_host,
                stream=True,
                timeout=self.ollama_timeout,
            ):
                if token.startswith("[ERROR]"):
                    yield f"data: {token}\n\n"
                    break
                yield f"data: {token}\n\n"
        except Exception as e:
            yield f"data: [ERROR] 生成回答失败: {e}\n\n"

        yield "data: COMPLETE\n\n"

    def process_query(self, query: str) -> Dict[str, Any]:
        """同步非流式查询"""
        docs_with_sources = self._retrieve(query)

        if not docs_with_sources:
            return {
                "answer": "未找到相关文档，无法回答该问题。",
                "sources": [],
                "retrieval_mode": (
                    "native_hybrid" if self.use_hybrid else "native_vector"
                ),
            }

        context = _format_native_context(docs_with_sources)
        prompt = self._prompt_template.format(context=context, question=query)

        answer_parts = list(
            _ollama_generate(
                model=self.llm_model,
                prompt=prompt,
                host=self.ollama_host,
                stream=False,
                timeout=self.ollama_timeout,
            )
        )
        answer = "".join(answer_parts)

        sources = [
            {
                "rank": item["source_info"]["rank"],
                "file_name": item["source_info"]["file_name"],
                "page": item["source_info"]["page"],
                "source_path": item["source_info"]["source_path"],
                "rrf_score": item["source_info"].get("rrf_score"),
                "content_preview": item["content_preview"],
            }
            for item in docs_with_sources
        ]

        return {
            "answer": answer,
            "sources": sources,
            "retrieval_mode": "native_hybrid" if self.use_hybrid else "native_vector",
        }
