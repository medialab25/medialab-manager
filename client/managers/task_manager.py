from typing import Dict, List, Callable, Optional
import json
import logging
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
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return [TaskConfig(**task) for task in config.get("tasks", [])]
    except Exception as e:
        logger.error(f"Error loading tasks: {e}")
        return [] 