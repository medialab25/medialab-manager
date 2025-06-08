from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import httpx
from urllib.parse import urlparse

from app.core.settings import settings
from app.models.event_types import SubEventType
from app.models.task import Task
from app.scheduler import add_task, remove_task, TaskConfig, run_task_now
from app.api.managers.event_manager import EventManager
from app.utils.time_utils import get_current_time, format_datetime

class TaskManager:
    def __init__(self, db: Session = None):
        self.db = db
        self.event_manager = EventManager(db=db) if db else None

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by its ID.
        
        Args:
            task_id: The ID of the task to retrieve
            
        Returns:
            Optional[Task]: The task if found, None otherwise
        """
        return self.db.query(Task).filter(Task.task_id == task_id).first()

    def create_task(
        self, 
        task_id: str, 
        name: str, 
        description: str, 
        group: str, 
        task_type: str = "external", 
        enabled: bool = True,
        host_url: str = None,
        hours: int = None,
        minutes: int = None,
        seconds: int = None,
        cron_hour: str = None,
        cron_minute: str = None,
        cron_second: str = None
    ) -> Task:
        """
        Create a new task in the database or update an existing one.
        
        Args:
            task_id: Unique identifier for the task
            name: Name of the task
            description: Description of the task
            group: Group the task belongs to
            task_type: Type of task ("interval", "cron", or "external"/"manual")
            enabled: Whether the task is enabled (default: True)
            host_url: Host URL associated with the task (optional)
            hours: Hours for interval scheduling (only used if task_type is "interval")
            minutes: Minutes for interval scheduling (only used if task_type is "interval")
            seconds: Seconds for interval scheduling (only used if task_type is "interval")
            cron_hour: Hour for cron scheduling (only used if task_type is "cron")
            cron_minute: Minute for cron scheduling (only used if task_type is "cron")
            cron_second: Second for cron scheduling (only used if task_type is "cron")
            
        Returns:
            Task: The created or updated task object
        """

        if task_type == "interval":
            task_type = "external_interval"
        elif task_type == "cron":
            task_type = "external_cron"

        # Check if task already exists
        existing_task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if existing_task:
            # Update existing task with new information
            existing_task.name = name
            existing_task.description = description
            existing_task.group = group
            existing_task.task_type = task_type
            existing_task.enabled = enabled
            existing_task.host_url = host_url
            
            # Update scheduling based on task type
            if task_type == "external_interval":
                self._clear_cron_schedule(existing_task)
                self._set_interval_schedule(existing_task, hours, minutes, seconds)
            elif task_type == "external_cron":
                self._clear_interval_schedule(existing_task)
                self._set_cron_schedule(existing_task, cron_hour, cron_minute, cron_second)
            else:
                self._clear_interval_schedule(existing_task)
                self._clear_cron_schedule(existing_task)
            
            self.db.commit()
            return existing_task
        
        # Create new task
        task = Task(
            task_id=task_id,
            name=name,
            description=description,
            group=group,
            enabled=enabled,
            task_type=task_type,
            function_name=task_id,
            host_url=host_url,
            hours=hours if task_type == "interval" else hours,
            minutes=minutes if task_type == "interval" else minutes,
            seconds=seconds if task_type == "interval" else seconds,
            cron_hour=cron_hour if task_type == "cron" else cron_hour,
            cron_minute=cron_minute if task_type == "cron" else cron_minute,
            cron_second=cron_second if task_type == "cron" else cron_second
        )
        
        # Add to database
        self.db.add(task)
        self.db.commit()
        
        return task

    @staticmethod
    def sync_tasks_from_config(db: Session):
        """Sync tasks from config to database on startup"""
        # Get all existing tasks from database
        existing_tasks = {task.task_id: task for task in db.query(Task).all()}
        
        # Get all task IDs from config
        config_task_ids = set(settings.TASKS.keys())
        
        # Create task manager instance for syncing
        task_manager = TaskManager(db)
        
        # Add or update tasks from config
        for task_id, task_data in settings.TASKS.items():
            task_type = task_data.get("task_type", "external")
            
            # Create or update task
            task_manager.create_task(
                task_id=task_id,
                name=task_data.get("name", task_id),
                description=task_data.get("description", ""),
                group=task_data.get("group", "other"),
                task_type=task_type,
                enabled=task_data.get("enabled", False),
                host_url=task_data.get("host_url", None),
                hours=task_data.get("hours", 0),
                minutes=task_data.get("minutes", 0),
                seconds=task_data.get("seconds", 0),
                cron_hour=task_data.get("cron_hour", "*"),
                cron_minute=task_data.get("cron_minute", "*"),
                cron_second=task_data.get("cron_second", "*")
            )

    def list_tasks(self) -> Dict:
        """List all tasks grouped by their group"""
        tasks = {}
        
        db_tasks = self.db.query(Task).all()
        for task in db_tasks:
            group = task.group
            if group not in tasks:
                tasks[group] = []
                
            task_dict = {
                "id": task.task_id,
                "name": task.name,
                "description": task.description,
                "enabled": task.enabled,
                "task_type": task.task_type,
                "host_url": task.host_url,
                "last_start_time": task.last_start_time.strftime("%Y-%m-%d %H:%M:%S") if task.last_start_time else None,
                "last_end_time": task.last_end_time.strftime("%Y-%m-%d %H:%M:%S") if task.last_end_time else None,
                "last_status": task.last_status
            }

            # Add schedule information based on task type
            if task.task_type == "interval" or task.task_type == "external_interval":
                task_dict["hours"] = task.hours
                task_dict["minutes"] = task.minutes
                task_dict["seconds"] = task.seconds
            elif task.task_type == "cron" or task.task_type == "external_cron":
                task_dict["cron_hour"] = task.cron_hour
                task_dict["cron_minute"] = task.cron_minute
                task_dict["cron_second"] = task.cron_second

            tasks[group].append(task_dict)
        
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
            task.last_status = "requested"
            self.db.commit()
            
            # If task has host URL and is external/cron/interval, send request to that host
            if task.host_url and task.task_type in ["external", "external_interval", "external_cron"]:
                try:
                    # Parse the URL properly to handle schemes and ports
                    parsed_url = urlparse(task.host_url)
                    host = parsed_url.hostname
                    port = str(parsed_url.port) if parsed_url.port else "4810"  # Default to 4810 if no port specified
                    
                    # Send request to the task's endpoint
                    with httpx.Client(timeout=30.0) as client:
                        response = client.post(f"http://{host}:{port}/api/tasks/{task_id}/run")
                        if response.status_code != 200:
                            raise ValueError(f"Remote task execution failed: {response.text}")
                except Exception as e:
                    task.last_status = "error"
                    task.last_end_time = datetime.now()
                    self.db.commit()
                    raise ValueError(f"Failed to execute remote task: {str(e)}")
            else:
                # Run task locally
                run_task_now(task_id)
            
            return {"status": "success", "message": f"Task {task_id} started"}
        except Exception as e:
            # Update task status to error
            task.last_status = "error"
            task.last_end_time = datetime.now()
            self.db.commit()
            raise ValueError(str(e))

    def update_task_status(self, task_id: str, status: str) -> None:
        """Update task status and timestamps"""
        task = self.get_task(task_id)
        if task:
            task.last_status = status
            if status == "running":
                task.last_start_time = get_current_time()
            else:
                task.last_end_time = get_current_time()
            self.db.commit()

    def start_task(self, task_id: str, name: str = None, description: str = None, group: str = "other") -> Task:
        """Start a task, creating it if it doesn't exist.
        
        Args:
            task_id: Unique identifier for the task
            name: Name of the task (optional, defaults to task_id if not provided)
            description: Description of the task (optional)
            group: Group the task belongs to (default: "other")
            
        Returns:
            Task: The task object that was started
        """
        task = self.get_task(task_id)
        
        if not task:
            # Create the task if it doesn't exist
            task = self.create_task(
                task_id=task_id,
                name=name or task_id,
                description=description or "",
                group=group
            )
        
        # Update task status to running
        task.last_start_time = datetime.now()
        task.last_status = "running"
        self.db.commit()
        
        return task

    def end_task(self, task_id: str, status: str = "success") -> Task:
        """End a task and update its status.
        
        Args:
            task_id: The ID of the task to end
            status: The final status of the task (default: "success")
            
        Returns:
            Task: The updated task object
            
        Raises:
            ValueError: If the task is not found or status is invalid
        """
        if status not in ["success", "error"]:
            raise ValueError("Status must be either 'success' or 'error'")
            
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
            
        task.last_end_time = datetime.now()
        task.last_status = status
        self.db.commit()
        
        return task

    def get_task_last_run(self, task_id: str) -> dict:
        """Get the last run information for a task"""
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
            
        return {
            "task_id": task.task_id,
            "name": task.name,
            "last_start_time": task.get_formatted_last_start_time(),
            "last_end_time": task.get_formatted_last_end_time(),
            "last_status": task.last_status
        }

    def _clear_interval_schedule(self, task: Task) -> None:
        """Clear interval schedule settings from a task"""
        task.hours = None
        task.minutes = None
        task.seconds = None

    def _clear_cron_schedule(self, task: Task) -> None:
        """Clear cron schedule settings from a task"""
        task.cron_hour = None
        task.cron_minute = None
        task.cron_second = None

    def _set_interval_schedule(self, task: Task, hours: int = None, minutes: int = None, seconds: int = None) -> None:
        """Set interval schedule settings for a task"""
        task.hours = hours
        task.minutes = minutes
        task.seconds = seconds

    def _set_cron_schedule(self, task: Task, cron_hour: str = None, cron_minute: str = None, cron_second: str = None) -> None:
        """Set cron schedule settings for a task"""
        task.cron_hour = cron_hour
        task.cron_minute = cron_minute
        task.cron_second = cron_second 