from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
from datetime import datetime

from app.core.database import get_db
from app.core.settings import settings
from app.scheduler import add_task, remove_task, TaskConfig

router = APIRouter()

@router.get("/")
def list_tasks():
    """List all tasks grouped by their group"""
    tasks = {}
    
    for task_id, task_data in settings.TASKS.items():
        group = task_data.get("group", "other")
        if group not in tasks:
            tasks[group] = []
            
        tasks[group].append({
            "id": task_id,
            "name": task_data.get("name", task_id),
            "description": task_data.get("description", ""),
            "enabled": task_data.get("enabled", False),
            "last_run": None  # TODO: Implement last run tracking
        })
    
    return tasks

@router.post("/{task_id}/toggle")
def toggle_task(task_id: str, enabled: bool):
    """Toggle a task's enabled status"""
    if task_id not in settings.TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = settings.TASKS[task_id]
    task_data["enabled"] = enabled
    
    # Update the task in the scheduler
    if enabled:
        config = TaskConfig(
            task_id=task_id,
            task_type=task_data.get("task_type", "interval"),
            function_name=task_data.get("function_name", task_id),
            cron_hour=task_data.get("cron_hour", "*"),
            cron_minute=task_data.get("cron_minute", "*"),
            cron_second=task_data.get("cron_second", "*")
        )
        add_task(task_id, config)
    else:
        remove_task(task_id)
    
    return {"status": "success", "enabled": enabled} 