from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from app.api.managers.event_manager import EventManager
from app.core.database import get_db

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