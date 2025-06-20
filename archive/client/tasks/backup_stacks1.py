import logging
from typing import Optional, List
import docker
import os
import aiohttp
from managers.event_manager import event_manager
from managers.task_manager import TaskConfig
from managers.docker_manager import DockerManager
import asyncio
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

# Environment variables for restic configuration
RESTIC_PATH = os.getenv("RESTIC_PATH")
RESTIC_REPO = os.getenv("RESTIC_REPO")
RESTIC_PASSWORD = os.getenv("RESTIC_PASSWORD")

if not all([RESTIC_PATH, RESTIC_REPO, RESTIC_PASSWORD]):
    raise ValueError("Missing required environment variables: RESTIC_PATH, RESTIC_REPO, or RESTIC_PASSWORD")

async def execute_restic_command(cmd: str) -> bool:
    """Execute a restic command and verify its success."""
    import subprocess
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Restic command failed: {stderr.decode()}")
            return False
            
        logger.info(f"Restic command output: {stdout.decode()}")
        return True
    except Exception as e:
        logger.error(f"Error executing restic command: {str(e)}")
        return False

async def prepare_containers(docker_manager: DockerManager, project_name: str) -> tuple[List[str], List[str], List[str]]:
    """Prepare containers for backup by stopping them if needed."""
    container_infos = docker_manager.get_project_containers(project_name)
    logger.info(f"Container infos: {container_infos}")

    backup_paths = []
    backup_tags = []
    running_containers = []

    for container_info in container_infos:
        if container_info.needs_backup:
            try:
                container = docker_manager.client.containers.get(container_info.container_id)
                if container.status == "running":
                    logger.info(f"Stopping container {container_info.container_id}")
                    container.stop()
                    if not await docker_manager.wait_for_container_status(container, "exited", timeout=30):
                        logger.error(f"Container {container_info.container_id} failed to stop within timeout")
                        continue
                    running_containers.append(container_info.container_id)
                
                container_name = container.name.lstrip('/')
                
                backup_paths.extend([
                    os.path.join(RESTIC_PATH, project_name),
                    os.path.join(RESTIC_PATH, project_name, container_name)
                ])
                
                backup_tags.extend([
                    f"--tag container:{container_info.container_id}",
                    f"--tag project:{project_name}",
                    f"--tag service:{container.labels.get('com.docker.compose.service', 'unknown')}"
                ])
                
            except docker.errors.NotFound:
                logger.warning(f"Container {container_info.container_id} not found")
            except Exception as e:
                logger.error(f"Error preparing container {container_info.container_id}: {e}")

    return backup_paths, backup_tags, running_containers

async def perform_backup(backup_paths: List[str], backup_tags: List[str]) -> bool:
    """Perform the backup using restic."""
    if not backup_paths:
        return True

    # Initialize restic repository if needed
    init_cmd = f"restic -r {RESTIC_REPO} check --password-file <(echo '{RESTIC_PASSWORD}') || restic -r {RESTIC_REPO} init --password-file <(echo '{RESTIC_PASSWORD}')"
    if not await execute_restic_command(init_cmd):
        logger.error("Failed to initialize restic repository")
        return False
    
    # Perform backup
    include_args = " ".join(f"--include {path}" for path in backup_paths)
    backup_cmd = (
        f"restic -r {RESTIC_REPO} backup {RESTIC_PATH} "
        f"--password-file <(echo '{RESTIC_PASSWORD}') "
        f"{include_args} "
        f"{' '.join(backup_tags)}"
    )
    return await execute_restic_command(backup_cmd)

async def restart_containers(docker_manager: DockerManager, running_containers: List[str]) -> bool:
    """Restart containers that were previously running."""
    success = True
    for container_id in running_containers:
        try:
            container = docker_manager.client.containers.get(container_id)
            if container.status != "running":
                logger.info(f"Restarting container {container_id}")
                container.start()
                if not await docker_manager.verify_container_health(container):
                    logger.error(f"Container {container_id} failed health check after restart")
                    success = False
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found during restart")
        except Exception as e:
            logger.error(f"Error restarting container {container_id}: {e}")
            success = False
    return success

async def notify_server(task_config: TaskConfig, backup_success: bool, server_url: str) -> None:
    """Notify the server about the backup status"""
    try:
        endpoint = "success" if backup_success else "failure"
        data = {
            "task": task_config.name,
            "status": "success" if backup_success else "failure",
            "server": server_url,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{server_url}/api/backup/{task_config.name}/{endpoint}",
                json=data,
            )
            response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to notify server: {e}")

async def backup_stacks_task(task_config: Optional[TaskConfig] = None) -> None:
    """Execute a backup stacks task."""
    if not task_config:
        logger.error("No task configuration provided")
        return

    try:
        logger.info(f"Executing backup stacks task: {task_config.name}")
        server_url = os.getenv("SERVER_URL", "http://192.168.10.10:4800")
        logger.info(f"Using server: {server_url}")

        docker_manager = DockerManager()
        project_name = docker_manager.get_project_for_current_container()

        backup_paths, backup_tags, running_containers = await prepare_containers(docker_manager, project_name)
#        backup_success = await perform_backup(backup_paths, backup_tags)
#        restart_success = await restart_containers(docker_manager, running_containers)
        
#        final_success = backup_success and restart_success
#        await notify_server(task_config, final_success, server_url)

    except Exception as e:
        logger.error(f"Error executing backup stacks task: {e}")
        await notify_server(task_config, False, server_url)

