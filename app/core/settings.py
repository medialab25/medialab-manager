from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 4800
    DEBUG: bool = False
    
    # Application settings
    VERSION: str = "0.1.0"
    LOG_FILE: Path = Path("logs/app.log")
    PROJECT_NAME: str = "MediaVault Manager"
    DESCRIPTION: str = "A FastAPI application for managing media files."
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 