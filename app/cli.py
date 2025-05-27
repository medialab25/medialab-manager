#!/usr/bin/env python3
import typer
import logging
import sys
from pathlib import Path

# Import project settings
from app.core.settings import settings
from app.cli.media import media_app

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOG_FILE)
    ]
)

logger = logging.getLogger(__name__)

app = typer.Typer()
app.add_typer(media_app, name="media", help="Media management commands")

@app.command()
def start(
    host: str = typer.Option(settings.HOST, "--host", "-h", help="Host to run the server on"),
    port: int = typer.Option(settings.PORT, "--port", "-p", help="Port to run the server on"),
    debug: bool = typer.Option(settings.DEBUG, "--debug", "-d", help="Run in debug mode")
):
    """Start the MediaLab Manager server"""
    from app.main import run_service
    logger.info(f"Starting server on {host}:{port}")
    run_service()

@app.command()
def version():
    """Show the current version of MediaLab Manager"""
    typer.echo(f"MediaLab Manager version: {settings.VERSION}")

if __name__ == "__main__":
    app() 