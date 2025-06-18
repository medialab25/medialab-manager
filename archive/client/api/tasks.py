from fastapi import APIRouter, HTTPException
from typing import Dict, List
import logging
import json
from managers.task_manager import TaskManager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/run/{task_name}")
async def run_task(task_name: str) -> Dict:
    """
    Run a specified task immediately using its configuration from config.json.
    
    Args:
        task_name: The name of the task as defined in config.json
        
    Returns:
        Dict containing the status of the operation
        
    Raises:
        HTTPException: If the task is not found or fails to run
    """
    try:
        # Load all tasks from config
        tasks = load_tasks()
        logger.info(f"Loaded {len(tasks)} tasks from config")
        logger.info(f"Available tasks: {[task.name for task in tasks]}")
        
        # Find the task configuration
        task_config = next((task for task in tasks if task.name == task_name), None)
        if not task_config:
            logger.error(f"Task '{task_name}' not found in configuration")
            raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found in configuration")
            
        logger.info(f"Found task config: {task_config}")
            
        # Get the task function
        task_func = get_task_function(task_config.function_name)
        if not task_func:
            logger.error(f"Task function '{task_config.function_name}' not found")
            raise HTTPException(status_code=404, detail=f"Task function '{task_config.function_name}' not found")
            
        logger.info(f"Found task function: {task_func.__name__}")
            
        # Run the task with its configuration
        await task_func(task_config)
        
        return {
            "status": "success",
            "message": f"Task {task_name} executed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error running task {task_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
