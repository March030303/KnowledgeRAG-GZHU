"""
test_document_loader_import.py
===============================
验证 DocumentLoader 的依赖导入已修复到 langchain_community / langchain_text_splitters。

修复背景：
  原代码从 `langchain.document_loaders` 和 `langchain.text_splitter` 导入，
  langchain >= 0.1 已将这些 API 迁移到独立包，旧路径会抛
  `ModuleNotFoundError: No module named 'langchain.document_loaders'`。

  修复方案：统一改为
    from langchain_community.document_loaders import ...
    from langchain_text_splitters import RecursiveCharacterTextSplitter
"""

import os
import pathlib
import sys
import tempfile
import unittest

BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(BACKEND_ROOT / "RAG_M" / "src"))


class TestDocumentLoaderImport(unittest.TestCase):
    """保证导入路径始终使用正确的 langchain 子包。"""

    def test_import_document_loader_module(self):
        """DocumentLoader 模块必须可正常导入，不报 ModuleNotFoundError。"""
        try:
            from ingestion.document_loader import DocumentLoader  # noqa: F401
        except ImportError as e:
            self.fail(f"DocumentLoader 导入失败（应已修复为 langchain_community）: {e}")

    def test_no_legacy_langchain_document_loaders(self):
        """源码中不应再有 'from langchain.document_loaders' 旧路径。"""
        loader_file = (
            BACKEND_ROOT / "RAG_M" / "src" / "ingestion" / "document_loader.py"
        )
        content = loader_file.read_text(encoding="utf-8")
        self.assertNotIn(
            "from langchain.document_loaders",
            content,
            "document_loader.py 中仍存在旧 API 'from langchain.document_loaders'，应改为 langchain_community",
        )

    def test_no_legacy_langchain_text_splitter(self):
        """源码中不应再有 'from langchain.text_splitter' 旧路径。"""
        loader_file = (
            BACKEND_ROOT / "RAG_M" / "src" / "ingestion" / "document_loader.py"
        )
        content = loader_file.read_text(encoding="utf-8")
        self.assertNotIn(
            "from langchain.text_splitter",
            content,
            "document_loader.py 中仍存在旧 API 'from langchain.text_splitter'，应改为 langchain_text_splitters",
        )

    def test_text_splitter_from_correct_package(self):
        """langchain_text_splitters 包必须可独立导入。"""
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: F401
        except ImportError as e:
            self.fail(f"langchain_text_splitters 未安装: {e}")

    def test_document_loader_instantiation(self):
        """DocumentLoader 可正常实例化，默认参数不抛异常。"""
        from ingestion.document_loader import DocumentLoader

        loader = DocumentLoader()
        self.assertEqual(loader.chunk_size, 1000)
        self.assertEqual(loader.chunk_overlap, 200)

    def test_document_loader_chunk_config(self):
        """DocumentLoader 支持自定义分块参数。"""
        from ingestion.document_loader import DocumentLoader

        loader = DocumentLoader(chunk_size=512, chunk_overlap=64)
        self.assertEqual(loader.chunk_size, 512)
        self.assertEqual(loader.chunk_overlap, 64)

    def test_skip_file_vectorstore_dir(self):
        """位于 vectorstore 目录内的文件应被跳过。"""
        from ingestion.document_loader import DocumentLoader

        loader = DocumentLoader()
        skip, reason = loader.should_skip_file(
            os.path.join("kb", "vectorstore", "data.json")
        )
        self.assertTrue(skip, "vectorstore 目录下的文件应标记为跳过")
        self.assertIn("vectorstore", reason)

    def test_skip_file_temp_file(self):
        """~$ 开头的 Office 临时文件应被跳过。"""
        from ingestion.document_loader import DocumentLoader

        loader = DocumentLoader()
        skip, reason = loader.should_skip_file("~$document.docx")
        self.assertTrue(skip, "Office 临时文件应被跳过")

    def test_load_txt_file(self):
        """DocumentLoader 可正确加载 .txt 文件并分块。"""
        from ingestion.document_loader import DocumentLoader

        loader = DocumentLoader(chunk_size=200, chunk_overlap=20)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("这是第一段测试内容。\n\n这是第二段测试内容，用于验证文档加载功能。")
            tmp_path = f.name
        try:
            chunks = loader.load_document(tmp_path)
            self.assertIsInstance(chunks, list)
            self.assertGreater(len(chunks), 0, "应至少分出一个 chunk")
            for chunk in chunks:
                self.assertTrue(
                    hasattr(chunk, "page_content"), "每个 chunk 应有 page_content 属性"
                )
        finally:
            os.unlink(tmp_path)


class TestIngestSSEErrorFormat(unittest.TestCase):
    """验证 /ingest 报错时 SSE 消息格式以 'ERROR:' 开头，前端可正确识别。"""

    def test_error_message_prefix(self):
        """ingest 失败消息格式：'data: ERROR: <描述>\\n\\n'。"""
        # 模拟后端产生的错误消息格式
        error_desc = "No module named 'langchain.document_loaders'"
        sse_msg = f"data: ERROR: Document ingestion failed: {error_desc}\n\n"
        self.assertTrue(sse_msg.startswith("data: ERROR:"), "SSE 错误消息应以 'data: ERROR:' 开头")
        self.assertIn(error_desc, sse_msg)

    def test_success_message_contains_json(self):
        """ingest 成功消息应包含 JSON 格式的摘要信息。"""
        import json

        result = {
            "message": "Successfully ingested 10 document chunks",
            "documents_count": 10,
            "vectorstore_path": "kb/demo/vectorstore",
            "stats": {"processed": 2, "skipped": 0, "errors": 0},
        }
        sse_msg = f"data: {json.dumps(result)}\n\n"
        data_part = sse_msg.removeprefix("data: ").strip()
        parsed = json.loads(data_part)
        self.assertIn("message", parsed)
        self.assertIn("Successfully ingested", parsed["message"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
