import subprocess
import sys
import os
from app.utils.file_utils import AttachDataMimeType
from app.utils.event_utils import EventManagerUtil


def _run_script_base(script_path: str, sub_type: str, description_prefix: str) -> str:
    """
    Base function for running scripts with event logging and output capture.
    
    Args:
        script_path (str): Full path to the script to execute
        sub_type (str): Event sub_type for logging
        description_prefix (str): Prefix for event descriptions
        
    Returns:
        str: The script's output
        
    Raises:
        subprocess.CalledProcessError: If the script execution fails
    """
    # Add event before task execution
    with EventManagerUtil.get_event_manager() as event_manager:
        event_manager.add_event(
            type="notify",
            sub_type=sub_type,
            status="info",
            description=f"{description_prefix} script execution",
            details=f"Will execute script at: {script_path}"
        )
    
    print(f"Executing script at: {script_path}")
    
    try:
        script_result = subprocess.run(['python', script_path], 
            capture_output=True, 
            text=True, 
            check=True)
        
        print("\n=== Script Output ===")
        print(script_result.stdout)
        if script_result.stderr:
            print("Script Errors:", file=sys.stderr)
            print(script_result.stderr, file=sys.stderr)
            
        with EventManagerUtil.get_event_manager() as event_manager:
            event_manager.add_event_with_output(
                type="notify",
                sub_type=sub_type,
                status="success",
                description=f"{description_prefix} script executed successfully",
                details=f"Executed script at: {script_path}",
                attachment_data=script_result.stdout.encode('utf-8'),
                attachment_mime_type=AttachDataMimeType.TEXT
            )
            
        return script_result.stdout
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Error running script: {e}"
        print(error_msg, file=sys.stderr)
        
        with EventManagerUtil.get_event_manager() as event_manager:
            event_manager.add_event_with_output(
                type="notify",
                sub_type=sub_type,
                status="error",
                description=f"{description_prefix} script execution failed",
                details=error_msg,
                attachment_data=str(e).encode('utf-8'),
                attachment_mime_type=AttachDataMimeType.TEXT
            )
            
        raise


def run_script_task(script_path: str) -> str:
    """
    Runs a script and captures its output, adding events before and after execution.
    
    Args:
        script_path (str): Path to the script to execute. If relative, will be resolved from project root.
        
    Returns:
        str: The script's output
        
    Raises:
        subprocess.CalledProcessError: If the script execution fails
    """
    if not os.path.isabs(script_path):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        script_path = os.path.join(project_root, script_path)
    
    return _run_script_base(script_path, "script", "Starting")


def run_media_systems_script_task(script_path: str) -> str:
    """
    Runs a script from the media-stacks/systems folder and captures its output.
    
    Args:
        script_path (str): Path to the script to execute relative to media-stacks/systems folder.
        
    Returns:
        str: The script's output
        
    Raises:
        subprocess.CalledProcessError: If the script execution fails
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    media_root = os.path.dirname(project_root)
    full_script_path = os.path.join(media_root, 'media-stacks', 'systems', script_path)
    
    return _run_script_base(full_script_path, "media_systems_script", "Media systems")


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