import aiohttp
import logging
import json
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def get_server_url() -> str:
    """Get the main app server URL from the config file."""
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            server = config.get("server", {}).get("host", "192.168.10.10")
            port = config.get("server", {}).get("port", "4800")
            return f"http://{server}:{port}"
    except Exception as e:
        logger.error(f"Error loading server URL from config: {e}")
        return "http://192.168.10.10:4800"  # Fallback to default

class EventManager:
    def __init__(self):
        self.server_url = get_server_url()
        self.session: Optional[aiohttp.ClientSession] = None

    async def ensure_session(self):
        """Ensure we have an active aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def record_event(self, event_type: str, details: Dict, status: str = "success") -> bool:
        """
        Record an event by sending it to the main app's event endpoint.
        
        Args:
            event_type: Type of event (e.g., 'backup_started', 'backup_completed')
            details: Dictionary containing event details
            status: Status of the event ('success', 'error', etc.)
            
        Returns:
            bool: True if event was recorded successfully, False otherwise
        """
        try:
            await self.ensure_session()
            
            event_data = {
                "event_type": event_type,
                "details": details,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            async with self.session.post(
                f"{self.server_url}/api/events",
                json=event_data
            ) as response:
                if response.status == 200:
                    logger.info(f"Successfully recorded event: {event_type}")
                    return True
                else:
                    logger.error(f"Failed to record event: {event_type}. Status: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error recording event {event_type}: {str(e)}")
            return False

# Create a singleton instance
event_manager = EventManager() 