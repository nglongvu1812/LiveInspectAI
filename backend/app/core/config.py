from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    FRONTEND_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    SECRET_KEY: str = "dev-secret-key-32-characters-minimum-abc123"
    
    AGENT_ID: str = "agent-win-gtx1660ti"
    AGENT_TOKEN: str = "liveinspect-secret-agent-token-xyz-123"
    AGENT_HEARTBEAT_SECONDS: int = 15
    INFERENCE_TIMEOUT_SECONDS: int = 30
    MAX_INFERENCE_QUEUE: int = 5
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./liveinspect.db"
    SAVE_IMAGES: bool = False
    
    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.FRONTEND_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
