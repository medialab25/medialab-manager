import subprocess
import sys
from app.utils.file_utils import AttachDataMimeType
from app.utils.event_utils import EventManagerUtil


def backup_system_task() -> str:
    """
    Runs the backup system shell script and captures its output.
    
    Returns:
        str: The script's output
        
    Raises:
        subprocess.CalledProcessError: If the script execution fails
    """
    script_path = "/srv/system-backups/backup_system.sh"
    
    # Add event before task execution
    with EventManagerUtil.get_event_manager() as event_manager:
        event_manager.add_event(
            type="notify",
            sub_type="backup",
            status="info",
            description="Starting system backup",
            details=f"Will execute backup script at: {script_path}"
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
            
        # Add event after successful execution
        with EventManagerUtil.get_event_manager() as event_manager:
            event_manager.add_event_with_output(
                type="notify",
                sub_type="backup",
                status="success",
                description="System backup completed successfully",
                details=f"Backup script executed at: {script_path}",
                attachment_data=script_result.stdout.encode('utf-8'),
                attachment_mime_type=AttachDataMimeType.TEXT
            )
            
        return script_result.stdout
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Error running backup script: {e}"
        print(error_msg, file=sys.stderr)
        
        # Add event for failed execution
        with EventManagerUtil.get_event_manager() as event_manager:
            event_manager.add_event_with_output(
                type="notify",
                sub_type="backup",
                status="error",
                description="System backup failed",
                details=error_msg,
                attachment_data=str(e).encode('utf-8'),
                attachment_mime_type=AttachDataMimeType.TEXT
            )
            
        raise


if __name__ == "__main__":
    try:
        output = backup_system_task()
        print("\nBackup completed successfully!")
    except subprocess.CalledProcessError:
        print("\nBackup failed!")
        sys.exit(1) 