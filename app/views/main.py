from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from datetime import datetime
import httpx
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.core.database import get_db
from app.views.logs import router as logs_router
from app.api.managers.task_manager import TaskManager
from app.schemas.event import EventFilter
from app.api.managers.event_manager import EventManager

router = APIRouter()
router.include_router(logs_router)
templates = Jinja2Templates(directory="app/templates")

@router.get("/tasks")
async def tasks(request: Request, db: Session = Depends(get_db)):
    """Tasks page view"""
    task_manager = TaskManager(db=db)
    tasks_data = task_manager.list_tasks()
    
    return templates.TemplateResponse(
        "pages/tasks.html",
        {
            "request": request,
            "title": "Tasks",
            "tasks": tasks_data
        }
    )

@router.get("/events")
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
    """Events page view"""
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
            "title": "Events",
            "page": page,
            "type": type,
            "sub_type": sub_type,
            "start_date": start_date,
            "end_date": end_date,
            "status": status,
            "events": events,
            "task_filters": settings.TASK_FILTERS
        }
    )

@router.get("/media-data")
async def media_data(request: Request):
    """Media data page view"""
    return templates.TemplateResponse(
        "pages/media_data.html",
        {
            "request": request,
            "title": "Media Data"
        }
    )

@router.get("/disk-manager")
async def disk_manager(request: Request):
    """Disk manager page view"""
    return templates.TemplateResponse(
        "pages/disk_manager.html",
        {
            "request": request,
            "title": "Disk Manager"
        }
    )

@router.get("/torrent-manager")
async def torrent_manager(request: Request):
    """Torrent manager page view"""
    return templates.TemplateResponse(
        "pages/torrent_manager.html",
        {
            "request": request,
            "title": "Torrent Manager"
        }
    )

@router.get("/admin")
async def admin(request: Request):
    """Admin page view"""
    return templates.TemplateResponse(
        "pages/admin.html",
        {
            "request": request,
            "title": "Admin"
        }
    )

@router.get("/notifications")
async def notifications(request: Request):
    """Notifications page view"""
    return templates.TemplateResponse(
        "pages/notifications.html",
        {
            "request": request,
            "title": "Notifications"
        }
    ) 