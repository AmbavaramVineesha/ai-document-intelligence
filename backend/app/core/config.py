import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Intelligent Document Intelligence & Extraction Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Persistence
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./document_intelligence.db")
    
    # Validation Limits
    MAX_FILE_SIZE_MB: int = 15
    MAX_PAGE_COUNT: int = 3
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "jpg", "jpeg", "png"]
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/jpg"
    ]
    
    # AI / LLM Keys (Optional)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OCR_SPACE_API_KEY: str = os.getenv("OCR_SPACE_API_KEY", "")
    
    # Financial tolerance percentage (e.g. 0.02 = 2% or 0.05 absolute)
    FINANCIAL_TOLERANCE_PERCENT: float = 0.02
    FINANCIAL_TOLERANCE_ABSOLUTE: float = 1.00
    
    class Config:
        case_sensitive = True

settings = Settings()
