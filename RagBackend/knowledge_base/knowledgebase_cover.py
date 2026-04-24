"""
知识库封面图床

安全加固：
- KLB_id 经过路径遍历验证
- 文件类型白名单校验
- 文件大小限制
- 统一使用 logging 替代 print()
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

import aiofiles
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================================
# 常量与配置
# ============================================================================

UPLOAD_DIR = Path("local-KLB-files").resolve()
COVER_DIR = UPLOAD_DIR / "covers"
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
MAX_COVER_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

# 危险字符集（与 knowledgeBASE4CURD.py 保持一致）
_DANGEROUS_PATH_CHARS = {"..", "/", "\\", "\x00"}


def _validate_kb_id(raw_id: str) -> str:
    """验证知识库 ID，防止路径遍历攻击"""
    if not raw_id or not raw_id.strip():
        raise ValueError("知识库 ID 不能为空")
    cleaned = raw_id.strip()
    for char in _DANGEROUS_PATH_CHARS:
        if char in cleaned:
            raise ValueError(f"知识库 ID 包含非法字符")
    if len(cleaned) > 255:
        raise ValueError("知识库 ID 长度超过限制")
    return cleaned


def _safe_kb_path(kb_id: str) -> Path:
    """构建安全的知识库目录路径"""
    target = (UPLOAD_DIR / kb_id).resolve()
    try:
        target.relative_to(UPLOAD_DIR)
    except ValueError:
        raise HTTPException(status_code=400, detail="非法的知识库路径")
    return target


# ============================================================================
# API 端点
# ============================================================================


@router.post("/api/upload-cover")
async def upload_cover_image(image: UploadFile = File(...), KLB_id=Form(...)):
    """
    上传知识库封面图片

    安全：
    - KLB_id 经路径遍历验证
    - 文件扩展名白名单校验
    - 文件大小限制 5MB
    """
    # 验证 KLB_id
    try:
        safe_id = _validate_kb_id(KLB_id)
    except (ValueError, AttributeError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 验证文件名和扩展名
    if not image.filename:
        raise HTTPException(status_code=400, detail="缺少文件名")
    
    file_ext = Path(image.filename).suffix.lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"不支持的图片格式: {file_ext}，允许的格式: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}",
        )

    try:
        COVER_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"cover_{timestamp}_{uuid.uuid4().hex[:8]}{file_ext}"
        image_path = COVER_DIR / unique_filename

        # 读取并验证文件大小
        content = await image.read()
        if len(content) > MAX_COVER_IMAGE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"图片过大（{len(content) / 1024 / 1024:.1f}MB > 5MB）",
            )

        async with aiofiles.open(str(image_path), "wb") as f:
            await f.write(content)

        # 构建图片访问 URL
        image_url = f"/static/covers/{unique_filename}"

        # 更新知识库配置中的 cover 字段
        kb_dir = _safe_kb_path(safe_id)
        json_file_path = kb_dir / "knowledge_data.json"

        if not json_file_path.exists():
            raise HTTPException(
                status_code=404, detail=f"知识库 '{safe_id}' 配置文件不存在"
            )

        with open(json_file_path, "r", encoding="utf-8") as f:
            kb_data = json.load(f)

        # 动态获取请求根 URL（不硬编码 localhost）
        kb_data["cover"] = image_url  # 使用相对路径，前端自行拼接域名

        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(kb_data, f, ensure_ascii=False, indent=4)

        logger.info(f"[Cover] 封面上传成功: kb={safe_id}, file={unique_filename}")

        return {
            "success": True,
            "message": "封面图片上传成功",
            "imageUrl": image_url,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Cover] 封面图片上传失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"封面图片上传失败: {str(e)}")
