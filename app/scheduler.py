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
import pytz

# from app.api.managers.sync_manager import SyncManager
from app.core.settings import settings
from app.tasks import backup_opnsense, run_script, run_snapraid, test_task, spindown_disks, sync_data_cloud
from app.tasks.restic_backup import restic_backup
from app.tasks.backup_stacks import backup_stacks
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
scheduler = BackgroundScheduler(
    executors=executors,
    job_defaults=job_defaults,
    timezone=pytz.timezone('Europe/London')
)

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
    """Create a task event in the database and update task status"""
    try:
        # Update task status in database
        from app.core.database import MainSessionLocal
        from app.models.task import Task
        from datetime import datetime
        
        db = MainSessionLocal()
        try:
            task = db.query(Task).filter(Task.task_id == task_id).first()
            if task:
                if status == "started":
                    task.last_start_time = datetime.now()
                elif status in ["success", "error"]:
                    task.last_end_time = datetime.now()
                task.last_status = status
                db.commit()
        finally:
            db.close()
            
        # Create event
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

def task_wrapper(func_task_id: str, func: Callable, default_args: List[Any] = None, default_parameters: Dict[str, Any] = None) -> Callable:
    """Wrapper function that creates events before and after task execution"""
    if default_args is None:
        default_args = []
    if default_parameters is None:
        default_parameters = {}

    def wrapped(*args, **kwargs):
        try:
            # Check if task is enabled in database
            try:
                if args and len(args) > 0:
                    task_id = args[0]
                else:
                    task_id = kwargs.get('task_id', func_task_id)
                    
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
                
            # Notify task start
            create_task_event(task_id, "started")
            
            # Get function signature to check if it accepts arguments
            import inspect
            sig = inspect.signature(func)
            
            # Only merge args/kwargs if the function accepts them
            if len(sig.parameters) > 0:
                # Get task configuration
                task_data = settings.TASKS.get(task_id, {})
                task_params = task_data.get("params", {})
                
                # Merge default args/kwargs with provided ones and task params
                merged_args = list(default_args) + list(args)
                merged_kwargs = {**default_parameters, **task_params, **kwargs}
                
                # Check if the function is a coroutine
                if asyncio.iscoroutinefunction(func):
                    # Create event loop if it doesn't exist
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    # Run the async function
                    result = loop.run_until_complete(func(*merged_args, **merged_kwargs))
                else:
                    # Run the sync function directly
                    result = func(*merged_args, **merged_kwargs)
            else:
                # Function doesn't accept arguments, call it directly
                result = func()
                
            # Notify task success
            create_task_event(task_id, "success")
            return result
        except Exception as e:
            # Notify task error
            create_task_event(task_id, "error")
            logger.error(f"Error in task {task_id}: {str(e)}", exc_info=True)
            raise e
    return wrapped

def register_task(name: str, func: Callable, create_events: bool = True, default_args: List[Any] = None, default_parameters: Dict[str, Any] = None, task_id_prefix: str = None) -> None:
    """Register a task function with the scheduler
    
    Args:
        name: The name of the task
        func: The function to execute
        create_events: Whether to create events for this task
        default_args: Default positional arguments to pass to the task
        default_parameters: Default keyword arguments to pass to the task
        task_id_prefix: Optional prefix for the task ID to allow multiple registrations of the same function
    """
    # Create a unique task ID if prefix is provided
    task_id = f"{task_id_prefix}_{name}" if task_id_prefix else name
    
    # Always wrap with task_wrapper to check enabled status
    task_registry[task_id] = task_wrapper(task_id, func, default_args, default_parameters)

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
            # Skip manual and external tasks
            if task_data.get("task_type") in ["manual", "external"]:
                continue
                
            # Get the task function
            task_func = get_task_function(task_data.get("function_name", task_id))
            if not task_func:
                logger.warning(f"Skipping task '{task_id}' - function '{task_data.get('function_name', task_id)}' not registered")
                continue

            # Create the appropriate trigger based on task type
            task_type = task_data.get("task_type")
            if task_type == "interval":
                trigger = IntervalTrigger(
                    hours=task_data.get("hours", 0),
                    minutes=task_data.get("minutes", 0),
                    seconds=task_data.get("seconds", 0)
                )
            elif task_type == "cron":
                trigger = CronTrigger(
                    hour=task_data.get("cron_hour", "*"),
                    minute=task_data.get("cron_minute", "*"),
                    second=task_data.get("cron_second", "*")
                )
            else:
                logger.warning(f"Invalid task type for task '{task_id}': {task_type}")
                continue

            # Add the job to the scheduler with parameters from config
            scheduler.add_job(
                task_func,
                trigger=trigger,
                id=task_id,
                replace_existing=True,
                args=[task_id],
                kwargs=task_data.get("params", {})  # Use params from config
            )

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
        args=[task_id],  # Always pass task_id as first argument
        kwargs=task_config.kwargs  # Pass all other parameters as kwargs
    )

def remove_task(task_id: str) -> None:
    """Remove a task from the scheduler"""
    scheduler.remove_job(task_id)

def run_task_now(task_id: str) -> None:
    """Run a task immediately"""
    # Check if task is external
    task_data = settings.TASKS.get(task_id)
    if task_data and task_data.get("task_type") == "external":
        raise ValueError(f"Cannot run external task '{task_id}' directly")

    function_name = task_data.get("function_name", task_id) if task_data else task_id
    task_func = get_task_function(function_name)
    if not task_func:
        raise ValueError(f"Task function '{function_name}' not registered")

    # Get parameters from task configuration
    params = task_data.get("params", {}) if task_data else {}
    
    # Run the task with parameters
    task_func(task_id, **params)  # Pass task_id and parameters

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
register_task("test_task", test_task.dummy_task, create_events=False)  # Register once, used by multiple config entries
register_task("spindown_disks", spindown_disks.spindown_disks)
register_task("sync_data_cloud", sync_data_cloud.sync_data_cloud)
register_task("backup_opnsense", backup_opnsense.backup_opnsense)
register_task("run_script", run_script.run_script_task)
register_task("run_media_systems_script", run_script.run_media_systems_script_task)
register_task("restic_backup", restic_backup)
register_task("backup_stacks", backup_stacks)

# You can add more task functions here 