import typer
import logging
import sys
import httpx
from rich.console import Console
from rich.panel import Panel

from app.core.settings import settings
from app.cli.media import media_app
from app.cli.notification import notification_app

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

app = typer.Typer(help="MediaVault Manager CLI")
console = Console()

app.add_typer(media_app, name="media", help="Media management commands")
app.add_typer(notification_app, name="notify", help="Notification commands")

def get_server_url() -> str:
    """Get the server URL based on settings"""
    return f"http://{settings.HOST}:{settings.PORT}"

@app.command()
def start(
    host: str = typer.Option(settings.HOST, "--host", "-h", help="Host to run the server on"),
    port: int = typer.Option(settings.PORT, "--port", "-p", help="Port to run the server on"),
    debug: bool = typer.Option(settings.DEBUG, "--debug", "-d", help="Run in debug mode")
):
    """Start the MediaLab Manager server"""
    from app.main import run_service
    logger.info(f"Starting server on {host}:{port}")
    run_service(debug=debug)

@app.command()
def status():
    """Check if the server is running and get its status"""
    try:
        with httpx.Client() as client:
            response = client.get(f"{get_server_url()}/")
            if response.status_code == 200:
                console.print(Panel.fit("Server is running", style="green"))
            else:
                console.print(Panel.fit(f"Server returned status code: {response.status_code}", style="yellow"))
    except httpx.ConnectError:
        console.print(Panel.fit("Server is not running", style="red"))

@app.command()
def version():
    """Show the current version of MediaLab Manager"""
    typer.echo(f"MediaLab Manager version: {settings.VERSION}")

if __name__ == "__main__":
    app()
