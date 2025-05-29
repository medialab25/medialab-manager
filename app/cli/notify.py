"""Notify CLI module."""

import typer
import httpx
from rich.panel import Panel
from pathlib import Path

from app.cli.utils import get_server_url, console, handle_server_error

notify_app = typer.Typer(help="Notify commands")

@notify_app.command()
def mail(
    to: str = typer.Option(..., "--to", "-t", help="Recipient email address"),
    subject: str = typer.Option(..., "--subject", "-s", help="Email subject"),
    body: str = typer.Option(..., "--body", "-b", help="Email body content"),
    attachment: Path = typer.Option(None, "--attachment", "-a", help="Path to file attachment"),
    attachment_name: str = typer.Option(None, "--attachment-name", "-n", help="Custom name for the attachment file")
):
    """Send an email using the notification API"""
    try:
        with httpx.Client() as client:
            files = {}
            data = {"to": to, "subject": subject, "body": body}
            
            if attachment:
                if not attachment.exists():
                    console.print(Panel.fit(f"Attachment file not found: {attachment}", style="red"))
                    return
                # Use custom attachment name if provided, otherwise use original filename
                filename = attachment_name if attachment_name else attachment.name
                files["attachment"] = (filename, open(attachment, "rb"))
            
            response = client.post(
                f"{get_server_url()}/api/notify/mail",
                data=data,
                files=files
            )
            
            if response.status_code == 200:
                console.print(Panel.fit("Email sent successfully", style="green"))
            else:
                console.print(Panel.fit(f"Failed to send email: {response.text}", style="red"))
    except Exception as e:
        handle_server_error(e)
    finally:
        if attachment and "files" in locals():
            files["attachment"][1].close()

if __name__ == "__main__":
    notify_app() 