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
    # 数据库类型: postgresql, mysql, sqlite
    DATABASE_TYPE: str = "mysql"  # 默认使用MySQL
    
    # PostgreSQL配置
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "devteam"
    POSTGRES_PASSWORD: str = "devteam123"
    POSTGRES_DB: str = "devteam_manager"
    POSTGRES_PORT: int = 5432
    
    # MySQL配置
    MYSQL_SERVER: str = "10.254.68.77"
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "123456"
    MYSQL_DB: str = "devteam_manager"
    MYSQL_PORT: int = 3306
    
    # 直接指定数据库URL（优先级最高）
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
        
        if self.DATABASE_TYPE == "mysql":
            return (
                f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
                f"@{self.MYSQL_SERVER}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
                f"?charset=utf8mb4&use_unicode=1"
            )
        elif self.DATABASE_TYPE == "postgresql":
            return (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        else:
            # 默认使用SQLite
            return f"sqlite:///./{self.SQLITE_DB}"
    
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
