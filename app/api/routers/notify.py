from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.api.managers.notify_manager import NotifyManager
from app.core.database import get_db
from sqlalchemy.orm import Session
import tempfile
import os
from pathlib import Path

router = APIRouter()

class MailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str

async def handle_attachment(attachment: UploadFile, attachment_name: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
    """Handle file attachment and return the temporary file path and filename."""
    if not attachment:
        return None, None
        
    filename = attachment_name or attachment.filename
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        content = await attachment.read()
        temp_file.write(content)
        return temp_file.name, filename

@router.post("/mail")
async def send_mail(
    to: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    attachment: Optional[UploadFile] = File(None),
    attachment_name: Optional[str] = Form(None),
    db: Session = Depends(get_db)
) -> dict:
    """
    Send an email with optional attachment.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
        attachment: Optional file attachment
        attachment_name: Optional custom name for the attachment
        db: Database session
        
    Returns:
        dict: Status of the operation
        
    Raises:
        HTTPException: If email sending fails
    """
    notify_manager = NotifyManager(db)
    temp_path = None
    
    try:
        # Handle attachment if present
        if attachment:
            temp_path, filename = await handle_attachment(attachment, attachment_name)
            if not temp_path:
                raise HTTPException(status_code=400, detail="Failed to process attachment")
                
            success = notify_manager.send_mail(to, subject, body, temp_path, filename)
        else:
            success = notify_manager.send_mail(to, subject, body)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to send email")

        return {"status": "success", "message": "Email sent successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file if it exists
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass  # Ignore cleanup errors 