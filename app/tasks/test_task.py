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
                sub_type="email",
                status=status,
                description=description,
                details=details,
                attachment_data=attachment_data,
                attachment_mime_type=AttachDataMimeType.TEXT
            )
        else:
            event_manager.add_event(
                type="notify",
                sub_type="email",
                status=status,
                description=description,
                details=details
            )


def dummy_task(message: str = "Hello from dummy task!") -> str:
    """
    A dummy task that prints a message, adds an event, and returns the message.
    
    Args:
        message (str): The message to print and return
        
    Returns:
        str: The input message
    """
    start_time = time.time()
    
    # Add event before task execution
    _create_event(
        "info",
        "Starting dummy task execution",
        f"Task will process message: {message}\nStart time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    print(f"Executing dummy task with message: {message}")
    
    # Run cat command and capture its output
    try:
        # Run cat command with the input text
        cat_result = subprocess.run(['echo', 'test'], 
            capture_output=True, 
            text=True, 
            check=True)
        
        print("\n=== Cat Command Output ===")
        print(cat_result.stdout)
        if cat_result.stderr:
            print("Cat Command Errors:", file=sys.stderr)
            print(cat_result.stderr, file=sys.stderr)
            
        # Calculate duration
        end_time = time.time()
        duration = end_time - start_time
            
        # Add event after task completion
        _create_event(
            "success",
            "Dummy task completed successfully",
            f"Processed message: {message}\nDuration: {duration:.2f} seconds\nEnd time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            cat_result.stdout.encode('utf-8')
        )
            
    except subprocess.CalledProcessError as e:
        # Calculate duration even for failed operations
        end_time = time.time()
        duration = end_time - start_time
        
        error_msg = f"Error running cat command: {e}"
        print(error_msg, file=sys.stderr)
        
        # Add event for failed execution
        _create_event(
            "error",
            "Dummy task failed",
            f"{error_msg}\nDuration: {duration:.2f} seconds\nEnd time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            str(e).encode('utf-8')
        )
    
    return message


def run_script_task(script_path: str) -> str:
    """
    Runs a script and captures its output, adding events before and after execution.
    
    Args:
        script_path (str): Path to the script to execute
        
    Returns:
        str: The script's output
    """
    start_time = time.time()
    
    # Add event before task execution
    _create_event(
        "info",
        "Starting script execution",
        f"Will execute script at: {script_path}\nStart time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
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
            
        # Calculate duration
        end_time = time.time()
        duration = end_time - start_time
            
        # Add event after successful execution
        _create_event(
            "success",
            "Script executed successfully",
            f"Executed script at: {script_path}\nDuration: {duration:.2f} seconds\nEnd time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            script_result.stdout.encode('utf-8')
        )
            
        return script_result.stdout
        
    except subprocess.CalledProcessError as e:
        # Calculate duration even for failed operations
        end_time = time.time()
        duration = end_time - start_time
        
        error_msg = f"Error running script: {e}"
        print(error_msg, file=sys.stderr)
        
        # Add event for failed execution
        _create_event(
            "error",
            "Script execution failed",
            f"{error_msg}\nDuration: {duration:.2f} seconds\nEnd time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            str(e).encode('utf-8')
        )
            
        raise
