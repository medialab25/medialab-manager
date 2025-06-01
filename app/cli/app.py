import typer
import logging
import sys
import httpx
import signal
import os
from rich.panel import Panel
from pathlib import Path

from app.core.settings import settings
from app.cli.media import media_app
from app.cli.notify import notify_app
from app.cli.event import event_app
from app.cli.utils import get_server_url, console, handle_server_error

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

app = typer.Typer(help="MediaLab Manager CLI")

app.add_typer(media_app, name="media", help="Media management commands")
app.add_typer(notify_app, name="notify", help="Notification commands")
app.add_typer(event_app, name="event", help="Event management commands")

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
    except Exception as e:
        handle_server_error(e)

@app.command()
def version():
    """Show the current version of MediaLab Manager"""
    typer.echo(f"MediaLab Manager version: {settings.VERSION}")

@app.command()
def stop():
    """Stop the MediaLab Manager server"""
    try:
        # First check if server is running
        with httpx.Client() as client:
            try:
                response = client.get(f"{get_server_url()}/")
                if response.status_code != 200:
                    console.print(Panel.fit("Server is not running", style="yellow"))
                    return
            except Exception:
                console.print(Panel.fit("Server is not running", style="yellow"))
                return

        # Try systemd first
        try:
            result = os.system("systemctl is-active --quiet medialab-manager")
            if result == 0:
                # Service is running under systemd
                stop_result = os.system("sudo systemctl stop medialab-manager")
                if stop_result == 0:
                    console.print(Panel.fit("Server stopped via systemd", style="green"))
                else:
                    console.print(Panel.fit("Failed to stop systemd service", style="red"))
                return
        except Exception:
            pass

        # If not running under systemd, try direct process management
        pid = None
        try:
            # Read the PID file if it exists
            pid_file = Path.home() / "medialab-manager" / "medialab-manager.pid"
            if pid_file.exists():
                with open(pid_file) as f:
                    pid = int(f.read().strip())
        except Exception:
            pass

        if pid:
            try:
                # Try to stop gracefully first
                os.kill(pid, signal.SIGTERM)
                console.print(Panel.fit("Server stop signal sent. Waiting for graceful shutdown...", style="yellow"))
                
                # Wait a bit for graceful shutdown
                import time
                time.sleep(2)
                
                # Check if process is still running
                try:
                    os.kill(pid, 0)
                    # If we get here, process is still running, force kill
                    os.kill(pid, signal.SIGKILL)
                    console.print(Panel.fit("Server forcefully stopped", style="red"))
                except OSError:
                    console.print(Panel.fit("Server stopped gracefully", style="green"))
            except ProcessLookupError:
                console.print(Panel.fit("Server process not found", style="yellow"))
            except PermissionError:
                console.print(Panel.fit("Permission denied. Try running with sudo if using systemd", style="red"))
        else:
            console.print(Panel.fit("Could not find running server process", style="yellow"))
    except Exception as e:
        handle_server_error(e)

if __name__ == "__main__":
    app()
