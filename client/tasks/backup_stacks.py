import logging
import os
import json
from typing import Dict, Any, List, Optional
import docker
from datetime import datetime
import aiohttp
from managers.event_manager import event_manager
from tasks.restic_backup import TaskConfig

logger = logging.getLogger(__name__)

def get_server_url() -> str:
    """Get the main app server URL from environment variables."""
    server = os.getenv("SERVER_HOST", "192.168.10.10")
    port = os.getenv("SERVER_PORT", "4800")
    return f"http://{server}:{port}"

def get_restic_server() -> str:
    """Get the Restic server URL from environment variables."""
    return os.getenv("RESTIC_SERVER", "192.168.10.10:4500")

class DockerManager:
    def __init__(self):
        # Check if we can access the Docker socket
        socket_path = '/var/run/docker.sock'
        if not os.path.exists(socket_path):
            raise RuntimeError(f"Docker socket not found at {socket_path}")
        
        # Get detailed socket information
        try:
            socket_stat = os.stat(socket_path)
            logger.info(f"Docker socket permissions: {oct(socket_stat.st_mode)}")
            logger.info(f"Docker socket owner: {socket_stat.st_uid}")
            logger.info(f"Docker socket group: {socket_stat.st_gid}")
            
            # Get current process user/group
            import pwd
            import grp
            current_uid = os.getuid()
            current_gid = os.getgid()
            logger.info(f"Current process UID: {current_uid}")
            logger.info(f"Current process GID: {current_gid}")
            
            # Check if we're in the docker group
            try:
                docker_group = grp.getgrnam('docker')
                logger.info(f"Docker group members: {docker_group.gr_mem}")
            except KeyError:
                logger.warning("Docker group not found")
                
        except Exception as e:
            logger.error(f"Error checking socket permissions: {e}")

        if not os.access(socket_path, os.R_OK | os.W_OK):
            raise RuntimeError(f"No permission to access Docker socket at {socket_path}")

        try:
            # Initialize Docker client with explicit configuration
            import docker
            self.client = docker.APIClient(
                base_url=f'unix://{socket_path}',
                version='1.41',
                timeout=30
            )
            
            # Test the connection
            self.client.ping()
            logger.info("Successfully connected to Docker")
            
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise

    def get_stack_containers(self, stack_name: str) -> List[Dict[str, Any]]:
        """Get all containers belonging to a specific stack, excluding the current container."""
        try:
            # Get current container name from environment
            current_container = os.getenv("HOSTNAME")
            
            # Use low-level API to get containers
            containers = self.client.containers(
                filters={"label": f"com.docker.compose.project={stack_name}"}
            )
            return [
                {
                    'id': container['Id'],
                    'name': container['Names'][0].lstrip('/'),  # Remove leading slash
                    'status': container['State']
                }
                for container in containers
                if container['Names'][0].lstrip('/') != current_container  # Exclude current container
            ]
        except Exception as e:
            logger.error(f"Error getting containers for stack {stack_name}: {e}")
            return []

    def get_current_stack_name(self) -> Optional[str]:
        """Get the stack name of the current container using Docker labels."""
        try:
            current_container = os.getenv("HOSTNAME")
            if not current_container:
                logger.error("HOSTNAME environment variable not set")
                return None
                
            # Use low-level API to get container info
            container_info = self.client.inspect_container(current_container)
            labels = container_info['Config']['Labels']
            
            # Docker Compose sets this label for all containers in a stack
            stack_name = labels.get('com.docker.compose.project')
            if not stack_name:
                logger.warning(f"No stack name found in container labels for {current_container}")
                return None
                
            return stack_name
        except Exception as e:
            logger.error(f"Error getting current stack name: {e}")
            return None


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
    except Exception as e:
        logger.error(f"Error executing backup stacks task: {e}")

    try:
        # Notify task start
        #await event_manager.notify_task_start(task_config.task_id)
        
        docker_manager = DockerManager()
        #restic_server = get_restic_server()
        return
        # Get current stack name and then get all containers in that stack
        current_stack = docker_manager.get_current_stack_name()
        if not current_stack:
            logger.error("Could not determine current stack name")
            return
            
        logger.info(f"Found current stack: {current_stack}")
        containers = docker_manager.get_stack_containers(current_stack)
        if not containers:
            logger.warning(f"No containers found for stack: {current_stack}")
            return
            
        logger.info(f"Found {len(containers)} containers in stack {current_stack}:")
        for container in containers:
            logger.info(f"- {container['name']} ({container['status']})")

    except Exception as e:
        error_msg = f"Error executing backup stacks task: {e}"
        logger.error(error_msg)
        #await event_manager.notify_task_error(task_config.task_id, error_msg) 