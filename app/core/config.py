import os
from pydantic_settings import BaseSettings
from typing import List

print("Entering config.py")

class Settings(BaseSettings):
    PROJECT_NAME: str = "Algorithmic Trading Platform"
    PROJECT_VERSION: str = "1.0.0"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    POLYGON_API_KEY: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    REDIS_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

    @classmethod
    def parse_allowed_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

print("Defined Settings class")

try:
    settings = Settings(_env_file=os.path.join(os.getcwd(), '.env'))
    settings.ALLOWED_ORIGINS = Settings.parse_allowed_origins(settings.ALLOWED_ORIGINS)
    print("Created settings instance")
    print(f"Settings: {settings.dict()}")
except Exception as e:
    print(f"Error loading settings: {str(e)}")
    raise

print("Exiting config.py")

__all__ = ["settings"]