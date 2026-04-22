#!/usr/bin/env python3
"""
Demo: Generate a complete ASF-RAG presentation using the PPT workflow
This demonstrates the full capability of the PPT engine with real content
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ppt_builder import PPTBuilder, CHAPTER_COLORS, NEON_PURPLE, NEON_EMERALD, NEON_ORANGE, NEON_BLUE, NEON_PINK


def create_rag_presentation():
    """Create a comprehensive ASF-RAG presentation"""
    
    builder = PPTBuilder()
    
    # ============================================================
    # Slide 1: Cover
    # ============================================================
    builder.add_cover(
        title="ASF-RAG",
        subtitle="智能知识管理平台",
        description="基于检索增强生成（RAG）的私有化知识中枢",
        accent=NEON_PURPLE
    )
    
    # ============================================================
    # Slide 2: TOC
    # ============================================================
    builder.add_toc(
        title="目录",
        items=[
            ("01", "项目综述", "定位、架构与技术栈全景", NEON_PURPLE),
            ("02", "核心功能", "RAG引擎、知识库、Agent与检索", NEON_EMERALD),
            ("03", "工程实现", "源码解析、配置与部署方案", NEON_ORANGE),
            ("04", "测试验证", "检索质量与生成效果评估", NEON_BLUE),
        ]
    )
    
    # ============================================================
    # Chapter 1: 项目综述
    # ============================================================
    builder.add_chapter("01", "项目综述", "定位、架构与技术栈全景", NEON_PURPLE)
    
    # Slide 4: 项目定位
    builder.add_two_col(
        title="项目定位",
        left_title="核心定位",
        left_items=[
            "防幻觉问答系统 —— 回答严格基于上传文档",
            "私有化知识中枢 —— 数据不出本地",
            "个人与团队的可靠AI助手",
        ],
        right_title="核心价值",
        right_items=[
            "每处信息可追溯原文出处",
            "深度理解用户私有文档",
            "多知识库联动检索",
        ],
        left_accent=NEON_PURPLE,
        right_accent=NEON_PINK,
        quote="通过技术手段确保AI的回答严格基于上传的文档，且每一处信息都可追溯至原文出处，从而成为个人与团队可靠的私有化知识中枢。"
    )
    
    # Slide 5: 系统架构
    builder.add_list(
        title="系统架构",
        subtitle="三层解耦架构：客户端层 / 服务层 / 存储层",
        items=[
            "客户端层：Vue 3 + Vite + TypeScript —— 响应式SPA，流畅用户体验",
            "服务层：FastAPI 0.116.1 + RAG Pipeline + Agent引擎 + 模型路由",
            "存储层：MySQL 结构化数据 + FAISS 向量数据库 + Redis Stream 队列",
            "通信协议：RESTful API + SSE（Server-Sent Events）流式推送",
        ],
        accent=NEON_PURPLE
    )
    
    # Slide 6: 技术栈详解
    builder.add_two_col(
        title="技术栈详解",
        left_title="后端依赖",
        left_items=[
            "fastapi 0.116.1 —— 高性能异步框架",
            "langchain 0.3.27 —— RAG Pipeline构建",
            "faiss-cpu >=1.12 —— 毫秒级向量检索",
            "sentence-transformers >=5.1 —— 嵌入模型",
            "redis[hiredis] >=5.0 —— 异步任务队列",
            "uvicorn 0.35.0 —— ASGI服务器",
        ],
        right_title="前端依赖",
        right_items=[
            "vue ^3.4.21 —— 响应式框架",
            "vite ^5.2.8 —— 极速构建工具",
            "pinia ^3.0.3 —— 状态管理",
            "tdesign-vue-next —— UI组件库",
            "tailwindcss ^3.4.17 —— 原子CSS",
            "typescript ^5.4.4 —— 类型安全",
        ],
        left_accent=NEON_PURPLE,
        right_accent=NEON_EMERALD
    )
    
    # ============================================================
    # Chapter 2: 核心功能
    # ============================================================
    builder.add_chapter("02", "核心功能", "RAG引擎、知识库、Agent与检索", NEON_EMERALD)
    
    # Slide 8: RAG Pipeline
    builder.add_list(
        title="RAG Pipeline 引擎",
        subtitle="基于 LangChain 构建的完整检索增强生成流水线",
        items=[
            "用户提问 → 检索模块：接收查询并分发到检索策略",
            "多策略检索：Vector / BM25 / Hybrid / RRF / MMR 五种策略",
            "RRF/MMR 重排序：精排候选文档，提升相关性",
            "上下文组装 → LLM 生成：Prompt工程 + 来源自动标注",
            "带溯源的 SSE 流式输出：实时打字机效果，每句可追溯",
        ],
        accent=NEON_EMERALD
    )
    
    # Slide 9: 检索策略
    builder.add_grid(
        title="检索策略详解",
        subtitle="五种核心检索策略，适配不同查询场景",
        items=[
            ("Vector", "稠密向量检索\nFAISS语义相似度", NEON_PURPLE),
            ("BM25", "稀疏关键词检索\n基于词频统计", NEON_BLUE),
            ("Hybrid", "加权线性融合\nvectorWeight+bm25Weight", NEON_EMERALD),
            ("RRF", "倒数排序融合\n默认推荐策略", NEON_ORANGE),
            ("MMR", "最大边际相关性\n去重多样化", NEON_PINK),
        ],
        cols=5
    )
    
    # Slide 10: 知识库管理
    builder.add_two_col(
        title="知识库与文档管理",
        left_title="权限系统",
        left_items=[
            "RBAC：管理员 / 查看者角色分级",
            "ACL：个人 / 共享 / 公开三级可见性",
            "前端驱动即时配置 + 后端实时生效",
        ],
        right_title="增量更新算法",
        right_items=[
            "SHA-256 文件哈希比对，秒级检测变更",
            "块级差异定位，精准更新向量库",
            "更新开销从 O(n) 降至 O(Δn)",
        ],
        left_accent=NEON_EMERALD,
        right_accent=NEON_BLUE
    )
    
    # Slide 11: 异步处理与OCR
    builder.add_two_col(
        title="异步处理与 OCR 降级",
        left_title="异步处理架构",
        left_items=[
            "文件上传 → 持久化存储（本地磁盘）",
            "生成任务 → Redis Stream 事件总线",
            "Worker 消费 → 解析/分块/向量化",
            "FAISS 索引更新，毫秒级检索就绪",
        ],
        right_title="OCR 三级降级",
        right_items=[
            "MinerU OCR —— 首选，深度学习版面分析",
            "PaddleOCR —— 降级，中文表格擅长",
            "Tesseract —— 兜底，英文版面分析",
        ],
        left_accent=NEON_EMERALD,
        right_accent=NEON_ORANGE
    )
    
    # Slide 12: ReAct Agent
    builder.add_three_col(
        title="ReAct Agent 任务模式",
        subtitle="让 LLM 具备拆解任务和自主决策的能力",
        cols=[
            {
                "title": "1. Thought",
                "content": "分析任务目标与历史记录，输出下一步思考",
                "example": '"要完成对比，我需要先获取A知识库关于X的政策..."',
                "accent": NEON_PURPLE,
            },
            {
                "title": "2. Action",
                "content": "解析思考输出，调用对应工具执行",
                "example": 'search_kb(keywords="政策", kb_id="A")',
                "accent": NEON_EMERALD,
            },
            {
                "title": "3. Observation",
                "content": "获取工具返回，追加到历史记录",
                "example": '"检索到3份相关政策文档..."',
                "accent": NEON_BLUE,
            },
        ]
    )
    
    # ============================================================
    # Chapter 3: 工程实现
    # ============================================================
    builder.add_chapter("03", "工程实现", "源码解析、配置与部署方案", NEON_ORANGE)
    
    # Slide 14: main.py
    builder.add_code(
        title="后端核心：FastAPI 应用初始化",
        subtitle="main.py —— 应用入口与生命周期管理",
        code_text='''import logging
import os
import sys
from pathlib import Path
from fastapi import FastAPI

def _first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value not in (None, ""):
            return value
    return default

def _apply_env_compat_aliases() -> None:
    groups = [
        ("JWT_SECRET", "JWT_SECRET_KEY"),
        ("JWT_EXPIRATION_HOURS", "JWT_EXPIRE_HOURS"),
        ("MODEL", "DEFAULT_LLM_MODEL"),
    ]
    for names in groups:
        value = _first_env(*names, default="")
        if not value:
            continue
        for name in names:
            os.environ.setdefault(name, value)

_apply_env_compat_aliases()

app = FastAPI(title="RAG Backend Service", version="1.0")

@app.on_event("startup")
async def _init_db_tables():
    try:
        from RAGF_User_Management.LogonAndLogin import ensure_tables_exist
        ensure_tables_exist()
    except Exception as e:
        logger.warning(f"MySQL 初始化失败: {e}")''',
        highlight="环境变量别名兼容 + 启动时惰性初始化（MySQL未启动不崩溃）"
    )
    
    # Slide 15: settings.py
    builder.add_code(
        title="统一配置管理",
        subtitle="config/settings.py —— 环境切换 + 集中化配置",
        code_text='''import os
from enum import Enum
from pathlib import Path

ENV_MODE = os.getenv("ENV_MODE", "development").lower()

class EnvironmentMode(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

class BaseConfig:
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    JWT_SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(BaseConfig):
    DEBUG = False
    LOG_LEVEL = "WARNING"
    _jwt_secret = os.getenv("JWT_SECRET", "")
    if not _jwt_secret:
        raise ValueError("生产环境必须设置 JWT_SECRET")

def get_config():
    mode = EnvironmentMode(ENV_MODE)
    if mode == EnvironmentMode.DEVELOPMENT:
        return DevelopmentConfig()
    elif mode == EnvironmentMode.PRODUCTION:
        return ProductionConfig()
    return DevelopmentConfig()

config = get_config()''',
        highlight="工厂模式 + 多环境继承 + 生产环境敏感配置校验"
    )
    
    # Slide 16: task_queue.py
    builder.add_code(
        title="Redis Stream 任务队列",
        subtitle="document_processing/task_queue.py —— 异步任务基础设施",
        code_text='''import asyncio
import logging
import os
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
STREAM_KEY = "rag:upload:tasks"
GROUP_NAME = "rag-worker-group"

class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"

_redis_client = None
_redis_available = False

async def _get_redis():
    global _redis_client, _redis_available
    if _redis_client is not None:
        return _redis_client if _redis_available else None
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=2)
        await client.ping()
        _redis_client = client
        _redis_available = True
        logger.info("[TaskQueue] Redis 连接成功")
        return client
    except Exception as e:
        _redis_available = False
        logger.warning("[TaskQueue] Redis 不可用，降级为内存队列: %s", e)
        return None

_TASK_REGISTRY: Dict[str, Callable] = {}

def register_task(task_type: str, func: Callable):
    _TASK_REGISTRY[task_type] = func''',
        highlight="三层解耦 + Redis Stream持久化 + 消费者组 + 内存队列降级"
    )
    
    # Slide 17: incremental_vectorizer.py
    builder.add_code(
        title="增量向量化管理器",
        subtitle="document_processing/incremental_vectorizer.py —— 核心优化算法",
        code_text='''import hashlib
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

VECTORSTORE_ROOT = "knowledge_base/vectorstores"
HASH_INDEX_ROOT = "metadata/vector_hash_index"

os.makedirs(VECTORSTORE_ROOT, exist_ok=True)
os.makedirs(HASH_INDEX_ROOT, exist_ok=True)

class HashIndex:
    def __init__(self, kb_id: str):
        self.kb_id = kb_id
        self.index_path = os.path.join(HASH_INDEX_ROOT, f"{kb_id}.json")
        self._data: Dict[str, dict] = self._load()

    def _load(self) -> Dict[str, dict]:
        if os.path.exists(self.index_path):
            with open(self.index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save(self):
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get_hash(self, doc_key: str) -> Optional[str]:
        entry = self._data.get(doc_key)
        if entry and not entry.get("deleted"):
            return entry.get("file_hash")
        return None

    def set_hash(self, doc_key: str, file_hash: str, chunk_ids: List[str]):
        self._data[doc_key] = {
            "file_hash": file_hash,
            "chunk_ids": chunk_ids,
            "vectorized_at": datetime.now().isoformat(),
            "chunk_count": len(chunk_ids),
            "deleted": False,
        }
        self._save()''',
        highlight="SHA-256哈希比对 + 块级索引 + 软删除标记，更新开销O(n)→O(Δn)"
    )
    
    # Slide 18: retrieval_strategy.py
    builder.add_code(
        title="检索策略路由",
        subtitle="document_processing/retrieval_strategy.py —— 策略配置与执行",
        code_text='''from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class RetrievalConfig:
    strategy: str = "rrf"
    topK: int = 6
    scoreThreshold: float = 0.0
    vectorWeight: float = 0.6
    bm25Weight: float = 0.4
    rerank: bool = False
    rerankTopN: int = 3

    @classmethod
    def from_dict(cls, d: dict) -> "RetrievalConfig":
        return cls(
            strategy=d.get("strategy", "rrf"),
            topK=int(d.get("topK", 6)),
            scoreThreshold=float(d.get("scoreThreshold", 0.0)),
            vectorWeight=float(d.get("vectorWeight", 0.6)),
            bm25Weight=float(d.get("bm25Weight", 0.4)),
            rerank=bool(d.get("rerank", False)),
            rerankTopN=int(d.get("rerankTopN", 3)),
        )''',
        highlight="策略模式 + 数据类配置 + 字典反序列化，前后端配置完全同步"
    )
    
    # Slide 19: docker-compose.yml
    builder.add_code(
        title="Docker Compose 部署",
        subtitle="docker-compose.yml —— 完整容器化编排",
        code_text='''version: '3.9'

services:
  redis:
    image: redis:7-alpine
    ports: ['6380:6379']
  
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME}
    ports: ['3307:3306']
  
  ollama:
    image: ollama/ollama:latest
    ports: ['11435:11434']
    deploy:
      resources:
        limits:
          memory: 2g
  
  backend:
    build: ./RagBackend
    ports: ['8000:8000']
    depends_on:
      - mysql
      - redis
      - ollama
    deploy:
      resources:
        limits:
          memory: 1500m
          cpus: '1.0'
  
  worker:
    build: ./RagBackend
    command: python -c "启动Worker..."
    depends_on:
      - redis
      - mysql
    deploy:
      resources:
        limits:
          memory: 2000m
          cpus: '1.5'
  
  frontend:
    build: ./RagFrontend
    ports: ['8089:80']
    depends_on:
      - backend''',
        highlight="6服务编排 + 健康检查依赖 + 资源隔离 + 命名卷持久化 + 独立Worker"
    )
    
    # ============================================================
    # Chapter 4: 测试验证
    # ============================================================
    builder.add_chapter("04", "测试验证", "检索质量与生成效果评估", NEON_BLUE)
    
    # Slide 21: 检索层测试
    builder.add_stats(
        title="检索层质量测试",
        left_data={
            "title": "实验设计",
            "items": [
                "测试文档：3 类典型文档（~1.5 万字）",
                "查询数量：50 个标注 query",
                "检索策略：5 种核心策略对比",
                "硬件：16GB 内存 + R9 9955HX",
            ],
        },
        right_data={
            "title": "评估指标",
            "items": [
                "Recall@5 —— 召回率",
                "Precision@5 —— 精确率",
                "mAP —— 平均精度均值",
                "NDCG@5 —— 折损增益",
            ],
        },
        stats=[
            ("88%", "Recall@5（RRF策略）"),
            ("0.85", "NDCG@5（RRF策略）"),
        ]
    )
    
    # Slide 22: 生成层测试
    builder.add_stats(
        title="生成层质量测试",
        left_data={
            "title": "实验设置",
            "items": [
                "本地模型：llama3:8b-instruct-q4_0",
                "云端模型：DeepSeek Chat",
                "温度系数：0.3",
                "最大 tokens：500",
                "评测框架：RAGAs",
            ],
        },
        right_data={
            "title": "核心结论",
            "items": [
                "RAG 模式忠实度提升 23%-17%",
                "Context Precision >= 85%",
                "完全贴合防幻觉问答价值",
                "低配模型表现超出预期",
            ],
        },
        big_stat=(">= 88%", "忠实度")
    )
    
    # Slide 23: 作品特色
    builder.add_grid(
        title="作品特色与创新点",
        items=[
            ("双模式切换", "LangChain与原生两种RAG模式，兼顾快速问答与深度检索", NEON_PURPLE),
            ("ReAct Agent", "LLM自主决定何时采取行动，实现更智能的问答系统", NEON_EMERALD),
            ("增量更新", "SHA-256哈希+块级差异比对，更新开销降至O(Δn)", NEON_ORANGE),
            ("权限治理", "RBAC+ACL三级权限，个人/共享/公开灵活配置", NEON_BLUE),
        ],
        cols=4
    )
    
    # Slide 24: 应用展望
    builder.add_two_col(
        title="应用推广与展望",
        left_title="应用场景",
        left_items=[
            "垂直领域知识服务：法律、教育、医疗 —— 可溯源的知识问答",
            "企业内部智能知识库：文档统一管理，团队协作共享",
        ],
        right_title="未来展望",
        right_items=[
            "RAG 优化：提升数据清洗质量，增强检索精度",
            "多智能体协作：多个 Agent 协同解决复杂问题",
        ],
        left_accent=NEON_PURPLE,
        right_accent=NEON_EMERALD
    )
    
    # Slide 25: End
    builder.add_cover(
        title="谢谢观看",
        subtitle="ASF-RAG 智能知识管理平台",
        description="防幻觉问答 · 私有化部署 · 无限记忆",
        accent=NEON_PURPLE
    )
    
    # Save
    output_path = r"D:\KnowledgeRAG-GZHU-Backup\slides\ASF-RAG-Complete.pptx"
    builder.save(output_path)
    return output_path


if __name__ == "__main__":
    print("=" * 60)
    print("ASF-RAG Complete Presentation Generator")
    print("=" * 60)
    
    path = create_rag_presentation()
    
    print("\n" + "=" * 60)
    print(f"Presentation created: {path}")
    print("=" * 60)
