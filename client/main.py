from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional, Dict, List, Callable
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import logging
from contextlib import asynccontextmanager
from api.health import router as health_router
from api.tasks import router as tasks_router
from tasks.backup_project_stacks import backup_project_stacks_task
from managers.task_manager import TaskConfig, TaskManager, register_task, get_task_function, load_tasks
from managers.event_manager import event_manager
import pytz
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set default timezone
os.environ['TZ'] = 'Europe/London'
timezone = pytz.timezone('Europe/London')

# Create scheduler with timezone configuration
scheduler = AsyncIOScheduler(timezone=timezone)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()
    await event_manager.close()

app = FastAPI(title="Client Service", lifespan=lifespan)
app.include_router(health_router)
app.include_router(tasks_router, prefix="/api/tasks", tags=["tasks"])

class HealthResponse(BaseModel):
    status: str
    timestamp: str

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

async def dummy_task(task_config: Optional[TaskConfig] = None):
    logger.info("Running dummy task")
    if task_config:
        logger.info(f"Task configuration: {task_config}")
        await event_manager.record_event(
            "dummy_task_executed",
            {
                "task_name": task_config.name,
                "task_type": task_config.task_type
            }
        )

async def setup_scheduler():
    tasks = load_tasks()
    task_manager = TaskManager()
    
    for task in tasks:
        task_func = get_task_function(task.function_name)
        if not task_func:
            logger.warning(f"Task function '{task.function_name}' not found for task {task.name}")
            continue

        # Create task via API
        try:
            # Create the task
            await task_manager.create_task(task)

            # Create the appropriate trigger based on task type
            if task.task_type == "interval":
                trigger = IntervalTrigger(
                    hours=task.hours,
                    minutes=task.minutes,
                    seconds=task.seconds
                )
            elif task.task_type == "cron":
                trigger = CronTrigger(
                    hour=task.cron_hour,
                    minute=task.cron_minute,
                    second=task.cron_second
                )
            else:
                logger.warning(f"Invalid task type for task '{task.name}': {task.task_type}")
                continue

            # Add the job to the scheduler
            scheduler.add_job(
                task_func,
                trigger=trigger,
                id=task.name,
                args=[task],
                replace_existing=True
            )
            logger.info(f"Scheduled task: {task.name} using function {task.function_name}")
        except Exception as e:
            logger.error(f"Error setting up task {task.name}: {str(e)}")

# Register available tasks
register_task("backup_project_stacks", backup_project_stacks_task) 