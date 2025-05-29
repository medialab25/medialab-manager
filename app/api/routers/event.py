"""Event management router."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.core.database import get_db
from app.schemas.event import EventCreate, Event as EventSchema, EventFilter
from app.api.managers.event_manager import EventManager

router = APIRouter()

@router.post("/", response_model=EventSchema)
def create_event(
    event: EventCreate,
    db: Session = Depends(get_db)
):
    """Create a new event"""
    event_manager = EventManager(db)
    return event_manager.add_event(
        type=event.type,
        sub_type=event.sub_type,
        status=event.status,
        title=event.title,
        details=event.details
    )

@router.get("/{event_id}", response_model=EventSchema)
def get_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific event by ID"""
    event_manager = EventManager(db)
    event = event_manager.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.get("/", response_model=List[EventSchema])
def list_events(
    filter: EventFilter = Depends(),
    skip: int = 0,
    limit: int = 100,
    sort_by: str = Query("timestamp", description="Field to sort by (id, timestamp, type, status, title)"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    db: Session = Depends(get_db)
):
    """List events with optional filtering and sorting"""
    if sort_order.lower() not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="sort_order must be 'asc' or 'desc'")
    
    valid_sort_fields = ["id", "timestamp", "type", "status", "title"]
    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=400, 
            detail=f"sort_by must be one of: {', '.join(valid_sort_fields)}"
        )
    
    event_manager = EventManager(db)
    return event_manager.list_events(filter, skip, limit, sort_by, sort_order)

@router.get("/{event_id}/attachment")
def get_event_attachment(
    event_id: int,
    db: Session = Depends(get_db)
):
    """Get the attachment content for a specific event"""
    event_manager = EventManager(db)
    event = event_manager.get_event(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    if not event.has_attachment or not event.attachment_data:
        raise HTTPException(status_code=404, detail="Event has no attachment")
        
    # For text-based content, return as JSON
    if event.attachment_mime_type and event.attachment_mime_type.startswith(('text/', 'application/json', 'application/xml')):
        try:
            content = event.attachment_data.decode('utf-8')
            return {"content": content}
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Attachment content is not readable text")
    
    # For binary content, return as file download
    return Response(
        content=event.attachment_data,
        media_type=event.attachment_mime_type or 'application/octet-stream',
        headers={
            'Content-Disposition': f'attachment; filename="event_{event_id}_attachment"'
        }
    )

@router.get("/{event_id}/details")
def get_event_details(
    event_id: int,
    db: Session = Depends(get_db)
):
    """Get the details content for a specific event as formatted JSON"""
    event_manager = EventManager(db)
    event = event_manager.get_event(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    if not event.details:
        raise HTTPException(status_code=404, detail="Event has no details")
        
    try:
        # Try to parse the details as JSON
        details_json = json.loads(event.details)
        return details_json
    except json.JSONDecodeError:
        # If not valid JSON, return as plain text
        return {"content": event.details} 