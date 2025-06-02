from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from datetime import datetime
import httpx
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.core.database import get_db
from app.views.logs import router as logs_router
from app.api.managers.task_manager import TaskManager

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