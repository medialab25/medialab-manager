from pydantic_settings import BaseSettings
from pathlib import Path
import json
from typing import Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

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
    TASK_FILTERS: Dict[str, Dict[str, Any]] = {}
    TASKS_FILE: str = "tasks.json"
    
    @classmethod
    def from_config(cls):
        try:
            with open("config.json") as f:
                config = json.load(f)
                settings = cls(
                    DATABASE=DatabaseSettings.from_config(),
                    TASKS_FILE=config.get("TASKS_FILE", "tasks.json")
                )
                
                logger.info(f"Loading tasks from file: {settings.TASKS_FILE}")
                
                # Load tasks and filters from the tasks file
                try:
                    with open(settings.TASKS_FILE) as f:
                        tasks_config = json.load(f)
                        settings.TASKS = tasks_config.get("TASKS", {})
                        settings.TASK_FILTERS = tasks_config.get("TASK_FILTERS", {})
                        logger.info(f"Successfully loaded {len(settings.TASKS)} tasks from {settings.TASKS_FILE}")
                except FileNotFoundError:
                    logger.warning(f"Tasks file {settings.TASKS_FILE} not found")
                    settings.TASKS = {}
                    settings.TASK_FILTERS = {}
                
                return settings
        except FileNotFoundError:
            logger.warning("config.json not found, using default settings")
            return cls()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "MEDIALAB_"  # This allows setting PORT via MEDIALAB_PORT environment variable

settings = Settings.from_config() 