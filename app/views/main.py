from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from datetime import datetime
import httpx

from app.core.settings import settings
from app.views.logs import router as logs_router
from app.api.routers.tasks import list_tasks  # Import the list_tasks function

router = APIRouter()
router.include_router(logs_router)
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse(
        "pages/dashboard.html",
        {
            "request": request,
            "title": "Dashboard",
            "config": settings,
            "now": datetime.now()
        }
    )

@router.get("/tasks")
async def tasks(request: Request):
    """Tasks page view"""
    tasks_data = list_tasks()  # Call the list_tasks function directly
    
    return templates.TemplateResponse(
        "pages/tasks.html",
        {
            "request": request,
            "title": "Tasks",
            "tasks": tasks_data
        }
    ) 