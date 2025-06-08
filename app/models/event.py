from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, LargeBinary, Text
from app.core.database import Base
from app.utils.time_utils import get_current_time, format_datetime

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=get_current_time, index=True)
    type = Column(String(50), index=True)
    sub_type = Column(String(50), nullable=True)
    status = Column(String(10), nullable=True)  # success, error, warning, info
    description = Column(String(255))
    details = Column(Text, nullable=True)
    has_attachment = Column(Boolean, default=False)
    attachment_data = Column(LargeBinary, nullable=True)
    attachment_mime_type = Column(String(100), nullable=True)  # MIME type
    
    @property
    def formatted_timestamp(self):
        """Return timestamp formatted as YYYY-MM-DD HH:MM:SS in Europe/London timezone"""
        return format_datetime(self.timestamp)
    
    def __repr__(self):
        return f"<Event(id={self.id}, type={self.type}, status={self.status}, description={self.description})>" 