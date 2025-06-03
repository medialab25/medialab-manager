import subprocess
import sys
import time
from app.utils.file_utils import AttachDataMimeType
from app.utils.event_utils import create_event


def sync_data_cloud(backup_path: str, bucket_name: str) -> str:
    """
    A task that syncs data to cloud storage using rclone.
    
    Args:
        backup_path (str): The local path to sync
        bucket_name (str): The cloud bucket name to sync to
        
    Returns:
        str: Status message about the sync operation
    """
    start_time = time.time()
    
    # Add start event
    create_event(
        status="info",
        event_type="backup",
        sub_type="cloud_sync",
        description="Starting cloud sync operation",
        details=f"Syncing from {backup_path} to {bucket_name}\nStart time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    print(f"Executing cloud sync from {backup_path} to {bucket_name}")
    
    try:
        # Run rclone sync command
        rclone_result = subprocess.run(
            ['rclone', 'sync', backup_path, bucket_name],
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
            details=f"Synced from {backup_path} to {bucket_name}\nDuration: {duration:.2f} seconds\nEnd time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
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
            details=f"Error: {str(e)}\nDuration: {duration:.2f} seconds\nEnd time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            attachment_data=e.stderr.encode('utf-8') if e.stderr else str(e).encode('utf-8'),
            attachment_mime_type=AttachDataMimeType.TEXT
        )
        print(f"Error running rclone sync: {e}", file=sys.stderr)
    
    return f"Cloud sync from {backup_path} to {bucket_name} completed"
