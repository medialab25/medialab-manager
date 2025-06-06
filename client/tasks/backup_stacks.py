import logging
from typing import Optional, List, Dict, NamedTuple
import docker
import os
import socket
from managers.event_manager import event_manager
from managers.task_manager import TaskConfig

logger = logging.getLogger(__name__)

# Environment variables for restic configuration
RESTIC_PATH = os.getenv("RESTIC_PATH", "/data")
RESTIC_REPO = os.getenv("RESTIC_REPO", "rest:http://rest-server:8000/backup")
RESTIC_PASSWORD = os.getenv("RESTIC_PASSWORD", "media")

class ContainerInfo(NamedTuple):
    """Container information including backup status."""
    container_id: str
    needs_backup: bool

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
    needs_backup = labels.get('medialab-client.full-backup', 'true').lower() != 'false'
    
    logger.info(f"Container ID: {container.id[:12]}")
    logger.info(f"Name: {container.name}")
    logger.info(f"Status: {container.status}")
    logger.info(f"Image: {container.image.tags[0] if container.image.tags else container.image.id[:12]}")
    logger.info(f"Service: {service_name}")
    logger.info(f"Needs Backup: {needs_backup}")
    
    if labels:
        logger.info("\nLabels:")
        for key, value in labels.items():
            logger.info(f"  {key}: {value}")
    
    logger.info("-" * 70)

def get_stack_containers() -> List[ContainerInfo]:
    """Get all containers in the current stack except the current container.
    
    Returns:
        List[ContainerInfo]: List of container information including container IDs and backup status.
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
            needs_backup = container.labels.get('medialab-client.full-backup', 'true').lower() != 'false'
            
            container_infos.append(ContainerInfo(
                container_id=container.id[:12],
                needs_backup=needs_backup
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

        client = docker.from_env()
        container_infos = get_stack_containers()
        
        # Track containers that were running
        running_containers = []
        backup_paths = []
        backup_tags = []
        
        # First, check and stop running containers
        for container_info in container_infos:
            if container_info.needs_backup:
                try:
                    container = client.containers.get(container_info.container_id)
                    if container.status == "running":
                        logger.info(f"Stopping container {container_info.container_id}")
                        container.stop()
                        running_containers.append(container_info.container_id)
                    
                    project_name = container.labels.get('com.docker.compose.project', 'unknown')
                    container_name = container.name.lstrip('/')  # Remove leading slash if present
                    
                    # Add paths to backup
                    backup_paths.extend([
                        os.path.join(RESTIC_PATH, project_name),
                        os.path.join(RESTIC_PATH, project_name, container_name)
                    ])
                    
                    # Add tags for this container
                    backup_tags.extend([
                        f"--tag container:{container_info.container_id}",
                        f"--tag project:{project_name}",
                        f"--tag service:{container.labels.get('com.docker.compose.service', 'unknown')}"
                    ])
                    
                except docker.errors.NotFound:
                    logger.warning(f"Container {container_info.container_id} not found")
                except Exception as e:
                    logger.error(f"Error preparing container {container_info.container_id}: {e}")

        # Perform single backup for all containers if we have any to backup
        if backup_paths:
            # Log the restic init command (if needed)
            init_cmd = f"restic -r {RESTIC_REPO} check --password-file <(echo '{RESTIC_PASSWORD}') || restic -r {RESTIC_REPO} init --password-file <(echo '{RESTIC_PASSWORD}')"
            logger.info(f"Restic init command (if needed): {init_cmd}")
            
            # Log the restic backup command
            include_args = " ".join(f"--include {path}" for path in backup_paths)
            backup_cmd = (
                f"restic -r {RESTIC_REPO} backup {RESTIC_PATH} "
                f"--password-file <(echo '{RESTIC_PASSWORD}') "
                f"{include_args} "
                f"{' '.join(backup_tags)}"
            )
            logger.info(f"Restic backup command: {backup_cmd}")

        # Restart containers that were previously running
        for container_id in running_containers:
            try:
                container = client.containers.get(container_id)
                if container.status != "running":
                    logger.info(f"Restarting container {container_id}")
                    container.start()
            except docker.errors.NotFound:
                logger.warning(f"Container {container_id} not found during restart")
            except Exception as e:
                logger.error(f"Error restarting container {container_id}: {e}")

        # Record successful completion
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

