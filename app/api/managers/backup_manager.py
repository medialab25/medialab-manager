from sqlalchemy.orm import Session
import os
import subprocess
import logging
from typing import Optional
from app.api.managers.task_manager import TaskManager

logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self, db: Session):
        self.db = db
        self.restic_server = os.getenv("RESTIC_SERVER", "http://192.168.10.10:4500")
        self.task_manager = TaskManager(db)

    def register_backup(self, repo_id: str) -> bool:
        """
        Register a new backup task.
        
        Args:
            repo_id: ID of the repository to backup (used as task_id)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Construct the repository URL
            repo_url = f"rest:{self.restic_server}/{repo_id}"
            
            # Set environment variables
            env = os.environ.copy()
            env["RESTIC_PASSWORD"] = "media"  # Default password
            
            # Initialize repository if it doesn't exist
            try:
                logger.info(f"Checking if repository exists: {repo_url}")
                subprocess.run(
                    ["restic", "-r", repo_url, "snapshots"],
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info("Repository already exists")
            except subprocess.CalledProcessError:
                logger.info(f"Initializing repository: {repo_url}")
                init_result = subprocess.run(
                    ["restic", "-r", repo_url, "init"],
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info("Repository initialized successfully")
           
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to initialize repository: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during backup registration: {str(e)}")
            return False 