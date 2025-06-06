"""Media management CLI module.

This module provides command-line interface functionality for managing media-related operations.
"""

import typer
import httpx
from rich.console import Console
from rich.panel import Panel

from app.core.settings import settings
from app.cli.utils import get_server_url, console, handle_server_error

media_app = typer.Typer(help="Media management commands")

def get_server_url() -> str:
    """Get the server URL based on settings"""
    return f"http://{settings.HOST}:{settings.PORT}"

@media_app.command()
def config():
    """Show the current configuration"""
    typer.echo("Current configuration:")
    for key, value in settings.model_dump().items():
        typer.echo(f"{key}: {value}")

@media_app.command()
def refresh():
    """Refresh the media library"""
    try:
        with httpx.Client() as client:
            response = client.post(f"{get_server_url()}/api/media/refresh")
            if response.status_code == 200:
                console.print(Panel.fit("Media refresh completed successfully", style="green"))
            else:
                console.print(Panel.fit(f"Media refresh failed with status code: {response.status_code}", style="red"))
    except Exception as e:
        handle_server_error(e)

@media_app.command()
def merge():
    """Merge media files"""
    try:
        with httpx.Client() as client:
            response = client.post(f"{get_server_url()}/api/media/merge")
            if response.status_code == 200:
                console.print(Panel.fit("Media merge completed successfully", style="green"))
            else:
                console.print(Panel.fit(f"Media merge failed with status code: {response.status_code}", style="red"))
    except Exception as e:
        handle_server_error(e)

if __name__ == "__main__":
    media_app()
