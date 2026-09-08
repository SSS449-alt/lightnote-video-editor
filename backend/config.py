"""
Centralized configuration management using pydantic-settings.
All environment variables are typed and validated here.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # API Keys
    ANTHROPIC_API_KEY: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Storage
    UPLOAD_DIR: str = "./uploads"
    OUTPUT_DIR: str = "./outputs"
    MAX_VIDEO_SIZE_MB: int = 100
    MAX_VIDEO_DURATION_SECONDS: int = 60
    
    # ML Models
    DEVICE: str = "cpu"  # 'cuda' for GPU
    GROUNDING_DINO_CONFIG: str = ""
    GROUNDING_DINO_CHECKPOINT: str = ""
    SAM2_CHECKPOINT: str = ""
    SAM2_CONFIG: str = "sam2_hiera_l.yaml"
    
    # App
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"


settings = Settings()