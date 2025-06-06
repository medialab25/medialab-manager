import logging
from typing import Optional
import docker
import os
import socket
from managers.event_manager import event_manager

from managers.task_manager import TaskConfig

logger = logging.getLogger(__name__)

def get_current_container_id():
    """Get the current container ID from hostname."""
    try:
        # Docker sets the hostname to the container ID by default
        hostname = socket.gethostname()
        # The hostname is the full container ID, but we only need the first 12 characters
        return hostname[:12]
    except:
        return None

def list_project_containers():
    try:
        # Create a Docker client
        client = docker.from_env()
        
        # Get current container ID
        current_container_id = get_current_container_id()
        if not current_container_id:
            logger.error("Could not determine current container ID.")
            return

        # Get current container
        try:
            current_container = client.containers.get(current_container_id)
        except docker.errors.NotFound:
            logger.error("Current container not found.")
            return

        # Get project name from current container's labels
        project_name = current_container.labels.get('com.docker.compose.project')
        if not project_name:
            logger.error("Current container is not part of a Docker Compose project.")
            return

        # Get all containers
        all_containers = client.containers.list(all=True)
        
        # Filter containers by project
        project_containers = [
            container for container in all_containers
            if container.labels.get('com.docker.compose.project') == project_name
        ]

        if not project_containers:
            logger.warning(f"No containers found in project: {project_name}")
            return

        logger.info(f"\nContainers in project: {project_name}")
        logger.info("-" * 70)
        
        # Print container information
        for container in project_containers:
            # Get container labels
            labels = container.labels
            service_name = labels.get('com.docker.compose.service', 'N/A')
            
            # Mark current container
            is_current = container.id == current_container_id
            current_marker = " (current)" if is_current else ""
            
            logger.info(f"Container ID: {container.id[:12]}{current_marker}")
            logger.info(f"Name: {container.name}")
            logger.info(f"Status: {container.status}")
            logger.info(f"Image: {container.image.tags[0] if container.image.tags else container.image.id[:12]}")
            logger.info(f"Service: {service_name}")
            
            # Print all labels if they exist
            if labels:
                logger.info("\nLabels:")
                for key, value in labels.items():
                    logger.info(f"  {key}: {value}")
            
            logger.info("-" * 70)
            

            
    except docker.errors.DockerException as e:
        logger.error(f"Error connecting to Docker: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

async def backup_stacks_task(task_config: Optional[TaskConfig] = None) -> None:
    """Execute a backup stacks task"""
    if not task_config:
        logger.error("No task configuration provided")
        return

    try:
        server_host = os.getenv("SERVER_HOST", "192.168.10.10")
        server_port = os.getenv("SERVER_PORT", "4800")
        logger.info(f"Executing backup stacks task: {task_config.name}")
        logger.info(f"Using server: {server_host}:{server_port}")

        list_project_containers()

        # Create success event
        await event_manager.record_event(
            "backup_stacks_completed",
            {
                "task_name": task_config.name,
                "status": "success",
                "server": f"{server_host}:{server_port}",
                "description": f"Successfully completed backup stacks task: {task_config.name}"
            }
        )

    except Exception as e:
        logger.error(f"Error executing backup stacks task: {e}")
        # Create error event
        await event_manager.record_event(
            "backup_stacks_failed",
            {
                "task_name": task_config.name,
                "status": "error",
                "server": f"{server_host}:{server_port}",
                "description": f"Failed to execute backup stacks task: {task_config.name}",
                "error": str(e)
            }
        )

