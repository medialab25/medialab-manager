import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
from pathlib import Path
import mimetypes
import logging
from sqlalchemy.orm import Session
from app.core.database import DBManager

logger = logging.getLogger(__name__)

class NotifyManager:
    def __init__(self, db: Session = None):
        self.config = self._load_config()
        self.smtp_settings = self.config["NOTIFICATION"]
        self.from_email = self.smtp_settings["SMTP_FROM"]
        self.to_email = self.smtp_settings["SMTP_TO"]

    def _load_config(self) -> dict:
        config_path = Path("config.json")
        with open(config_path) as f:
            return json.load(f)

    def send_mail(self, to: str, subject: str, body: str, attachment_path: str = None, filename: str = None) -> bool:
        try:
            
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
                attachment_data = self._get_attachment_data(attachment_path)
                part = MIMEBase(*mime_type.split('/'))
                part.set_payload(attachment_data)
                
                # Encode the attachment
                encoders.encode_base64(part)
                
                # Add header with custom filename if provided, otherwise use the original filename
                attachment_filename = filename if filename else Path(attachment_path).name
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={attachment_filename}'
                )
                
                msg.attach(part)

            with smtplib.SMTP(self.smtp_settings["SMTP_RELAY"], self.smtp_settings["SMTP_PORT"]) as server:
                server.send_message(msg)

        except Exception as e:
            return False
        
        return True

    
    def _get_attachment_data(self, attachment_path: str) -> tuple[bytes, str]:
        with open(attachment_path, 'rb') as attachment:
            mime_type, _ = mimetypes.guess_type(attachment_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'
            return attachment.read(), mime_type