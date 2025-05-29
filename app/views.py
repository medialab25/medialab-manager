from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from datetime import datetime
import logging
import os
from pathlib import Path

from app.core.settings import settings

def format_timestamp(timestamp_str: str) -> str:
    try:
        # Parse the timestamp string
        dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
        # Format it in a more readable way
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        return timestamp_str

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
    
    # Get all log files (main file and rotated backups)
    log_files = [log_file]
    for i in range(1, 6):  # Check for up to 5 backup files
        backup_file = log_file.parent / f"{log_file.name}.{i}"
        if backup_file.exists():
            log_files.append(backup_file)
    
    # Read logs from all files
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        # Parse log line (format: timestamp - name - level - message)
                        parts = line.strip().split(' - ', 3)  # Split into max 4 parts
                        if len(parts) == 4:
                            timestamp = parts[0].strip()
                            name = parts[1].strip()
                            level = parts[2].strip()
                            message = parts[3].strip()
                            logs.append({
                                'timestamp': format_timestamp(timestamp),
                                'level': level,
                                'message': message
                            })
                    except Exception as e:
                        continue
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
