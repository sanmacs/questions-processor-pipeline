from typing import List, Optional
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Question Extractor API"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Security settings
    API_TOKEN: str = os.getenv("API_TOKEN", "your-api-token")
    
    # API keys and settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "api-key")
    
    # File handling
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024  # 20 MB

    # Prompts file path
    PROMPTS_FILE: str = "prompts/prompts.json"
    
    class Config:
        case_sensitive = True


settings = Settings()