from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, List, Callable
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import logging
from contextlib import asynccontextmanager
from api.health import router as health_router
from api.tasks import router as tasks_router
from tasks.restic_backup import TaskConfig, restic_backup_task
from tasks.backup_stacks import backup_stacks_task
from managers.task_manager import register_task, get_task_function, load_tasks
from managers.event_manager import event_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_scheduler()
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

def setup_scheduler():
    tasks = load_tasks()
    for task in tasks:
        task_func = get_task_function(task.function_name)
        if not task_func:
            logger.warning(f"Task function '{task.function_name}' not found for task {task.name}")
            continue

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

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat()
    )

# Register available tasks
register_task("dummy_task", dummy_task)
register_task("restic_backup", restic_backup_task)
register_task("backup_stacks", backup_stacks_task) 