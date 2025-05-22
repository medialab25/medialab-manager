from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from typing import Dict, Callable, Any, List, Optional
from dataclasses import dataclass
import asyncio
import logging

from app.api.managers.sync_manager import SyncManager
from app.core.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class TaskConfig:
    task_id: str
    task_type: str
    function_name: str
    hours: Optional[int] = 0
    minutes: Optional[int] = 0
    cron_hour: Optional[str] = "*"
    cron_minute: Optional[str] = "*"
    cron_second: Optional[str] = "*"
    run_date: Optional[datetime] = None
    args: List[Any] = None
    kwargs: Dict[str, Any] = None

    def __post_init__(self):
        if self.args is None:
            self.args = []
        if self.kwargs is None:
            self.kwargs = {}

@dataclass
class Task:
    enabled: bool
    config: TaskConfig

# Create a scheduler instance
scheduler = BackgroundScheduler()

# Dictionary to store registered task functions
task_registry: Dict[str, Callable] = {}

def register_task(name: str, func: Callable) -> None:
    """Register a task function with the scheduler"""
    task_registry[name] = func

def get_task_function(name: str) -> Callable:
    """Get a registered task function by name"""
    if name not in task_registry:
        raise ValueError(f"Task function '{name}' not registered")
    return task_registry[name]

def start_scheduler():
    """Start the scheduler and add default jobs"""
    if not scheduler.running:
        scheduler.start()
        
        # Add tasks from settings
        for task_id, task_data in settings.TASKS.items():
            if task_data.get("enabled", False):
                config = TaskConfig(
                    task_id=task_id,
                    task_type=task_data.get("task_type", "interval"),
                    function_name=task_data.get("function_name", task_id),
                    cron_hour=task_data.get("cron_hour", 0),
                    cron_minute=task_data.get("cron_minute", 0),
                    cron_second=task_data.get("cron_second", 0)
                )
                add_task(task_id, config)

def stop_scheduler():
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()

def add_task(task_id: str, task_config: TaskConfig) -> None:
    """Add a new task to the scheduler"""
    # Get the task function
    task_func = get_task_function(task_config.function_name)
    if not task_func:
        raise ValueError(f"Task function '{task_config.function_name}' not registered")
    
    # Create the appropriate trigger
    if task_config.task_type == "interval":
        trigger = IntervalTrigger(
            hours=task_config.hours,
            minutes=task_config.minutes
        )
    elif task_config.task_type == "cron":
        trigger = CronTrigger(
            hour=task_config.cron_hour,
            minute=task_config.cron_minute,
            second=task_config.cron_second
        )
    elif task_config.task_type == "date":
        if not task_config.run_date:
            raise ValueError("run_date is required for date type tasks")
        trigger = DateTrigger(run_date=task_config.run_date)
    else:
        raise ValueError(f"Invalid task type: {task_config.task_type}")
    
    # Add the job to the scheduler
    scheduler.add_job(
        task_func,
        trigger=trigger,
        id=task_id,
        args=task_config.args,
        kwargs=task_config.kwargs,
        replace_existing=True
    )

def remove_task(task_id: str) -> None:
    """Remove a task from the scheduler"""
    scheduler.remove_job(task_id)

def sync_task():
    """Run the sync task"""
    try:
        logger.info(f"Running sync task at {datetime.now()}")
        sync_manager = SyncManager(settings.MEDIA_LIBRARY)
        
        # Create event loop for async operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the sync operation
        result = loop.run_until_complete(sync_manager.sync())
        loop.close()
        
        logger.info(f"Sync task completed: {result}")
    except Exception as e:
        logger.error(f"Error in sync task: {str(e)}", exc_info=True)

# Register example tasks
register_task("sync", sync_task)

# You can add more task functions here 