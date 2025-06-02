from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy.orm import Session
from app.api.managers.event_manager import EventManager
from app.core.database import get_db
from app.models.event_types import EventType, SubEventType, Status
from app.utils.file_utils import AttachDataMimeType


def create_event(
    status: Status,
    description: str,
    details: str,
    event_type: EventType = EventType.NONE,
    sub_type: SubEventType = SubEventType.NONE,
    attachment_data: Optional[bytes] = None,
    attachment_mime_type: Optional[AttachDataMimeType] = None
) -> None:
    """
    Helper function to create events with consistent parameters.
    
    Args:
        status: Event status
        description: Event description
        details: Event details
        event_type: Type of event (defaults to BACKUP)
        sub_type: Sub-type of event (defaults to SNAPRAID)
        attachment_data: Optional binary attachment data
        attachment_mime_type: Optional MIME type of the attachment
    """
    with EventManagerUtil.get_event_manager() as event_manager:
        if attachment_data:
            event_manager.add_event_with_output(
                type=event_type.value,
                sub_type=sub_type.value,
                status=status.value,
                description=description,
                details=details,
                attachment_data=attachment_data,
                attachment_mime_type=attachment_mime_type
            )
        else:
            event_manager.add_event(
                type=event_type.value,
                sub_type=sub_type.value,
                status=status.value,
                description=description,
                details=details
            )


class EventManagerUtil:
    """Utility class for managing EventManager instances with proper session handling."""
    
    @staticmethod
    @contextmanager
    def get_event_manager() -> Generator[EventManager, None, None]:
        """
        Context manager that provides an EventManager instance with a properly managed database session.
        
        Yields:
            EventManager: An EventManager instance with an active database session
            
        Example:
            with EventManagerUtil.get_event_manager() as event_manager:
                event_manager.add_event(...)
        """
        db = next(get_db())
        try:
            event_manager = EventManager(db)
            yield event_manager
        finally:
            db.close() 