"""Notification CLI module.

This module provides command-line interface functionality for sending notifications.
"""

import typer
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from rich.console import Console
from rich.panel import Panel
import json
from pathlib import Path

notification_app = typer.Typer(help="Notification commands")
console = Console()

def load_config() -> dict:
    """Load configuration from config.json"""
    config_path = Path("config.json")
    with open(config_path) as f:
        return json.load(f)

@notification_app.command()
def mail(
    to: str = typer.Argument(..., help="Recipient email address"),
    subject: str = typer.Argument(..., help="Email subject"),
    body: str = typer.Argument(..., help="Email body content")
):
    """Send an email using configured SMTP settings"""
    try:
        config = load_config()
        smtp_settings = config["NOTIFICATION"]
        
        # Create message
        msg = MIMEMultipart()
        msg["From"] = smtp_settings["SMTP_FROM"]
        msg["To"] = to
        msg["Subject"] = subject
        
        # Attach body
        msg.attach(MIMEText(body, "plain"))
        
        # Send email
        with smtplib.SMTP(smtp_settings["SMTP_RELAY"], smtp_settings["SMTP_PORT"]) as server:
            server.send_message(msg)
            
        console.print(Panel.fit("Email sent successfully", style="green"))
    except Exception as e:
        console.print(Panel.fit(f"Failed to send email: {str(e)}", style="red"))

if __name__ == "__main__":
    notification_app()
