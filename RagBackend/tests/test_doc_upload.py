"""
测试模块：文档上传（doc_upload.py）

覆盖功能：
- 文件类型验证
- 文件大小限制
- 分块上传
- 分块合并
- 文本分块计算
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException

from document_processing.doc_upload import (
    validate_file,
    get_file_type,
    get_file_hash,
    calculate_chunks,
    UploadChunkRequest,
    UploadCompleteRequest,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    KB_CHUNK_SIZE,
)


# 测试：文件验证
class TestFileValidation:
    """文件验证功能测试"""

    def test_get_file_type_pdf(self):
        """测试获取 PDF 文件类型"""
        assert get_file_type("document.pdf") == ".pdf"

    def test_get_file_type_uppercase(self):
        """测试大写扩展名转小写"""
        assert get_file_type("document.PDF") == ".pdf"

    def test_get_file_type_word(self):
        """测试 Word 文件"""
        assert get_file_type("report.docx") == ".docx"

    def test_validate_file_allowed_extension(self):
        """测试允许的文件类型"""
        content = b"Test PDF content"
        is_valid, msg = validate_file("test.pdf", content)
        assert is_valid is True
        assert msg == "验证通过"

    def test_validate_file_disallowed_extension(self):
        """测试不允许的文件类型"""
        content = b"Test content"
        is_valid, msg = validate_file("test.exe", content)
        assert is_valid is False
        assert "不支持的文件类型" in msg

    def test_validate_file_size_limit(self):
        """测试文件大小超过限制"""
        large_content = b"x" * (MAX_FILE_SIZE + 1)
        is_valid, msg = validate_file("test.txt", large_content)
        assert is_valid is False
        assert "文件大小超过限制" in msg


# 测试：哈希计算
class TestHashCalculation:
    """文件哈希计算测试"""

    def test_get_file_hash_consistency(self):
        """测试哈希值一致性"""
        content = b"Test content for hashing"
        hash1 = get_file_hash(content)
        hash2 = get_file_hash(content)
        assert hash1 == hash2

    def test_get_file_hash_different_content(self):
        """测试不同内容产生不同哈希"""
        hash1 = get_file_hash(b"Content A")
        hash2 = get_file_hash(b"Content B")
        assert hash1 != hash2

    def test_get_file_hash_length(self):
        """测试 SHA256 哈希长度"""
        hash_value = get_file_hash(b"Test")
        assert len(hash_value) == 64


# 测试：分块计算
class TestChunkCalculation:
    """文本分块计算测试"""

    def test_calculate_chunks_by_paragraph(self):
        """测试按段落分块"""
        content = b"Paragraph 1\\n\\nParagraph 2\\n\\nParagraph 3"
        chunks = calculate_chunks(content, "按段落")
        assert chunks == 3

    def test_calculate_chunks_empty_content(self):
        """测试空内容"""
        chunks = calculate_chunks(b"", "按段落")
        assert chunks == 1


# 测试：Pydantic 模型验证
class TestPydanticModels:
    """Pydantic 模型验证测试"""

    def test_upload_chunk_request_valid(self):
        """测试合法的分块上传请求"""
        req = UploadChunkRequest(
            fileHash="abc123def456",
            chunkIndex=0,
            totalChunks=5,
            fileName="document.pdf",
            KLB_id="kb_001"
        )
        assert req.fileName == "document.pdf"
        assert req.KLB_id == "kb_001"

    def test_upload_chunk_request_filename_with_path_separator(self):
        """测试文件名包含路径分隔符(应拒绝)"""
        with pytest.raises(ValueError):
            UploadChunkRequest(
                fileHash="abc123",
                chunkIndex=0,
                totalChunks=1,
                fileName="../../../etc/passwd",
                KLB_id="kb_001"
            )

    def test_upload_chunk_request_kb_id_with_parent_traversal(self):
        """测试知识库 ID 包含 .. 字符(应拒绝)"""
        with pytest.raises(ValueError):
            UploadChunkRequest(
                fileHash="abc123",
                chunkIndex=0,
                totalChunks=1,
                fileName="doc.pdf",
                KLB_id="../../../etc"
            )


# 测试：文件格式支持
class TestAllowedExtensions:
    """允许的文件格式测试"""

    def test_allowed_extensions_coverage(self):
        """验证所有承诺的文件格式都被支持"""
        required_formats = {
            ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv",
            ".txt", ".md", ".rtf",
            ".png", ".jpg", ".jpeg", ".gif", ".bmp"
        }

        for fmt in required_formats:
            assert fmt in ALLOWED_EXTENSIONS, f"缺少对 {fmt} 的支持"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
