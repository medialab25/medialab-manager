def dummy_task(message: str = "Hello from dummy task!") -> str:
    """
    A dummy task that prints a message, adds an event, and returns the message.
    
    Args:
        message (str): The message to print and return
        
    Returns:
        str: The input message
    """
    import time
    from app.api.managers.event_manager import EventManager
    from app.models.event_types import EventType, SubEventType
    from app.core.database import get_db
    
    # Get database session
    db = next(get_db())
    event_manager = EventManager(db)
    
    # Add event before task execution
    event_manager.add_event(
        type=EventType.NOTIFY.value,
        sub_type=SubEventType.EMAIL.value,
        status="info",
        description="Starting dummy task execution",
        details=f"Task will process message: {message}"
    )
    
    time.sleep(20)  # Add 20 second delay
    print(f"Executing dummy task with message: {message}")
    
    # Add event after task completion
    event_manager.add_event(
        type=EventType.NOTIFY.value,
        sub_type=SubEventType.EMAIL.value,
        status="success",
        description="Dummy task completed successfully",
        details=f"Processed message: {message}"
    )
    
    return message
