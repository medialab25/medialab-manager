import logging
from pathlib import Path
import json
from sqlalchemy.orm import Session
from app.models.event import Event
from app.core.database import DBManager
from app.schemas.event import EventFilter
from app.utils.file_utils import get_attachment_data, AttachDataMimeType, MIME_TYPE_MAPPING
from typing import List, Optional, Dict, Any
from sqlalchemy import desc, asc
from app.models.event_types import EventType, SubEventType
from datetime import datetime

logger = logging.getLogger(__name__)

class EventManager:
    def __init__(self, db: Session = None):
        self.config = self._load_config()
        self.db_manager = DBManager(Event, db) if db else None
        self.db = db

    def _load_config(self) -> dict:
        config_path = Path("config.json")
        with open(config_path) as f:
            return json.load(f)

    def add_event_with_output(self, type: str, sub_type: str, status: str, description: str, details: str, attachment_data: bytes = None, attachment_mime_type: AttachDataMimeType = None, parent_id: int = None) -> Event:
        """Create a new event with binary attachment data
        
        Args:
            type: Event type
            sub_type: Event sub-type
            status: Event status
            description: Event description
            details: Event details
            attachment_data: Binary attachment data
            attachment_mime_type: MIME type of the attachment (can be enum or string)
            parent_id: Optional parent event ID
            
        Returns:
            Event: Created event object
        """
        event = None
        if self.db_manager:
            # Handle attachment_mime_type - can be enum or string
            mime_type = None
            if attachment_mime_type:
                if isinstance(attachment_mime_type, AttachDataMimeType):
                    # If it's an enum, map it to MIME type string
                    mime_type = MIME_TYPE_MAPPING.get(attachment_mime_type)
                else:
                    # If it's already a string, use it directly
                    mime_type = attachment_mime_type
            
            event = self.db_manager.create(
                type=type,
                sub_type=sub_type,
                status=status,
                description=description,
                details=details,
                has_attachment=bool(attachment_data),
                attachment_data=attachment_data,
                attachment_mime_type=mime_type,
                parent_id=parent_id
            )

        return event

    def add_event(self, type: str, sub_type: str, status: str, description: str, details: str, attachment_path: str = None, parent_id: int = None) -> Event:
        """Create a new event"""
        event = None
        if self.db_manager:
            attachment_data = None
            mime_type = None

            if attachment_path:
                attachment_data, mime_type = get_attachment_data(attachment_path)

            event = self.db_manager.create(
                type=type,
                sub_type=sub_type,
                status=status,
                description=description,
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

    def list_events(
        self, 
        filter: EventFilter, 
        skip: int = 0, 
        limit: int = 100,
        sort_by: str = "timestamp",
        sort_order: str = "desc"
    ) -> List[Event]:
        """List events with optional filtering and sorting
        
        Args:
            filter: EventFilter object containing filter criteria
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            sort_by: Field to sort by (id, timestamp, type, status, description)
            sort_order: Sort order ('asc' or 'desc')
        """
        if not self.db:
            return []
            
        query = self.db.query(Event)
        
        # Apply filters
        if filter.type:
            types = [t.strip().lower() for t in filter.type.split(',')]
            query = query.filter(Event.type.ilike(f"%{types[0]}%"))
        if filter.sub_type:
            sub_types = [t.strip().lower() for t in filter.sub_type.split(',')]
            query = query.filter(Event.sub_type.ilike(f"%{sub_types[0]}%"))
        if filter.status:
            query = query.filter(Event.status == filter.status)
        if filter.description:
            query = query.filter(Event.description.ilike(f"%{filter.description}%"))
        if filter.start_date:
            query = query.filter(Event.timestamp >= filter.start_date)
        if filter.end_date:
            query = query.filter(Event.timestamp <= filter.end_date)
        if filter.has_attachment is not None:
            query = query.filter(Event.has_attachment == filter.has_attachment)
        if filter.parent_id is not None:
            query = query.filter(Event.parent_id == filter.parent_id)
        
        # Apply sorting
        sort_field = getattr(Event, sort_by, Event.timestamp)
        sort_func = desc if sort_order.lower() == "desc" else asc
        # Always include id as a secondary sort key to ensure stable pagination
        query = query.order_by(sort_func(sort_field), sort_func(Event.id))
        
        return query.offset(skip).limit(limit).all()

    def get_last_task_run(self, sub_type: str) -> Optional[datetime]:
        """Get the last run time for a task
        
        Args:
            task_id: The ID of the task
            
        Returns:
            Optional[datetime]: The timestamp of the last task run, or None if no runs found
        """
        if not self.db:
            return None
            
        # Query for the most recent task run event
        event = self.db.query(Event).filter(
            Event.type == EventType.TASK,
            Event.sub_type == sub_type
        ).order_by(Event.timestamp.desc()).first()
        
        return event.timestamp if event else None 