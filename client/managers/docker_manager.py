import logging
import docker
import socket
import asyncio
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ContainerInfo:
    container_id: str
    needs_backup: bool = False

class DockerManager:
    def __init__(self):
        self.client = docker.from_env()
        self._current_container_id = None

    @property
    def current_container_id(self) -> Optional[str]:
        """Get the current container ID from hostname."""
        if self._current_container_id is None:
            try:
                hostname = os.uname().nodename
                self._current_container_id = hostname
            except Exception as e:
                logger.error(f"Error getting container ID: {e}")
                return None
        return self._current_container_id

    def _get_project_name(self, container_id: str) -> Optional[str]:
        """Get the project name from container labels."""
        try:
            container = self.client.containers.get(container_id)
            return container.labels.get('com.docker.compose.project')
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting project name for container {container_id}: {e}")
            return None

    def _format_container_info(self, container: docker.models.containers.Container) -> None:
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

    def get_stack_containers(self) -> List[ContainerInfo]:
        """Get all containers that are part of the same project as the current container."""
        containers = []
        try:
            current_project = self.get_project_for_current_container()
            if not current_project:
                logger.error("Could not determine current project")
                return containers

            current_container_id = self.current_container_id
            if not current_container_id:
                logger.error("Could not determine current container ID")
                return containers

            logger.info(f"Current container ID: {current_container_id}")
            logger.info(f"Current project: {current_project}")

            for container in self.client.containers.list(all=True):
                # Skip the current container - compare both full ID and short ID
                if container.id == current_container_id or container.id.startswith(current_container_id):
                    logger.info(f"Skipping current container: {container.id}")
                    continue
                    
                # Only include containers from the same project
                if container.labels.get('com.docker.compose.project') == current_project:
                    needs_backup = container.labels.get('medialab-client.full-backup', 'true').lower() != 'false'
                    logger.info(f"Adding container to backup list: {container.id}")
                    containers.append(ContainerInfo(
                        container_id=container.id,
                        needs_backup=needs_backup
                    ))
        except Exception as e:
            logger.error(f"Error getting stack containers: {e}")
        return containers

    async def wait_for_container_status(self, container, status: str, timeout: int = 30) -> bool:
        """Wait for a container to reach a specific status."""
        try:
            for _ in range(timeout):
                container.reload()
                if container.status == status:
                    return True
                await asyncio.sleep(1)
            return False
        except Exception as e:
            logger.error(f"Error waiting for container status: {e}")
            return False

    async def verify_container_health(self, container) -> bool:
        """Verify that a container is healthy after starting."""
        try:
            for _ in range(30):  # 30 second timeout
                container.reload()
                if container.status == "running":
                    health = container.attrs.get('State', {}).get('Health', {}).get('Status')
                    if health == "healthy" or health is None:  # Some containers don't have health checks
                        return True
                await asyncio.sleep(1)
            return False
        except Exception as e:
            logger.error(f"Error verifying container health: {e}")
            return False

    def get_project_for_current_container(self) -> Optional[str]:
        """Get the project name for the current container."""
        container_id = self.current_container_id
        if not container_id:
            logger.error("Could not determine current container ID")
            return None
        return self._get_project_name(container_id) 