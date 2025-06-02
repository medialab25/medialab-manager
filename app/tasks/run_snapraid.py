import subprocess
import sys
import time
from app.models.event_types import Status
from app.utils.file_utils import AttachDataMimeType
from app.utils.event_utils import create_event


def run_snapraid(message: str = "Starting SnapRAID sync") -> str:
    """
    A task that runs SnapRAID sync and returns the status message.
    
    Args:
        message (str): The message to print and return
        
    Returns:
        str: The input message
    """
    start_time = time.time()
    
    # Add start event
    create_event(
        status=Status.INFO,
        description="Starting SnapRAID sync operation",
        details=f"Task will process: {message}\nStart time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    print(f"Executing SnapRAID sync: {message}")
    
    # Run snapraid sync command and capture its output
    try:
        # Run snapraid sync command
        snapraid_result = subprocess.run(['snapraid', 'sync'], 
            capture_output=True, 
            text=True, 
            check=True)
        
        print("\n=== SnapRAID Sync Output ===")
        print(snapraid_result.stdout)
        if snapraid_result.stderr:
            print("SnapRAID Sync Errors:", file=sys.stderr)
            print(snapraid_result.stderr, file=sys.stderr)
            
        # Calculate duration
        end_time = time.time()
        duration = end_time - start_time
        
        # Add success event
        create_event(
            status=Status.SUCCESS,
            description="SnapRAID sync completed successfully",
            details=f"Processed: {message}\nDuration: {duration:.2f} seconds\nEnd time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            attachment_data=snapraid_result.stdout.encode('utf-8'),
            attachment_mime_type=AttachDataMimeType.TEXT
        )
            
    except subprocess.CalledProcessError as e:
        # Calculate duration even for failed operations
        end_time = time.time()
        duration = end_time - start_time
        
        # Add error event
        create_event(
            status=Status.ERROR,
            description="SnapRAID sync failed",
            details=f"Error: {str(e)}\nDuration: {duration:.2f} seconds\nEnd time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            attachment_data=e.stderr.encode('utf-8') if e.stderr else str(e).encode('utf-8'),
            attachment_mime_type=AttachDataMimeType.TEXT
        )
        print(f"Error running SnapRAID sync: {e}", file=sys.stderr)
        # raise  # Re-raise the exception after logging
    
    return message
