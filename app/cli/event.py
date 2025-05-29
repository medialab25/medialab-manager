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
    """Test event creation, retrieval, filtering, and sorting"""
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
            
            # Retrieve the event by ID
            get_response = client.get(f"{get_server_url()}/api/events/{event_id}")
            
            if get_response.status_code == 200:
                event_data = get_response.json()
                console.print(Panel.fit(
                    f"Successfully retrieved event by ID:\n"
                    f"ID: {event_data['id']}\n"
                    f"Type: {event_data['type']}\n"
                    f"Status: {event_data['status']}\n"
                    f"Title: {event_data['title']}\n"
                    f"Details: {event_data['details']}",
                    style="green"
                ))
            else:
                console.print(Panel.fit(f"Failed to retrieve test event: {get_response.text}", style="red"))
                return

            # Test filtering and sorting events
            filter_params = {
                "type": "system",
                "status": "success",
                "title": "Test Event",
                "sort_by": "timestamp",
                "sort_order": "desc"
            }
            
            filter_response = client.get(
                f"{get_server_url()}/api/events/",
                params=filter_params
            )
            
            if filter_response.status_code == 200:
                events = filter_response.json()
                if events:
                    console.print(Panel.fit(
                        f"Successfully filtered and sorted events:\n"
                        f"Found {len(events)} matching events\n"
                        f"Sorted by: {filter_params['sort_by']} ({filter_params['sort_order']})\n"
                        f"First event:\n"
                        f"ID: {events[0]['id']}\n"
                        f"Type: {events[0]['type']}\n"
                        f"Status: {events[0]['status']}\n"
                        f"Title: {events[0]['title']}\n"
                        f"Timestamp: {events[0]['timestamp']}",
                        style="green"
                    ))
                else:
                    console.print(Panel.fit("No events found matching the filter criteria", style="yellow"))
            else:
                console.print(Panel.fit(f"Failed to filter events: {filter_response.text}", style="red"))
                
    except Exception as e:
        handle_server_error(e)

if __name__ == "__main__":
    event_app()
