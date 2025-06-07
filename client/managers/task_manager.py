from typing import Dict, List, Callable, Optional
import json
import logging
import os
import socket
from dataclasses import dataclass
from managers.docker_manager import DockerManager
import docker

logger = logging.getLogger(__name__)

# Global task registry
_task_registry: Dict[str, Callable] = {}

@dataclass
class TaskConfig:
    """Configuration for a task."""
    name: str
    description: str
    task_type: str
    function_name: str
    repo_name: Optional[str] = None
    cron_hour: str = "*"
    cron_minute: str = "*"
    cron_second: str = "*"

def register_task(task_name: str, task_func: Callable) -> None:
    """Register a task function with the given name."""
    _task_registry[task_name] = task_func
    logger.info(f"Registered task: {task_name}")

def get_task_function(task_name: str) -> Optional[Callable]:
    """Get a registered task function by name."""
    return _task_registry.get(task_name)

def load_tasks() -> List[TaskConfig]:
    """Load tasks from environment variables."""
    task_manager = TaskManager()
    return task_manager.load_tasks()

class TaskManager:
    def __init__(self):
        """Initialize the task manager"""
        self.docker_manager = DockerManager()

    def load_tasks(self) -> List[TaskConfig]:
        """Load tasks from environment variables"""
        try:
            # Check if stack backup is enabled
            stack_backup_enabled = os.getenv("STACK_BACKUP_ENABLE", "true").lower() == "true"
            
            tasks = []

            # Only add backup_stacks task if enabled
            if stack_backup_enabled:
                project_name = self.docker_manager.get_project_for_current_container()
                if not project_name:
                    logger.error("Could not determine project name for current container")
                    return []
                
                logger.info(f"Project name for current container: {project_name}")

                backup_stacks_task = TaskConfig(
                    name=f"Backup {project_name} stack",
                    description=f"Automated backup task for {project_name} - backs up all configured stacks",
                    task_type="cron",
                    function_name="backup_stacks",
                    repo_name=f"{project_name}-stack",
                    cron_hour=os.getenv("STACK_BACKUP_CRON_HOURS", "0"),
                    cron_minute=os.getenv("STACK_BACKUP_CRON_MINS", "0"),
                    cron_second=os.getenv("STACK_BACKUP_CRON_SECS", "0")
                )
                tasks.append(backup_stacks_task)
            
            return tasks
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            return [] 