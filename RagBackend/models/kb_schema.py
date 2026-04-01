"""
知识库数据模型定义 - Pydantic v2 规范
提供严格的数据校验和类型检查
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime


class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求模型"""
    
    kb_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="知识库名称（不能为空，最多100字符）"
    )
    owner_id: Optional[str] = Field(
        None,
        max_length=100,
        description="所有者ID（可选）"
    )
    
    @field_validator('kb_name')
    @classmethod
    def validate_kb_name(cls, v: str) -> str:
        """
        验证知识库名称
        - 不能为空或仅空格
        - 不能包含路径分隔符（防止目录遍历）
        - 不能包含特殊字符
        """
        v = v.strip()
        
        if not v:
            raise ValueError("知识库名称不能为空")
        
        # 防止目录遍历
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError("知识库名称不能包含路径分隔符")
        
        # 防止特殊字符
        forbidden_chars = ['<', '>', ':', '"', '|', '?', '*', '\n', '\r']
        if any(c in v for c in forbidden_chars):
            raise ValueError(f"知识库名称包含非法字符: {forbidden_chars}")
        
        return v


class KnowledgeBaseMetadata(BaseModel):
    """知识库元数据模型"""
    
    id: str = Field(..., description="知识库唯一ID")
    title: str = Field(..., description="知识库标题")
    description: str = Field("", max_length=500, description="知识库描述")
    avatar: str = Field("", description="知识库头像URL")
    cover: str = Field("", description="知识库封面URL")
    created_time: str = Field(
        default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        description="创建时间"
    )
    owner_id: str = Field("", description="所有者ID")
    
    model_config = ConfigDict(populate_by_name=True)


class KnowledgeBaseConfig(BaseModel):
    """知识库处理配置模型"""
    
    embedding_model: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2",
        description="嵌入模型"
    )
    chunk_size: int = Field(
        1000,
        ge=100,
        le=4000,
        description="文档分块大小（字符数）"
    )
    chunk_overlap: int = Field(
        200,
        ge=0,
        le=1000,
        description="文档分块重叠（字符数）"
    )
    pdf_parser: str = Field("PyPDFLoader", description="PDF 解析器")
    docx_parser: str = Field("Docx2txtLoader", description="Word 解析器")
    excel_parser: str = Field("Unstructured Excel Loader", description="Excel 解析器")
    csv_parser: str = Field("CsvLoader", description="CSV 解析器")
    txt_parser: str = Field("TextLoader", description="纯文本解析器")
    segment_method: str = Field("General", description="分段方法")
    vector_dimension: int = Field(768, description="向量维度")
    similarity_threshold: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="相似度阈值"
    )
    convert_table_to_html: bool = Field(True, description="是否转换表格为HTML")
    preserve_layout: bool = Field(False, description="是否保留布局")
    remove_headers: bool = Field(True, description="是否移除页头页脚")
    
    @field_validator('chunk_overlap')
    @classmethod
    def validate_overlap(cls, v: int, info) -> int:
        """分块重叠不能大于分块大小"""
        if 'chunk_size' in info.data and v >= info.data['chunk_size']:
            raise ValueError("分块重叠不能大于等于分块大小")
        return v


class KnowledgeBaseKGConfig(BaseModel):
    """知识图谱配置模型"""
    
    extract_knowledge_graph: bool = Field(False, description="是否提取知识图谱")
    kg_method: str = Field("通用", description="知识图谱提取方法")
    selected_entity_types: List[str] = Field(
        ["PERSON", "ORGANIZATION", "LOCATION"],
        description="要提取的实体类型"
    )
    entity_normalization: bool = Field(True, description="是否进行实体标准化")
    community_report: bool = Field(False, description="是否生成社区报告")
    relation_extraction: bool = Field(True, description="是否进行关系抽取")


class KnowledgeBaseSchema(
    KnowledgeBaseMetadata,
    KnowledgeBaseConfig,
    KnowledgeBaseKGConfig
):
    """完整知识库schema（元数据 + 配置 + 知识图谱）"""
    pass


class KnowledgeBaseUpdateRequest(BaseModel):
    """更新知识库请求模型"""
    
    title: Optional[str] = Field(None, max_length=100, description="标题")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    avatar: Optional[str] = Field(None, description="头像URL")
    cover: Optional[str] = Field(None, description="封面URL")
    chunk_size: Optional[int] = Field(None, ge=100, le=4000, description="分块大小")
    chunk_overlap: Optional[int] = Field(None, ge=0, le=1000, description="分块重叠")
    embedding_model: Optional[str] = Field(None, description="嵌入模型")
    similarity_threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="相似度阈值"
    )


class KnowledgeBaseResponse(BaseModel):
    """知识库响应模型"""
    
    code: int = Field(..., description="响应代码")
    message: str = Field(..., description="响应消息")
    data: Optional[KnowledgeBaseSchema] = Field(None, description="响应数据")
    total: Optional[int] = Field(None, description="总数")


class KnowledgeBaseListResponse(BaseModel):
    """知识库列表响应模型"""
    
    code: int = Field(..., description="响应代码")
    message: str = Field(..., description="响应消息")
    data: List[KnowledgeBaseSchema] = Field(..., description="知识库列表")
    total: int = Field(..., description="总数量")
