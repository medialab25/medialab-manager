import logging
from typing import Optional, List, Dict, NamedTuple
import docker
import os
import socket
from managers.event_manager import event_manager
from managers.task_manager import TaskConfig

logger = logging.getLogger(__name__)

class ContainerInfo(NamedTuple):
    """Container information including backup mode."""
    container_id: str
    backup_mode: Optional[str]

def get_current_container_id() -> Optional[str]:
    """Get the current container ID from hostname."""
    try:
        return socket.gethostname()[:12]
    except Exception:
        logger.error("Failed to get container ID from hostname")
        return None

def get_project_name(client: docker.DockerClient, container_id: str) -> Optional[str]:
    """Get the project name from container labels."""
    try:
        container = client.containers.get(container_id)
        project_name = container.labels.get('com.docker.compose.project')
        if not project_name:
            logger.error("Container is not part of a Docker Compose project")
            return None
        return project_name
    except docker.errors.NotFound:
        logger.error("Container not found")
        return None

def format_container_info(container: docker.models.containers.Container) -> None:
    """Format and log container information."""
    labels = container.labels
    service_name = labels.get('com.docker.compose.service', 'N/A')
    backup_mode = labels.get('medialab-client.backup.mode')
    
    logger.info(f"Container ID: {container.id[:12]}")
    logger.info(f"Name: {container.name}")
    logger.info(f"Status: {container.status}")
    logger.info(f"Image: {container.image.tags[0] if container.image.tags else container.image.id[:12]}")
    logger.info(f"Service: {service_name}")
    logger.info(f"Backup Mode: {backup_mode or 'None'}")
    
    if labels:
        logger.info("\nLabels:")
        for key, value in labels.items():
            logger.info(f"  {key}: {value}")
    
    logger.info("-" * 70)

def get_stack_containers() -> List[ContainerInfo]:
    """Get all containers in the current stack except the current container.
    
    Returns:
        List[ContainerInfo]: List of container information including container IDs and backup modes.
    """
    try:
        client = docker.from_env()
        current_container_id = get_current_container_id()
        
        if not current_container_id:
            return []

        project_name = get_project_name(client, current_container_id)
        if not project_name:
            return []

        # Get and filter containers, explicitly excluding the current container
        project_containers = [
            container for container in client.containers.list(all=True)
            if container.labels.get('com.docker.compose.project') == project_name
            and container.id != current_container_id
            and container.id[:12] != current_container_id  # Also check the short ID
        ]

        if not project_containers:
            logger.warning(f"No other containers found in stack: {project_name}")
            return []

        logger.info(f"\nOther containers in stack: {project_name}")
        logger.info("-" * 70)
        
        container_infos = []
        for container in project_containers:
            # Double check we're not including the current container
            if container.id == current_container_id or container.id[:12] == current_container_id:
                continue
                
            format_container_info(container)
            backup_mode = container.labels.get('medialab-client.backup.mode')
            container_infos.append(ContainerInfo(
                container_id=container.id[:12],
                backup_mode=backup_mode
            ))

        return container_infos

    except docker.errors.DockerException as e:
        logger.error(f"Error connecting to Docker: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return []

async def backup_stacks_task(task_config: Optional[TaskConfig] = None) -> None:
    """Execute a backup stacks task."""
    if not task_config:
        logger.error("No task configuration provided")
        return

    try:
        server_host = os.getenv("SERVER_HOST", "192.168.10.10")
        server_port = os.getenv("SERVER_PORT", "4800")
        logger.info(f"Executing backup stacks task: {task_config.name}")
        logger.info(f"Using server: {server_host}:{server_port}")

        container_infos = get_stack_containers()
        for container_info in container_infos:
            logger.info(f"Container {container_info.container_id} has backup mode: {container_info.backup_mode or 'None'}")

        # TODO: Implement backup logic and event recording
        # await event_manager.record_event(
        #     "backup_stacks_completed",
        #     {
        #         "task_name": task_config.name,
        #         "status": "success",
        #         "server": f"{server_host}:{server_port}",
        #         "description": f"Successfully completed backup stacks task: {task_config.name}"
        #     }
        # )

    except Exception as e:
        logger.error(f"Error executing backup stacks task: {e}")
        # TODO: Implement error event recording
        # await event_manager.record_event(
        #     "backup_stacks_failed",
        #     {
        #         "task_name": task_config.name,
        #         "status": "error",
        #         "server": f"{server_host}:{server_port}",
        #         "description": f"Failed to execute backup stacks task: {task_config.name}",
        #         "error": str(e)
        #     }
        # )

