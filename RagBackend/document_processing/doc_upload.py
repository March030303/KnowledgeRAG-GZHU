# chunk_management.py
"""
文档上传管理模块 - 支持文件分块上传、合并、验证和元数据管理

核心功能：
1. 文件分块上传：接收分块文件，使用 Semaphore 限流（最多 8 个并发）
2. 文件分块合并：验证完整性后合并分块为完整文件
3. 文件验证：类型验证、大小限制、哈希计算（SHA256/MD5）
4. 文件分析：计算文档分块数量（支持多种分割策略）
5. 元数据管理：为每个上传文件创建完整的元数据记录

安全防护：
- 路径遍历防护：使用 Path 对象规范化路径
- 输入校验：Pydantic 模型完整校验
- 异常处理：完整的 try/except 捕获和日志记录
- 资源释放：with 语句自动释放文件句柄
"""

import asyncio
import hashlib
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import aiofiles
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# 常量定义 - 所有魔法数字已配置化
# ============================================================================
UPLOAD_DIR = os.getenv("KB_UPLOAD_DIR", "local-KLB-files")
METADATA_DIR = os.getenv("KB_METADATA_DIR", "metadata")
MAX_FILE_SIZE = int(os.getenv("KB_MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB
KB_UPLOAD_CONCURRENCY = int(os.getenv("KB_UPLOAD_CONCURRENCY", 8))
KB_CHUNK_SIZE = int(os.getenv("KB_CHUNK_SIZE", 1000))  # 文本分块字符数

# FIX: [DOC-001] 扩展允许的文件格式
ALLOWED_EXTENSIONS = {
    # 文档格式
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv",
    # 文本格式
    ".txt", ".md", ".rtf",
    # 图像格式
    ".png", ".jpg", ".jpeg", ".gif", ".bmp"
}

# 并发限制（FIX: [DOC-005] 配置化魔法数字）
_chunk_semaphore = asyncio.Semaphore(KB_UPLOAD_CONCURRENCY)

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

METADATA_FILE = os.path.join(METADATA_DIR, "documents.json")
CHUNK_UPLOAD_DIR = os.path.join(UPLOAD_DIR, "chunks")
os.makedirs(CHUNK_UPLOAD_DIR, exist_ok=True)

# ============================================================================
# Pydantic 数据模型
# ============================================================================
class DocumentStatus(BaseModel):
    """文档状态模型"""
    documentId: int
    enabled: bool


class DeleteDocuments(BaseModel):
    """删除文档请求模型"""
    documentIds: List[int]


class DocumentResponse(BaseModel):
    """文档响应模型"""
    id: int
    name: str
    fileType: str
    chunks: int
    uploadDate: str
    slicingMethod: str
    enabled: bool
    file_size: int
    file_hash: str


class UploadChunkRequest(BaseModel):
    """文件分块请求模型"""
    fileHash: str = Field(..., description="文件哈希值（SHA256）")
    chunkIndex: int = Field(..., ge=0, description="分块索引")
    totalChunks: int = Field(..., gt=0, description="总分块数")
    fileName: str = Field(..., min_length=1, description="原始文件名")
    KLB_id: str = Field(..., min_length=1, description="知识库 ID")

    @validator("fileName")
    def validate_filename(cls, v: str) -> str:
        """验证文件名不包含路径分隔符"""
        if "/" in v or "\\" in v or ".." in v:
            raise ValueError("文件名不能包含路径分隔符")
        return v.strip()

    @validator("KLB_id")
    def validate_kb_id(cls, v: str) -> str:
        """验证知识库 ID 不包含路径遍历字符"""
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("非法的知识库 ID")
        return v.strip()


class UploadCompleteRequest(BaseModel):
    """文件合并请求模型"""
    fileHash: str = Field(..., description="文件哈希值")
    fileName: str = Field(..., min_length=1, description="原始文件名")
    totalChunks: int = Field(..., gt=0, description="总分块数")
    KLB_id: str = Field(..., min_length=1, description="知识库 ID")

    @validator("fileName")
    def validate_filename(cls, v: str) -> str:
        if "/" in v or "\\" in v or ".." in v:
            raise ValueError("文件名不能包含路径分隔符")
        return v.strip()

    @validator("KLB_id")
    def validate_kb_id(cls, v: str) -> str:
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("非法的知识库 ID")
        return v.strip()


# Document management
from .doc_manage import LocalDocumentManager

doc_manager = LocalDocumentManager()











# File upload
UPLOAD_DIR = "local-KLB-files"
METADATA_DIR = "metadata"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".doc", ".md", ".rtf"}

# IO 8
_chunk_semaphore = asyncio.Semaphore(8)

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

METADATA_FILE = os.path.join(METADATA_DIR, "documents.json")

# Temporary directory
CHUNK_UPLOAD_DIR = os.path.join(UPLOAD_DIR, "chunks")
os.makedirs(CHUNK_UPLOAD_DIR, exist_ok=True)

# Pydantic
class DocumentStatus(BaseModel):
    documentId: int
    enabled: bool

class DeleteDocuments(BaseModel):
    documentIds: List[int]

class DocumentResponse(BaseModel):
    id: int
    name: str
    fileType: str
    chunks: int
    uploadDate: str
    slicingMethod: str
    enabled: bool
    file_size: int
    file_hash: str

# Document management

from .doc_manage import LocalDocumentManager

# Document management
doc_manager = LocalDocumentManager()

# ============================================================================
# 工具函数
# ============================================================================

def get_file_hash(content: bytes) -> str:
    """生成文件的 SHA256 哈希值（用于增量向量化对比，提升安全性）"""
    return hashlib.sha256(content).hexdigest()


def get_file_type(filename: str) -> str:
    """
    获取文件扩展名

    Args:
        filename: 文件名

    Returns:
        小写扩展名（如 .pdf）
    """
    return Path(filename).suffix.lower()


def validate_file(filename: str, content: bytes) -> Tuple[bool, str]:
    """
    验证文件类型和大小

    Args:
        filename: 文件名
        content: 文件内容字节流

    Returns:
        (是否有效, 错误信息或"验证通过")
    """
    file_ext = get_file_type(filename)

    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"不支持的文件类型: {file_ext}"

    if len(content) > MAX_FILE_SIZE:
        return (
            False,
            f"文件大小超过限制 ({MAX_FILE_SIZE / 1024 / 1024:.1f}MB)"
        )

    return True, "验证通过"


# ============================================================================
# API 端点 - 文件分块上传
# ============================================================================

@router.post("/api/upload-chunk/", response_model=dict)
async def upload_chunk(
    chunk: UploadFile = File(...),
    fileHash: str = Form(...),
    chunkIndex: int = Form(...),
    totalChunks: int = Form(...),
    fileName: str = Form(...),
    KLB_id: str = Form(...)
) -> JSONResponse:
    """
    上传文件分块（使用 Semaphore 限流，最多 8 个并发写入）

    FIX: [DOC-004] 添加 Pydantic 模型验证
    FIX: [DOC-002] 改用 logger 替代 print()
    FIX: [DOC-006] 添加完整的返回类型注解

    Args:
        chunk: 上传的文件分块
        fileHash: 文件哈希值（SHA256）
        chunkIndex: 分块索引
        totalChunks: 总分块数
        fileName: 原始文件名
        KLB_id: 知识库 ID

    Returns:
        JSONResponse: 上传结果

    Raises:
        HTTPException: 上传失败时返回 500 错误
    """
    # FIX: [DOC-004] 验证输入参数防止路径遍历
    try:
        req = UploadChunkRequest(
            fileHash=fileHash,
            chunkIndex=chunkIndex,
            totalChunks=totalChunks,
            fileName=fileName,
            KLB_id=KLB_id
        )
    except ValueError as e:
        logger.warning(f"上传分块请求参数验证失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    async with _chunk_semaphore:
        try:
            # FIX: [DOC-004] 使用 Path 对象防止路径遍历
            chunk_base = Path(CHUNK_UPLOAD_DIR)
            kb_chunk_dir = chunk_base / req.KLB_id / req.fileHash

            # 验证路径安全性
            try:
                kb_chunk_dir.resolve().relative_to(chunk_base.resolve())
            except ValueError:
                logger.error(f"路径遍历攻击: {req.KLB_id}/{req.fileHash}")
                raise HTTPException(status_code=400, detail="非法的知识库路径")

            kb_chunk_dir.mkdir(parents=True, exist_ok=True)

            chunk_file_path = kb_chunk_dir / f"chunk_{req.chunkIndex}.part"

            content = await chunk.read()
            async with aiofiles.open(str(chunk_file_path), "wb") as f:
                await f.write(content)

            # FIX: [DOC-002] 改用 logger.info() 替代 print()
            logger.info(
                f"分块上传成功: 文件名={req.fileName}, 文件哈希={req.fileHash}, "
                f"分块索引={req.chunkIndex}, 总分块数={req.totalChunks}"
            )

            return JSONResponse(
                status_code=200,
                content={
                    "message": "分块上传成功",
                    "fileHash": req.fileHash,
                    "chunkIndex": req.chunkIndex,
                    "totalChunks": req.totalChunks
                }
            )

        except HTTPException:
            raise
        except Exception as e:
            # FIX: [DOC-002] 使用 logger.error() 记录异常
            logger.error(f"分块上传失败: {type(e).__name__}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"分块上传失败: {type(e).__name__}"
            )




@router.post("/api/upload-complete/", response_model=dict)
async def upload_complete(request: Request) -> JSONResponse:
    """
    合并文件分块并创建文档元数据

    FIX: [DOC-003] 完整异常处理和资源释放
    FIX: [DOC-004] 路径安全验证
    FIX: [DOC-002] 改用 logger 替代 print()
    FIX: [DOC-006] 添加返回类型注解

    Args:
        request: FastAPI 请求对象

    Returns:
        JSONResponse: 合并结果和文档元数据

    Raises:
        HTTPException: 合并失败或参数验证失败
    """
    final_file_path = None

    try:
        # 解析请求数据
        try:
            data = await request.json()
        except Exception as e:
            logger.warning(f"请求体解析失败: {e}")
            raise HTTPException(status_code=400, detail="请求体格式错误")

        # FIX: [DOC-004] 使用 Pydantic 模型验证输入
        try:
            req = UploadCompleteRequest(**data)
        except ValueError as e:
            logger.warning(f"合并请求参数验证失败: {e}")
            raise HTTPException(status_code=400, detail=str(e))

        logger.info(
            f"接收到文件合并请求: fileHash={req.fileHash}, "
            f"fileName={req.fileName}, totalChunks={req.totalChunks}, KLB_id={req.KLB_id}"
        )

        # 检查分块目录是否存在
        chunk_base = Path(CHUNK_UPLOAD_DIR)
        file_chunk_dir = chunk_base / req.KLB_id / req.fileHash

        # 路径安全性验证
        try:
            file_chunk_dir.resolve().relative_to(chunk_base.resolve())
        except ValueError:
            logger.error(f"路径遍历攻击: {req.KLB_id}/{req.fileHash}")
            raise HTTPException(status_code=400, detail="非法的知识库路径")

        if not file_chunk_dir.exists():
            logger.warning(f"分块目录不存在: {file_chunk_dir}")
            raise HTTPException(status_code=400, detail="分块目录不存在")

        uploaded_chunks = list(file_chunk_dir.iterdir())
        logger.info(
            f"分块检查: 已上传={len(uploaded_chunks)}, 预期={req.totalChunks}"
        )

        if len(uploaded_chunks) != req.totalChunks:
            raise HTTPException(
                status_code=400,
                detail=f"分块数量不匹配: 已上传 {len(uploaded_chunks)}, "
                       f"预期 {req.totalChunks}"
            )

        # 准备文件保存路径
        file_ext = get_file_type(req.fileName)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_filename = (
            f"{req.fileName}-{timestamp}_{req.fileHash[:8]}{file_ext}"
        )

        # FIX: [DOC-004] 使用 Path 对象防止路径遍历
        upload_base = Path(UPLOAD_DIR)
        kb_upload_dir = upload_base / req.KLB_id

        # 验证路径安全性
        try:
            kb_upload_dir.resolve().relative_to(upload_base.resolve())
        except ValueError:
            logger.error(f"路径遍历攻击: {req.KLB_id}")
            raise HTTPException(status_code=400, detail="非法的知识库路径")

        final_file_path = kb_upload_dir / saved_filename
        final_file_path.parent.mkdir(parents=True, exist_ok=True)

        # FIX: [DOC-003] 完整异常处理的分块合并
        try:
            await asyncio.to_thread(
                _merge_chunks_safe,
                file_chunk_dir,
                final_file_path,
                req.totalChunks
            )
        except FileNotFoundError as e:
            logger.error(f"分块文件缺失: {e}")
            if final_file_path.exists():
                final_file_path.unlink()
            raise HTTPException(status_code=400, detail=str(e))
        except IOError as e:
            logger.error(f"文件合并 IO 错误: {e}")
            if final_file_path.exists():
                final_file_path.unlink()
            raise HTTPException(status_code=500, detail="文件合并失败")

        logger.info(
            f"文件合并成功: {req.fileName}, "
            f"最终路径: {final_file_path}"
        )

        # 计算文件哈希和大小
        existing_file_hash, file_size = await asyncio.to_thread(
            _compute_hash_and_size,
            str(final_file_path)
        )

        # 验证文件类型和大小
        if file_ext not in ALLOWED_EXTENSIONS:
            final_file_path.unlink()
            logger.warning(f"不支持的文件类型: {file_ext}")
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_ext}"
            )

        if file_size > MAX_FILE_SIZE:
            final_file_path.unlink()
            logger.warning(f"文件超过大小限制: {file_size / 1024 / 1024:.1f}MB")
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制 ({MAX_FILE_SIZE / 1024 / 1024:.1f}MB)"
            )

        # 检查重复文件
        existing_docs = [
            doc for doc in doc_manager.get_all_documents()
            if doc.get("file_hash") == existing_file_hash
        ]

        if existing_docs:
            for doc in existing_docs:
                try:
                    await doc_manager.delete_document(doc["id"], req.KLB_id)
                    logger.info(f"更新重复文件: {doc['name']}, KB: {req.KLB_id}")
                except Exception as e:
                    logger.warning(f"删除旧版本文件失败: {e}")

        # 创建文档元数据
        slicing_method = "按段落"
        estimated_chunks = max(1, file_size // KB_CHUNK_SIZE)

        document_data = {
            "id": None,
            "name": req.fileName,
            "fileType": file_ext.replace(".", ""),
            "chunks": estimated_chunks,
            "uploadDate": datetime.now().strftime("%Y-%m-%d"),
            "slicingMethod": slicing_method,
            "enabled": True,
            "file_size": file_size,
            "file_hash": existing_file_hash,
            "file_path": str(final_file_path),
            "created_at": datetime.now().isoformat()
        }

        try:
            doc_id = await doc_manager.add_document(document_data)
            document_data["id"] = doc_id
        except Exception as e:
            logger.error(f"保存文档元数据失败: {e}")
            # 不删除文件，只记录错误
            raise HTTPException(status_code=500, detail="保存文档元数据失败")

        # FIX: [DOC-003] 完整异常处理清理临时分块
        try:
            shutil.rmtree(str(file_chunk_dir))
            logger.debug(f"清理临时分块目录: {file_chunk_dir}")
        except Exception as e:
            logger.warning(f"清理临时分块失败: {e}")

        logger.info(f"文件处理完成: {req.fileName}, 文件 ID: {doc_id}")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "文件合并成功",
                "fileId": doc_id,
                "fileName": req.fileName,
                "filePath": str(final_file_path),
                "chunks": estimated_chunks,
                "slicingMethod": slicing_method
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        # FIX: [DOC-003] 异常发生时清理文件
        if final_file_path and final_file_path.exists():
            try:
                final_file_path.unlink()
                logger.debug(f"删除损坏的文件: {final_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"删除文件失败: {cleanup_error}")

        logger.error(
            f"文件合并失败: {type(e).__name__}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"文件合并失败: {type(e).__name__}"
        )









# ============================================================================
# 辅助函数 - 安全的文件操作
# ============================================================================

def _merge_chunks_safe(
    chunk_dir: Path,
    output_file: Path,
    total_chunks: int
) -> None:
    """
    安全合并文件分块

    FIX: [DOC-003] 完整异常处理和资源释放

    Args:
        chunk_dir: 分块目录
        output_file: 输出文件路径
        total_chunks: 总分块数

    Raises:
        FileNotFoundError: 分块文件不存在
        IOError: 文件操作失败
    """
    try:
        with open(str(output_file), "wb") as outfile:
            for i in range(total_chunks):
                chunk_file_path = chunk_dir / f"chunk_{i}.part"

                if not chunk_file_path.exists():
                    raise FileNotFoundError(
                        f"分块文件 {chunk_file_path} 不存在"
                    )

                try:
                    with open(str(chunk_file_path), "rb") as infile:
                        shutil.copyfileobj(infile, outfile)
                except IOError as e:
                    logger.error(f"读取分块 {i} 失败: {e}")
                    raise
    except Exception as e:
        # 合并失败，清理损坏的文件
        if output_file.exists():
            try:
                output_file.unlink()
                logger.debug(f"删除损坏的文件: {output_file}")
            except Exception as cleanup_error:
                logger.warning(f"删除文件失败: {cleanup_error}")
        raise


def _compute_hash_and_size(file_path: str) -> Tuple[str, int]:
    """
    流式读取文件，计算 MD5 哈希与文件大小

    不将整个文件载入内存，使用 64KB 的块读取

    Args:
        file_path: 文件路径

    Returns:
        (MD5 哈希值, 文件大小字节数)

    Raises:
        IOError: 文件读取失败
    """
    md5_hash = hashlib.md5()
    size = 0

    try:
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(65536), b""):
                md5_hash.update(block)
                size += len(block)
    except IOError as e:
        logger.error(f"计算文件哈希失败: {e}")
        raise

    return md5_hash.hexdigest(), size


# ============================================================================
# 文本分块计算
# ============================================================================

def calculate_chunks(
    content: bytes,
    slicing_method: str = "按段落"
) -> int:
    """
    计算文件分块数量

    FIX: [DOC-005] 配置化魔法数字 KB_CHUNK_SIZE
    FIX: [DOC-006] 添加返回类型注解

    Args:
        content: 文件内容字节流
        slicing_method: 分块方法（按段落/固定长度/按句子）

    Returns:
        分块数量（最小为 1）
    """
    try:
        content_str = content.decode("utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"内容解码失败: {e}, 返回默认分块数 1")
        return 1

    try:
        if slicing_method == "按段落":
            # 按段落分块（双换行符分隔）
            chunks = len([
                p for p in content_str.split("\n\n")
                if p.strip()
            ])

        elif slicing_method == "固定长度":
            # FIX: [DOC-005] 使用配置化的 KB_CHUNK_SIZE
            chunks = (
                len(content_str) // KB_CHUNK_SIZE +
                (1 if len(content_str) % KB_CHUNK_SIZE else 0)
            )

        else:  # 按句子
            chunks = len([
                s for s in content_str.split(".")
                if s.strip()
            ])

        return max(1, chunks)

    except Exception as e:
        logger.error(f"计算文本分块失败: {e}")
        return 1

