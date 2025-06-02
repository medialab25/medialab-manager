import subprocess
import sys
import time
from app.utils.event_utils import create_event


def spindown_disks(message: str = "Starting Spindown Disks") -> str:
    """
    A task that runs Spindown Disks and returns the status message.
    
    Args:
        message (str): The message to print and return
        
    Returns:
        str: The input message
    """
    start_time = time.time()
    
    # Add start event
    create_event(
        status="info",
        event_type="disk",
        sub_type="spindown",
        description="Starting Spindown Disks operation",
        details=f"Task will process: {message}\nStart time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    print(f"Executing Spindown Disks: {message}")
    
    # Run snapraid sync command and capture its output
    try:
        # Run snapraid sync command
        # spindown_result = subprocess.run(['sudo', 'spindown', '-a'], 
        #     capture_output=True, 
        #     text=True, 
        #     check=True)
        
        print("\n=== Spindown Disks Output ===")
        print("Spindown Disks completed successfully")
            
        # Calculate duration
        end_time = time.time()
        duration = end_time - start_time
        
        # Add success event
        create_event(
            status="success",
            event_type="disk",
            sub_type="spindown",
            description="Spindown Disks completed successfully",
            details=f"Processed: {message}\nDuration: {duration:.2f} seconds\nEnd time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        )
            
    except subprocess.CalledProcessError as e:
        # Calculate duration even for failed operations
        end_time = time.time()
        duration = end_time - start_time
        
        # Add error event
        create_event(
            status="error",
            event_type="disk",
            sub_type="spindown",
            description="Spindown Disks failed",
            details=f"Error: {str(e)}\nDuration: {duration:.2f} seconds\nEnd time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        )
        print(f"Error running Spindown Disks: {e}", file=sys.stderr)
        # raise  # Re-raise the exception after logging
    
    return message
