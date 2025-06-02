from pydantic_settings import BaseSettings
from pathlib import Path
import json
from typing import Dict, Any
import os

class DatabaseSettings(BaseSettings):
    MAIN_DB_PATH: str = "data/main.db"
    MEDIA_DB_PATH: str = "data/media.db"

    @classmethod
    def from_config(cls):
        try:
            with open("config.json") as f:
                config = json.load(f)
                return cls(
                    MAIN_DB_PATH=config["DATABASE"]["MAIN_DB_PATH"],
                    MEDIA_DB_PATH=config["DATABASE"]["MEDIA_DB_PATH"]
                )
        except (FileNotFoundError, KeyError):
            return cls()

class Settings(BaseSettings):
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 4800
    DEBUG_PORT: int = 4801
    DEBUG: bool = False
    
    # Application settings
    VERSION: str = "0.1.0"
    LOG_FILE: Path = Path(os.path.expanduser("~/medialab-manager.log"))
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
        env_prefix = "MEDIALAB_"  # This allows setting PORT via MEDIALAB_PORT environment variable

settings = Settings.from_config() 