"""
知识库 CRUD 操作 - 规范化实现
遵循 PEP8、类型注解、异常处理、日志记录规范
"""

import logging
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from models.kb_schema import (
    KnowledgeBaseCreate,
    KnowledgeBaseSchema,
    KnowledgeBaseUpdateRequest,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
)
from config.settings import config
from exception.exceptions import (
    KnowledgeBaseNotFound,
    KnowledgeBaseAlreadyExists,
    APIException,
)

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Knowledge Base Management"])

KB_BASE_DIR = Path(config.KB_STORAGE_PATH)


def _ensure_kb_base_dir() -> Path:
    """
    确保知识库根目录存在
    
    Returns:
        Path: 知识库根目录路径
    """
    KB_BASE_DIR.mkdir(parents=True, exist_ok=True)
    return KB_BASE_DIR


def _get_kb_meta_file(kb_id: str) -> Path:
    """
    获取知识库元数据文件路径
    
    Args:
        kb_id: 知识库ID
    
    Returns:
        Path: 元数据文件路径
    """
    return KB_BASE_DIR / kb_id / "knowledge_data.json"


def _load_kb_meta(kb_id: str) -> Optional[dict]:
    """
    加载单个知识库元数据
    
    Args:
        kb_id: 知识库ID
    
    Returns:
        Optional[dict]: 元数据字典，如果文件不存在或损坏则返回 None
    
    Raises:
        无异常抛出，所有异常在内部处理并记录日志
    """
    try:
        meta_path = _get_kb_meta_file(kb_id)
        
        if not meta_path.exists():
            logger.debug(f"知识库 {kb_id} 元数据文件不存在: {meta_path}")
            return None
        
        with open(meta_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.debug(f"加载知识库 {kb_id} 元数据成功")
            return data
    
    except json.JSONDecodeError as e:
        logger.error(f"知识库 {kb_id} 元数据文件格式错误: {e}")
        return None
    except Exception as e:
        logger.error(f"加载知识库 {kb_id} 元数据异常: {type(e).__name__}: {e}")
        return None


def _load_all_kb_meta() -> List[dict]:
    """
    加载所有知识库元数据
    
    Returns:
        List[dict]: 知识库元数据列表（按创建时间降序排列）
    """
    _ensure_kb_base_dir()
    
    knowledge_bases = []
    
    try:
        # 扫描知识库目录
        for kb_dir in KB_BASE_DIR.iterdir():
            if not kb_dir.is_dir():
                continue
            
            kb_data = _load_kb_meta(kb_dir.name)
            if kb_data:
                knowledge_bases.append(kb_data)
        
        logger.info(f"扫描知识库目录完成，共发现 {len(knowledge_bases)} 个知识库")
    
    except PermissionError as e:
        logger.error(f"知识库目录权限不足: {e}")
    except Exception as e:
        logger.error(f"扫描知识库目录异常: {type(e).__name__}: {e}")
    
    # 按创建时间排序（降序）
    try:
        knowledge_bases.sort(
            key=lambda x: datetime.strptime(
                x.get('created_time', ''),
                '%Y-%m-%d %H:%M:%S'
            ),
            reverse=True
        )
        logger.debug(f"知识库排序成功")
    except (ValueError, KeyError) as e:
        logger.warning(f"知识库排序失败，使用原始顺序: {e}")
    
    return knowledge_bases


def _save_kb_meta(kb_id: str, kb_data: dict) -> bool:
    """
    保存知识库元数据
    
    Args:
        kb_id: 知识库ID
        kb_data: 元数据字典
    
    Returns:
        bool: 是否保存成功
    """
    try:
        kb_dir = KB_BASE_DIR / kb_id
        kb_dir.mkdir(parents=True, exist_ok=True)
        
        meta_path = kb_dir / "knowledge_data.json"
        
        # 使用临时文件 + 原子操作确保数据完整性
        temp_path = meta_path.with_suffix('.json.tmp')
        
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(kb_data, f, ensure_ascii=False, indent=4)
        
        # 原子替换
        temp_path.replace(meta_path)
        
        logger.info(f"保存知识库 {kb_id} 元数据成功")
        return True
    
    except Exception as e:
        logger.error(f"保存知识库 {kb_id} 元数据失败: {type(e).__name__}: {e}")
        return False


# ============ API 端点 ============


@router.post("/create-knowledgebase/", response_model=KnowledgeBaseResponse)
async def create_knowledgebase(
    request: KnowledgeBaseCreate
) -> KnowledgeBaseResponse:
    """
    创建新知识库
    
    Args:
        request: 创建请求（包含 kb_name, owner_id）
    
    Returns:
        KnowledgeBaseResponse: 创建结果
    
    Raises:
        HTTPException: 400 知识库已存在，500 创建失败
    """
    try:
        kb_name = request.kb_name
        owner_id = request.owner_id or ""
        
        _ensure_kb_base_dir()
        
        # 检查知识库是否已存在
        if (_get_kb_meta_file(kb_name)).exists():
            logger.warning(f"知识库 {kb_name} 已存在，创建失败")
            raise KnowledgeBaseAlreadyExists(kb_name)
        
        # 构建元数据
        kb_data = KnowledgeBaseSchema(
            id=kb_name,
            title=kb_name,
            description="新建知识库",
            avatar="https://avatars.githubusercontent.com/u/145737758?v=4",
            cover="https://picx.zhimg.com/80/v2-381cc3f4ba85f62cdc483136e5fa4f47_720w.webp",
            owner_id=owner_id,
        ).model_dump(exclude_unset=False)
        
        # 保存元数据
        if not _save_kb_meta(kb_name, kb_data):
            raise Exception("保存元数据失败")
        
        logger.info(f"创建知识库成功: {kb_name} (owner={owner_id})")
        
        return KnowledgeBaseResponse(
            code="000000",
            message="知识库创建成功",
            data=kb_data
        )
    
    except KnowledgeBaseAlreadyExists as e:
        logger.warning(f"知识库创建异常: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except APIException as e:
        logger.error(f"知识库创建异常: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"创建知识库异常: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建知识库失败，请稍后重试"
        )


@router.delete("/delete-knowledgebase/{kb_id}")
async def delete_knowledgebase(kb_id: str) -> JSONResponse:
    """
    删除知识库
    
    Args:
        kb_id: 知识库ID
    
    Returns:
        JSONResponse: 删除结果
    
    Raises:
        HTTPException: 404 知识库不存在，500 删除失败
    """
    try:
        kb_dir = KB_BASE_DIR / kb_id
        
        if not kb_dir.exists():
            logger.warning(f"知识库 {kb_id} 不存在，删除失败")
            raise KnowledgeBaseNotFound(kb_id)
        
        # 递归删除知识库目录
        shutil.rmtree(kb_dir)
        
        logger.info(f"删除知识库成功: {kb_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "code": "000000",
                "message": f"知识库 '{kb_id}' 已成功删除",
                "data": {
                    "deleted_at": datetime.now().isoformat()
                }
            }
        )
    
    except KnowledgeBaseNotFound as e:
        logger.warning(f"知识库删除异常: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except PermissionError as e:
        logger.error(f"删除知识库权限不足: {kb_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限删除该知识库"
        )
    except Exception as e:
        logger.error(f"删除知识库异常: {kb_id}: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除知识库失败，请稍后重试"
        )


@router.get("/get-knowledge-item/", response_model=KnowledgeBaseListResponse)
async def get_knowledge_items(
    user_id: Optional[str] = None
) -> KnowledgeBaseListResponse:
    """
    获取知识库列表
    
    Args:
        user_id: 用户ID（可选，为空则返回全部）
    
    Returns:
        KnowledgeBaseListResponse: 知识库列表
    """
    try:
        data = _load_all_kb_meta()
        
        # 过滤用户知识库
        if user_id:
            data = [
                kb for kb in data
                if kb.get("owner_id", "") in (user_id, "")
            ]
            logger.info(f"获取用户 {user_id} 的知识库列表，共 {len(data)} 个")
        else:
            logger.info(f"获取全部知识库列表，共 {len(data)} 个")
        
        return KnowledgeBaseListResponse(
            code="000000",
            message="获取知识库列表成功",
            data=data,
            total=len(data)
        )
    
    except Exception as e:
        logger.error(f"获取知识库列表异常: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取知识库列表失败"
        )


@router.get("/get-knowledge-item/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_item_by_id(kb_id: str) -> KnowledgeBaseResponse:
    """
    根据ID获取单个知识库
    
    Args:
        kb_id: 知识库ID
    
    Returns:
        KnowledgeBaseResponse: 知识库详情
    
    Raises:
        HTTPException: 404 知识库不存在
    """
    try:
        kb_data = _load_kb_meta(kb_id)
        
        if not kb_data:
            logger.warning(f"知识库 {kb_id} 不存在")
            raise KnowledgeBaseNotFound(kb_id)
        
        logger.info(f"获取知识库 {kb_id} 成功")
        
        return KnowledgeBaseResponse(
            code="000000",
            message="获取知识库成功",
            data=kb_data
        )
    
    except KnowledgeBaseNotFound as e:
        logger.warning(f"知识库获取异常: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"获取知识库 {kb_id} 异常: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取知识库失败"
        )


@router.post("/update-knowledgebase-config/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledgebase_config(
    kb_id: str,
    request: KnowledgeBaseUpdateRequest
) -> KnowledgeBaseResponse:
    """
    更新知识库配置
    
    Args:
        kb_id: 知识库ID
        request: 更新请求
    
    Returns:
        KnowledgeBaseResponse: 更新后的知识库数据
    
    Raises:
        HTTPException: 404 知识库不存在，500 更新失败
    """
    try:
        kb_data = _load_kb_meta(kb_id)
        
        if not kb_data:
            logger.warning(f"知识库 {kb_id} 不存在")
            raise KnowledgeBaseNotFound(kb_id)
        
        # 更新字段
        update_data = request.model_dump(exclude_unset=True)
        kb_data.update(update_data)
        
        # 保存更新
        if not _save_kb_meta(kb_id, kb_data):
            raise Exception("保存更新失败")
        
        logger.info(f"更新知识库 {kb_id} 成功: {list(update_data.keys())}")
        
        return KnowledgeBaseResponse(
            code="000000",
            message="知识库配置已更新",
            data=kb_data
        )
    
    except KnowledgeBaseNotFound as e:
        logger.warning(f"知识库更新异常: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"更新知识库 {kb_id} 异常: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新知识库失败"
        )


@router.get("/list-knowledge-bases/")
async def list_knowledge_bases_alias(
    user_id: Optional[str] = None
) -> List[dict]:
    """
    /api/get-knowledge-item/ 的别名接口
    返回格式更简洁（直接 list）
    """
    try:
        data = _load_all_kb_meta()
        
        if user_id:
            data = [
                kb for kb in data
                if kb.get("owner_id", "") in (user_id, "")
            ]
        
        logger.info(f"获取知识库列表别名接口成功，返回 {len(data)} 个")
        return data
    
    except Exception as e:
        logger.error(f"获取知识库列表别名接口异常: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取知识库列表失败"
        )
