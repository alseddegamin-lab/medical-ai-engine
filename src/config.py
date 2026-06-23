"""
Configuration management for Medical AI Engine
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    claude_api_key: Optional[str] = os.getenv("CLAUDE_API_KEY", None)
    
    # DeepSeek API
    deepseek_api_url: str = "https://api.deepseek.com/v1/chat/completions"
    deepseek_model: str = "deepseek-chat"
    deepseek_temperature: float = 0.3
    deepseek_max_tokens: int = 4000
    
    # Database
    database_url: str = "sqlite:///./medical_questions.db"
    database_path: str = "./medical_questions.db"
    
    # OCR Settings
    ocr_engine: str = "paddleocr"  # paddleocr, easyocr
    ocr_language: str = "en"  # en, ar, en+ar
    ocr_use_gpu: bool = False
    
    # PDF Processing
    pdf_dpi: int = 300
    pdf_max_pages: int = 500
    
    # File paths
    data_dir: Path = Path("./data")
    pdf_dir: Path = Path("./data/pdfs")
    image_dir: Path = Path("./data/images")
    output_dir: Path = Path("./data/output")
    
    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    server_reload: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "medical_ai_engine.log"
    
    # Processing
    batch_size: int = 10
    max_workers: int = 4
    timeout_seconds: int = 300
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **data):
        super().__init__(**data)
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings()
