"""
统一配置管理文件 - 环境切换 + 集中化配置
兼容 Python 3.8+，使用环境变量覆盖
"""

import os
from enum import Enum
from pathlib import Path

# 环境模式
ENV_MODE = os.getenv("ENV_MODE", "development").lower()


def _get_env_value(*names: str, default: str = "") -> str:
    """按顺序返回第一个非空环境变量值。"""
    for name in names:
        value = os.getenv(name)
        if value not in (None, ""):
            return value
    return default


class EnvironmentMode(str, Enum):
    """运行环境枚举"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class BaseConfig:
    """基础配置"""

    # 项目路径
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    KB_STORAGE_PATH = os.getenv(
        "KB_STORAGE_PATH", str(PROJECT_ROOT / "RagBackend" / "local-KLB-files")
    )

    # 文件上传限制
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 100 * 1024))  # 100KB

    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = os.getenv("LOG_DIR", str(PROJECT_ROOT / "logs"))
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 数据库配置
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "rag_user_db")

    # JWT 配置
    JWT_SECRET_KEY = _get_env_value(
        "JWT_SECRET", "JWT_SECRET_KEY", default="your-secret-key-change-in-production"
    )

    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = int(
        _get_env_value("JWT_EXPIRATION_HOURS", "JWT_EXPIRE_HOURS", default="24")
    )

    # Ollama 配置
    OLLAMA_BASE_URL = _get_env_value(
        "OLLAMA_BASE_URL", default="http://localhost:11434"
    )
    OLLAMA_TIMEOUT = int(_get_env_value("OLLAMA_TIMEOUT", default="300"))
    DEFAULT_LLM_MODEL = _get_env_value(
        "MODEL", "DEFAULT_LLM_MODEL", default="deepseek-chat"
    )

    # 向量模型配置
    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", 384))

    # Redis 配置（可选）
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"

    # 知识库默认参数
    KB_DEFAULT_CHUNK_SIZE = int(os.getenv("KB_DEFAULT_CHUNK_SIZE", 1000))
    KB_DEFAULT_CHUNK_OVERLAP = int(os.getenv("KB_DEFAULT_CHUNK_OVERLAP", 200))
    KB_DEFAULT_SIMILARITY_THRESHOLD = float(
        os.getenv("KB_DEFAULT_SIMILARITY_THRESHOLD", 0.7)
    )

    # CORS 配置
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # 调试模式
    DEBUG = ENV_MODE == EnvironmentMode.DEVELOPMENT


class DevelopmentConfig(BaseConfig):
    """开发环境配置"""

    DEBUG = True
    LOG_LEVEL = "DEBUG"
    TESTING = False


class TestingConfig(BaseConfig):
    """测试环境配置"""

    DEBUG = False
    LOG_LEVEL = "DEBUG"
    TESTING = True
    KB_STORAGE_PATH = str(BaseConfig.PROJECT_ROOT / "tests" / "fixtures" / "kb")
    OLLAMA_TIMEOUT = 60


class ProductionConfig(BaseConfig):
    """生产环境配置"""

    DEBUG = False
    LOG_LEVEL = "WARNING"
    TESTING = False
    # 生产环境需要显式设置敏感配置
    _jwt_secret = _get_env_value("JWT_SECRET", "JWT_SECRET_KEY", default="")
    if not _jwt_secret or _jwt_secret == "your-secret-key-change-in-production":
        raise ValueError(
            "⚠️ 生产环境必须设置 JWT_SECRET（兼容旧名 JWT_SECRET_KEY）环境变量"
        )


# 配置工厂函数
def get_config() -> BaseConfig:
    """根据环境变量返回对应配置"""
    mode = EnvironmentMode(ENV_MODE)

    if mode == EnvironmentMode.DEVELOPMENT:
        return DevelopmentConfig()
    elif mode == EnvironmentMode.TESTING:
        return TestingConfig()
    elif mode == EnvironmentMode.PRODUCTION:
        return ProductionConfig()
    else:
        return DevelopmentConfig()


# 全局配置对象
config: BaseConfig = get_config()

# 创建必要的目录
Path(config.LOG_DIR).mkdir(parents=True, exist_ok=True)
Path(config.KB_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
