import subprocess
import sys
from app.utils.file_utils import AttachDataMimeType
from app.utils.event_utils import EventManagerUtil


def run_script_task(script_path: str) -> str:
    """
    Runs a script and captures its output, adding events before and after execution.
    
    Args:
        script_path (str): Path to the script to execute
        
    Returns:
        str: The script's output
        
    Raises:
        subprocess.CalledProcessError: If the script execution fails
    """
    # Add event before task execution
    with EventManagerUtil.get_event_manager() as event_manager:
        event_manager.add_event(
            type="notify",
            sub_type="script",
            status="info",
            description="Starting script execution",
            details=f"Will execute script at: {script_path}"
        )
    
    print(f"Executing script at: {script_path}")
    
    # Run the script and capture its output
    try:
        # Run the script with subprocess
        script_result = subprocess.run(['python', script_path], 
            capture_output=True, 
            text=True, 
            check=True)
        
        print("\n=== Script Output ===")
        print(script_result.stdout)
        if script_result.stderr:
            print("Script Errors:", file=sys.stderr)
            print(script_result.stderr, file=sys.stderr)
            
        # Add event after successful execution
        with EventManagerUtil.get_event_manager() as event_manager:
            event_manager.add_event_with_output(
                type="notify",
                sub_type="script",
                status="success",
                description="Script executed successfully",
                details=f"Executed script at: {script_path}",
                attachment_data=script_result.stdout.encode('utf-8'),
                attachment_mime_type=AttachDataMimeType.TEXT
            )
            
        return script_result.stdout
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Error running script: {e}"
        print(error_msg, file=sys.stderr)
        
        # Add event for failed execution
        with EventManagerUtil.get_event_manager() as event_manager:
            event_manager.add_event_with_output(
                type="notify",
                sub_type="script",
                status="error",
                description="Script execution failed",
                details=error_msg,
                attachment_data=str(e).encode('utf-8'),
                attachment_mime_type=AttachDataMimeType.TEXT
            )
            
        raise


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_script.py <script_path>")
        sys.exit(1)
        
    script_path = sys.argv[1]
    try:
        output = run_script_task(script_path)
        print("\nScript completed successfully!")
    except subprocess.CalledProcessError:
        print("\nScript execution failed!")
        sys.exit(1) 