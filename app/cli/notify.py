"""Notify CLI module."""

import typer
import httpx
from rich.console import Console
from rich.panel import Panel
from app.core.settings import settings

notify_app = typer.Typer(help="Notify commands")
console = Console()

def get_server_url() -> str:
    """Get the server URL based on settings"""
    return f"http://{settings.HOST}:{settings.PORT}"

@notify_app.command()
def mail(
    to: str = typer.Option(..., "--to", "-t", help="Recipient email address"),
    subject: str = typer.Option(..., "--subject", "-s", help="Email subject"),
    body: str = typer.Option(..., "--body", "-b", help="Email body content")
):
    """Send an email using the notification API"""
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{get_server_url()}/api/notify/mail",
                json={"to": to, "subject": subject, "body": body}
            )
            if response.status_code == 200:
                console.print(Panel.fit("Email sent successfully", style="green"))
            else:
                console.print(Panel.fit(f"Failed to send email: {response.text}", style="red"))
    except httpx.ConnectError:
        console.print(Panel.fit("Could not connect to server. Make sure it's running.", style="red"))
    except Exception as e:
        console.print(Panel.fit(f"Failed to send email: {str(e)}", style="red"))

if __name__ == "__main__":
    notify_app() 