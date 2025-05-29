import logging
from pathlib import Path
import json
from sqlalchemy.orm import Session
from app.models.event import Event
from app.core.database import DBManager
from app.api.managers.notify_manager import NotifyManager
from app.schemas.event import EventFilter
from typing import List, Optional

logger = logging.getLogger(__name__)

class EventManager:
    def __init__(self, db: Session = None):
        self.config = self._load_config()
        self.db_manager = DBManager(Event, db) if db else None
        self.notify_manager = NotifyManager(db)
        self.db = db

    def _load_config(self) -> dict:
        config_path = Path("config.json")
        with open(config_path) as f:
            return json.load(f)

    def add_event(self, type: str, sub_type: str, status: str, title: str, details: str, attachment_path: str = None, parent_id: int = None) -> Event:
        """Create a new event"""
        event = None
        if self.db_manager:
            attachment_data = None
            mime_type = None

            if attachment_path:
                attachment_data, mime_type = self.notify_manager._get_attachment_data(attachment_path)

            event = self.db_manager.create(
                type=type,
                sub_type=sub_type,
                status=status,
                title=title,
                details=details,
                has_attachment=bool(attachment_path),
                attachment_data=attachment_data,
                attachment_mime_type=mime_type,
                parent_id=parent_id
            )

        return event

    def get_event(self, event_id: int) -> Optional[Event]:
        """Get a specific event by ID"""
        if not self.db:
            return None
        return self.db.query(Event).filter(Event.id == event_id).first()

    def list_events(self, filter: EventFilter, skip: int = 0, limit: int = 100) -> List[Event]:
        """List events with optional filtering"""
        if not self.db:
            return []
            
        query = self.db.query(Event)
        
        if filter.type:
            query = query.filter(Event.type == filter.type)
        if filter.sub_type:
            query = query.filter(Event.sub_type == filter.sub_type)
        if filter.status:
            query = query.filter(Event.status == filter.status)
        if filter.title:
            query = query.filter(Event.title.ilike(f"%{filter.title}%"))
        if filter.start_date:
            query = query.filter(Event.timestamp >= filter.start_date)
        if filter.end_date:
            query = query.filter(Event.timestamp <= filter.end_date)
        if filter.has_attachment is not None:
            query = query.filter(Event.has_attachment == filter.has_attachment)
        if filter.parent_id is not None:
            query = query.filter(Event.parent_id == filter.parent_id)
        
        return query.order_by(Event.timestamp.desc()).offset(skip).limit(limit).all() 