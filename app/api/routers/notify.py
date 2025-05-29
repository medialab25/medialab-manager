from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel
from typing import Optional
from app.api.managers.notify_manager import NotifyManager
from app.api.managers.event_manager import EventManager
from app.core.database import get_db
from sqlalchemy.orm import Session
import tempfile
import os

router = APIRouter()

class MailRequest(BaseModel):
    to: str
    subject: str
    body: str

@router.post("/mail")
async def send_mail(
    to: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    attachment: Optional[UploadFile] = File(None),
    attachment_name: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    notify_manager = NotifyManager(db)
    event_manager = EventManager(db)
    try:
        # If there's an attachment, save it temporarily and send it
        if attachment:
            # Use provided attachment name or fall back to original filename
            filename = attachment_name if attachment_name else attachment.filename
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                # Write the uploaded file content to the temporary file
                content = await attachment.read()
                temp_file.write(content)
                temp_path = temp_file.name

            try:
                # Send the email with the attachment
                success = notify_manager.send_mail(to, subject, body, temp_path, filename)
                if success:
                    event_manager.add_event(
                        type="notification",
                        sub_type="email",
                        status="success",
                        title=f"Email sent to {to}",
                        details=f"Email sent successfully to {to} with subject: {subject}"
                    )
                else:
                    event_manager.add_event(
                        type="notification",
                        sub_type="email",
                        status="error",
                        title=f"Failed to send email to {to}",
                        details=f"Failed to send email to {to} with subject: {subject}"
                    )
            finally:
                # Clean up the temporary file
                os.unlink(temp_path)
        else:
            # Send email without attachment
            success = notify_manager.send_mail(to, subject, body)
            if success:
                event_manager.add_event(
                    type="notification",
                    sub_type="email",
                    status="success",
                    title=f"Email sent to {to}",
                    details=f"Email sent successfully to {to} with subject: {subject}"
                )
            else:
                event_manager.add_event(
                    type="notification",
                    sub_type="email",
                    status="error",
                    title=f"Failed to send email to {to}",
                    details=f"Failed to send email to {to} with subject: {subject}"
                )

        return {"status": "success"}
    except Exception as e:
        error_msg = str(e)
        event_manager.add_event(
            type="notification",
            sub_type="email",
            status="error",
            title=f"Failed to send email to {to}",
            details=f"Error: {error_msg}"
        )
        raise HTTPException(status_code=500, detail=error_msg) 