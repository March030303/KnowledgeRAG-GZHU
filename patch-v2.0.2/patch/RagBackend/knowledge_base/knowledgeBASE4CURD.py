import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)
router = APIRouter()


"""
知识库管理，实现知识库的增删改查

安全加固：
- 所有 KLB_id/kbName 参数均经过路径遍历防护验证
- 使用 Path.resolve().relative_to() 确保路径不逃逸基础目录
- Pydantic 模型级输入校验（禁止 ../ / \\ 等字符）
"""

# ============================================================================
# 常量与安全工具函数
# ============================================================================

KB_BASE_DIR = Path("local-KLB-files").resolve()

# 危险字符集：路径遍历 + 空字节 + 控制符
_DANGEROUS_PATH_CHARS = {"..", "/", "\\", "\x00"}


def _validate_kb_id(raw_id: str) -> str:
    """
    验证并清洗知识库 ID，防止路径遍历攻击。

    规则：
    1. 不允许包含 .. / \\ \\x00
    2. 长度限制 1-255 字符
    3. 去除首尾空白

    Args:
        raw_id: 原始知识库 ID

    Returns:
        清洗后的安全 ID

    Raises:
        ValueError: 包含非法字符时抛出
    """
    if not raw_id or not raw_id.strip():
        raise ValueError("知识库 ID 不能为空")

    cleaned = raw_id.strip()

    for char in _DANGEROUS_PATH_CHARS:
        if char in cleaned:
            raise ValueError(f"知识库 ID 包含非法字符: {repr(char)}")

    if len(cleaned) > 255:
        raise ValueError("知识库 ID 长度超过限制 (255)")

    return cleaned


def _safe_kb_path(kb_id: str) -> Path:
    """
    构建安全的知识库目录路径，确保不会逃逸 KB_BASE_DIR。

    Args:
        kb_id: 已通过 _validate_kb_id 验证的 ID

    Returns:
        安全的知识库目录绝对路径

    Raises:
        HTTPException: 路径解析后仍逃逸基础目录时抛出 (400)
    """
    target = (KB_BASE_DIR / kb_id).resolve()
    try:
        target.relative_to(KB_BASE_DIR)
    except ValueError:
        raise HTTPException(status_code=400, detail="非法的知识库路径")
    return target


# ============================================================================
# Pydantic 数据模型（带完整校验）
# ============================================================================


class KnowledgeItem(BaseModel):
    """知识库项目响应模型"""

    id: str = Field(..., description="知识库唯一标识")
    title: str = Field(..., min_length=1, max_length=255, description="知识库名称")
    avatar: str = Field(default="", description="头像 URL")
    description: str = Field(default="", max_length=2000, description="描述")
    createdTime: str = Field(..., description="创建时间")
    cover: str = Field(default="", description="封面 URL")


class CreateKBRequest(BaseModel):
    """创建知识库请求模型"""

    kbName: str = Field(..., min_length=1, max_length=255, description="知识库名称")

    @validator("kbName")
    def validate_kb_name(cls, v: str) -> str:
        """验证知识库名称不包含路径遍历字符"""
        return _validate_kb_id(v)


class UpdateKBConfigRequest(BaseModel):
    """更新知识库配置请求模型"""

    name: Optional[str] = Field(None, max_length=255, description="名称")
    description: Optional[str] = Field(None, max_length=2000, description="描述")
    embedding_model: Optional[str] = Field(None, max_length=255)
    chunk_size: Optional[int] = Field(None, gt=0, le=100000)
    chunk_overlap: Optional[int] = Field(None, ge=0, le=50000)
    pdfParser: Optional[str] = Field(None)
    docxParser: Optional[str] = Field(None)
    excelParser: Optional[str] = Field(None)
    csvParser: Optional[str] = Field(None)
    txtParser: Optional[str] = Field(None)
    segmentMethod: Optional[str] = Field(None)


# ============================================================================
# 数据访问层
# ============================================================================


