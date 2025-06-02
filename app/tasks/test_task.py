import subprocess
import sys
import time
from app.utils.file_utils import AttachDataMimeType
from app.utils.event_utils import EventManagerUtil


def dummy_task(message: str = "Hello from dummy task!") -> str:
    """
    A dummy task that prints a message, adds an event, and returns the message.
    
    Args:
        message (str): The message to print and return
        
    Returns:
        str: The input message
    """
    # Add event before task execution
#    with EventManagerUtil.get_event_manager() as event_manager:
#        event_manager.add_event(
#            type="notify",
#            sub_type="email",
#            status="info",#
#            description="Starting dummy task execution",
#            details=f"Task will process message: {message}"
#        )
    
   # time.sleep(20)  # Add 20 second delay
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
    except subprocess.CalledProcessError as e:
        print(f"Error running cat command: {e}", file=sys.stderr)

    # Add event after task completion
#    with EventManagerUtil.get_event_manager() as event_manager:
 #       event_manager.add_event_with_output(
  #          type="notify",
   #         sub_type="email",
    #        status="success",
     #       description="Dummy task completed successfully",
      #      details=f"Processed message: {message}",
       #     attachment_data=cat_result.stdout.encode('utf-8'),  # Convert string to bytes
        #    attachment_mime_type=AttachDataMimeType.TEXT
        #)
    
    return message
