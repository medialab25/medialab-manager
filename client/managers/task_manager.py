from typing import Dict, List, Callable, Optional
import json
import logging
import os
from tasks.restic_backup import TaskConfig

logger = logging.getLogger(__name__)

# Dictionary to store registered task functions
task_registry: Dict[str, Callable] = {}

def register_task(name: str, func: Callable) -> None:
    """Register a task function with the scheduler"""
    task_registry[name] = func
    logger.info(f"Registered task function: {name}")

def get_task_function(name: str) -> Callable:
    """Get a registered task function by name"""
    if name not in task_registry:
        logger.warning(f"Task function '{name}' not registered")
        return None
    return task_registry[name]

def load_tasks() -> List[TaskConfig]:
    """Load tasks from environment variables"""
    try:
        # Get server configuration from environment variables with defaults
        server_host = os.getenv("SERVER_HOST", "192.168.10.10")
        server_port = os.getenv("SERVER_PORT", "4800")
        restic_server = os.getenv("RESTIC_SERVER", "192.168.10.10:4500")
        
        # Check if stack backup is enabled
        stack_backup_enabled = os.getenv("STACK_BACKUP_ENABLE", "true").lower() == "true"
        
        tasks = []
        
        # Only add backup_stacks task if enabled
        if stack_backup_enabled:
            backup_stacks_task = TaskConfig(
                name="backup_stacks",
                task_type="cron",
                function_name="backup_stacks",
                cron_hour=os.getenv("STACK_BACKUP_CRON_HOURS", "0"),
                cron_minute=os.getenv("STACK_BACKUP_CRON_MINS", "0"),
                cron_second=os.getenv("STACK_BACKUP_CRON_SECS", "0")
            )
            tasks.append(backup_stacks_task)
        
        return tasks
    except Exception as e:
        logger.error(f"Error loading tasks: {e}")
        return [] 