import os
import logging
from typing import Dict, Any
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class EventManager:
    def __init__(self):
        self.server_url = os.getenv("SERVER_URL", "http://192.168.10.10:4800")
        self.events = []
        self.client = httpx.AsyncClient()

    async def record_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record an event and send it to the server"""
        event = {
            "type": event_type,
            "sub_type": data.get("sub_type", "none"),
            "status": data.get("status", "info"),
            "description": data.get("description", ""),
            "details": str(data),
            "timestamp": datetime.now().isoformat()
        }
        
        # Store locally
        self.events.append(event)
        logger.info(f"Recorded event: {event_type}")
        
        # Send to server
        try:
            response = await self.client.post(
                f"{self.server_url}/api/events/",
                json=event
            )
            response.raise_for_status()
            logger.info(f"Event sent to server successfully: {event_type}")
        except Exception as e:
            logger.error(f"Failed to send event to server: {str(e)}")

    async def close(self) -> None:
        """Clean up resources"""
        await self.client.aclose()

event_manager = EventManager() 