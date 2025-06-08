from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, CheckConstraint
from app.core.database import Base
from app.utils.time_utils import get_current_time, format_datetime

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
    host_url = Column(String(255), nullable=True)  # Can store full URLs or host:port combinations
    hours = Column(Integer, default=0)
    minutes = Column(Integer, default=0)
    seconds = Column(Integer, default=0)
    cron_hour = Column(String(10), default="*")
    cron_minute = Column(String(10), default="*")
    cron_second = Column(String(10), default="*")
    last_start_time = Column(DateTime, nullable=True)
    last_end_time = Column(DateTime, nullable=True)
    last_status = Column(String(10), nullable=True)  # success/error/running
    created_at = Column(DateTime, default=get_current_time)
    updated_at = Column(DateTime, default=get_current_time, onupdate=get_current_time)

    __table_args__ = (
        CheckConstraint(
            "task_type IN ('interval', 'cron', 'manual', 'external', 'external_interval', 'external_cron')",
            name='valid_task_type'
        ),
        CheckConstraint(
            "last_status IN ('success', 'error', 'running', NULL)",
            name='valid_last_status'
        ),
    )

    def get_formatted_last_start_time(self) -> str:
        """Get formatted last start time"""
        return format_datetime(self.last_start_time) if self.last_start_time else None

    def get_formatted_last_end_time(self) -> str:
        """Get formatted last end time"""
        return format_datetime(self.last_end_time) if self.last_end_time else None

    def get_last_run_time(self) -> str:
        """Get the last run time in a formatted string
        
        Returns:
            str: Formatted last run time or 'Never' if not run yet
        """
        if self.last_start_time:
            return format_datetime(self.last_start_time)
        return "Never"

    def __repr__(self):
        return f"<Task(task_id={self.task_id}, name={self.name}, enabled={self.enabled})>" 