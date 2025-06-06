import logging
import os
import json
from typing import Dict, Any, List, Optional
import docker
from datetime import datetime
import aiohttp
from managers.event_manager import event_manager

logger = logging.getLogger(__name__)

def get_server_url() -> str:
    """Get the main app server URL from the config file."""
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            server = config.get("server", {}).get("host", "192.168.10.10")
            port = config.get("server", {}).get("port", "4800")
            return f"http://{server}:{port}"
    except Exception as e:
        logger.error(f"Error loading server URL from config: {e}")
        return "http://192.168.10.10:4800"  # Fallback to default

def get_restic_server() -> str:
    """Get the Restic server URL from the config file."""
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return config.get("restic", {}).get("server", "192.168.10.10:4500")
    except Exception as e:
        logger.error(f"Error loading restic server URL from config: {e}")
        return "192.168.10.10:4500"  # Fallback to default

class TaskConfig:
    def __init__(self, config: Dict[str, Any]):
        self.stacks = config.get("stacks", [])  # List of stack names to backup
        self.backup_path = config.get("backup_path")  # Base path where backups will be stored
        self.repo_name = config.get("repo_name")  # Repository name on the REST server
        self.password = config.get("password", "media")  # Password for the restic repository
        self.additional_args = config.get("additional_args", [])  # Additional arguments for restic

class DockerManager:
    def __init__(self):
        self.client = docker.from_env()
        self.api_client = docker.APIClient()

    def get_stack_containers(self, stack_name: str) -> List[Dict[str, Any]]:
        """Get all containers belonging to a specific stack."""
        try:
            containers = self.client.containers.list(
                filters={"label": f"com.docker.compose.project={stack_name}"}
            )
            return [
                {
                    'id': container.id,
                    'name': container.name,
                    'status': container.status
                }
                for container in containers
            ]
        except Exception as e:
            logger.error(f"Error getting containers for stack {stack_name}: {e}")
            return []

    def stop_containers(self, containers: List[Dict[str, Any]]) -> None:
        """Stop the specified containers."""
        for container_info in containers:
            try:
                container = self.client.containers.get(container_info['id'])
                logger.info(f"Stopping container: {container.name}")
                container.stop()
            except Exception as e:
                logger.error(f"Error stopping container {container_info['id']}: {e}")
                raise

    def start_containers(self, containers: List[Dict[str, Any]]) -> None:
        """Start the specified containers."""
        for container_info in containers:
            try:
                container = self.client.containers.get(container_info['id'])
                logger.info(f"Starting container: {container.name}")
                container.start()
            except Exception as e:
                logger.error(f"Error starting container {container_info['id']}: {e}")
                raise

async def backup_stacks_task(task_id: str, config: Dict[str, Any]) -> None:
    """
    Execute a stack backup task.
    
    Args:
        task_id: The ID of the task being executed
        config: Task configuration dictionary containing:
            - stacks: List of stack names to backup
            - backup_path: Base path where backups will be stored
            - repo_name: Repository name on the REST server
            - password: Password for the restic repository
            - additional_args: Additional arguments for restic
    """
    task_config = TaskConfig(config)
    
    # Validate required parameters
    if not task_config.stacks:
        error_msg = "Missing required parameter: stacks"
        logger.error(error_msg)
        await event_manager.notify_task_error(task_id, error_msg)
        return

    if not task_config.backup_path or not task_config.repo_name:
        error_msg = "backup_path and repo_name are required parameters"
        logger.error(error_msg)
        await event_manager.notify_task_error(task_id, error_msg)
        return

    # Notify task start
    await event_manager.notify_task_start(task_id)
    
    docker_manager = DockerManager()
    restic_server = get_restic_server()
    
    for stack in task_config.stacks:
        try:
            # Create stack-specific paths
            repo_url = f"rest:http://{restic_server}/{task_config.repo_name}/{stack}"
            backup_path = os.path.join(task_config.backup_path, stack)
            
            # Create backup directory if it doesn't exist
            os.makedirs(backup_path, exist_ok=True)
            
            logger.info(f"Starting backup for stack: {stack}")
            await event_manager.notify_task_start(task_id)

            # Get running containers for this stack
            containers = docker_manager.get_stack_containers(stack)
            if not containers:
                logger.warning(f"No containers found for stack: {stack}")
                continue

            # Stop containers
            logger.info(f"Stopping containers for {stack}...")
            docker_manager.stop_containers(containers)
            
            try:
                # Prepare backup data
                backup_data = {
                    "stack": stack,
                    "containers": containers,
                    "backup_path": backup_path,
                    "repo_url": repo_url,
                    "password": task_config.password,
                    "additional_args": task_config.additional_args,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Send backup request to server
                server_url = get_server_url()
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{server_url}/api/backup/execute-stack",
                        json=backup_data
                    ) as response:
                        if response.status != 200:
                            error_msg = f"Backup request failed with status {response.status}"
                            logger.error(error_msg)
                            raise Exception(error_msg)
                        
                        result = await response.json()
                        logger.info(f"Backup completed for stack {stack}: {result}")
                
            finally:
                # Always try to start containers back up
                logger.info(f"Starting containers for {stack}...")
                docker_manager.start_containers(containers)
            
            logger.info(f"Backup completed for stack: {stack}")
            
        except Exception as e:
            error_msg = f"Error backing up stack {stack}: {str(e)}"
            logger.error(error_msg)
            await event_manager.notify_task_error(task_id, error_msg)
            
            # Try to start containers if they were stopped
            if containers:
                try:
                    logger.info(f"Attempting to start containers for {stack} after error...")
                    docker_manager.start_containers(containers)
                except Exception as start_error:
                    logger.error(f"Failed to start containers after error: {start_error}")

    await event_manager.notify_task_end(task_id) 