from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from langchain_core.documents import Document

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import document_processing.retrieval_strategy as rs


def make_doc(text: str, **metadata) -> Document:
    return Document(page_content=text, metadata=metadata)


class TestRetrievalStrategyHelpers:
    def test_retrieval_config_from_dict_casts_types(self):
        cfg = rs.RetrievalConfig.from_dict(
            {
                "strategy": "hybrid",
                "topK": "4",
                "scoreThreshold": "0.35",
                "vectorWeight": "0.7",
                "bm25Weight": "0.3",
                "rerank": 1,
                "rerankTopN": "2",
            }
        )

        assert cfg.strategy == "hybrid"
        assert cfg.topK == 4
        assert cfg.scoreThreshold == 0.35
        assert cfg.vectorWeight == 0.7
        assert cfg.bm25Weight == 0.3
        assert cfg.rerank is True
        assert cfg.rerankTopN == 2

    def test_extract_filename_prefers_first_available_key(self):
        assert rs._extract_filename({"source": "/tmp/a/demo.pdf"}) == "demo.pdf"
        assert rs._extract_filename({"file_path": "/tmp/b/report.docx"}) == "report.docx"
        assert rs._extract_filename({}) == "未知来源"

    def test_build_result_item_uses_metadata_fallbacks(self):
        doc = make_doc(
            "x" * 240,
            file_path="/kb/chapter1.md",
            page_number=9,
            seq_num=12,
        )

        item = rs._build_result_item(rank=3, doc=doc, score=0.12345678)

        assert item["document"] is doc
        assert item["source_info"] == {
            "rank": 3,
            "score": 0.123457,
            "file_name": "chapter1.md",
            "page": 9,
            "chunk_index": 12,
            "source_path": "/kb/chapter1.md",
        }
        assert item["content_preview"] == "x" * 200

    def test_lightweight_rerank_reorders_and_marks_top_n(self):
        docs = [
            {
                "document": make_doc("alpha beta gamma"),
                "source_info": {"rank": 9, "score": 0.1},
            },
            {
                "document": make_doc("alpha"),
                "source_info": {"rank": 8, "score": 0.2},
            },
            {
                "document": make_doc("theta"),
                "source_info": {"rank": 7, "score": 0.3},
            },
        ]

        result = rs._lightweight_rerank("alpha beta", docs, top_n=2)

        assert len(result) == 2
        assert result[0]["document"].page_content == "alpha beta gamma"
        assert result[0]["source_info"]["rank"] == 1
        assert result[0]["source_info"]["reranked"] is True
        assert result[1]["document"].page_content == "alpha"
        assert result[1]["source_info"]["rank"] == 2
        assert result[1]["source_info"]["reranked"] is True


