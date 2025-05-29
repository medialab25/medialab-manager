import mimetypes
from pathlib import Path

def get_attachment_data(attachment_path: str) -> tuple[bytes, str]:
    """Get file data and mime type from a file path"""
    with open(attachment_path, 'rb') as attachment:
        mime_type, _ = mimetypes.guess_type(attachment_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        return attachment.read(), mime_type 