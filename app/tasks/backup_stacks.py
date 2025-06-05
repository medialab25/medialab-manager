import logging
import subprocess
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.utils.event_utils import EventManagerUtil
from app.utils.file_utils import AttachDataMimeType

logger = logging.getLogger(__name__)

def _create_event(status: str, description: str, details: str, attachment_data: Optional[bytes] = None) -> None:
    """Helper function to create events with consistent parameters."""
    with EventManagerUtil.get_event_manager() as event_manager:
        if attachment_data:
            event_manager.add_event_with_output(
                type="backup",
                sub_type="stacks",
                status=status,
                description=description,
                details=details,
                attachment_data=attachment_data,
                attachment_mime_type=AttachDataMimeType.TEXT
            )
        else:
            event_manager.add_event(
                type="backup",
                sub_type="stacks",
                status=status,
                description=description,
                details=details
            )

def _run_command(cmd: List[str], env: Dict[str, str], capture_output: bool = True) -> subprocess.CompletedProcess:
    """Helper function to run commands with consistent error handling."""
    try:
        return subprocess.run(
            cmd,
            check=True,
            capture_output=capture_output,
            text=True,
            env=env
        )
    except subprocess.CalledProcessError as e:
        error_msg = f"Command failed: {' '.join(cmd)}\nError: {str(e)}"
        logger.error(error_msg)
        _create_event("error", "Command execution failed", error_msg, str(e).encode('utf-8'))
        raise

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
        _create_event("warning", "No stacks specified for backup", f"Task {task_id} had no stacks specified")
        return

    if not base_backup_path or not base_repo:
        error_msg = "backup_path and restic_repo are required parameters"
        _create_event("error", "Backup failed", error_msg)
        return

    # Get full path to restic
    try:
        restic_path = subprocess.check_output(['which', 'restic'], text=True).strip()
    except subprocess.CalledProcessError:
        _create_event("error", "Backup failed", "restic command not found")
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
            _create_event("info", f"Starting backup for stack: {stack}", 
                         f"Backup path: {backup_path}\nRepository: {restic_repo}")

            # Check if repository exists by trying to get its config
            try:
                _run_command(["sudo", restic_path, "-r", restic_repo, "cat", "config"], env)
                logger.info("Repository exists, proceeding with backup...")
            except subprocess.CalledProcessError:
                logger.info(f"Initializing restic repository at {restic_repo}...")
                init_result = _run_command(["sudo", restic_path, "init", "-r", restic_repo], env)
                _create_event("info", f"Initialized restic repository for {stack}",
                            f"Repository path: {restic_repo}",
                            init_result.stdout.encode('utf-8'))

            # Get running containers for this stack
            result = _run_command([
                "docker", "ps",
                "--filter", f"label=com.docker.compose.project={stack}",
                "--format", "{{.Names}}"
            ], env)
            
            running_containers = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            if running_containers:
                logger.info(f"Stopping containers for {stack}...")
                _run_command(["docker", "stop"] + running_containers, env)
            
            # Run backup
            logger.info(f"Running restic backup for {stack}...")
            restic_cmd = ["sudo", restic_path, "backup", "-r", restic_repo]
            restic_cmd.extend(additional_args)
            restic_cmd.append(backup_path)
            
            backup_result = _run_command(restic_cmd, env)
            _create_event("success", f"Backup completed for stack: {stack}",
                         f"Backup path: {backup_path}\nRepository: {restic_repo}",
                         backup_result.stdout.encode('utf-8'))
            
            if running_containers:
                logger.info(f"Starting containers for {stack}...")
                _run_command(["docker", "start"] + running_containers, env)
            
            logger.info(f"Backup completed for {stack}")
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Error backing up stack {stack}: {str(e)}"
            logger.error(error_msg)
            _create_event("error", f"Backup failed for stack: {stack}", error_msg, str(e).encode('utf-8'))
        except Exception as e:
            error_msg = f"Unexpected error backing up stack {stack}: {str(e)}"
            logger.error(error_msg)
            _create_event("error", f"Unexpected error backing up stack: {stack}", error_msg, str(e).encode('utf-8')) 