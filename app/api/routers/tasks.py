from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.api.managers.task_manager import TaskManager
from app.api.managers.event_manager import EventManager

router = APIRouter()

class TaskToggleAPIRequest(BaseModel):
    enabled: bool

class TaskStartAPIRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    group: str = "other"

class TaskEndAPIRequest(BaseModel):
    status: str = "success"

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
            details=f"Task {task_id} started at {datetime.now()}"
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
            details=f"Task {task_id} completed at {datetime.now()}"
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
            details=f"Task {task_id} failed at {datetime.now()}" + (f": {error_message}" if error_message else "")
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
            details=f"Task {task_id} started at {datetime.now()}"
        )
        
        return {
            "status": "success",
            "message": f"Task {task_id} started",
            "task": {
                "id": task.task_id,
                "name": task.name,
                "description": task.description,
                "group": task.group,
                "last_start_time": task.last_start_time.strftime("%Y-%m-%d %H:%M:%S") if task.last_start_time else None,
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
            details=f"Task {task_id} ended at {datetime.now()}"
        )
        
        return {
            "status": "success",
            "message": f"Task {task_id} ended",
            "task": {
                "id": task.task_id,
                "name": task.name,
                "last_start_time": task.last_start_time.strftime("%Y-%m-%d %H:%M:%S") if task.last_start_time else None,
                "last_end_time": task.last_end_time.strftime("%Y-%m-%d %H:%M:%S") if task.last_end_time else None,
                "last_status": task.last_status
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 