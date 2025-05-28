import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from pathlib import Path

class NotifyManager:
    def __init__(self):
        self.config = self._load_config()
        self.smtp_settings = self.config["NOTIFICATION"]

    def _load_config(self) -> dict:
        config_path = Path("config.json")
        with open(config_path) as f:
            return json.load(f)

    def send_mail(self, to: str, subject: str, body: str) -> None:
        msg = MIMEMultipart()
        msg["From"] = self.smtp_settings["SMTP_FROM"]
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP(self.smtp_settings["SMTP_RELAY"], self.smtp_settings["SMTP_PORT"]) as server:
            server.send_message(msg) 