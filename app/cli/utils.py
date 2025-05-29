"""Common utilities for CLI commands."""

import httpx
from rich.console import Console
from app.core.settings import settings

console = Console()

def get_server_url() -> str:
    """Get the server URL based on settings"""
    return f"http://{settings.HOST}:{settings.PORT}"

def get_http_client() -> httpx.Client:
    """Get an HTTP client with default timeout"""
    return httpx.Client(timeout=30.0)  # 30 second timeout

def handle_server_error(error: Exception) -> None:
    """Handle common server connection errors"""
    if isinstance(error, httpx.ConnectError):
        console.print("Could not connect to server. Make sure it's running.", style="red")
    elif isinstance(error, httpx.TimeoutException):
        console.print("Request timed out. The server might be busy or not responding.", style="red")
    else:
        console.print(f"An error occurred: {str(error)}", style="red") 