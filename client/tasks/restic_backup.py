import os
import subprocess
import logging
import json
from typing import Optional, List
from pydantic import BaseModel

logger = logging.getLogger(__name__)

def get_restic_server() -> str:
    """Get the Restic server URL from the config file."""
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return config.get("restic", {}).get("server", "192.168.10.10:4500")
    except Exception as e:
        logger.error(f"Error loading restic server from config: {e}")
        return "192.168.10.10:4500"  # Fallback to default

class TaskConfig(BaseModel):
    name: str
    task_type: str  # "interval" or "cron"
    function_name: str
    enabled: bool
    
    # Interval scheduling
    hours: Optional[int] = 0
    minutes: Optional[int] = 0
    seconds: Optional[int] = 0
    
    # Cron scheduling
    cron_hour: Optional[str] = "*"
    cron_minute: Optional[str] = "*"
    cron_second: Optional[str] = "*"
    
    # Restic specific parameters
    src_path: Optional[str] = None
    repo_name: Optional[str] = None  # This will be used as the repository name on the REST server
    password: Optional[str] = "media"  # Default password is 'media'
    additional_args: Optional[List[str]] = None

async def restic_backup_task(task_config: TaskConfig):
    """Run a Restic backup task with the given configuration."""
    if not task_config.src_path or not task_config.repo_name:
        logger.error(f"Task {task_config.name}: Missing required parameters (src_path or repo_name)")
        return

    try:
        # Set up environment with RESTIC_PASSWORD if provided
        env = os.environ.copy()
        if task_config.password:
            env['RESTIC_PASSWORD'] = task_config.password

        # Get the REST server URL from config
        restic_server = get_restic_server()
        repo_url = f"rest:http://{restic_server}/{task_config.repo_name}"

        # Check if repository exists
        try:
            subprocess.run(
                ['restic', '-r', repo_url, 'snapshots'],
                capture_output=True,
                check=True,
                env=env
            )
        except subprocess.CalledProcessError:
            # Repository doesn't exist, initialize it
            logger.info(f"Initializing Restic repository at {repo_url}")
            subprocess.run(
                ['restic', 'init', '-r', repo_url],
                capture_output=True,
                check=True,
                env=env
            )

        # Run backup
        cmd = ['restic', 'backup', '-r', repo_url]
        if task_config.additional_args:
            cmd.extend(task_config.additional_args)
        cmd.append(task_config.src_path)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        logger.info(f"Task {task_config.name}: Backup completed successfully")
        logger.debug(f"Backup output: {result.stdout}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Task {task_config.name}: Backup failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Task {task_config.name}: Unexpected error: {str(e)}") 