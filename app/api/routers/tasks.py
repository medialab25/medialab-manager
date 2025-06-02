from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.api.managers.task_manager import TaskManager

router = APIRouter()

class TaskToggleRequest(BaseModel):
    enabled: bool

@router.get("/")
def list_tasks_endpoint(db: Session = Depends(get_db)):
    """API endpoint to list all tasks"""
    task_manager = TaskManager(db=db)
    return task_manager.list_tasks()

@router.post("/{task_id}/toggle")
def toggle_task_endpoint(task_id: str, request: TaskToggleRequest, db: Session = Depends(get_db)):
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