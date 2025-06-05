import logging
import subprocess
import os
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

def backup_stacks(task_id: str, **params: Dict[str, Any]) -> None:
    """
    Backup specified Docker stacks using restic.
    
    Args:
        task_id: The ID of the task
        **params: Dictionary containing:
            - stacks: List of stack names to backup
            - backup_path: Base path where backups will be stored
            - restic_repo: Base path for restic repository
            - password: Password for the restic repository
            - additional_args: Additional arguments to pass to restic
    """
    stacks = params.get('stacks', [])
    base_backup_path = params.get('backup_path')
    base_repo = params.get('restic_repo')
    password = params.get('password', 'media')
    additional_args = params.get('additional_args', [])

    if not stacks:
        logger.warning(f"No stacks specified for backup in task {task_id}")
        return

    if not base_backup_path or not base_repo:
        logger.error(f"backup_path and restic_repo are required parameters")
        return

    # Get full path to restic
    try:
        restic_path = subprocess.check_output(['which', 'restic'], text=True).strip()
    except subprocess.CalledProcessError:
        logger.error("restic command not found")
        return

    # Set up environment with RESTIC_PASSWORD
    env = os.environ.copy()
    env['RESTIC_PASSWORD'] = password

    for stack in stacks:
        try:
            # Create stack-specific paths
            restic_repo = os.path.join(base_repo, stack)
            backup_path = os.path.join(base_backup_path, stack)
            
            # Create directories if they don't exist
            os.makedirs(restic_repo, exist_ok=True)
            os.makedirs(backup_path, exist_ok=True)
            
            logger.info(f"Starting backup for stack: {stack}")
            logger.info(f"Backup path: {backup_path}")
            logger.info(f"Repository: {restic_repo}")

            # Check if repository exists by trying to get its config
            try:
                subprocess.run([
                    "sudo", restic_path, "-r", restic_repo,
                    "cat", "config"
                ], check=True, capture_output=True, env=env)
                logger.info("Repository exists, proceeding with backup...")
            except subprocess.CalledProcessError:
                logger.info(f"Initializing restic repository at {restic_repo}...")
                subprocess.run([
                    "sudo", restic_path, "init",
                    "-r", restic_repo
                ], check=True, env=env)

            # Get running containers for this stack
            result = subprocess.run([
                "docker", "ps",
                "--filter", f"label=com.docker.compose.project={stack}",
                "--format", "{{.Names}}"
            ], check=True, capture_output=True, text=True)
            
            running_containers = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            if running_containers:
                logger.info(f"Stopping containers for {stack}...")
                subprocess.run(["docker", "stop"] + running_containers, check=True)
                
                logger.info(f"Running restic backup for {stack}...")
                restic_cmd = [
                    "sudo", restic_path, "backup",
                    "-r", restic_repo
                ]
                restic_cmd.extend(additional_args)
                restic_cmd.append(backup_path)
                
                subprocess.run(restic_cmd, check=True, env=env)
                
                logger.info(f"Starting containers for {stack}...")
                subprocess.run(["docker", "start"] + running_containers, check=True)
            else:
                logger.info(f"{stack} containers not running, backing up directly...")
                logger.info(f"Running restic backup for {stack}...")
                restic_cmd = [
                    "sudo", restic_path, "backup",
                    "-r", restic_repo
                ]
                restic_cmd.extend(additional_args)
                restic_cmd.append(backup_path)
                
                subprocess.run(restic_cmd, check=True, env=env)
            
            logger.info(f"Backup completed for {stack}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error backing up stack {stack}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error backing up stack {stack}: {str(e)}") 