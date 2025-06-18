import asyncio
from asyncio.log import logger
import os
from managers.docker_manager import DockerManager
from managers.task_manager import TaskConfig
from typing import Optional, List

RESTIC_PASSWORD = os.getenv("RESTIC_PASSWORD")
RESTIC_REPO = os.getenv("RESTIC_REPO")

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
    
async def perform_backup(source_path: str, project_name: str, backup_paths: List[str]) -> bool:
    """Perform the backup using restic."""
    logger.info(f"**************Performing backup for project {project_name} with source path {source_path} and backup paths {backup_paths}")
    if not backup_paths:
        return True

    # Ensure RESTIC_REPO ends with '/' if it doesn't already
    restic_repo = f"{RESTIC_REPO.rstrip('/')}/{project_name}"

    # Initialize restic repository if needed
    init_cmd = f"restic -r {restic_repo} check --password-file <(echo '{RESTIC_PASSWORD}') || restic -r {restic_repo} init --password-file <(echo '{RESTIC_PASSWORD}')"
    if not await execute_restic_command(init_cmd):
        logger.error("Failed to initialize restic repository")
        return False
    logger.info(f"Initializing restic repository: {init_cmd}")
    
    # Perform backup
    include_args = " ".join(backup_paths)  # Just list the paths directly
    backup_cmd = (
        f"restic -r {restic_repo} backup "
        f"--password-file <(echo '{RESTIC_PASSWORD}') "
        f"{include_args} "
    )

    logger.info(f"Performing backup with command: {backup_cmd}")
    logger.info(f"Source path: {source_path}")
    logger.info(f"Backup paths: {backup_paths}")
    logger.info(f"Restic repo: {restic_repo}")
    logger.info(f"Restic password: {RESTIC_PASSWORD}")
    logger.info(f"Include args: {include_args}")

    return await execute_restic_command(backup_cmd)

async def backup_project_stacks_task(task_config: Optional[TaskConfig] = None) -> None:
    """Execute a backup project stacks task."""
    logger.info(f"Executing backup project stacks task: {task_config.name}")
    logger.info(f"Task configuration: {task_config}")

    if not task_config:
        logger.error("No task configuration provided")
        return

    try:
        logger.info(f"Executing backup stacks task: {task_config.name}")
        server_url = os.getenv("SERVER_URL", "http://192.168.10.10:4800")
        logger.info(f"Using server: {server_url}")

        docker_manager = DockerManager()
        project_name = docker_manager.get_project_for_current_container()

        containers = docker_manager.get_project_containers_by_name(project_name)

        # Remove the current container from the list
        current_container_id = docker_manager.current_container_id
        logger.info(f"Current container ID: {current_container_id}")
        containers = [container for container in containers if not container.container_id.startswith(current_container_id)]
        logger.info(f"Containers after filtering current: {[c.container_name for c in containers]}")

        # Get list of running containers
        running_containers = []
        backup_paths = []
        for container_info in containers:
            try:
                backup_paths.append(f"/stack-data/{project_name}/{container_info.container_name}")
                container = docker_manager.client.containers.get(container_info.container_id)
                logger.info(f"Checking container {container_info.container_name} - Status: {container.status}")
                if container.status == "running" and not container_info.container_id.startswith(current_container_id):
                    running_containers.append(container_info)
            except Exception as e:
                logger.error(f"Error getting container status for {container_info.container_name}: {e}")

        logger.info(f"Running containers: {[c.container_name for c in running_containers]}")

        # Stop the running containers
        for container_info in running_containers:
            try:
                container = docker_manager.client.containers.get(container_info.container_id)
                logger.info(f"Stopping container {container_info.container_name}")
                container.stop()
            except Exception as e:
                logger.error(f"Error stopping container {container_info.container_name}: {e}")

        # Wait for the containers to stop
        for container_info in running_containers:
            try:
                container = docker_manager.client.containers.get(container_info.container_id)
                logger.info(f"Waiting for container {container_info.container_name} to stop")
                await docker_manager.wait_for_container_status(container, "stopped")
            except Exception as e:
                logger.error(f"Error waiting for container {container_info.container_name} to stop: {e}")

        # Backup the container data for all containers in the project using restic
        stack_data_path = f"/stack-data/{project_name}"
        await perform_backup(stack_data_path, project_name, backup_paths)
        logger.info(f"Backup paths: {backup_paths}")

        # Start the running containers
        for container_info in running_containers:
            try:
                container = docker_manager.client.containers.get(container_info.container_id)
                logger.info(f"Starting container {container_info.container_name}")
                container.start()
            except Exception as e:
                logger.error(f"Error starting container {container_info.container_name}: {e}")

    except Exception as e:
        logger.error(f"Error executing backup stacks task: {e}")

