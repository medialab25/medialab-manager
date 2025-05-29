"""Event management CLI module.

This module provides command-line interface functionality for managing events.
"""

import typer
import httpx
from rich.panel import Panel
from datetime import datetime

from app.cli.utils import get_server_url, console, handle_server_error, get_http_client

event_app = typer.Typer(help="Event management commands")

@event_app.command()
def test():
    """Test event creation and retrieval"""
    try:
        with get_http_client() as client:
            # Create a test event
            test_event = {
                "type": "system",
                "sub_type": "test",
                "status": "success",
                "title": "Test Event",
                "details": f"This is a test event created at {datetime.now()}"
            }
            
            # Create the event
            create_response = client.post(
                f"{get_server_url()}/api/events/",
                json=test_event
            )
            
            if create_response.status_code != 200:
                console.print(Panel.fit(f"Failed to create test event: {create_response.text}", style="red"))
                return
                
            event_id = create_response.json()["id"]
            console.print(Panel.fit(f"Test event created with ID: {event_id}", style="green"))
            
            # Retrieve the event
            get_response = client.get(f"{get_server_url()}/api/events/{event_id}")
            
            if get_response.status_code == 200:
                event_data = get_response.json()
                console.print(Panel.fit(
                    f"Successfully retrieved event:\n"
                    f"ID: {event_data['id']}\n"
                    f"Type: {event_data['type']}\n"
                    f"Status: {event_data['status']}\n"
                    f"Title: {event_data['title']}\n"
                    f"Details: {event_data['details']}",
                    style="green"
                ))
            else:
                console.print(Panel.fit(f"Failed to retrieve test event: {get_response.text}", style="red"))
                
    except Exception as e:
        handle_server_error(e)

if __name__ == "__main__":
    event_app()
