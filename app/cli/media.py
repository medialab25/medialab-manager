"""Media management CLI module.

This module provides command-line interface functionality for managing media-related operations.
"""

import typer

from app.core.settings import settings

media_app = typer.Typer(help="Media management commands")

@media_app.command()
def config():
    """Show the current configuration"""
    typer.echo("Current configuration:")
    for key, value in settings.dict().items():
        typer.echo(f"{key}: {value}")

if __name__ == "__main__":
    media_app()
