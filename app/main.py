import os
from fastapi import FastAPI, Request, Depends
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
def remove_query_param(query_params: dict, param: str) -> str:
    params = parse_qs(query_params)
    if param in params:
        del params[param]
    return urlencode(params, doseq=True)

templates.env.filters["remove_param"] = remove_query_param

# Include routers
app.include_router(views_router)
#app.include_router(tasks.router)
#app.include_router(system_router, prefix="/api/system", tags=["system"])
#app.include_router(media_router, prefix="/api/media", tags=["media"])
#app.include_router(search_router, prefix="/api/search", tags=["search"])
#app.include_router(cache_router, prefix="/api/cache", tags=["cache"])
#app.include_router(sync_router, prefix="/api/sync", tags=["sync"])
app.include_router(notification_router, prefix="/api/notify", tags=["notify"])
app.include_router(event_router, prefix="/api/events", tags=["events"])

# Dummy data for projects
PROJECTS = [
    {
        "id": 1,
        "name": "Documentary Series",
        "description": "A 6-part documentary series exploring local wildlife",
        "status": "active",
        "start_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
        "equipment_count": 5
    },
    {
        "id": 2,
        "name": "Music Video Production",
        "description": "Music video shoot for local band's new single",
        "status": "pending",
        "start_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
        "equipment_count": 3
    },
    {
        "id": 3,
        "name": "Corporate Event Coverage",
        "description": "Video coverage of annual company conference",
        "status": "completed",
        "start_date": (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=85)).strftime("%Y-%m-%d"),
        "equipment_count": 4
    }
]

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "pages/home.html",
        {
            "request": request,
            "user": None,  # Replace with actual user when auth is implemented
            "messages": [],
            "dashboard": {
                "total_projects": 3,
                "active_projects": 1,
                "total_equipment": 12,
                "available_equipment": 8,
                "recent_activity": [
                    {
                        "time": "2 hours ago",
                        "description": "New project 'Documentary Series' created"
                    },
                    {
                        "time": "1 day ago",
                        "description": "Equipment 'Sony A7III' checked out"
                    }
                ]
            }
        }
    )

@app.get("/projects")
async def projects(request: Request):
    return templates.TemplateResponse(
        "pages/projects.html",
        {
            "request": request,
            "user": None,  # Replace with actual user when auth is implemented
            "messages": [],
            "projects": PROJECTS
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
