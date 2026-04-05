from __future__ import annotations

import pathlib
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent
NATIVE_RAG_PATH = BACKEND_ROOT / "RAG_M" / "src" / "rag" / "native_rag.py"


class FakePdfPlumberPage:
    def __init__(self, text: str):
        self._text = text

    def extract_text(self) -> str:
        return self._text


class FakePdfPlumberDocument:
    def __init__(self, pages):
        self.pages = pages

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class NativeDocumentLoadingTests(unittest.TestCase):
    def _load_native_namespace(self, injected_modules: dict[str, types.ModuleType] | None = None):
        source = NATIVE_RAG_PATH.read_text(encoding="utf-8")
        namespace = {"__name__": "native_rag_test", "__file__": str(NATIVE_RAG_PATH)}
        injected_modules = injected_modules or {}

        previous_modules = {name: sys.modules.get(name) for name in injected_modules}
        sys.modules.update(injected_modules)
        try:
            exec(compile(source, str(NATIVE_RAG_PATH), "exec"), namespace)
        finally:
            for name, previous in previous_modules.items():
                if previous is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = previous

        return namespace

    def test_load_pdf_falls_back_to_pdfplumber_when_pypdf_breaks(self):
        fake_pypdf = types.ModuleType("pypdf")

        class BrokenPdfReader:
            def __init__(self, *_args, **_kwargs):
                raise ValueError("broken pdf")

        fake_pypdf.PdfReader = BrokenPdfReader

        fake_pdfplumber = types.ModuleType("pdfplumber")
        fake_pdfplumber.open = lambda _path: FakePdfPlumberDocument(
            [FakePdfPlumberPage("第一页内容"), FakePdfPlumberPage("第二页内容")]
        )

        namespace = self._load_native_namespace()

        with tempfile.TemporaryDirectory() as temp_dir:
            broken_pdf = pathlib.Path(temp_dir) / "broken.pdf"
            broken_pdf.write_bytes(b"%PDF-1.4 broken")

            with patch.dict(
                sys.modules,
                {
                    "pypdf": fake_pypdf,
                    "pdfplumber": fake_pdfplumber,
                },
            ):
                docs, error = namespace["_load_pdf"](str(broken_pdf))


        self.assertIsNone(error)
        self.assertEqual(len(docs), 2)
        self.assertEqual(docs[0].metadata["page"], 0)
        self.assertEqual(docs[0].metadata["source"], str(broken_pdf))
        self.assertEqual(docs[0].page_content, "第一页内容")


    def test_inspect_documents_from_dir_reports_loaded_failed_and_skipped_files(self):
        namespace = self._load_native_namespace()
        native_document = namespace["NativeDocument"]

        with tempfile.TemporaryDirectory() as temp_dir:
            root = pathlib.Path(temp_dir)
            (root / "ok.txt").write_text("ok", encoding="utf-8")
            (root / "bad.pdf").write_text("broken", encoding="utf-8")
            (root / "skip.doc").write_text("unsupported", encoding="utf-8")

            def fake_load_file(file_path: str):
                name = pathlib.Path(file_path).name
                if name == "ok.txt":
                    return [native_document("ok", {"source": file_path})], None
                if name == "bad.pdf":
                    return [], "pdfplumber 解析失败"
                return [], "unexpected"

            with patch.dict(namespace, {"_load_file": fake_load_file}):
                docs, report = namespace["inspect_documents_from_dir"](str(root))

        self.assertEqual(len(docs), 1)
        self.assertEqual(len(report["loaded_files"]), 1)
        self.assertEqual(len(report["failed_files"]), 1)
        self.assertEqual(len(report["skipped_files"]), 1)
        self.assertEqual(report["failed_files"][0]["extension"], ".pdf")
        self.assertEqual(report["skipped_files"][0]["extension"], ".doc")

    def test_supported_extensions_cover_excel_rtf_and_images(self):
        namespace = self._load_native_namespace()
        supported_extensions = namespace["SUPPORTED_EXTENSIONS"]

        for extension in (".xlsx", ".xls", ".rtf", ".png", ".jpg"):
            self.assertIn(extension, supported_extensions)

    def test_summarize_document_load_report_includes_failure_and_skipped_extensions(self):
        namespace = self._load_native_namespace()
        summary = namespace["summarize_document_load_report"](

            {
                "loaded_files": [{"path": "kb/demo.pdf", "extension": ".pdf"}],
                "failed_files": [
                    {
                        "path": "kb/bad.pdf",
                        "extension": ".pdf",
                        "reason": "pypdf 解析失败",
                    }
                ],
                "skipped_files": [
                    {
                        "path": "kb/legacy.doc",
                        "extension": ".doc",
                        "reason": "原生 RAG 暂不支持该文件类型",
                    }
                ],
                "supported_extensions": [".pdf", ".txt"],
            }
        )

        self.assertIn("成功加载 1 个文件", summary)
        self.assertIn("1 个文件解析失败", summary)
        self.assertIn(".doc", summary)

    def test_native_vector_store_save_uses_ascii_temp_dir_for_unicode_target(self):
        namespace = self._load_native_namespace()

        fake_faiss = types.ModuleType("faiss")
        written_paths: list[str] = []

        def fake_write_index(_index, path):
            written_paths.append(path)
            if "全站第一知识库" in str(path):
                raise RuntimeError("unicode path is not supported by fake faiss")
            pathlib.Path(path).write_bytes(b"index")

        fake_faiss.write_index = fake_write_index
        namespace["pickle"].dump = lambda _documents, file_obj: file_obj.write(b"pickle")

        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(
            sys.modules, {"faiss": fake_faiss}, clear=False
        ):
            save_path = pathlib.Path(temp_dir) / "全站第一知识库" / "native_vectorstore"
            vector_store = namespace["NativeVectorStore"]()
            vector_store._index = object()
            vector_store._documents = [namespace["NativeDocument"]("hello", {"source": "a.txt"})]

            vector_store.save(str(save_path))


            self.assertTrue((save_path / "native.index").exists())
            self.assertTrue((save_path / "native_docs.pkl").exists())
            self.assertTrue((save_path / "native_config.json").exists())

        self.assertTrue(written_paths)
        self.assertTrue(all("全站第一知识库" not in path for path in written_paths))


if __name__ == "__main__":
    unittest.main(verbosity=2)

