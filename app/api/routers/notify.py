from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from app.api.managers.notify_manager import NotifyManager
import tempfile
import os

router = APIRouter()
notify_manager = NotifyManager()

class MailRequest(BaseModel):
    to: str
    subject: str
    body: str

@router.post("/mail")
async def send_mail(
    to: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    attachment: Optional[UploadFile] = File(None)
):
    try:
        # If there's an attachment, save it temporarily and send it
        if attachment:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                # Write the uploaded file content to the temporary file
                content = await attachment.read()
                temp_file.write(content)
                temp_path = temp_file.name

            try:
                # Send the email with the attachment
                notify_manager.send_mail(to, subject, body, temp_path)
            finally:
                # Clean up the temporary file
                os.unlink(temp_path)
        else:
            # Send email without attachment
            notify_manager.send_mail(to, subject, body)

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 