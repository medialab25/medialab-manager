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
    task_id: str
    name: str
    description: str
    task_type: str
    function_name: str
    group: str = "other"
    enabled: bool = True
    repo_name: Optional[str] = None
    hours: Optional[int] = 0
    minutes: Optional[int] = 0
    seconds: Optional[int] = 0
    cron_hour: str = "*"
    cron_minute: str = "*"
    cron_second: str = "*"
    params: Optional[Dict] = None
    host_url: str = "http://192.168.10.30:4810"

    def __post_init__(self):
        if self.params is None:
            self.params = {}

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
        self.server_url = os.getenv("SERVER_URL", "http://192.168.10.10:4800")

    async def create_task(self, task: TaskConfig) -> bool:
        """Create a task via the API.
        
        Args:
            task: The task configuration to create
            
        Returns:
            bool: True if task was created successfully, False otherwise
        """
        try:
            import httpx
            
            # Prepare request data based on task type
            request_data = {
                "name": task.name,
                "description": task.description,
                "group": task.group,
                "task_type": task.task_type,
                "enabled": task.enabled,
                "host_url": task.host_url
            }
            
            # Add scheduling information based on task type
            if task.task_type == "interval":
                request_data.update({
                    "hours": task.hours,
                    "minutes": task.minutes,
                    "seconds": task.seconds
                })
            elif task.task_type == "cron":
                cron_data = {
                    "cron_hour": int(task.cron_hour),
                    "cron_minute": int(task.cron_minute),
                    "cron_second": int(task.cron_second)
                }
                logger.info(f"Adding cron data to request: {cron_data}")
                request_data.update(cron_data)
            
            logger.info(f"Task config: {task}")
            logger.info(f"Creating task with data: {request_data}")
            
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        f"{self.server_url}/api/tasks/{task.task_id}/create",
                        json=request_data,
                        timeout=30.0
                    )
                    logger.info(f"Response status: {response.status_code}")
                    logger.info(f"Response body: {response.text}")
                    
                    if response.status_code != 200:
                        logger.error(f"Failed to create task {task.name}: {response.text}")
                        return False
                    logger.info(f"Created task {task.name} via API")
                    return True
                except httpx.RequestError as e:
                    logger.error(f"Request error creating task {task.name}: {str(e)}")
                    return False
                except httpx.TimeoutException as e:
                    logger.error(f"Timeout creating task {task.name}: {str(e)}")
                    return False
                except Exception as e:
                    logger.error(f"Unexpected error creating task {task.name}: {str(e)}")
                    return False
        except Exception as e:
            logger.error(f"Error creating task {task.name}: {str(e)}")
            return False

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

                # Get cron values from environment
                cron_hour = os.getenv("STACK_BACKUP_CRON_HOUR", "0")
                cron_minute = os.getenv("STACK_BACKUP_CRON_MINUTE", "0")
                cron_second = os.getenv("STACK_BACKUP_CRON_SECOND", "0")
                
                logger.info(f"Cron values from env: hour={cron_hour}, minute={cron_minute}, second={cron_second}")

                backup_stacks_task = TaskConfig(
                    task_id=f"backup_stacks_{project_name}",
                    name=f"Backup {project_name} stack",
                    description=f"Automated backup task for {project_name} - backs up all configured stacks",
                    task_type="cron",
                    group="backup",
                    function_name="backup_project_stacks",
                    repo_name=f"{project_name}-stack",
                    cron_hour=cron_hour,
                    cron_minute=cron_minute,
                    cron_second=cron_second,
                    host_url=os.getenv("HOST_URL", "http://192.168.10.30:4810")
                )
                logger.info(f"Created task config with cron values: hour={backup_stacks_task.cron_hour}, minute={backup_stacks_task.cron_minute}, second={backup_stacks_task.cron_second}")
                tasks.append(backup_stacks_task)
            
            return tasks
        except Exception as e:
            logger.error(f"Error loading tasks: {str(e)}")
            return [] 