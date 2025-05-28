from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, DateTime, Boolean, LargeBinary, Text
from app.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    recipient = Column(String(255), nullable=True)
    title = Column(String(255))
    details = Column(Text, nullable=True)
    has_attachment = Column(Boolean, default=False)
    attachment_name = Column(String(255), nullable=True)
    attachment_data = Column(LargeBinary, nullable=True)
    attachment_type = Column(String(100), nullable=True)  # MIME type
    status = Column(String(50), default="passed")  # passed, failed, pending, error
    
    def __repr__(self):
        return f"<Notification(id={self.id}, recipient={self.recipient}, subject={self.subject})>" 