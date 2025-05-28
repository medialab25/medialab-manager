import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
from pathlib import Path
import mimetypes

class NotifyManager:
    def __init__(self):
        self.config = self._load_config()
        self.smtp_settings = self.config["NOTIFICATION"]

    def _load_config(self) -> dict:
        config_path = Path("config.json")
        with open(config_path) as f:
            return json.load(f)

    def send_mail(self, to: str, subject: str, body: str, attachment_path: str = None) -> None:
        msg = MIMEMultipart()
        msg["From"] = self.smtp_settings["SMTP_FROM"]
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        if attachment_path:
            # Get the MIME type of the file
            mime_type, _ = mimetypes.guess_type(attachment_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'
            
            # Create the attachment
            with open(attachment_path, 'rb') as attachment:
                part = MIMEBase(*mime_type.split('/'))
                part.set_payload(attachment.read())
            
            # Encode the attachment
            encoders.encode_base64(part)
            
            # Add header
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={Path(attachment_path).name}'
            )
            
            msg.attach(part)
        
        with smtplib.SMTP(self.smtp_settings["SMTP_RELAY"], self.smtp_settings["SMTP_PORT"]) as server:
            server.send_message(msg) 