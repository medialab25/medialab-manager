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
        self.restic_server = os.getenv("RESTIC_SERVER", "192.168.10.10:4500")
        self.task_manager = TaskManager(db)

    def notify_start(self, task_id: str) -> bool:
        """
        Notify that a backup task has started.
        
        Args:
            task_id: Unique identifier for the backup task
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update task status to running
            self.task_manager.update_task_status(task_id, "running")
            logger.info(f"Task {task_id} started")
            return True
        except Exception as e:
            logger.error(f"Failed to notify task start: {str(e)}")
            return False

    def notify_end(self, task_id: str) -> bool:
        """
        Notify that a backup task has ended.
        
        Args:
            task_id: Unique identifier for the backup task
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update task status to success
            self.task_manager.update_task_status(task_id, "success")
            logger.info(f"Task {task_id} completed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to notify task end: {str(e)}")
            return False

    def register_backup(self, task_id: str, name: str, description: str, repo_id: str) -> bool:
        """
        Register a new backup task.
        
        Args:
            task_id: Unique identifier for the backup task
            name: Name of the backup task
            description: Description of the backup task
            repo_id: ID of the repository to backup
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if task already exists
            existing_task = self.task_manager.get_task(task_id)
            if existing_task:
                logger.info(f"Task {task_id} already exists, skipping creation")
                return True

            # Construct the repository URL
            repo_url = f"rest:http://{self.restic_server}/{repo_id}"
            
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
            
            try:
                # Create task in database
                self.task_manager.create_task(
                    task_id=task_id,
                    name=name,
                    description=description,
                    group="backup",
                    task_type="external",
                    enabled=True
                )
                logger.info(f"Successfully created task {task_id}")
                return True
            except ValueError as e:
                logger.error(f"Failed to create task: {str(e)}")
                return False
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to initialize repository: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during backup registration: {str(e)}")
            return False 