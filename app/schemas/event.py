from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EventBase(BaseModel):
    type: str
    sub_type: Optional[str] = None
    status: str
    description: str
    details: str

class EventCreate(EventBase):
    pass

class Event(EventBase):
    id: int
    timestamp: datetime
    has_attachment: bool
    attachment_data: Optional[bytes] = None
    attachment_mime_type: Optional[str] = None
    parent_id: Optional[int] = None

    class Config:
        from_attributes = True

class EventFilter(BaseModel):
    type: Optional[str] = None
    sub_type: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    has_attachment: Optional[bool] = None
    parent_id: Optional[int] = None 