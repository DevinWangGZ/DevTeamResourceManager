"""应用配置管理"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import json


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_NAME: str = "DevTeam Manager API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # 数据库配置
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "devteam"
    POSTGRES_PASSWORD: str = "devteam123"
    POSTGRES_DB: str = "devteam_manager"
    DATABASE_URL: Optional[str] = None
    
    # SQLite配置（开发环境）
    SQLITE_DB: str = "devteam_manager.db"
    USE_SQLITE: bool = False
    
    @property
    def database_url(self) -> str:
        """构建数据库URL"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        if self.USE_SQLITE:
            return f"sqlite:///./{self.SQLITE_DB}"
        
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
        )
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60  # 30天
    
    # Redis配置（可选）
    REDIS_URL: Optional[str] = None
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> any:
            """解析环境变量"""
            if field_name == "BACKEND_CORS_ORIGINS":
                try:
                    return json.loads(raw_val)
                except json.JSONDecodeError:
                    return raw_val.split(",")
            return cls.json_schema_extra(field_name, raw_val)


settings = Settings()
