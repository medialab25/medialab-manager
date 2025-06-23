from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.schemas.event import EventFilter
from app.api.managers.event_manager import EventManager

router = APIRouter()

@router.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    """Redirect to events page"""
    return RedirectResponse(url="/events")

@router.get("/api/events/")
async def get_events(
    page: int = Query(1, ge=1),
    type: Optional[str] = None,
    sub_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        # Convert query parameters to filter
        filter_params = {}
        if type:
            filter_params["type"] = type.lower()
        if sub_type:
            filter_params["sub_type"] = sub_type.lower()
        if start_date:
            try:
                filter_params["start_date"] = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        if end_date:
            try:
                filter_params["end_date"] = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        if status:
            filter_params["status"] = status

        # Create filter object
        event_filter = EventFilter(**filter_params)

        # Calculate pagination - use 100 items per page for infinite scroll
        per_page = 100
        skip = (page - 1) * per_page

        # Get events using EventManager
        event_manager = EventManager(db)
        events = event_manager.list_events(event_filter, skip, per_page, "timestamp", "desc")

        # Convert events to JSON-serializable format
        events_json = []
        for event in events:
            events_json.append({
                "id": event.id,
                "formatted_timestamp": event.formatted_timestamp,
                "type": event.type,
                "sub_type": event.sub_type,
                "status": event.status,
                "description": event.description,
                "details": event.details,
                "has_attachment": event.has_attachment
            })

        return events_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 