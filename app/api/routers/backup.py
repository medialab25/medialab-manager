from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.managers.backup_manager import BackupManager
from pydantic import BaseModel

class BackupRegistrationRequest(BaseModel):
    name: str
    description: str
    repo_id: str

router = APIRouter()

@router.post("/{task_id}/notify-start")
async def notify_backup_start(
    task_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Notify that a backup task has started.
    
    Args:
        task_id: Unique identifier for the backup task
        db: Database session
        
    Returns:
        dict: Status of the operation
        
    Raises:
        HTTPException: If notification fails
    """
    backup_manager = BackupManager(db)
    try:
        success = backup_manager.notify_start(task_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to notify backup start")
        return {"status": "success", "message": f"Backup {task_id} start notification sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{task_id}/notify-end")
async def notify_backup_end(
    task_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Notify that a backup task has ended.
    
    Args:
        task_id: Unique identifier for the backup task
        db: Database session
        
    Returns:
        dict: Status of the operation
        
    Raises:
        HTTPException: If notification fails
    """
    backup_manager = BackupManager(db)
    try:
        success = backup_manager.notify_end(task_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to notify backup end")
        return {"status": "success", "message": f"Backup {task_id} end notification sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{task_id}/register")
async def register_backup(
    task_id: str,
    request: BackupRegistrationRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Register a new backup task.
    
    Args:
        task_id: Unique identifier for the backup task
        request: Backup registration request containing name, description and repo_id
        db: Database session
        
    Returns:
        dict: Status of the operation
        
    Raises:
        HTTPException: If backup registration fails
    """
    backup_manager = BackupManager(db)
    try:
        success = backup_manager.register_backup(
            task_id=task_id,
            name=request.name,
            description=request.description,
            repo_id=request.repo_id
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to register backup")
        return {"status": "success", "message": f"Backup {task_id} registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 