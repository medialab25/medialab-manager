import subprocess
import sys
import os
from typing import List, Dict, Any
from app.utils.file_utils import AttachDataMimeType
from app.utils.event_utils import EventManagerUtil

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def _run_restic_command(cmd: List[str], password: str, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run a Restic command and handle its output
    
    Args:
        cmd: The command to run
        password: The Restic repository password
        capture_output: Whether to capture output
        
    Returns:
        subprocess.CompletedProcess: The command result
    """
    try:
        # Set RESTIC_PASSWORD environment variable
        env = os.environ.copy()
        env['RESTIC_PASSWORD'] = password
        
        # Print the command being run (without the password)
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            ['sudo'] + cmd,
            capture_output=capture_output,
            text=True,
            check=True,
            env=env
        )
        
        # Print the output
        if result.stdout:
            print("Command output:", result.stdout)
        if result.stderr:
            print("Command errors:", result.stderr, file=sys.stderr)
            
        return result
    except subprocess.CalledProcessError as e:
        error_msg = f"Restic command failed: {e.stderr if e.stderr else str(e)}"
        print(error_msg, file=sys.stderr)
        if e.stdout:
            print("Command output:", e.stdout)
        if e.stderr:
            print("Command errors:", e.stderr, file=sys.stderr)
        raise subprocess.CalledProcessError(e.returncode, e.cmd, e.stdout, e.stderr)

def restic_backup(task_id: str, **kwargs) -> str:
    """
    Perform a backup using Restic.
    
    Args:
        task_id (str): The ID of the task
        **kwargs: Additional parameters including:
            - backup_path (str): Path to the data to backup
            - include_file (str): Path to a file containing paths to include in backup (relative to script location)
            - restic_repo (str): Path to the Restic repository
            - password (str): Password for the Restic repository (defaults to 'media')
            - additional_args (List[str]): Additional arguments to pass to Restic
    
    Returns:
        str: The backup output
        
    Raises:
        ValueError: If required parameters are missing or paths don't exist
        subprocess.CalledProcessError: If the backup fails
    """
    backup_path = kwargs.get('backup_path')
    include_file = kwargs.get('include_file')
    restic_repo = kwargs.get('restic_repo')
    password = kwargs.get('password', 'media')  # Default password is 'media'
    additional_args = kwargs.get('additional_args', [])
    
    if not restic_repo:
        raise ValueError("restic_repo is a required parameter")
    
    if not backup_path and not include_file:
        raise ValueError("Either backup_path or include_file must be provided")
    
    # Check if backup path exists if provided
    if backup_path and not os.path.exists(backup_path):
        error_msg = f"Backup path does not exist: {backup_path}"
        print(error_msg, file=sys.stderr)
        with EventManagerUtil.get_event_manager() as event_manager:
            event_manager.add_event(
                type="backup",
                sub_type=task_id,
                status="error",
                description="Restic backup failed",
                details=error_msg
            )
        raise ValueError(error_msg)
    
    # Check if include file exists if provided and make it relative to script location
    if include_file:
        include_file = os.path.join(SCRIPT_DIR, include_file)
        if not os.path.exists(include_file):
            error_msg = f"Include file does not exist: {include_file}"
            print(error_msg, file=sys.stderr)
            with EventManagerUtil.get_event_manager() as event_manager:
                event_manager.add_event(
                    type="backup",
                    sub_type=task_id,
                    status="error",
                    description="Restic backup failed",
                    details=error_msg
                )
            raise ValueError(error_msg)
    
    # Check if repository directory exists, create if it doesn't
    repo_dir = os.path.dirname(restic_repo)
    if not os.path.exists(repo_dir):
        print(f"Creating repository directory: {repo_dir}")
        os.makedirs(repo_dir, exist_ok=True)
    
    # Add event before backup
    with EventManagerUtil.get_event_manager() as event_manager:
        event_manager.add_event(
            type="backup",
            sub_type=task_id,
            status="info",
            description="Starting Restic backup",
            details=f"Backing up using {'include file' if include_file else backup_path} to {restic_repo}"
        )
    
    try:
        # Check if repository exists, if not initialize it
        try:
            print("Checking if repository exists...")
            _run_restic_command(['restic', '--repo', restic_repo, 'snapshots'], password)
        except subprocess.CalledProcessError:
            # Repository doesn't exist or is not initialized
            print("Repository not found, initializing...")
            init_result = _run_restic_command(['restic', 'init', '--repo', restic_repo], password)
            with EventManagerUtil.get_event_manager() as event_manager:
                event_manager.add_event(
                    type="backup",
                    sub_type=task_id,
                    status="info",
                    description="Initialized Restic repository",
                    details=f"Initialized repository at {restic_repo}"
                )
        
        # Construct and run the backup command
        print("Starting backup...")
        cmd = ['restic', 'backup', '--repo', restic_repo]
        
        if include_file:
            cmd.extend(['--files-from', include_file])
        else:
            cmd.append(backup_path)
            
        cmd.extend(additional_args)
        result = _run_restic_command(cmd, password)
        
        # Add event for successful backup
        with EventManagerUtil.get_event_manager() as event_manager:
            event_manager.add_event_with_output(
                type="backup",
                sub_type=task_id,
                status="success",
                description="Restic backup completed successfully",
                details=f"Backed up using {'include file' if include_file else backup_path} to {restic_repo}",
                attachment_data=result.stdout.encode('utf-8'),
                attachment_mime_type=AttachDataMimeType.TEXT
            )
        
        return result.stdout
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Error running Restic backup: {e.stderr if e.stderr else str(e)}"
        print(error_msg, file=sys.stderr)
        
        # Add event for failed backup
        with EventManagerUtil.get_event_manager() as event_manager:
            event_manager.add_event_with_output(
                type="backup",
                sub_type=task_id,
                status="error",
                description="Restic backup failed",
                details=error_msg,
                attachment_data=str(e).encode('utf-8'),
                attachment_mime_type=AttachDataMimeType.TEXT
            )
        
        raise 