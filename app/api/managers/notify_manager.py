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
from app.models.notification import Notification
from app.core.database import DBManager

logger = logging.getLogger(__name__)

class NotifyManager:
    def __init__(self, db: Session = None):
        self.config = self._load_config()
        self.smtp_settings = self.config["NOTIFICATION"]
        self.db_manager = DBManager(Notification, db) if db else None
        self.from_email = self.smtp_settings["SMTP_FROM"]
        self.to_email = self.smtp_settings["SMTP_TO"]

    def _load_config(self) -> dict:
        config_path = Path("config.json")
        with open(config_path) as f:
            return json.load(f)

    def send_system_notification(self, type: str, sub_type: str, status: str, title: str, details: str, attachment_path: str = None, parent_id: int = None) -> Notification:
        notification = None
        if self.db_manager:
            attachment_data = None
            mime_type = None

            if attachment_path:
                attachment_data, mime_type = self._get_attachment_data(attachment_path)

            notification = self.add_notification(
                type=type,
                sub_type=sub_type,
                status=status,
                title=title,
                details=details,
                has_attachment=bool(attachment_path),
                attachment_data=attachment_data,
                attachment_mime_type=mime_type,
                parent_id=parent_id
            )

        self.send_mail(to=self.to_email, subject=title, body=details, attachment_path=attachment_path)
        return notification

    def add_notification(self, type: str, sub_type: str, status: str, title: str, details: str, attachment_data: bytes = None, mime_type: str = None, parent_id: int = None) -> Notification:
        print("DEBUG: Entering add_notification")  # Debug print
        notification = None
        if self.db_manager:
            notification = self.db_manager.create(
                type=type,
                sub_type=sub_type,
                status=status,
                title=title,
                details=details,
                has_attachment=bool(attachment_data),
                attachment_data=attachment_data,
                attachment_mime_type=mime_type,
                parent_id=parent_id
            )

            # Get total count of notifications
            total_count = self.db_manager.db.query(Notification).count()
            logger.debug(f"Total notifications in database: {total_count}")

        return notification

    def send_mail(self, to: str, subject: str, body: str, attachment_path: str = None, filename: str = None, notification: Notification = None) -> Notification:
        status = "passed"
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
            status = "failed"
            details = f"{body}\n\nError: {str(e)}"

        self.add_notification(
            type="email",
            status=status,
            title=subject,
            details=details,
        )
        return notification
    
    def _get_attachment_data(self, attachment_path: str) -> tuple[bytes, str]:
        with open(attachment_path, 'rb') as attachment:
            mime_type, _ = mimetypes.guess_type(attachment_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'
            return attachment.read(), mime_type