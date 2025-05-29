from typing import Optional, Dict, Any
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
from app.utils.file_utils import get_attachment_data
from app.models.event_types import EventType, SubEventType
from app.api.managers.event_manager import EventManager

logger = logging.getLogger(__name__)

class NotifyManager:
    """Manager class for handling email notifications and related events."""

    def __init__(self, db: Optional[Session] = None) -> None:
        """Initialize the NotifyManager with configuration and database session.

        Args:
            db: Optional SQLAlchemy database session
        """
        self.config = self._load_config()
        self.smtp_settings = self.config["NOTIFICATION"]
        self.from_email = self.smtp_settings["SMTP_FROM"]
        self.to_email = self.smtp_settings["SMTP_TO"]
        self.db = db
        self.event_manager = EventManager(db) if db else None

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json file.

        Returns:
            Dict containing configuration settings

        Raises:
            FileNotFoundError: If config.json is not found
            json.JSONDecodeError: If config.json is not valid JSON
        """
        config_path = Path("config.json")
        try:
            with open(config_path) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load config: {str(e)}")
            raise

    def _create_email_message(
        self, 
        to: str, 
        subject: str, 
        body: str, 
        attachment_path: Optional[str] = None,
        filename: Optional[str] = None
    ) -> MIMEMultipart:
        """Create an email message with optional attachment.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            attachment_path: Optional path to attachment file
            filename: Optional custom filename for attachment

        Returns:
            MIMEMultipart message object
        """
        msg = MIMEMultipart()
        msg["From"] = self.smtp_settings["SMTP_FROM"]
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        if attachment_path:
            msg = self._attach_file(msg, attachment_path, filename)

        return msg

    def _attach_file(
        self, 
        msg: MIMEMultipart, 
        attachment_path: str, 
        filename: Optional[str] = None
    ) -> MIMEMultipart:
        """Attach a file to the email message.

        Args:
            msg: Email message to attach file to
            attachment_path: Path to the file to attach
            filename: Optional custom filename for attachment

        Returns:
            MIMEMultipart message with attachment
        """
        mime_type, _ = mimetypes.guess_type(attachment_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'

        try:
            attachment_data, _ = get_attachment_data(attachment_path)
            part = MIMEBase(*mime_type.split('/'))
            part.set_payload(attachment_data)
            encoders.encode_base64(part)

            attachment_filename = filename if filename else Path(attachment_path).name
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={attachment_filename}'
            )
            msg.attach(part)
        except Exception as e:
            logger.error(f"Failed to attach file {attachment_path}: {str(e)}")
            raise

        return msg

    def _create_event(
        self,
        status: str,
        description: str,
        to: str,
        subject: str,
        body: str,
        attachment_path: Optional[str] = None,
        filename: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """Create an event record for the email notification.

        Args:
            status: Event status (success/error)
            description: Event description
            to: Recipient email
            subject: Email subject
            body: Email body
            attachment_path: Optional path to attachment
            filename: Optional custom filename
            error: Optional error message
        """
        if not self.event_manager:
            return

        details = {
            "to": to,
            "subject": subject,
            "has_attachment": bool(attachment_path),
            "body": body
        }

        if error:
            details["error"] = error

        self.event_manager.add_event(
            type=EventType.NOTIFY.value,
            sub_type=SubEventType.EMAIL.value,
            status=status,
            description=description,
            details=json.dumps(details),
            attachment_path=attachment_path if attachment_path else None
        )

    def send_mail(
        self,
        to: str,
        subject: str,
        body: str,
        attachment_path: Optional[str] = None,
        filename: Optional[str] = None
    ) -> bool:
        """Send an email with optional attachment.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            attachment_path: Optional path to attachment file
            filename: Optional custom filename for attachment

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            msg = self._create_email_message(to, subject, body, attachment_path, filename)

            with smtplib.SMTP(
                self.smtp_settings["SMTP_RELAY"],
                self.smtp_settings["SMTP_PORT"],
                timeout=30
            ) as server:
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to} with subject: {subject}")
            self._create_event(
                status="success",
                description=f"Email sent successfully to {to} with subject: {subject}",
                to=to,
                subject=subject,
                body=body
            )
            return True

        except Exception as e:
            error_msg = f"Failed to send email to {to} with subject: {subject}. Error: {str(e)}"
            logger.error(error_msg)
            self._create_event(
                status="error",
                description=error_msg,
                to=to,
                subject=subject,
                body=body,
                error=str(e)
            )
            return False