class TestRetrievalStrategyExecutor:
    def test_get_bm25_requires_documents(self):
        executor = rs.RetrievalStrategyExecutor(vectorstore=MagicMock(), documents=[])

        with pytest.raises(ValueError, match="BM25 检索需要提供 documents 列表"):
            executor._get_bm25()

    def test_get_bm25_is_cached(self, monkeypatch):
        docs = [make_doc("hello world")]
        created = []

        class FakeBM25:
            def __init__(self, documents):
                created.append(documents)

        monkeypatch.setattr(rs, "BM25", FakeBM25)
        executor = rs.RetrievalStrategyExecutor(vectorstore=MagicMock(), documents=docs)

        bm25_a = executor._get_bm25()
        bm25_b = executor._get_bm25()

        assert bm25_a is bm25_b
        assert created == [docs]

    def test_vector_search_applies_threshold_and_top_k(self):
        docs = [
            make_doc("best", source="a.txt"),
            make_doc("filtered", source="b.txt"),
            make_doc("kept", source="c.txt"),
        ]
        vectorstore = MagicMock()
        vectorstore.similarity_search_with_score.return_value = [
            (docs[0], 0.0),
            (docs[1], 9.0),
            (docs[2], 1.0),
        ]
        executor = rs.RetrievalStrategyExecutor(vectorstore=vectorstore, documents=docs)

        results = executor._vector_search("query", top_k=2, score_threshold=0.3)

        vectorstore.similarity_search_with_score.assert_called_once_with("query", k=4)
        assert [item["document"].page_content for item in results] == ["best", "kept"]
        assert [item["source_info"]["rank"] for item in results] == [1, 3]

    def test_bm25_search_re_raises_value_error(self, monkeypatch):
        executor = rs.RetrievalStrategyExecutor(vectorstore=MagicMock(), documents=[])

        def raise_value_error():
            raise ValueError("missing docs")

        monkeypatch.setattr(executor, "_get_bm25", raise_value_error)

        with pytest.raises(ValueError, match="missing docs"):
            executor._bm25_search("query", top_k=2)

    def test_bm25_search_logs_and_returns_empty_on_generic_exception(
        self, monkeypatch, caplog
    ):
        executor = rs.RetrievalStrategyExecutor(vectorstore=MagicMock(), documents=[])
        fake_bm25 = MagicMock()
        fake_bm25.retrieve.side_effect = RuntimeError("boom")
        monkeypatch.setattr(executor, "_get_bm25", lambda: fake_bm25)

        with caplog.at_level("ERROR"):
            results = executor._bm25_search("query", top_k=2)

        assert results == []
        assert any("BM25Search" in record.message for record in caplog.records)

    def test_hybrid_search_combines_vector_and_bm25_scores(self, monkeypatch):
        doc_a = make_doc("doc a", source="a.txt")
        doc_b = make_doc("doc b", source="b.txt")
        fake_bm25 = MagicMock()
        fake_bm25.retrieve.return_value = [(doc_a, 10.0), (doc_b, 5.0)]

        vectorstore = MagicMock()
        vectorstore.similarity_search_with_score.return_value = [
            (doc_b, 0.0),
            (doc_a, 3.0),
        ]
        executor = rs.RetrievalStrategyExecutor(vectorstore=vectorstore, documents=[doc_a, doc_b])
        monkeypatch.setattr(executor, "_get_bm25", lambda: fake_bm25)

        config = rs.RetrievalConfig(strategy="hybrid", topK=2, vectorWeight=0.7, bm25Weight=0.3)
        results = executor._hybrid_search("query", config)

        assert [item["document"].page_content for item in results] == ["doc b", "doc a"]
        assert results[0]["source_info"]["score"] > results[1]["source_info"]["score"]

    def test_rrf_search_falls_back_to_vector_search(self, monkeypatch):
        doc = make_doc("fallback")
        fake_bm25 = MagicMock()
        fake_bm25.retrieve.return_value = [(doc, 1.0)]
        vectorstore = MagicMock()
        vectorstore.similarity_search_with_score.return_value = [(doc, 0.2)]
        executor = rs.RetrievalStrategyExecutor(vectorstore=vectorstore, documents=[doc])
        executor._vector_search = MagicMock(return_value=[{"fallback": True}])
        monkeypatch.setattr(executor, "_get_bm25", lambda: fake_bm25)
        monkeypatch.setattr(rs, "reciprocal_rank_fusion", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("rrf failed")))

        results = executor._rrf_search("query", rs.RetrievalConfig(topK=3, scoreThreshold=0.25))

        executor._vector_search.assert_called_once_with("query", 3, 0.25)
        assert results == [{"fallback": True}]

    def test_mmr_search_falls_back_to_vector_search(self):
        vectorstore = MagicMock()
        vectorstore.max_marginal_relevance_search.side_effect = RuntimeError("mmr failed")
        executor = rs.RetrievalStrategyExecutor(vectorstore=vectorstore, documents=[])
        executor._vector_search = MagicMock(return_value=[{"fallback": True}])

        results = executor._mmr_search("query", rs.RetrievalConfig(topK=4, scoreThreshold=0.4))

        executor._vector_search.assert_called_once_with("query", 4, 0.4)
        assert results == [{"fallback": True}]

    def test_retrieve_unknown_strategy_uses_rrf_and_optional_rerank(self, monkeypatch):
        doc = make_doc("alpha beta", source="demo.txt")
        initial = [rs._build_result_item(1, doc, 0.8)]
        reranked = [dict(initial[0])]
        reranked[0]["source_info"] = dict(initial[0]["source_info"], reranked=True)

        executor = rs.RetrievalStrategyExecutor(vectorstore=MagicMock(), documents=[doc])
        executor._rrf_search = MagicMock(return_value=initial)
        monkeypatch.setattr(rs, "_lightweight_rerank", lambda query, results, top_n: reranked)

        results = executor.retrieve(
            "alpha",
            rs.RetrievalConfig(strategy="unknown", rerank=True, rerankTopN=1),
        )

        executor._rrf_search.assert_called_once()
        assert results == reranked

    def test_retrieve_vector_strategy_without_explicit_config_uses_default_rrf(self):
        doc = make_doc("default")
        executor = rs.RetrievalStrategyExecutor(vectorstore=MagicMock(), documents=[doc])
        executor._rrf_search = MagicMock(return_value=[{"ok": True}])

        results = executor.retrieve("query")

        executor._rrf_search.assert_called_once()
        assert results == [{"ok": True}]
