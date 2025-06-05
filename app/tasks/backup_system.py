import subprocess
import sys
import time
from typing import Optional
from app.utils.file_utils import AttachDataMimeType
from app.utils.event_utils import EventManagerUtil


def _create_event(status: str, description: str, details: str, attachment_data: Optional[bytes] = None) -> None:
    """Helper function to create events with consistent parameters."""
    with EventManagerUtil.get_event_manager() as event_manager:
        if attachment_data:
            event_manager.add_event_with_output(
                type="notify",
                sub_type="backup",
                status=status,
                description=description,
                details=details,
                attachment_data=attachment_data,
                attachment_mime_type=AttachDataMimeType.TEXT
            )
        else:
            event_manager.add_event(
                type="notify",
                sub_type="backup",
                status=status,
                description=description,
                details=details
            )


def backup_system_task() -> str:
    """
    Runs the backup system shell script and captures its output.
    
    Returns:
        str: The script's output
        
    Raises:
        subprocess.CalledProcessError: If the script execution fails
    """
    start_time = time.time()
    script_path = "/srv/system-backups/backup_system.sh"
    
    # Add event before task execution
    _create_event(
        "info",
        "Starting system backup",
        f"Will execute backup script at: {script_path}\nStart time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    print(f"Executing backup script at: {script_path}")
    
    # Run the script and capture its output
    try:
        # Run the script with subprocess
        script_result = subprocess.run(['bash', script_path], 
            capture_output=True, 
            text=True, 
            check=True)
        
        print("\n=== Backup Script Output ===")
        print(script_result.stdout)
        if script_result.stderr:
            print("Backup Script Errors:", file=sys.stderr)
            print(script_result.stderr, file=sys.stderr)
            
        # Calculate duration
        end_time = time.time()
        duration = end_time - start_time
            
        # Add event after successful execution
        _create_event(
            "success",
            "System backup completed successfully",
            f"Backup script executed at: {script_path}\nDuration: {duration:.2f} seconds\nEnd time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            script_result.stdout.encode('utf-8')
        )
            
        return script_result.stdout
        
    except subprocess.CalledProcessError as e:
        # Calculate duration even for failed operations
        end_time = time.time()
        duration = end_time - start_time
        
        error_msg = f"Error running backup script: {e}"
        print(error_msg, file=sys.stderr)
        
        # Add event for failed execution
        _create_event(
            "error",
            "System backup failed",
            f"{error_msg}\nDuration: {duration:.2f} seconds\nEnd time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            str(e).encode('utf-8')
        )
            
        raise


if __name__ == "__main__":
    try:
        output = backup_system_task()
        print("\nBackup completed successfully!")
    except subprocess.CalledProcessError:
        print("\nBackup failed!")
        sys.exit(1) 