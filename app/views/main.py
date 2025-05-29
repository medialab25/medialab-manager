from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from datetime import datetime

from app.core.settings import settings
from app.views.logs import router as logs_router

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