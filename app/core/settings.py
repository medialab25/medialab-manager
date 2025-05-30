from pydantic_settings import BaseSettings
from pathlib import Path
import json
from typing import Dict, Any

class DatabaseSettings(BaseSettings):
    SQLITE_PATH: str = "data"

    @classmethod
    def from_config(cls):
        try:
            with open("config.json") as f:
                config = json.load(f)
                return cls(SQLITE_PATH=config["DATABASE"]["SQLITE_PATH"])
        except (FileNotFoundError, KeyError):
            return cls()

class Settings(BaseSettings):
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 4800
    DEBUG: bool = False
    
    # Application settings
    VERSION: str = "0.1.0"
    LOG_FILE: Path = Path("logs/app.log")
    PROJECT_NAME: str = "MediaLab Manager"
    DESCRIPTION: str = "A FastAPI application for managing media files."
    
    # Database settings
    DATABASE: DatabaseSettings = DatabaseSettings.from_config()
    
    # Task settings
    TASKS: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def from_config(cls):
        try:
            with open("config.json") as f:
                config = json.load(f)
                return cls(
                    DATABASE=DatabaseSettings.from_config(),
                    TASKS=config.get("TASKS", {})
                )
        except FileNotFoundError:
            return cls()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings.from_config() 