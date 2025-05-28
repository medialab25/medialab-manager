from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, DateTime, Boolean, LargeBinary, Text
from app.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    type = Column(String(20), index=True)       # email, starr, ntfy, backup, snapraid, rclone, radarr
    sub_type = Column(String(20), nullable=True)
    status = Column(String(10), nullable=True)  # passed, failed, pending, error
    title = Column(String(255))
    details = Column(Text, nullable=True)
    has_attachment = Column(Boolean, default=False)
    attachment_data = Column(LargeBinary, nullable=True)
    attachment_mime_type = Column(String(100), nullable=True)  # MIME type
    
    def __repr__(self):
        return f"<Notification(id={self.id}, recipient={self.recipient}, subject={self.subject})>" 