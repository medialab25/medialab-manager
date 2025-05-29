from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import mimetypes

from app.core.database import get_db
from app.schemas.event import NotificationCreate, Notification as NotificationSchema, NotificationFilter

router = APIRouter()

@router.post("/", response_model=NotificationSchema)
def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db)
):
    db_notification = Notification(
        recipient=notification.recipient,
        subject=notification.subject,
        body=notification.body
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

@router.post("/with-attachment", response_model=NotificationSchema)
async def create_notification_with_attachment(
    recipient: str = Query(...),
    subject: str = Query(...),
    body: str = Query(...),
    attachment: bytes = Query(...),
    attachment_name: str = Query(...),
    db: Session = Depends(get_db)
):
    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(attachment_name)
    
    db_notification = Notification(
        recipient=recipient,
        subject=subject,
        body=body,
        has_attachment=True,
        attachment_name=attachment_name,
        attachment_data=attachment,
        attachment_type=mime_type or 'application/octet-stream'
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

@router.get("/", response_model=List[NotificationSchema])
def list_notifications(
    filter: NotificationFilter = Depends(),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Notification)
    
    if filter.recipient:
        query = query.filter(Notification.recipient.ilike(f"%{filter.recipient}%"))
    if filter.subject:
        query = query.filter(Notification.subject.ilike(f"%{filter.subject}%"))
    if filter.start_date:
        query = query.filter(Notification.timestamp >= filter.start_date)
    if filter.end_date:
        query = query.filter(Notification.timestamp <= filter.end_date)
    if filter.status:
        query = query.filter(Notification.status == filter.status)
    if filter.has_attachment is not None:
        query = query.filter(Notification.has_attachment == filter.has_attachment)
    
    return query.order_by(Notification.timestamp.desc()).offset(skip).limit(limit).all()

@router.get("/{notification_id}/attachment")
def get_attachment(
    notification_id: int,
    db: Session = Depends(get_db)
):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification or not notification.has_attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    return Response(
        content=notification.attachment_data,
        media_type=notification.attachment_type,
        headers={
            "Content-Disposition": f"inline; filename={notification.attachment_name}"
        }
    ) 