def knowledge_base_data() -> List[dict]:
    """
    知识库数据获取（从本地文件系统读取所有知识库元数据）

    安全：仅读取 KB_BASE_DIR 下已存在的目录，不接受外部输入构造路径

    Returns:
        按创建时间排序的知识库列表
    """
    knowledge_bases = []

    if not KB_BASE_DIR.exists():
        logger.warning(f"[KB] 基础目录不存在: {KB_BASE_DIR}")
        return knowledge_bases

    for kb_name in os.listdir(KB_BASE_DIR):
        kb_dir = KB_BASE_DIR / kb_name
        # 跳过非目录项（如文件、符号链接）
        if not kb_dir.is_dir():
            continue
        json_file_path = kb_dir / "knowledge_data.json"

        if json_file_path.exists():
            try:
                with open(json_file_path, "r", encoding="utf-8") as f:
                    kb_data = json.load(f)
                    knowledge_bases.append(kb_data)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"[KB] 读取 {json_file_path} 失败: {e}")

    # 按 createdTime 降序排列（增加容错：跳过格式异常的条目）
    try:
        knowledge_bases.sort(
            key=lambda x: datetime.strptime(x["createdTime"], "%Y-%m-%d %H:%M:%S"),
            reverse=True,
        )
    except (ValueError, KeyError) as e:
        logger.warning(f"[KB] 知识库排序失败，使用原始顺序: {e}")

    logger.debug(f"[KB] 加载知识库列表，共 {len(knowledge_bases)} 个")
    return knowledge_bases


@router.post("/api/create-knowledgebase/")
async def create_knowledgebase(
    kbName: str = Form(...), owner_id: Optional[str] = Form(None)
):
    """
    创建知识库（owner_id 可选，传入则绑定到该用户）

    安全：kbName 经过 _validate_kb_id 验证，防止路径遍历
    """
    # 输入验证（复用 Pydantic 验证逻辑）
    try:
        safe_kb_name = _validate_kb_id(kbName)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    kb_dir = _safe_kb_path(safe_kb_name)

    # 确保基础目录存在
    KB_BASE_DIR.mkdir(parents=True, exist_ok=True)

    if kb_dir.exists():
        raise HTTPException(status_code=400, detail="Knowledge base already exists.")

    kb_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "id": safe_kb_name,
        "title": safe_kb_name,
        "avatar": "https://avatars.githubusercontent.com/u/145737758?v=4",
        "description": "新建知识库",
        "createdTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cover": (
            "https://picx.zhimg.com/80/v2-381cc3f4ba85f62cdc483136e5fa4f47_"
            "720w.webp?source=d16d100b"
        ),
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "pdfParser": "PyPDFLoader",
        "docxParser": "Docx2txtLoader",
        "excelParser": "Unstructured Excel Loader",
        "csvParser": "CsvLoader",
        "txtParser": "TextLoader",
        "segmentMethod": "General",
        "name": safe_kb_name,
        "vector_dimension": 768,
        "similarity_threshold": 0.7,
        "convert_table_to_html": True,
        "preserve_layout": False,
        "remove_headers": True,
        "extract_knowledge_graph": False,
        "kg_method": "通用",
        "selected_entity_types": ["PERSON", "ORGANIZATION", "LOCATION"],
        "entity_normalization": True,
        "community_report": False,
        "relation_extraction": True,
        "owner_id": owner_id or "",
    }

    json_file_path = kb_dir / "knowledge_data.json"
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    logger.info(f"[KB] 知识库创建成功: {safe_kb_name}, owner={owner_id or 'none'}")

    return JSONResponse(
        content={"message": "Knowledge base created successfully."}, status_code=200
    )


