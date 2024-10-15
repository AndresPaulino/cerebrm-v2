import os
from pydantic_settings import BaseSettings
from typing import List

print("Entering config.py")

class Settings(BaseSettings):
    PROJECT_NAME: str = "Algorithmic Trading Platform"
    PROJECT_VERSION: str = "1.0.0"
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    POLYGON_API_KEY: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

    @property
    def ALLOWED_ORIGINS_LIST(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

print("Defined Settings class")

try:
    settings = Settings(_env_file=os.path.join(os.getcwd(), '.env'))
    print("Created settings instance")
except Exception as e:
    print(f"Error loading settings: {str(e)}")
    raise

__all__ = ["settings"]
