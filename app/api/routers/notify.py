from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.api.managers.notify_manager import NotifyManager

router = APIRouter()
notify_manager = NotifyManager()

class MailRequest(BaseModel):
    to: str
    subject: str
    body: str

@router.post("/mail")
async def send_mail(request: MailRequest):
    try:
        notify_manager.send_mail(request.to, request.subject, request.body)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 