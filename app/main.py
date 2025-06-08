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
app.include_router(tasks_router, prefix="/api/tasks", tags=["tasks"])
app.include_router(backup_router, prefix="/api/backup", tags=["backup"])
#app.include_router(system_router, prefix="/api/system", tags=["system"])
#app.include_router(media_router, prefix="/api/media", tags=["media"])
#app.include_router(search_router, prefix="/api/search", tags=["search"])
#app.include_router(cache_router, prefix="/api/cache", tags=["cache"])
#app.include_router(sync_router, prefix="/api/sync", tags=["sync"])
app.include_router(notification_router, prefix="/api/notify", tags=["notify"])
app.include_router(event_router, prefix="/api/events", tags=["events"])

@app.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    # Get the last 10 events using EventManager
    event_manager = EventManager(db)
    recent_events = event_manager.list_events(
        EventFilter(),
        skip=0,
        limit=10,
        sort_by="timestamp",
        sort_order="desc"
    )

    # Format events for display
    recent_activity = [
        {
            "time": event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "description": f"{event.description} - {event.details}"
        }
        for event in recent_events
    ]

    return templates.TemplateResponse(
        "pages/home.html",
        {
            "request": request,
            "user": None,  # Replace with actual user when auth is implemented
            "messages": [],
            "dashboard": {
                "total_equipment": 12,
                "recent_activity": recent_activity
            }
        }
    )

@app.get("/api/events/")
async def get_events(
    page: int = Query(1, ge=1),
    type: Optional[str] = None,
    sub_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        # Convert query parameters to filter
        filter_params = {}
        if type:
            filter_params["type"] = type.lower()
        if sub_type:
            filter_params["sub_type"] = sub_type.lower()
        if start_date:
            try:
                filter_params["start_date"] = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        if end_date:
            try:
                filter_params["end_date"] = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        if status:
            filter_params["status"] = status

        # Create filter object
        event_filter = EventFilter(**filter_params)

        # Calculate pagination
        per_page = 10
        skip = (page - 1) * per_page

        # Get events using EventManager
        event_manager = EventManager(db)
        events = event_manager.list_events(event_filter, skip, per_page, "timestamp", "desc")

        # Convert events to JSON-serializable format
        events_json = []
        for event in events:
            events_json.append({
                "id": event.id,
                "formatted_timestamp": event.formatted_timestamp,
                "type": event.type,
                "sub_type": event.sub_type,
                "status": event.status,
                "description": event.description,
                "details": event.details,
                "has_attachment": event.has_attachment
            })

        return events_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/events")
async def events_page(
    request: Request,
    page: int = 1,
    type: str = None,
    sub_type: str = None,
    start_date: str = None,
    end_date: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    # Convert query parameters to filter
    filter_params = {}
    if type:
        filter_params["type"] = type.lower()
    if sub_type:
        filter_params["sub_type"] = sub_type.lower()
    if start_date:
        filter_params["start_date"] = datetime.fromisoformat(start_date)
    if end_date:
        filter_params["end_date"] = datetime.fromisoformat(end_date)
    if status:
        filter_params["status"] = status

    # Create filter object
    event_filter = EventFilter(**filter_params)

    # Calculate pagination
    per_page = 10
    skip = (page - 1) * per_page

    # Get events using EventManager
    event_manager = EventManager(db)
    events = event_manager.list_events(event_filter, skip, per_page, "timestamp", "desc")

    return templates.TemplateResponse(
        "pages/events.html",
        {
            "request": request,
            "user": None,  # Replace with actual user when auth is implemented
            "messages": [],
            "events": events,
            "task_filters": settings.TASK_FILTERS  # Get task filters from settings
        }
    )

@app.get("/media-data")
async def media_data(request: Request):
    return templates.TemplateResponse(
        "pages/media_data.html",
        {
            "request": request,
            "user": None,  # Replace with actual user when auth is implemented
            "messages": []
        }
    )

@app.get("/disk-manager")
async def disk_manager(request: Request):
    return templates.TemplateResponse(
        "pages/disk_manager.html",
        {
            "request": request,
            "user": None,  # Replace with actual user when auth is implemented
            "messages": []
        }
    )

@app.get("/torrent-manager")
async def torrent_manager(request: Request):
    return templates.TemplateResponse(
        "pages/torrent_manager.html",
        {
            "request": request,
            "user": None,  # Replace with actual user when auth is implemented
            "messages": []
        }
    )

@app.get("/admin")
async def admin(request: Request):
    return templates.TemplateResponse(
        "pages/admin.html",
        {
            "request": request,
            "user": None,  # Replace with actual user when auth is implemented
            "messages": []
        }
    )

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
