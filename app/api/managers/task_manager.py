from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.settings import settings
from app.models.event_types import SubEventType
from app.scheduler import add_task, remove_task, TaskConfig, run_task_now
from app.api.managers.event_manager import EventManager

class TaskManager:
    def __init__(self, db: Session = None):
        self.db = db
        self.event_manager = EventManager(db=db) if db else None

    def list_tasks(self) -> Dict:
        """List all tasks grouped by their group"""
        tasks = {}
        
        for task_id, task_data in settings.TASKS.items():
            group = task_data.get("group", "other")
            if group not in tasks:
                tasks[group] = []
                
            # Get the last run time for this task
            last_run = self.event_manager.get_last_task_run(task_id) if self.event_manager else None
                
            tasks[group].append({
                "id": task_id,
                "name": task_data.get("name", task_id),
                "description": task_data.get("description", ""),
                "enabled": task_data.get("enabled", False),
                "last_run": last_run.strftime("%Y-%m-%d %H:%M:%S") if last_run else None
            })
        
        return tasks

    def toggle_task(self, task_id: str, enabled: bool) -> Dict:
        """Toggle a task's enabled status"""
        if task_id not in settings.TASKS:
            raise ValueError("Task not found")
        
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

    def run_task(self, task_id: str) -> Dict:
        """Run a task immediately"""
        if task_id not in settings.TASKS:
            raise ValueError("Task not found")
        
        try:
            run_task_now(task_id)
            return {"status": "success", "message": f"Task {task_id} started"}
        except Exception as e:
            raise ValueError(str(e)) 