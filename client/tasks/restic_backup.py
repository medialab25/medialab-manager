import os
import subprocess
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from managers.event_manager import event_manager
from pydantic import BaseModel

logger = logging.getLogger(__name__)

def get_restic_server() -> str:
    """Get the Restic server URL from the config file."""
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return config.get("restic", {}).get("server", "192.168.10.10:4500")
    except Exception as e:
        logger.error(f"Error loading restic server URL from config: {e}")
        return "192.168.10.10:4500"  # Fallback to default

class TaskConfig(BaseModel):
    name: str
    task_type: str
    function_name: str
    enabled: bool
    hours: Optional[int] = 0
    minutes: Optional[int] = 0
    seconds: Optional[int] = 0
    cron_hour: Optional[str] = None
    cron_minute: Optional[str] = None
    cron_second: Optional[str] = None
    src_path: Optional[str] = None
    repo_name: Optional[str] = None
    additional_args: Optional[List[str]] = None

async def restic_backup_task(task_config: Optional[TaskConfig] = None) -> None:
    """Execute a restic backup task"""
    if not task_config:
        logger.error("No task configuration provided")
        return

    try:
        restic_server = os.getenv("RESTIC_SERVER", "192.168.10.10:4500")
        logger.info(f"Executing restic backup task: {task_config.name}")
        logger.info(f"Using restic server: {restic_server}")
        logger.info(f"Source path: {task_config.src_path}")
        logger.info(f"Repository: {task_config.repo_name}")
        if task_config.additional_args:
            logger.info(f"Additional arguments: {task_config.additional_args}")

        # Notify task start
        await event_manager.notify_task_start(task_config.name)
        
        # Get server URL from config
        server_url = get_restic_server()
        repo_url = f"rest:http://{server_url}/{task_config.repo_name}"
        
        # Set environment variables
        env = os.environ.copy()
        env["RESTIC_PASSWORD"] = task_config.password
        
        # Initialize repository if it doesn't exist
        try:
            logger.info(f"Initializing repository: {repo_url}")
            subprocess.run(
                ["restic", "-r", repo_url, "init"],
                env=env,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            if "already initialized" not in e.stderr:
                raise
        
        # Perform backup
        logger.info(f"Starting backup from {task_config.src_path} to {repo_url}")
        result = subprocess.run(
            ["restic", "-r", repo_url, "backup", task_config.src_path],
            env=env,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Apply retention policy
        logger.info(f"Applying retention policy: {task_config.retention}")
        subprocess.run(
            ["restic", "-r", repo_url, "forget", "--keep-within", task_config.retention],
            env=env,
            check=True,
            capture_output=True,
            text=True
        )
        
        logger.info("Backup completed successfully")
        await event_manager.notify_task_end(task_config.name)
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Backup failed: {e.stderr}"
        logger.error(error_msg)
        await event_manager.notify_task_error(task_config.name, error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during backup: {str(e)}"
        logger.error(error_msg)
        await event_manager.notify_task_error(task_config.name, error_msg) 