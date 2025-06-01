import os
from fastapi import FastAPI, Request, Depends, HTTPException
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

from app.core.settings import settings
from app.core.database import engine, Base, get_db
from app.api.routers.notify import router as notification_router
from app.api.routers.event import router as event_router
from app.api.routers.tasks import router as tasks_router
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

log_file_path = '/var/log/medialab-manager/medialab-manager.log'

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    start_scheduler()
    yield
    stop_scheduler()

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

@app.get("/events")
async def events(
    request: Request,
    page: int = 1,
    type: str = None,
    sub_type: str = None,
    start_date: str = None,
    end_date: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    # Validate event type if provided
    if type:
        try:
            # Try to convert to EventType enum
            event_type = EventType(type)
            type = event_type.value
        except ValueError:
            # If invalid type, return empty results instead of error
            return templates.TemplateResponse(
                "pages/events.html",
                {
                    "request": request,
                    "user": None,
                    "messages": [{"type": "warning", "text": f"Invalid event type: {type}"}],
                    "events": [],
                    "page": page,
                    "has_next": False
                }
            )

    # Validate sub_type if provided
    if sub_type:
        try:
            # Try to convert to SubEventType enum
            event_sub_type = SubEventType(sub_type)
            sub_type = event_sub_type.value
        except ValueError:
            # If invalid sub_type, return empty results instead of error
            return templates.TemplateResponse(
                "pages/events.html",
                {
                    "request": request,
                    "user": None,
                    "messages": [{"type": "warning", "text": f"Invalid sub-type: {sub_type}"}],
                    "events": [],
                    "page": page,
                    "has_next": False
                }
            )

    # Convert query parameters to filter
    filter_params = {}
    if type:
        filter_params["type"] = type
    if sub_type:
        filter_params["sub_type"] = sub_type
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

    # Get total count for pagination
    total = db.query(Event).count()
    has_next = total > page * per_page

    return templates.TemplateResponse(
        "pages/events.html",
        {
            "request": request,
            "user": None,  # Replace with actual user when auth is implemented
            "messages": [],
            "events": events,
            "page": page,
            "has_next": has_next
        }
    )

@app.get("/media-manage")
async def media_manage(request: Request):
    return templates.TemplateResponse(
        "pages/media_manage.html",
        {
            "request": request,
            "user": None,  # Replace with actual user when auth is implemented
            "messages": []
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

def run_service(debug: bool = None):
    """Run the FastAPI service with uvicorn"""
    if debug is not None:
        settings.DEBUG = debug
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
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
