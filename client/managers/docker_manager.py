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
    container_name: str
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

    def get_project_name(self, container_id: str) -> Optional[str]:
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

    def get_project_containers_by_name(self, project_name: str) -> List[ContainerInfo]:
        """Get all containers that are part of the same project as the current container."""
        containers = []
        try:
            for container in self.client.containers.list(all=True):
                if container.labels.get('com.docker.compose.project') == project_name:
                    containers.append(ContainerInfo(container.id, container.name))
            return containers
        except Exception as e:
            logger.error(f"Error getting project containers by name: {e}")
            return []

    def get_project_containers(self, current_container_id: str, include_current: bool = False) -> List[ContainerInfo]:
        """Get all containers that are part of the same project as the current container."""
        containers = []
        try:
            if not current_container_id:
                logger.error("Could not determine current container ID")
                return containers

            project_name = self.get_project_name(current_container_id)
            if not project_name:
                logger.error("Could not determine project name for current container")
                return containers

            for container in self.client.containers.list(all=True):
                if not include_current:
                    # Skip the current container - compare both full ID and short ID
                    if container.id == current_container_id or container.id.startswith(current_container_id):
                        logger.info(f"Skipping current container: {container.id}")
                        continue
                    
                # Only include containers from the same project
                if container.labels.get('com.docker.compose.project') == project_name:
                    needs_backup = container.labels.get('medialab-client.full-backup', 'true').lower() != 'false'
                    containers.append(ContainerInfo(
                        container_id=container.id,
                        container_name=container.name,
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
        return self.get_project_name(container_id) 