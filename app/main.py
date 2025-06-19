import os
from fastapi import FastAPI, Request, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import logging
import sys
import uvicorn
import argparse
from sqlalchemy.orm import Session
from urllib.parse import urlencode, parse_qs
from logging.handlers import RotatingFileHandler
import json
from typing import Optional

from app.core.settings import settings
from app.core.database import engine, Base, get_db, MainBase, main_engine, MediaBase, media_engine
from app.api.routers.notify import router as notification_router
from app.api.routers.event import router as event_router
from app.api.routers.tasks import router as tasks_router
from app.api.routers.backup import router as backup_router
from app.api.routers.main_routes import router as main_routes_router
from app.views import router as views_router
#from app.api.routers.media import router as media_router
#from app.api.routers.search import router as search_router
#from app.api.routers.cache import router as cache_router
#from app.api.routers.sync import router as sync_router
#from app.api.routers.system import router as system_router
from app.scheduler import start_scheduler, stop_scheduler
from app.schemas.event import EventFilter
from app.models.event import Event
from app.api.managers.event_manager import EventManager
from app.models.event_types import EventType, SubEventType

# Configure logging
logger = logging.getLogger(__name__)

# Use the log file path from settings
log_file_path = str(settings.LOG_FILE)

# Create the log directory if it doesn't exist, but if permissions fail create a log file in the current users home directory
log_dir = Path(log_file_path).parent
if not log_dir.exists():
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        log_file_path = os.path.expanduser('~/medialab-manager.log')

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(
            log_file_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,  # Keep 5 backup files
            encoding='utf-8'
        )
    ]
)

def write_pid_file():
    """Write the current process ID to a file"""
    pid_dir = Path.home() / "medialab-manager"
    pid_dir.mkdir(parents=True, exist_ok=True)
    pid_file = pid_dir / "medialab-manager.pid"
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

def remove_pid_file():
    """Remove the PID file"""
    pid_file = Path.home() / "medialab-manager" / "medialab-manager.pid"
    try:
        pid_file.unlink()
    except Exception:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Create database tables for both databases
    MainBase.metadata.create_all(bind=main_engine)
    MediaBase.metadata.create_all(bind=media_engine)
    
    # Write PID file
    write_pid_file()
    
    # Sync tasks from config
    db = next(get_db())
    try:
        from app.api.managers.task_manager import TaskManager
        TaskManager.sync_tasks_from_config(db)
    finally:
        db.close()
    
    start_scheduler()
    yield
    stop_scheduler()
    
    # Remove PID file
    remove_pid_file()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Add template filter for removing query parameters
def remove_query_param(query_params: str, param: str) -> str:
    """Remove a parameter from query string"""
    params = parse_qs(str(query_params))
    if param in params:
        del params[param]
    return urlencode(params, doseq=True)

templates.env.filters["remove_param"] = remove_query_param

# Include routers
app.include_router(views_router)
app.include_router(main_routes_router)
app.include_router(tasks_router, prefix="/api/tasks", tags=["tasks"])
app.include_router(backup_router, prefix="/api/backup", tags=["backup"])
#app.include_router(system_router, prefix="/api/system", tags=["system"])
#app.include_router(media_router, prefix="/api/media", tags=["media"])
#app.include_router(search_router, prefix="/api/search", tags=["search"])
#app.include_router(cache_router, prefix="/api/cache", tags=["cache"])
#app.include_router(sync_router, prefix="/api/sync", tags=["sync"])
app.include_router(notification_router, prefix="/api/notify", tags=["notify"])
app.include_router(event_router, prefix="/api/events", tags=["events"])

def run_service(debug: bool = None):
    """Run the FastAPI service with uvicorn"""
    if debug is not None:
        settings.DEBUG = debug
    
    port = settings.DEBUG_PORT if settings.DEBUG else settings.PORT
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=port,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )

def main():
    """Entry point for the mvm-service command"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    args = parser.parse_args()
    run_service(debug=args.debug) 

if __name__ == "__main__":
    main() 