@router.delete("/api/delete-knowledgebase/{KLB_id}")
async def delete_knowledgebase(KLB_id: str):
    """
    删除知识库
    根据知识库ID删除对应的文件夹及其内容

    安全：KLB_id 经过路径遍历验证
    """
    try:
        safe_id = _validate_kb_id(KLB_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        kb_dir = _safe_kb_path(safe_id)

        if not kb_dir.exists():
            raise HTTPException(status_code=404, detail=f"知识库 '{safe_id}' 不存在")

        import shutil

        shutil.rmtree(kb_dir)

        logger.info(f"[KB] 知识库已删除: {safe_id}")

        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": f"知识库 '{safe_id}' 已成功删除",
                "deletedAt": datetime.now().isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[KB] 删除知识库失败: {safe_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除知识库失败: {str(e)}")


@router.post("/api/update-knowledgebase-config/{KLB_id}")
async def update_knowledgebase_config(KLB_id: str, request: Request):
    """
    更新知识库配置
    接收知识库ID和配置数据，更新对应知识库的配置信息

    安全：KLB_id 经过路径遍历验证
    """
    # 验证 KLB_id
    try:
        safe_id = _validate_kb_id(KLB_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        body = await request.json()
        logger.info(f"[KB] 接收到更新请求: KLB_id={safe_id}")

        name = body.get("name")
        description = body.get("description")
        embedding_model = body.get("embedding_model")
        chunk_size = body.get("chunk_size")
        chunk_overlap = body.get("chunk_overlap")
        pdfParser = body.get("pdfParser")
        docxParser = body.get("docxParser")
        excelParser = body.get("excelParser")
        csvParser = body.get("csvParser")
        txtParser = body.get("txtParser")
        segmentMethod = body.get("segmentMethod")

        # 使用安全路径
        kb_dir = _safe_kb_path(safe_id)
        json_file_path = kb_dir / "knowledge_data.json"

        if not kb_dir.exists():
            raise HTTPException(status_code=404, detail=f"知识库 '{safe_id}' 不存在")

        with open(json_file_path, "r", encoding="utf-8") as f:
            kb_data = json.load(f)

        # 逐字段安全更新（只接受非 None 值）
        if name is not None:
            kb_data["title"] = str(name)[:255]
        if description is not None:
            kb_data["description"] = str(description)[:2000]
        if embedding_model is not None:
            kb_data["embedding_model"] = str(embedding_model)
        if chunk_size is not None:
            kb_data["chunk_size"] = int(chunk_size)
        if chunk_overlap is not None:
            kb_data["chunk_overlap"] = int(chunk_overlap)
        if pdfParser is not None:
            kb_data["pdfParser"] = str(pdfParser)
        if docxParser is not None:
            kb_data["docxParser"] = str(docxParser)
        if excelParser is not None:
            kb_data["excelParser"] = str(excelParser)
        if csvParser is not None:
            kb_data["csvParser"] = str(csvParser)
        if txtParser is not None:
            kb_data["txtParser"] = str(txtParser)
        if segmentMethod is not None:
            kb_data["segmentMethod"] = str(segmentMethod)

        # 批量写入其他合法字段（白名单模式，防止注入非法键）
        _SAFE_CONFIG_KEYS = {
            "embedding_model", "chunk_size", "chunk_overlap",
            "pdfParser", "docxParser", "excelParser", "csvParser",
            "txtParser", "segmentMethod", "name", "description",
            "vector_dimension", "similarity_threshold",
            "convert_table_to_html", "preserve_layout", "remove_headers",
            "extract_knowledge_graph", "kg_method",
            "selected_entity_types", "entity_normalization",
            "community_report", "relation_extraction",
        }
        for key, value in body.items():
            if key in _SAFE_CONFIG_KEYS and value is not None:
                kb_data[key] = value

        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(kb_data, f, ensure_ascii=False, indent=4)

        logger.info(f"[KB] 知识库配置已更新: {safe_id}")

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "知识库配置已更新", "data": kb_data},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[KB] 更新知识库配置失败: {safe_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新知识库配置失败: {str(e)}")


@router.get("/api/get-knowledge-item/")
async def get_knowledge_items(user_id: Optional[str] = None):
    """
    获取知识库项目列表
    - user_id 为空：返回所有知识库（全局列表，用于 Chat 等场景）
    - user_id 非空：只返回该用户创建的知识库（用于广场发布选择等场景）

    安全：数据来自 knowledge_base_data()，该函数仅读取本地固定目录
    """
    try:
        data = knowledge_base_data()

        # 按 owner_id 过滤
        if user_id:
            safe_user_id = user_id.strip()[:255]
            data = [
                kb
                for kb in data
                if kb.get("owner_id", "") in (safe_user_id, "")
            ]

        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "获取知识库数据成功",
                "data": data,
                "total": len(data),
            },
        )

    except Exception as e:
        logger.error(f"[KB] 获取知识库数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取知识库数据失败: {str(e)}")


@router.get("/api/list-knowledge-bases/")
async def list_knowledge_bases_alias(user_id: Optional[str] = None):
    """
    /api/get-knowledge-item/ 的别名接口，返回格式更简洁（直接 list）
    - user_id 非空：只返回该用户的知识库（owner_id 匹配 或 owner_id 为空的旧数据）
    """
    try:
        data = knowledge_base_data()

        if user_id:
            safe_user_id = user_id.strip()[:255]
            data = [
                kb
                for kb in data
                if kb.get("owner_id", "") in (safe_user_id, "")
            ]

        return JSONResponse(status_code=200, content=data)

    except Exception as e:
        logger.error(f"[KB] 获取知识库列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取知识库列表失败: {str(e)}")


@router.get("/api/get-knowledge-item/{item_id}")
async def get_knowledge_item_by_id(item_id: str):
    """
    根据ID获取单个知识库项目

    安全：item_id 仅用于内存中匹配（不构造文件路径），无路径遍历风险
    """
    try:
        data = knowledge_base_data()
        item = next((item for item in data if item["id"] == item_id), None)

        if not item:
            raise HTTPException(
                status_code=404, detail=f"未找到ID为 {item_id} 的知识库项目"
            )

        return JSONResponse(
            status_code=200,
            content={"code": 200, "message": "获取知识库项目成功", "data": item},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[KB] 获取知识库项目失败: item_id={item_id}, error={e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取知识库项目失败: {str(e)}")
