import subprocess
import sys
import time
from typing import Dict, Any
from app.utils.file_utils import AttachDataMimeType
from app.utils.event_utils import create_event


def sync_data_cloud(task_id: str, **params: Dict[str, Any]) -> str:
    """
    A task that syncs data to cloud storage using rclone.
    
    Args:
        task_id (str): The ID of the task
        **params: Dictionary containing:
            - backup_path (str): The local path to sync
            - bucket_name (str): The cloud bucket name to sync to
            - dry_run (bool, optional): If True, perform a dry run without making changes. Defaults to False.
        
    Returns:
        str: Status message about the sync operation
        
    Raises:
        ValueError: If required parameters are missing
        subprocess.CalledProcessError: If the rclone sync operation fails
    """
    backup_path = params.get('backup_path')
    bucket_name = params.get('bucket_name')
    dry_run = params.get('dry_run', False)
    
    if not backup_path or not bucket_name:
        error_msg = "backup_path and bucket_name are required parameters"
        print(error_msg, file=sys.stderr)
        create_event(
            status="error",
            event_type="backup",
            sub_type="cloud_sync",
            description="Cloud sync failed",
            details=error_msg
        )
        raise ValueError(error_msg)
    
    start_time = time.time()
    
    # Add start event
    create_event(
        status="info",
        event_type="backup",
        sub_type="cloud_sync",
        description="Starting cloud sync operation",
        details=f"Syncing from {backup_path} to {bucket_name}\nStart time: {time.strftime('%Y-%m-%d %H:%M:%S')}\nDry run: {dry_run}"
    )
    
    print(f"Executing cloud sync from {backup_path} to {bucket_name} (dry run: {dry_run})")
    
    try:
        # Build rclone command
        rclone_cmd = ['sudo', 'rclone', 'sync']
        if dry_run:
            rclone_cmd.append('--dry-run')
        rclone_cmd.extend([backup_path, bucket_name])
        
        # Run rclone sync command
        rclone_result = subprocess.run(
            rclone_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\n=== Rclone Sync Output ===")
        print(rclone_result.stdout)
        if rclone_result.stderr:
            print("Rclone Sync Errors:", file=sys.stderr)
            print(rclone_result.stderr, file=sys.stderr)
            
        # Calculate duration
        end_time = time.time()
        duration = end_time - start_time
        
        # Add success event
        create_event(
            status="success",
            event_type="backup",
            sub_type="cloud_sync",
            description="Cloud sync completed successfully",
            details=f"Synced from {backup_path} to {bucket_name}\nDuration: {duration:.2f} seconds\nEnd time: {time.strftime('%Y-%m-%d %H:%M:%S')}\nDry run: {dry_run}",
            attachment_data=rclone_result.stdout.encode('utf-8'),
            attachment_mime_type=AttachDataMimeType.TEXT
        )
            
    except subprocess.CalledProcessError as e:
        # Calculate duration even for failed operations
        end_time = time.time()
        duration = end_time - start_time
        
        # Add error event
        create_event(
            status="error",
            event_type="backup",
            sub_type="cloud_sync",
            description="Cloud sync failed",
            details=f"Error: {str(e)}\nDuration: {duration:.2f} seconds\nEnd time: {time.strftime('%Y-%m-%d %H:%M:%S')}\nDry run: {dry_run}",
            attachment_data=e.stderr.encode('utf-8') if e.stderr else str(e).encode('utf-8'),
            attachment_mime_type=AttachDataMimeType.TEXT
        )
        print(f"Error running rclone sync: {e}", file=sys.stderr)
        raise  # Re-raise the exception to be handled by the caller
    
    return f"Cloud sync from {backup_path} to {bucket_name} completed"
