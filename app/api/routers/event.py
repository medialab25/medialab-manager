"""Event management router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

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
    db: Session = Depends(get_db)
):
    """List events with optional filtering"""
    event_manager = EventManager(db)
    return event_manager.list_events(filter, skip, limit) 