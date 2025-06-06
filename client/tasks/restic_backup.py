import os
import subprocess
import logging
from typing import Optional, List
from pydantic import BaseModel

logger = logging.getLogger(__name__)

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
    repo_name: Optional[str] = None
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

        # Check if repository exists
        try:
            subprocess.run(
                ['restic', '-r', task_config.repo_name, 'snapshots'],
                capture_output=True,
                check=True,
                env=env
            )
        except subprocess.CalledProcessError:
            # Repository doesn't exist, initialize it
            logger.info(f"Initializing Restic repository at {task_config.repo_name}")
            subprocess.run(
                ['restic', 'init', '-r', task_config.repo_name],
                capture_output=True,
                check=True,
                env=env
            )

        # Run backup
        cmd = ['restic', 'backup', '-r', task_config.repo_name]
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