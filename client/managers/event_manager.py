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

    async def notify_task_start(self, task_id: str) -> bool:
        """Notify that a task has started"""
        try:
            await self.ensure_session()
            async with self.session.post(f"{self.server_url}/tasks/{task_id}/notify-start") as response:
                if response.status == 200:
                    logger.info(f"Successfully notified task start: {task_id}")
                    return True
                else:
                    logger.error(f"Failed to notify task start: {task_id}. Status: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error notifying task start {task_id}: {str(e)}")
            return False

    async def notify_task_end(self, task_id: str) -> bool:
        """Notify that a task has completed successfully"""
        try:
            await self.ensure_session()
            async with self.session.post(f"{self.server_url}/tasks/{task_id}/notify-end") as response:
                if response.status == 200:
                    logger.info(f"Successfully notified task end: {task_id}")
                    return True
                else:
                    logger.error(f"Failed to notify task end: {task_id}. Status: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error notifying task end {task_id}: {str(e)}")
            return False

    async def notify_task_error(self, task_id: str, error_message: str) -> bool:
        """Notify that a task has encountered an error"""
        try:
            await self.ensure_session()
            async with self.session.post(
                f"{self.server_url}/tasks/{task_id}/notify-error",
                params={"error_message": error_message}
            ) as response:
                if response.status == 200:
                    logger.info(f"Successfully notified task error: {task_id}")
                    return True
                else:
                    logger.error(f"Failed to notify task error: {task_id}. Status: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error notifying task error {task_id}: {str(e)}")
            return False

# Create a singleton instance
event_manager = EventManager() 