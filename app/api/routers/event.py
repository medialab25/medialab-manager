"""Event management router."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.core.database import get_db
from app.schemas.event import EventCreate, Event as EventSchema, EventFilter
from app.api.managers.event_manager import EventManager
from app.utils.file_utils import AttachDataMimeType

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
        description=event.description,
        details=event.details
    )

@router.post("/add_event", response_model=EventSchema)
async def add_event(
    type: str = Form(...),
    sub_type: Optional[str] = Form(None),
    status: str = Form(...),
    description: str = Form(...),
    details: str = Form(...),
    attachment: Optional[UploadFile] = File(None),
    attachment_type: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Add a new event with optional file attachment"""
    event_manager = EventManager(db)
    
    # Handle attachment if provided
    attachment_data = None
    attachment_mime_type = None
    
    if attachment:
        try:
            attachment_data = await attachment.read()
            
            # Use provided attachment_type if specified, otherwise determine MIME type from file extension or content
            if attachment_type:
                attachment_mime_type = attachment_type
            elif attachment.content_type:
                attachment_mime_type = attachment.content_type
            else:
                # Try to determine MIME type from filename
                filename = attachment.filename.lower() if attachment.filename else ""
                if filename.endswith('.txt') or filename.endswith('.log'):
                    attachment_mime_type = "text/plain"
                elif filename.endswith('.json'):
                    attachment_mime_type = "application/json"
                elif filename.endswith('.md') or filename.endswith('.markdown'):
                    attachment_mime_type = "text/markdown"
                elif filename.endswith('.html') or filename.endswith('.htm'):
                    attachment_mime_type = "text/html"
                elif filename.endswith('.sh') or filename.endswith('.bash'):
                    attachment_mime_type = "text/x-shellscript"
                else:
                    # Try to detect text content by attempting to decode as UTF-8
                    try:
                        content_str = attachment_data.decode('utf-8')
                        # If it's valid UTF-8 and looks like text, treat as text/plain
                        if content_str.isprintable() or '\n' in content_str:
                            attachment_mime_type = "text/plain"
                        else:
                            attachment_mime_type = "application/octet-stream"
                    except UnicodeDecodeError:
                        # If it can't be decoded as UTF-8, it's likely binary
                        attachment_mime_type = "application/octet-stream"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading attachment: {str(e)}")
    
    # Create the event using the manager
    event = event_manager.add_event_with_output(
        type=type,
        sub_type=sub_type,
        status=status,
        description=description,
        details=details,
        attachment_data=attachment_data,
        attachment_mime_type=attachment_mime_type
    )
    
    if not event:
        raise HTTPException(status_code=500, detail="Failed to create event")
    
    return event

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
    sort_by: str = Query("timestamp", description="Field to sort by (id, timestamp, type, status, description)"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    db: Session = Depends(get_db)
):
    """List events with optional filtering and sorting"""
    if sort_order.lower() not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="sort_order must be 'asc' or 'desc'")
    
    valid_sort_fields = ["id", "timestamp", "type", "status", "description"]
    if sort_by not in valid_sort_fields:
        raise HTTPException(
            status_code=400, 
            detail=f"sort_by must be one of: {', '.join(valid_sort_fields)}"
        )
    
    event_manager = EventManager(db)
    events = event_manager.list_events(filter, skip, limit, sort_by, sort_order)
    
    # Convert events to JSON-serializable format
    events_json = []
    for event in events:
        events_json.append({
            "id": event.id,
            "timestamp": event.timestamp.isoformat(),  # Required by EventSchema
            "type": event.type,
            "sub_type": event.sub_type,
            "status": event.status,
            "description": event.description,
            "details": event.details,
            "has_attachment": event.has_attachment,
            "formatted_timestamp": event.formatted_timestamp
        })
    
    return events_json

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
            if event.attachment_mime_type.startswith('application/json'):
                # Only wrap JSON content in a JSON response
                return {"content": content}
            # Return plain text directly
            return Response(
                content=content,
                media_type=event.attachment_mime_type
            )
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