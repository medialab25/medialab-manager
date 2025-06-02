from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, Callable, Any, List, Optional
from dataclasses import dataclass
import asyncio
import logging

# from app.api.managers.sync_manager import SyncManager
from app.core.settings import settings
from app.tasks import run_snapraid, test_task, spindown_disks
from app.utils.event_utils import EventManagerUtil
from app.models.event_types import EventType, SubEventType

logger = logging.getLogger(__name__)

# Configure executors
executors = {
    'default': ThreadPoolExecutor(max_workers=5)  # Adjust this number based on your needs
}

# Configure job defaults
job_defaults = {
    'coalesce': True,  # Combine multiple waiting executions
    'max_instances': 1  # Allow up to 1 concurrent executions of the same task
}

# Create a scheduler instance with custom executors and job defaults
scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults)

@dataclass
class TaskConfig:
    task_id: str
    task_type: str
    function_name: str
    hours: Optional[int] = 0
    minutes: Optional[int] = 0
    seconds: Optional[int] = 0
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

# Dictionary to store registered task functions
task_registry: Dict[str, Callable] = {}

def create_task_event(task_id: str, status: str = "started") -> None:
    """Create a task event in the database"""
    try:
        with EventManagerUtil.get_event_manager() as event_manager:
            event_manager.add_event(
                type=EventType.TASK,
                sub_type=task_id,
                status=status,
                description=f"Task {task_id} {status}",
                details=f"Task {task_id} {status} at {datetime.now()}"
            )
    except Exception as e:
        logger.error(f"Error creating task event: {str(e)}", exc_info=True)

def task_wrapper(task_id: str, func: Callable) -> Callable:
    """Wrapper function that creates events before and after task execution"""
    def wrapped(*args, **kwargs):
        try:
            # Check if task is enabled in database
            try:
                from app.core.database import MainSessionLocal
                db = MainSessionLocal()
                from app.models.task import Task
                task = db.query(Task).filter(Task.task_id == task_id).first()
                db.close()
                
                if not task or not task.enabled:
                    logger.info(f"Skipping disabled task: {task_id}")
                    return
            except Exception as e:
                logger.error(f"Error checking task status in database: {str(e)}")
                return
                
            create_task_event(task_id)
            # Check if the function is a coroutine
            if asyncio.iscoroutinefunction(func):
                # Create event loop if it doesn't exist
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                # Run the async function
                result = loop.run_until_complete(func(*args, **kwargs))
            else:
                # Run the sync function directly
                result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Error in task {task_id}: {str(e)}", exc_info=True)
            raise e
    return wrapped

def register_task(name: str, func: Callable, create_events: bool = True) -> None:
    """Register a task function with the scheduler"""
    # Always wrap with task_wrapper to check enabled status
    task_registry[name] = task_wrapper(name, func)

def get_task_function(name: str) -> Callable:
    """Get a registered task function by name"""
    if name not in task_registry:
        logger.warning(f"Task function '{name}' not registered")
        return None
    return task_registry[name]

def start_scheduler():
    """Start the scheduler and add default jobs"""
    if not scheduler.running:
        scheduler.start()
        # Add tasks from settings
        for task_id, task_data in settings.TASKS.items():
            # Skip manual tasks
            if task_data.get("task_type") == "manual":
                continue
                
            config = TaskConfig(
                task_id=task_id,
                task_type=task_data.get("task_type", "interval"),
                function_name=task_data.get("function_name", task_id),
                hours=task_data.get("hours", 0),
                minutes=task_data.get("minutes", 0),
                seconds=task_data.get("seconds", 0),
                cron_hour=task_data.get("cron_hour", "*"),
                cron_minute=task_data.get("cron_minute", "*"),
                cron_second=task_data.get("cron_second", "*")
            )
            add_task(task_id, config)

def stop_scheduler():
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()

def add_task(task_id: str, task_config: TaskConfig) -> None:
    """Add a task to the scheduler"""
    task_func = get_task_function(task_config.function_name)
    if not task_func:
        logger.warning(f"Skipping task '{task_id}' - function '{task_config.function_name}' not registered")
        return

    # Create the appropriate trigger based on task type
    if task_config.task_type == "interval":
        trigger = IntervalTrigger(
            hours=task_config.hours,
            minutes=task_config.minutes,
            seconds=task_config.seconds
        )
    elif task_config.task_type == "cron":
        trigger = CronTrigger(
            hour=task_config.cron_hour,
            minute=task_config.cron_minute,
            second=task_config.cron_second
        )
    elif task_config.task_type == "date":
        if not task_config.run_date:
            raise ValueError("run_date is required for date tasks")
        trigger = DateTrigger(run_date=task_config.run_date)
    else:
        raise ValueError(f"Invalid task type: {task_config.task_type}")

    # Add the job to the scheduler
    scheduler.add_job(
        task_func,  # Use the already wrapped function
        trigger=trigger,
        id=task_id,
        replace_existing=True,
        args=task_config.args,
        kwargs=task_config.kwargs
    )

def remove_task(task_id: str) -> None:
    """Remove a task from the scheduler"""
    scheduler.remove_job(task_id)

def run_task_now(task_id: str) -> None:
    """Run a task immediately"""
    task_func = get_task_function(task_id)
    if not task_func:
        raise ValueError(f"Task function '{task_id}' not registered")
    
    task_func()  # The function is already wrapped with enabled check

def sync_task():
    """Run the sync task"""
    try:
        logger.info(f"Running sync task at {datetime.now()}")
        # sync_manager = SyncManager(settings.MEDIA_LIBRARY)
        
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
register_task("snapraid", run_snapraid.run_snapraid)
register_task("test_task", test_task.dummy_task, create_events=False)
register_task("spindown_disks", spindown_disks.spindown_disks)

# You can add more task functions here 