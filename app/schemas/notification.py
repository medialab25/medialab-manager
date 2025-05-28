from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NotificationBase(BaseModel):
    recipient: str
    title: str
    details: str

class NotificationCreate(NotificationBase):
    pass

class Notification(NotificationBase):
    id: int
    timestamp: datetime
    has_attachment: bool
    attachment_name: Optional[str] = None
    attachment_type: Optional[str] = None
    status: str

    class Config:
        from_attributes = True

class NotificationFilter(BaseModel):
    recipient: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    has_attachment: Optional[bool] = None 