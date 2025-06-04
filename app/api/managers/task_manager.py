from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.settings import settings
from app.models.event_types import SubEventType
from app.models.task import Task
from app.scheduler import add_task, remove_task, TaskConfig, run_task_now
from app.api.managers.event_manager import EventManager

class TaskManager:
    def __init__(self, db: Session = None):
        self.db = db
        self.event_manager = EventManager(db=db) if db else None

    @staticmethod
    def sync_tasks_from_config(db: Session):
        """Sync tasks from config to database on startup"""
        # Get all existing tasks from database
        existing_tasks = {task.task_id: task for task in db.query(Task).all()}
        
        # Get all task IDs from config
        config_task_ids = set(settings.TASKS.keys())
        
        # Remove tasks that no longer exist in config
        for task_id in list(existing_tasks.keys()):
            if task_id not in config_task_ids:
                db.delete(existing_tasks[task_id])
        
        # Add or update tasks from config
        for task_id, task_data in settings.TASKS.items():
            if task_id in existing_tasks:
                # Update existing task with config values
                task = existing_tasks[task_id]
                task.name = task_data.get("name", task_id)
                task.description = task_data.get("description", "")
                task.group = task_data.get("group", "other")
                task.task_type = task_data.get("task_type", "interval")
                task.function_name = task_data.get("function_name", task_id)
                task.hours = task_data.get("hours", 0)
                task.minutes = task_data.get("minutes", 0)
                task.seconds = task_data.get("seconds", 0)
                task.cron_hour = task_data.get("cron_hour", "*")
                task.cron_minute = task_data.get("cron_minute", "*")
                task.cron_second = task_data.get("cron_second", "*")
            else:
                # Create new task in database
                task = Task(
                    task_id=task_id,
                    name=task_data.get("name", task_id),
                    description=task_data.get("description", ""),
                    group=task_data.get("group", "other"),
                    enabled=task_data.get("enabled", False),
                    task_type=task_data.get("task_type", "interval"),
                    function_name=task_data.get("function_name", task_id),
                    hours=task_data.get("hours", 0),
                    minutes=task_data.get("minutes", 0),
                    seconds=task_data.get("seconds", 0),
                    cron_hour=task_data.get("cron_hour", "*"),
                    cron_minute=task_data.get("cron_minute", "*"),
                    cron_second=task_data.get("cron_second", "*")
                )
                db.add(task)
        
        db.commit()

    def list_tasks(self) -> Dict:
        """List all tasks grouped by their group"""
        tasks = {}
        
        db_tasks = self.db.query(Task).all()
        for task in db_tasks:
            group = task.group
            if group not in tasks:
                tasks[group] = []
                
            tasks[group].append({
                "id": task.task_id,
                "name": task.name,
                "description": task.description,
                "enabled": task.enabled,
                "task_type": task.task_type,
                "last_start_time": task.last_start_time.strftime("%Y-%m-%d %H:%M:%S") if task.last_start_time else None,
                "last_end_time": task.last_end_time.strftime("%Y-%m-%d %H:%M:%S") if task.last_end_time else None,
                "last_status": task.last_status
            })
        
        return tasks

    def toggle_task(self, task_id: str, enabled: bool) -> Dict:
        """Toggle a task's enabled status"""
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            raise ValueError("Task not found")
        
        # For manual tasks, enabled status is always True
        if task.task_type == "manual":
            enabled = True
        
        task.enabled = enabled
        self.db.commit()
        
        return {"status": "success", "enabled": enabled}

    def run_task(self, task_id: str) -> Dict:
        """Run a task immediately"""
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            raise ValueError("Task not found")
        
        try:
            # Update task status to running
            task.last_start_time = datetime.now()
            task.last_status = "running"
            self.db.commit()
            
            run_task_now(task_id)
            return {"status": "success", "message": f"Task {task_id} started"}
        except Exception as e:
            # Update task status to error
            task.last_status = "error"
            task.last_end_time = datetime.now()
            self.db.commit()
            raise ValueError(str(e))

    def update_task_status(self, task_id: str, status: str) -> None:
        """Update a task's status"""
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            return
        
        task.last_status = status
        if status in ["success", "error"]:
            task.last_end_time = datetime.now()
        
        self.db.commit()

    def get_task_last_run(self, task_id: str) -> Dict:
        """Get the last run information for a task
        
        Args:
            task_id: The ID of the task
            
        Returns:
            Dict: Dictionary containing last run information
        """
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            raise ValueError("Task not found")
            
        return {
            "task_id": task.task_id,
            "name": task.name,
            "last_start_time": task.last_start_time.strftime("%Y-%m-%d %H:%M:%S") if task.last_start_time else None,
            "last_end_time": task.last_end_time.strftime("%Y-%m-%d %H:%M:%S") if task.last_end_time else None,
            "last_status": task.last_status,
            "duration": (task.last_end_time - task.last_start_time).total_seconds() if task.last_end_time and task.last_start_time else None
        } 