from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from datetime import datetime
import logging
import os
from pathlib import Path

from app.core.settings import settings

router = APIRouter()
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

@router.get("/logs")
async def view_logs(request: Request):
    # Get the log file path from settings
    log_file = settings.LOG_FILE
    logs = []
    
    # Ensure the logs directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    if log_file.exists():
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    # Parse log line (format: timestamp - name - level - message)
                    parts = line.strip().split(' - ', 3)
                    if len(parts) == 4:
                        timestamp, name, level, message = parts
                        logs.append({
                            'timestamp': timestamp,
                            'level': level,
                            'message': message
                        })
                except Exception as e:
                    continue
    
    # Sort logs by timestamp in reverse order (newest first)
    logs.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Limit to last 1000 logs to prevent UI performance issues
    logs = logs[:1000]
    
    return templates.TemplateResponse(
        "pages/logs.html",
        {
            "request": request,
            "title": "System Logs",
            "logs": logs
        }
    )
