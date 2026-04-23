"""
应用配置管理
"""
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用设置"""
    
    # 应用配置
    APP_NAME: str = "多Agent图书管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./library.db"
    
    # Agent配置
    MAX_CONCURRENT_AGENTS: int = 5
    AGENT_TIMEOUT: int = 30  # 秒
    
    # 借阅规则
    MAX_BORROW_DAYS: int = 30
    MAX_BORROW_COUNT: int = 10
    FINE_PER_DAY: float = 0.5  # 每天罚款金额
    
    # 推荐配置
    RECOMMENDATION_COUNT: int = 10
    SIMILARITY_THRESHOLD: float = 0.3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 全局设置实例
settings = Settings()
