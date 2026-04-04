"""
test_exceptions_unit.py - exception/exceptions.py 模块单元测试
测试所有异常类、ErrorCode 枚举、ErrorResponse 模型、异常处理器
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status


class TestErrorCode:
    """ErrorCode 枚举测试"""

    def test_success_code(self):
        from exception.exceptions import ErrorCode
        assert ErrorCode.SUCCESS == "000000"

    def test_all_codes_are_strings(self):
        from exception.exceptions import ErrorCode
        for code in ErrorCode:
            assert isinstance(code.value, str)

    def test_kb_not_found_code(self):
        from exception.exceptions import ErrorCode
        assert ErrorCode.KB_NOT_FOUND == "404101"

    def test_kb_already_exists_code(self):
        from exception.exceptions import ErrorCode
        assert ErrorCode.KB_ALREADY_EXISTS == "409101"

    def test_file_too_large_code(self):
        from exception.exceptions import ErrorCode
        assert ErrorCode.FILE_TOO_LARGE == "413001"

    def test_invalid_format_code(self):
        from exception.exceptions import ErrorCode
        assert ErrorCode.FILE_INVALID_FORMAT == "415001"

    def test_db_connection_error_code(self):
        from exception.exceptions import ErrorCode
        assert ErrorCode.DB_CONNECTION_ERROR == "503001"


class TestAPIException:
    """APIException 基类测试"""

    def test_default_attributes(self):
        from exception.exceptions import APIException, ErrorCode
        exc = APIException()
        assert exc.code == ErrorCode.INTERNAL_ERROR
        assert exc.message == "服务器内部错误"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_custom_attributes(self):
        from exception.exceptions import APIException
        exc = APIException(
            code="TEST001",
            message="测试错误",
            status_code=400,
            detail="详细描述",
            data={"key": "value"},
        )
        assert exc.code == "TEST001"
        assert exc.message == "测试错误"
        assert exc.status_code == 400
        assert exc.detail == "详细描述"
        assert exc.data == {"key": "value"}

    def test_detail_defaults_to_message(self):
        from exception.exceptions import APIException
        exc = APIException(message="自动 detail")
        assert exc.detail == "自动 detail"

    def test_data_defaults_to_empty_dict(self):
        from exception.exceptions import APIException
        exc = APIException()
        assert exc.data == {}

    def test_is_exception(self):
        from exception.exceptions import APIException
        exc = APIException()
        assert isinstance(exc, Exception)


class TestKnowledgeBaseException:
    """KnowledgeBaseException 及子类测试"""

    def test_kb_base_defaults(self):
        from exception.exceptions import KnowledgeBaseException
        exc = KnowledgeBaseException()
        assert exc.message == "知识库操作失败"

    def test_kb_not_found(self):
        from exception.exceptions import KnowledgeBaseNotFound
        exc = KnowledgeBaseNotFound("my-kb")
        assert "my-kb" in exc.message
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.data["kb_id"] == "my-kb"

    def test_kb_already_exists(self):
        from exception.exceptions import KnowledgeBaseAlreadyExists
        exc = KnowledgeBaseAlreadyExists("existing-kb")
        assert "existing-kb" in exc.message
        assert exc.status_code == status.HTTP_409_CONFLICT
        assert exc.data["kb_name"] == "existing-kb"

    def test_kb_not_found_is_api_exception(self):
        from exception.exceptions import APIException, KnowledgeBaseNotFound
        exc = KnowledgeBaseNotFound("test")
        assert isinstance(exc, APIException)


class TestFileUploadException:
    """文件上传异常类测试"""

    def test_file_upload_base_defaults(self):
        from exception.exceptions import FileUploadException
        exc = FileUploadException()
        assert exc.message == "文件上传失败"

    def test_file_too_large(self):
        from exception.exceptions import FileTooLargeException
        exc = FileTooLargeException(file_size=10_000_000, max_size=5_000_000)
        assert exc.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert exc.data["file_size"] == 10_000_000
        assert exc.data["max_size"] == 5_000_000
        assert "10000000" in exc.message

    def test_invalid_file_format(self):
        from exception.exceptions import InvalidFileFormatException
        exc = InvalidFileFormatException(
            file_name="evil.exe",
            allowed_formats=["pdf", "txt"],
        )
        assert exc.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        assert exc.data["file_name"] == "evil.exe"
        assert "evil.exe" in exc.message


class TestDatabaseException:
    """数据库异常测试"""

    def test_database_exception_defaults(self):
        from exception.exceptions import DatabaseException
        exc = DatabaseException()
        assert exc.message == "数据库查询失败"
        assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_database_exception_custom_code(self):
        from exception.exceptions import DatabaseException, ErrorCode
        exc = DatabaseException(code=ErrorCode.DB_CONNECTION_ERROR, message="连接失败")
        assert exc.code == ErrorCode.DB_CONNECTION_ERROR


class TestValidationException:
    """数据验证异常测试"""

    def test_validation_exception(self):
        from exception.exceptions import ValidationException
        exc = ValidationException("字段必填")
        assert exc.message == "字段必填"
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestErrorResponse:
    """ErrorResponse Pydantic 模型测试"""

    def test_minimal_response(self):
        from exception.exceptions import ErrorResponse
        resp = ErrorResponse(code="000001", message="测试")
        assert resp.code == "000001"
        assert resp.message == "测试"
        assert resp.detail is None
        assert resp.data is None
        assert resp.trace_id is None

    def test_full_response(self):
        from exception.exceptions import ErrorResponse
        resp = ErrorResponse(
            code="400001",
            message="请求错误",
            detail="详细说明",
            data={"field": "kb_name"},
            trace_id="abc12345",
        )
        assert resp.detail == "详细说明"
        assert resp.trace_id == "abc12345"

    def test_serialization(self):
        from exception.exceptions import ErrorResponse
        resp = ErrorResponse(code="000000", message="ok")
        d = resp.model_dump()
        assert "code" in d
        assert "message" in d


class TestApiExceptionHandler:
    """api_exception_handler 函数测试"""

    @pytest.mark.asyncio
    async def test_handler_returns_json_response(self):
        from exception.exceptions import APIException, api_exception_handler

        request = MagicMock()
        request.url.path = "/api/test"
        request.app.debug = False

        exc = APIException(
            code="400001",
            message="请求无效",
            status_code=400,
        )

        response = await api_exception_handler(request, exc)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_handler_includes_trace_id_header(self):
        from exception.exceptions import APIException, api_exception_handler

        request = MagicMock()
        request.url.path = "/api/test"
        request.app.debug = False

        exc = APIException()
        response = await api_exception_handler(request, exc)
        assert "X-Trace-Id" in response.headers

    @pytest.mark.asyncio
    async def test_handler_response_body_contains_code(self):
        import json
        from exception.exceptions import APIException, api_exception_handler

        request = MagicMock()
        request.url.path = "/api/test"
        request.app.debug = False

        exc = APIException(code="TEST_CODE", message="test message")
        response = await api_exception_handler(request, exc)
        body = json.loads(response.body)
        assert body["code"] == "TEST_CODE"
        assert body["message"] == "test message"
