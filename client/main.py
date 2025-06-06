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
from tasks.restic_backup import TaskConfig, restic_backup_task

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

# Dictionary to store registered task functions
task_registry: Dict[str, Callable] = {}

def register_task(name: str, func: Callable) -> None:
    """Register a task function with the scheduler"""
    task_registry[name] = func
    logger.info(f"Registered task function: {name}")

def get_task_function(name: str) -> Callable:
    """Get a registered task function by name"""
    if name not in task_registry:
        logger.warning(f"Task function '{name}' not registered")
        return None
    return task_registry[name]

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="Client Service", lifespan=lifespan)
app.include_router(health_router)

class HealthResponse(BaseModel):
    status: str
    timestamp: str

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

def load_tasks() -> List[TaskConfig]:
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return [TaskConfig(**task) for task in config.get("tasks", [])]
    except Exception as e:
        logger.error(f"Error loading tasks: {e}")
        return []

async def dummy_task():
    logger.info("Running dummy task")

def setup_scheduler():
    tasks = load_tasks()
    for task in tasks:
        if task.enabled:
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