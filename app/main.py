import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
import logging
import sys
import uvicorn
import argparse

from app.core.settings import settings
from app.api.routers.notify import router as notification_router
# from app.api.routers import views
#from app.api.routers.media import router as media_router
#from app.api.routers.search import router as search_router
#from app.api.routers.cache import router as cache_router
#from app.api.routers.sync import router as sync_router
#from app.api.routers.system import router as system_router
from app.scheduler import start_scheduler, stop_scheduler

log_file_path = '/var/log/mediavault-manager/mediavault-manager.log'

# Create the log directory if it doesn't exist, but if permissions fail create a log file in the current users home directory
log_dir = Path(log_file_path).parent
if not log_dir.exists():
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        log_file_path = os.path.expanduser('~/mediavault-manager.log')

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file_path)
    ]
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
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

# Include routers
#app.include_router(views.router)
#app.include_router(tasks.router)
#app.include_router(system_router, prefix="/api/system", tags=["system"])
#app.include_router(media_router, prefix="/api/media", tags=["media"])
#app.include_router(search_router, prefix="/api/search", tags=["search"])
#app.include_router(cache_router, prefix="/api/cache", tags=["cache"])
#app.include_router(sync_router, prefix="/api/sync", tags=["sync"])
app.include_router(notification_router, prefix="/api/notify", tags=["notify"])

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "pages/home.html",
        {
            "request": request,
            "title": "Home",
            "config": settings,
            "now": datetime.now()
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

if __name__ == "__main__":
    main()

def main():
    """Entry point for the mvm-service command"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    args = parser.parse_args()
    run_service(debug=args.debug) 
