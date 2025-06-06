import os
import subprocess
import logging
import json
from typing import Dict, Any
from datetime import datetime
from managers.event_manager import event_manager

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

class TaskConfig:
    def __init__(self, config: Dict[str, Any]):
        self.src_path = config.get("src_path")
        self.repo_name = config.get("repo_name")  # This will be used as the repository name on the REST server
        self.password = config.get("password", "media")
        self.retention = config.get("retention", "7d")

async def restic_backup_task(task_id: str, config: Dict[str, Any]) -> None:
    """
    Execute a Restic backup task.
    
    Args:
        task_id: The ID of the task being executed
        config: Task configuration dictionary
    """
    task_config = TaskConfig(config)
    
    # Validate required parameters
    if not task_config.src_path:
        error_msg = "Missing required parameter: src_path"
        logger.error(error_msg)
        await event_manager.notify_task_error(task_id, error_msg)
        return
        
    if not task_config.repo_name:
        error_msg = "Missing required parameter: repo_name"
        logger.error(error_msg)
        await event_manager.notify_task_error(task_id, error_msg)
        return

    # Notify task start
    await event_manager.notify_task_start(task_id)
    
    try:
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
        await event_manager.notify_task_end(task_id)
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Backup failed: {e.stderr}"
        logger.error(error_msg)
        await event_manager.notify_task_error(task_id, error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during backup: {str(e)}"
        logger.error(error_msg)
        await event_manager.notify_task_error(task_id, error_msg) 