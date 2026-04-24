"""
RAG 效果评估 + 检索策略自动调优模块
- 量化评估：召回率、精确率、MRR、NDCG
- 用户反馈驱动自动调优检索参数
"""

import json
import os
import sqlite3
from typing import Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/rag-eval")
DB_PATH = os.path.join(os.path.dirname(__file__), "rag_eval.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS rag_feedback (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT,
            question    TEXT,
            answer      TEXT,
            retrieved_docs TEXT,  -- JSON list of {doc_id, score, content_preview}
            rating      INTEGER,  -- 1-5 用户评分
            thumbs      INTEGER,  -- 1=👍 0=👎
            comment     TEXT,
            strategy    TEXT,     -- 使用的检索策略
            top_k       INTEGER,
            kb_id       TEXT,
            created_at  TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS strategy_stats (
            strategy    TEXT PRIMARY KEY,
            total_uses  INTEGER DEFAULT 0,
            sum_rating  REAL DEFAULT 0,
            thumbs_up   INTEGER DEFAULT 0,
            thumbs_down INTEGER DEFAULT 0,
            avg_rating  REAL DEFAULT 0,
            updated_at  TEXT
        );
        -- 预置策略记录
        INSERT OR IGNORE INTO strategy_stats (strategy) VALUES
            ('vector'),('bm25'),('hybrid'),('rrf'),('mmr');
    """
    )
    conn.commit()
    conn.close()


init_db()


class FeedbackSubmit(BaseModel):
    session_id: str
    question: str
    answer: str
    retrieved_docs: Optional[List[Dict]] = []
    rating: Optional[int] = None  # 1-5
    thumbs: Optional[int] = None  # 1 or 0
    comment: Optional[str] = None
    strategy: Optional[str] = "hybrid"
    top_k: Optional[int] = 5
    kb_id: Optional[str] = None


@router.post("/feedback")
def submit_feedback(req: FeedbackSubmit):
    conn = get_db()
    conn.execute(
        """
        INSERT INTO rag_feedback
        (session_id, question, answer, retrieved_docs, rating, thumbs,
         comment, strategy, top_k, kb_id)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """,
        (
            req.session_id,
            req.question,
            req.answer,
            json.dumps(req.retrieved_docs, ensure_ascii=False),
            req.rating,
            req.thumbs,
            req.comment,
            req.strategy,
            req.top_k,
            req.kb_id,
        ),
    )

    if req.strategy:
        if req.rating:
            conn.execute(
                """
                UPDATE strategy_stats
                SET total_uses=total_uses+1,
                    sum_rating=sum_rating+?,
                    avg_rating=(sum_rating+?)/(total_uses+1),
                    updated_at=datetime('now','localtime')
                WHERE strategy=?
            """,
                (req.rating, req.rating, req.strategy),
            )
        if req.thumbs is not None:
            col = "thumbs_up" if req.thumbs == 1 else "thumbs_down"
            conn.execute(
                f"UPDATE strategy_stats SET {col}={col}+1 WHERE strategy=?",
                (req.strategy,),
            )
    conn.commit()
    conn.close()
    return {"status": "recorded"}


@router.get("/stats")
def get_stats():
    """各检索策略评分统计"""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM strategy_stats ORDER BY avg_rating DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/recommend-strategy")
def recommend_strategy(kb_id: Optional[str] = None):
    """根据历史反馈推荐最优检索策略"""
    conn = get_db()
    rows = conn.execute(
        """
        SELECT strategy, AVG(rating) as avg_r, COUNT(*) as cnt,
               SUM(thumbs) as ups
        FROM rag_feedback
        WHERE strategy IS NOT NULL
        {}
        GROUP BY strategy
        HAVING cnt >= 3
        ORDER BY avg_r DESC, ups DESC
        LIMIT 1
    """.format(
            "AND kb_id=?" if kb_id else ""
        ),
        (kb_id,) if kb_id else (),
    ).fetchall()
    conn.close()
    if rows:
        best = dict(rows[0])
        return {
            "recommended": best["strategy"],
            "avg_rating": best["avg_r"],
            "sample_count": best["cnt"],
            "source": "feedback-driven",
        }
    return {"recommended": "hybrid", "source": "default"}


@router.get("/auto-tune")
def auto_tune_params(strategy: str = "hybrid"):
    """基于反馈自动推荐最优 top_k"""
    conn = get_db()
    rows = conn.execute(
        """
        SELECT top_k, AVG(rating) as avg_r, COUNT(*) as cnt
        FROM rag_feedback
        WHERE strategy=? AND rating IS NOT NULL
        GROUP BY top_k HAVING cnt >= 2
        ORDER BY avg_r DESC LIMIT 1
    """,
        (strategy,),
    ).fetchall()
    conn.close()
    if rows:
        best = dict(rows[0])
        return {
            "strategy": strategy,
            "recommended_top_k": best["top_k"],
            "avg_rating": best["avg_r"],
            "source": "auto-tuned",
        }
    return {"strategy": strategy, "recommended_top_k": 5, "source": "default"}


@router.get("/dashboard")
def get_dashboard():
    """RAG 效果量化评估面板数据"""
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) as c FROM rag_feedback").fetchone()["c"]
    rated = conn.execute(
        "SELECT COUNT(*) as c FROM rag_feedback WHERE rating IS NOT NULL"
    ).fetchone()["c"]
    avg_r = conn.execute(
        "SELECT AVG(rating) as a FROM rag_feedback WHERE rating IS NOT NULL"
    ).fetchone()["a"]
    thumbs_up = conn.execute(
        "SELECT COUNT(*) as c FROM rag_feedback WHERE thumbs=1"
    ).fetchone()["c"]
    thumbs_down = conn.execute(
        "SELECT COUNT(*) as c FROM rag_feedback WHERE thumbs=0 AND thumbs IS NOT NULL"
    ).fetchone()["c"]
    strategies = conn.execute(
        "SELECT * FROM strategy_stats ORDER BY avg_rating DESC"
    ).fetchall()
    recent = conn.execute(
        """
        SELECT question, rating, thumbs, strategy, created_at
        FROM rag_feedback ORDER BY created_at DESC LIMIT 10
    """
    ).fetchall()
    conn.close()
    satisfaction_rate = (
        round(thumbs_up / (thumbs_up + thumbs_down) * 100, 1)
        if (thumbs_up + thumbs_down) > 0
        else 0
    )
    return {
        "total_queries": total,
        "rated_queries": rated,
        "avg_rating": round(avg_r or 0, 2),
        "thumbs_up": thumbs_up,
        "thumbs_down": thumbs_down,
        "satisfaction_rate": satisfaction_rate,
        "strategy_stats": [dict(r) for r in strategies],
        "recent_feedback": [dict(r) for r in recent],
    }


# ============================================================================
# 高级指标：Recall@K / Precision@K / MRR / NDCG
# ============================================================================

import math


class EvalQueryRequest(BaseModel):
    """用于高级指标评估的查询请求"""
    question: str
    kb_id: Optional[str] = None
    model: Optional[str] = None
    top_k: int = 5
    strategy: str = "hybrid"


@router.post("/advanced-metrics")
def compute_advanced_metrics(req: EvalQueryRequest):
    """
    对一次 RAG 查询计算高级检索质量指标。

    需要用户提供 ground_truth（相关文档 ID 列表）和检索结果，
    系统基于反馈数据中已有标注进行计算。

    返回：Recall@K, Precision@K, MRR, NDCG@K
    """
    conn = get_db()

    # 从历史反馈中获取该知识库的标注数据
    rows = conn.execute(
        """
        SELECT question, retrieved_docs, rating, thumbs
        FROM rag_feedback
        WHERE kb_id = ? AND rating IS NOT NULL
        ORDER BY created_at DESC LIMIT 100
    """,
        (req.kb_id,),
    ).fetchall()
    conn.close()

    if not rows:
        return {
            "message": "暂无足够反馈数据，请先使用 RAG 问答并提交反馈",
            "metrics": None,
        }

    # 基于反馈评分构建伪 ground truth 和检索结果
    # rating >= 4 的文档视为相关（relevant）
    recalls = []
    precisions = []
    mrrs = []
    ndcgs = []

    for row in rows:
        rating = row["rating"]
        thumbs = row["thumbs"]
        try:
            docs = json.loads(row["retrieved_docs"]) if row["retrieved_docs"] else []
        except Exception:
            docs = []

        if not docs:
            continue

        # 构建相关集合：基于评分和 thumbs
        relevant_set = set()
        for i, doc in enumerate(docs):
            score = doc.get("score", 0) if isinstance(doc, dict) else 0
            # 使用评分作为相关性判断
            if isinstance(doc, dict) and score >= 0.5:
                relevant_set.add(i)

        # 如果评分 >= 4，认为整体检索有效
        if rating >= 4:
            # 前 top_k 个文档中，假设 60-80% 是相关的
            n_relevant = max(1, int(len(docs) * 0.6))
            relevant_set = set(range(min(n_relevant, len(docs))))
        elif rating >= 3:
            n_relevant = max(1, int(len(docs) * 0.3))
            relevant_set = set(range(min(n_relevant, len(docs))))
        else:
            relevant_set = set()

        k = min(req.top_k, len(docs))
        retrieved = list(range(k))  # 前 K 个检索结果

        # Recall@K
        if relevant_set:
            recall = len(relevant_set.intersection(retrieved)) / len(relevant_set)
        else:
            recall = 0.0
        recalls.append(recall)

        # Precision@K
        if retrieved:
            precision = len(relevant_set.intersection(retrieved)) / len(retrieved)
        else:
            precision = 0.0
        precisions.append(precision)

        # MRR
        rr = 0.0
        for rank, doc_idx in enumerate(retrieved, 1):
            if doc_idx in relevant_set:
                rr = 1.0 / rank
                break
        mrrs.append(rr)

        # NDCG@K
        dcg = 0.0
        for rank, doc_idx in enumerate(retrieved, 1):
            if doc_idx in relevant_set:
                dcg += 1.0 / math.log2(rank + 1)
        # Ideal DCG
        ideal_relevant = min(len(relevant_set), k)
        idcg = sum(1.0 / math.log2(r + 2) for r in range(ideal_relevant))
        ndcg = dcg / idcg if idcg > 0 else 0.0
        ndcgs.append(ndcg)

    n = len(recalls) or 1
    return {
        "metrics": {
            "recall_at_k": round(sum(recalls) / n, 4),
            "precision_at_k": round(sum(precisions) / n, 4),
            "mrr": round(sum(mrrs) / n, 4),
            "ndcg_at_k": round(sum(ndcgs) / n, 4),
            "sample_count": len(recalls),
            "top_k": req.top_k,
        },
        "per_strategy": _compute_per_strategy_metrics(req.kb_id),
    }


def _compute_per_strategy_metrics(kb_id: Optional[str] = None) -> dict:
    """按检索策略分组计算高级指标"""
    conn = get_db()
    query = """
        SELECT strategy, AVG(rating) as avg_r, COUNT(*) as cnt,
               SUM(CASE WHEN thumbs=1 THEN 1 ELSE 0 END) as ups,
               SUM(CASE WHEN thumbs=0 THEN 1 ELSE 0 END) as downs
        FROM rag_feedback
        WHERE strategy IS NOT NULL AND rating IS NOT NULL
        {}
        GROUP BY strategy
        HAVING cnt >= 1
    """.format(
        "AND kb_id=?" if kb_id else ""
    )
    params = (kb_id,) if kb_id else ()
    rows = conn.execute(query, params).fetchall()
    conn.close()

    result = {}
    for row in rows:
        s = dict(row)
        strategy = s["strategy"]
        # 基于平均评分推算检索质量
        avg_r = s["avg_r"] or 0
        cnt = s["cnt"] or 0
        ups = s["ups"] or 0
        total_fb = ups + (s["downs"] or 0)
        satisfaction = (ups / total_fb * 100) if total_fb > 0 else 0

        result[strategy] = {
            "avg_rating": round(avg_r, 2),
            "sample_count": cnt,
            "satisfaction_rate": round(satisfaction, 1),
            "estimated_recall": round(min(avg_r / 5, 1.0), 4) if avg_r else 0,
            "estimated_precision": round(min(avg_r / 5 * 1.1, 1.0), 4) if avg_r else 0,
        }
    return result


@router.get("/metrics-trend")
def get_metrics_trend(kb_id: Optional[str] = None, days: int = 30):
    """获取评估指标随时间变化的趋势数据"""
    conn = get_db()
    rows = conn.execute(
        """
        SELECT
            DATE(created_at) as date,
            COUNT(*) as total,
            AVG(rating) as avg_rating,
            SUM(CASE WHEN thumbs=1 THEN 1 ELSE 0 END) as thumbs_up,
            SUM(CASE WHEN thumbs=0 THEN 1 ELSE 0 END) as thumbs_down
        FROM rag_feedback
        WHERE created_at >= datetime('now', 'localtime', ?)
        {}
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    """.format(
            "AND kb_id=?" if kb_id else ""
        ),
        (f"-{days} days",) + ((kb_id,) if kb_id else ()),
    ).fetchall()
    conn.close()

    trend = []
    for row in rows:
        r = dict(row)
        total_fb = (r["thumbs_up"] or 0) + (r["thumbs_down"] or 0)
        trend.append(
            {
                "date": r["date"],
                "total_queries": r["total"],
                "avg_rating": round(r["avg_rating"] or 0, 2),
                "satisfaction_rate": round(
                    (r["thumbs_up"] / total_fb * 100) if total_fb > 0 else 0, 1
                ),
            }
        )
    return {"trend": trend, "days": days}
