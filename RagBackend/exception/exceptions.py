"""
统一异常定义和处理器
遵循防御性编程规范
"""

from fastapi import HTTPException, status
from typing import Any, Dict, Optional
from enum import Enum


class ErrorCode(str, Enum):
    """错误代码枚举"""
    
    # 通用错误
    SUCCESS = "000000"
    INVALID_REQUEST = "400001"
    UNAUTHORIZED = "401001"
    FORBIDDEN = "403001"
    NOT_FOUND = "404001"
    CONFLICT = "409001"
    INTERNAL_ERROR = "500001"
    
    # 知识库相关
    KB_NOT_FOUND = "404101"
    KB_ALREADY_EXISTS = "409101"
    KB_DELETE_FAILED = "500101"
    KB_CREATE_FAILED = "500102"
    KB_UPDATE_FAILED = "500103"
    
    # 文件上传相关
    FILE_TOO_LARGE = "413001"
    FILE_INVALID_FORMAT = "415001"
    UPLOAD_FAILED = "500201"
    
    # 数据库相关
    DB_CONNECTION_ERROR = "503001"
    DB_QUERY_ERROR = "500301"


class APIException(Exception):
    """
    API 层统一异常基类
    
    用于所有 API 相关的异常，便于统一处理
    """
    
    def __init__(
        self,
        code: str = ErrorCode.INTERNAL_ERROR,
        message: str = "服务器内部错误",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        """
        Args:
            code: 错误代码
            message: 用户展示消息
            status_code: HTTP 状态码
            detail: 技术细节（内部日志用）
            data: 额外数据
        """
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail or message
        self.data = data or {}
        
        super().__init__(self.detail)


class KnowledgeBaseException(APIException):
    """知识库异常基类"""
    
    def __init__(
        self,
        code: str = ErrorCode.KB_CREATE_FAILED,
        message: str = "知识库操作失败",
        **kwargs
    ):
        super().__init__(code=code, message=message, **kwargs)


class KnowledgeBaseNotFound(KnowledgeBaseException):
    """知识库不存在异常"""
    
    def __init__(self, kb_id: str, **kwargs):
        super().__init__(
            code=ErrorCode.KB_NOT_FOUND,
            message=f"知识库 '{kb_id}' 不存在",
            status_code=status.HTTP_404_NOT_FOUND,
            data={"kb_id": kb_id},
            **kwargs
        )


class KnowledgeBaseAlreadyExists(KnowledgeBaseException):
    """知识库已存在异常"""
    
    def __init__(self, kb_name: str, **kwargs):
        super().__init__(
            code=ErrorCode.KB_ALREADY_EXISTS,
            message=f"知识库 '{kb_name}' 已存在",
            status_code=status.HTTP_409_CONFLICT,
            data={"kb_name": kb_name},
            **kwargs
        )


class FileUploadException(APIException):
    """文件上传异常基类"""
    
    def __init__(
        self,
        code: str = ErrorCode.UPLOAD_FAILED,
        message: str = "文件上传失败",
        **kwargs
    ):
        super().__init__(code=code, message=message, **kwargs)


class FileTooLargeException(FileUploadException):
    """文件过大异常"""
    
    def __init__(self, file_size: int, max_size: int, **kwargs):
        super().__init__(
            code=ErrorCode.FILE_TOO_LARGE,
            message=f"文件过大（{file_size} > {max_size}）",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            data={"file_size": file_size, "max_size": max_size},
            **kwargs
        )


class InvalidFileFormatException(FileUploadException):
    """无效文件格式异常"""
    
    def __init__(self, file_name: str, allowed_formats: list, **kwargs):
        super().__init__(
            code=ErrorCode.FILE_INVALID_FORMAT,
            message=f"文件格式不支持: {file_name}",
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            data={
                "file_name": file_name,
                "allowed_formats": allowed_formats
            },
            **kwargs
        )


class DatabaseException(APIException):
    """数据库异常基类"""
    
    def __init__(
        self,
        code: str = ErrorCode.DB_QUERY_ERROR,
        message: str = "数据库查询失败",
        **kwargs
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            **kwargs
        )


class ValidationException(APIException):
    """数据验证异常"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            code=ErrorCode.INVALID_REQUEST,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            **kwargs
        )


# 全局异常响应格式
class ErrorResponse(BaseModel):
    """错误响应模型"""
    code: str
    message: str
    detail: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# 需要在 main.py 中注册异常处理器
async def api_exception_handler(request, exc: APIException):
    """API 异常处理器"""
    from fastapi.responses import JSONResponse
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail if request.app.debug else None,
            "data": exc.data if exc.data else None,
        }
    )


# 导入 BaseModel
from pydantic import BaseModel
