# -*- mode: python ; coding: utf-8 -*-
# KnowledgeRAG 后端 PyInstaller 打包配置
# 使用方式：pyinstaller rag_backend.spec
# 输出：dist/rag_backend.exe（Windows）或 dist/rag_backend（Linux/macOS）

import os
import sys
from pathlib import Path

# 项目根目录（spec 文件所在目录）
PROJECT_ROOT = Path(SPEC).parent.resolve()
BACKEND_DIR = PROJECT_ROOT / "RagBackend"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"

block_cipher = None

# 收集所有 Python 依赖和数据文件
hiddenimports = [
    # FastAPI 核心
    "fastapi",
    "fastapi.applications",
    "fastapi.routing",
    "starlette",
    "starlette.applications",
    "starlette.routing",
    "uvicorn",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    # 中间件和依赖
    "pydantic",
    "pydantic.functional_validators",
    "pydantic.functional_serializers",
    "pydantic.fields",
    "pydantic.main",
    "python_multipart",
    "python_dotenv",
    # 认证
    "PyJWT",
    "jwt",
    # 数据库
    "PyMySQL",
    "pymysql",
    "aiomysql",
    "sqlalchemy",
    "sqlalchemy.ext.asyncio",
    "sqlalchemy.orm",
    # RAG 和向量
    "langchain",
    "langchain_community",
    "langchain_ollama",
    "langchain_huggingface",
    "faiss",
    "faiss_cuda",
    "sentence_transformers",
    "numpy",
    "torch",
    # 文档解析
    "pdfplumber",
    "pdf2image",
    "PIL",
    "PIL.Image",
    "PIL.PpmImagePlugin",
    "PyPDF2",
    "pdf2image",
    "beautifulsoup4",
    "bs4",
    "camelot",
    "camelot.ext",
    "layoutparser",
    "python_docx",
    "docx2txt",
    "docx",
    "docx.document",
    "docx.table",
    "docx.text.paragraph",
    "pytesseract",
    "Jinja2",
    "jinja2",
    # API 客户端
    "googleapiclient",
    "googleapiclient.discovery",
    "googleapiclient.errors",
    "requests",
    # 异步
    "aiofiles",
    "aiohttp",
    "aiohttp.client_exceptions",
    # Redis
    "redis",
    "redis.asyncio",
    # 配置和日志
    "pydantic_settings",
    "pydantic_settings.main",
    "trace_logging",
    # 数据处理
    "pandas",
    "numpy",
    "chardet",
    "python_dateutil",
    "dateutil",
    "dateutil.relativedelta",
    # JSON 处理
    "orjson",
    "ujson",
    # 其他工具
    "cryptography",
    "cryptography.fernet",
    "passlib",
    "passlib.context",
    "python_jose",
    "jose",
    # RAG 模块
    "rag_enhancement",
    "rag_enhancement.query_rewriter",
    "knowledge_base",
    "knowledge_base.vector_store",
    "search",
    "search.hybrid_search",
    "chat_units",
    "chat_units.fallback_chain",
    "document_processing",
    "document_processing.vectorize_task",
    "document_processing.file_parser",
    "creation",
    "creation.doc_creation",
    "skills",
    "skills.skill_executor",
    "multi_model",
    "multi_model.model_router",
    "multi_model.extended_model_router",
    "rbac_manager",
    "billing",
    "billing.ticket_pricing",
    "rag_enhancement",
    "knowledge_graph",
    "knowledge_graph.entity_linking",
    "evaluation",
    "evaluation.metrics",
]

# 数据文件和目录
datas = [
    # 打包后端目录中的所有 .py 文件
    (str(BACKEND_DIR), "RagBackend"),
    # requirements.txt
    (str(BACKEND_DIR / "requirements.txt"), "RagBackend"),
]

# 添加后端目录下的子目录（包含静态资源、模板等）
for subdir in ["skills", "templates", "assets", "docs"]:
    subdir_path = BACKEND_DIR / subdir
    if subdir_path.exists():
        datas.append((str(subdir_path), f"RagBackend/{subdir}"))

# Windows 配置
if sys.platform == "win32":
    exe_options = [
        dict(
            name="rag_backend",
            debug=False,
            bootloader_ignore_signals=False,
            strip=False,
            upx=True,
            runtime_tmpdir=None,
            console=False,  # GUI 模式，无控制台窗口
            disable_windowed_traceback=False,
            argv_emulation=False,
            target_arch=None,
            codesign_identity=None,
            entitlements_file=None,
            icon=str(BACKEND_DIR / "assets" / "icon.ico") if (BACKEND_DIR / "assets" / "icon.ico").exists() else None,
        )
    ]
else:
    exe_options = [
        dict(
            name="rag_backend",
            debug=False,
            bootloader_ignore_signals=False,
            strip=False,
            upx=True,
            runtime_tmpdir=None,
            console=False,
            disable_windowed_traceback=False,
        )
    ]

a = Analysis(
    [str(BACKEND_DIR / "main.py")],
    pathex=[str(BACKEND_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="rag_backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
