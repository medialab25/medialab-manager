import logging
from typing import Optional
import os
import subprocess
import asyncio
from managers.event_manager import event_manager
from managers.task_manager import TaskConfig

logger = logging.getLogger(__name__)

async def execute_restic_command(cmd: str) -> bool:
    """Execute a restic command and verify its success."""
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Restic command failed: {stderr.decode()}")
            return False
            
        logger.info(f"Restic command output: {stdout.decode()}")
        return True
    except Exception as e:
        logger.error(f"Error executing restic command: {str(e)}")
        return False

async def restic_backup_task(task_config: Optional[TaskConfig] = None) -> None:
    """Execute a restic backup task."""
    if not task_config:
        logger.error("No task configuration provided")
        return

    try:
        logger.info(f"Executing restic backup task: {task_config.name}")
        
        # Get restic configuration from environment
        restic_path = os.getenv("RESTIC_PATH")
        restic_repo = os.getenv("RESTIC_REPO")
        restic_password = os.getenv("RESTIC_PASSWORD")

        if not all([restic_path, restic_repo, restic_password]):
            raise ValueError("Missing required environment variables: RESTIC_PATH, RESTIC_REPO, or RESTIC_PASSWORD")

        # Initialize restic repository if needed
        init_cmd = f"restic -r {restic_repo} check --password-file <(echo '{restic_password}') || restic -r {restic_repo} init --password-file <(echo '{restic_password}')"
        if not await execute_restic_command(init_cmd):
            logger.error("Failed to initialize restic repository")
            return

        # Perform backup
        backup_cmd = (
            f"restic -r {restic_repo} backup {restic_path} "
            f"--password-file <(echo '{restic_password}') "
            f"--tag task:{task_config.name}"
        )
        
        if not await execute_restic_command(backup_cmd):
            logger.error("Failed to perform backup")
            return

        # Record completion
        await event_manager.record_event(
            "restic_backup_completed",
            {
                "task_name": task_config.name,
                "status": "success",
                "description": f"Successfully completed restic backup task: {task_config.name}"
            }
        )

    except Exception as e:
        logger.error(f"Error executing restic backup task: {e}")
        await event_manager.record_event(
            "restic_backup_failed",
            {
                "task_name": task_config.name,
                "status": "error",
                "description": f"Failed to execute restic backup task: {task_config.name}",
                "error": str(e)
            }
        ) 