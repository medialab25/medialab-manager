from sqlalchemy import Column, Integer, String, Boolean, DateTime, CheckConstraint
from datetime import datetime, UTC
from app.core.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), unique=True, index=True)
    name = Column(String(100))
    description = Column(String(255), nullable=True)
    group = Column(String(50), default="other")
    enabled = Column(Boolean, default=False)
    task_type = Column(String(20), default="interval")
    function_name = Column(String(100))
    hours = Column(Integer, default=0)
    minutes = Column(Integer, default=0)
    seconds = Column(Integer, default=0)
    cron_hour = Column(String(10), default="*")
    cron_minute = Column(String(10), default="*")
    cron_second = Column(String(10), default="*")
    last_start_time = Column(DateTime, nullable=True)
    last_end_time = Column(DateTime, nullable=True)
    last_status = Column(String(10), nullable=True)  # success/error/running
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint(
            "task_type IN ('interval', 'cron', 'manual', 'external')",
            name='valid_task_type'
        ),
        CheckConstraint(
            "last_status IN ('success', 'error', 'running', NULL)",
            name='valid_last_status'
        ),
    )

    def __repr__(self):
        return f"<Task(task_id={self.task_id}, name={self.name}, enabled={self.enabled})>" 