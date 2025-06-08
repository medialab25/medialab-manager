from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.api.managers.task_manager import TaskManager, TaskStatus
from app.api.managers.event_manager import EventManager
from app.schemas.task import TaskCreateAPIRequest, TaskStartAPIRequest, TaskEndAPIRequest, TaskToggleAPIRequest
from app.utils.time_utils import get_current_time

router = APIRouter()

class TaskToggleAPIRequest(BaseModel):
    enabled: bool

class TaskStartAPIRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    group: str = "other"

class TaskEndAPIRequest(BaseModel):
    status: str = "success"

class TaskCreateAPIRequest(BaseModel):
    name: str
    description: str
    group: str = "other"
    task_type: str = "external"
    enabled: bool = True
    host_url: Optional[str] = None
    hours: Optional[int] = None
    minutes: Optional[int] = None
    seconds: Optional[int] = None
    cron_hour: Optional[int] = None
    cron_minute: Optional[int] = None
    cron_second: Optional[int] = None

@router.get("/")
def list_tasks_endpoint(db: Session = Depends(get_db)):
    """API endpoint to list all tasks"""
    task_manager = TaskManager(db=db)
    return task_manager.list_tasks()

@router.post("/{task_id}/toggle")
def toggle_task_endpoint(task_id: str, request: TaskToggleAPIRequest, db: Session = Depends(get_db)):
    """Toggle a task's enabled status"""
    task_manager = TaskManager(db=db)
    try:
        return task_manager.toggle_task(task_id, request.enabled)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{task_id}/run")
def run_task_endpoint(task_id: str, db: Session = Depends(get_db)):
    """Run a task immediately"""
    task_manager = TaskManager(db=db)
    try:
        return task_manager.run_task(task_id)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{task_id}/notify-start")
def notify_task_start_endpoint(task_id: str, db: Session = Depends(get_db)):
    """Notify that a task has started"""
    event_manager = EventManager(db=db)
    task_manager = TaskManager(db=db)
    try:
        # Update task status
        task_manager.update_task_status(task_id, "running")
        
        # Create event
        event_manager.add_event(
            type="task",
            sub_type=task_id,
            status="info",
            description=f"Task {task_id} started",
            details=f"Task {task_id} started at {get_current_time()}"
        )
        return {"status": "success", "message": f"Task {task_id} start notification sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{task_id}/notify-end")
def notify_task_end_endpoint(task_id: str, db: Session = Depends(get_db)):
    """Notify that a task has ended"""
    event_manager = EventManager(db=db)
    task_manager = TaskManager(db=db)
    try:
        # Update task status
        task_manager.update_task_status(task_id, "success")
        
        # Create event
        event_manager.add_event(
            type="task",
            sub_type=task_id,
            status="success",
            description=f"Task {task_id} completed",
            details=f"Task {task_id} completed at {get_current_time()}"
        )
        return {"status": "success", "message": f"Task {task_id} end notification sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{task_id}/notify-error")
def notify_task_error_endpoint(task_id: str, error_message: str = None, db: Session = Depends(get_db)):
    """Notify that a task has encountered an error"""
    event_manager = EventManager(db=db)
    task_manager = TaskManager(db=db)
    try:
        # Update task status
        task_manager.update_task_status(task_id, "error")
        
        # Create event
        event_manager.add_event(
            type="task",
            sub_type=task_id,
            status="error",
            description=f"Task {task_id} failed",
            details=f"Task {task_id} failed at {get_current_time()}" + (f": {error_message}" if error_message else "")
        )
        return {"status": "success", "message": f"Task {task_id} error notification sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{task_id}/last-run")
def get_task_last_run(task_id: str, db: Session = Depends(get_db)):
    """Get the last run information for a task"""
    task_manager = TaskManager(db=db)
    try:
        return task_manager.get_task_last_run(task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{task_id}/start")
def start_task_endpoint(task_id: str, request: TaskStartAPIRequest, db: Session = Depends(get_db)):
    """Start a task, creating it if it doesn't exist"""
    task_manager = TaskManager(db=db)
    event_manager = EventManager(db=db)
    try:
        # Start the task
        task = task_manager.start_task(
            task_id=task_id,
            name=request.name,
            description=request.description,
            group=request.group
        )
        
        # Create event
        event_manager.add_event(
            type="task",
            sub_type=task_id,
            status="info",
            description=f"Task {task_id} started",
            details=f"Task {task_id} started at {get_current_time()}"
        )
        
        return {
            "status": "success",
            "message": f"Task {task_id} started",
            "task": {
                "id": task.task_id,
                "name": task.name,
                "description": task.description,
                "group": task.group,
                "last_start_time": task.get_formatted_last_start_time(),
                "last_status": task.last_status
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{task_id}/end")
def end_task_endpoint(task_id: str, request: TaskEndAPIRequest, db: Session = Depends(get_db)):
    """End a task and update its status"""
    task_manager = TaskManager(db=db)
    event_manager = EventManager(db=db)
    try:
        # End the task
        task = task_manager.end_task(task_id, request.status)
        
        # Create event
        event_manager.add_event(
            type="task",
            sub_type=task_id,
            status=request.status,
            description=f"Task {task_id} ended with status: {request.status}",
            details=f"Task {task_id} ended at {get_current_time()}"
        )
        
        return {
            "status": "success",
            "message": f"Task {task_id} ended",
            "task": {
                "id": task.task_id,
                "name": task.name,
                "last_start_time": task.get_formatted_last_start_time(),
                "last_end_time": task.get_formatted_last_end_time(),
                "last_status": task.last_status
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{task_id}/create")
def create_task_endpoint(task_id: str, request: TaskCreateAPIRequest, db: Session = Depends(get_db)):
    """Create a new task"""
    task_manager = TaskManager(db=db)
    event_manager = EventManager(db=db)
    try:
        # Create the task
        task, status = task_manager.create_task(
            task_id=task_id,
            name=request.name,
            description=request.description,
            group=request.group,
            task_type=request.task_type,
            enabled=request.enabled,
            host_url=request.host_url,
            hours=request.hours,
            minutes=request.minutes,
            seconds=request.seconds,
            cron_hour=request.cron_hour,
            cron_minute=request.cron_minute,
            cron_second=request.cron_second
        )
        
        # Create event only if task was created or updated
        if status in [TaskStatus.CREATED, TaskStatus.UPDATED]:
            event_manager.add_event(
                type="task",
                sub_type=task_id,
                status="info",
                description=f"Task {task_id} {status.value}",
                details=f"Task {task_id} {status.value} at {get_current_time()}"
            )
        
        # Prepare schedule information based on task type
        schedule = {
            "type": task.task_type
        }
        if task.task_type == "interval":
            schedule.update({
                "hours": task.hours,
                "minutes": task.minutes,
                "seconds": task.seconds
            })
        elif task.task_type == "cron":
            schedule.update({
                "cron_hour": task.cron_hour,
                "cron_minute": task.cron_minute,
                "cron_second": task.cron_second
            })
        
        return {
            "status": "success",
            "message": f"Task {task_id} {status.value}",
            "task": {
                "id": task.task_id,
                "name": task.name,
                "description": task.description,
                "group": task.group,
                "task_type": task.task_type,
                "enabled": task.enabled,
                "host_url": task.host_url,
                "schedule": schedule
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 