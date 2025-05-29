import mimetypes
from pathlib import Path
import re

# Add MIME type mappings for Markdown files
mimetypes.add_type('text/markdown', '.md')
mimetypes.add_type('text/markdown', '.markdown')
mimetypes.add_type('text/markdown', '.mdown')

# Add MIME type mappings for shell scripts
mimetypes.add_type('text/x-shellscript', '.sh')
mimetypes.add_type('text/x-shellscript', '.bash')
mimetypes.add_type('text/x-shellscript', '.zsh')

# Add MIME type mappings for HTML files
mimetypes.add_type('text/html', '.html')
mimetypes.add_type('text/html', '.htm')
mimetypes.add_type('text/html', '.xhtml')

def is_markdown_content(content: bytes) -> bool:
    """Check if content appears to be Markdown by looking for common patterns"""
    try:
        text = content.decode('utf-8', errors='ignore')
        # Common Markdown patterns
        patterns = [
            r'^#\s',  # Headers
            r'^\*\s',  # Unordered lists
            r'^\d+\.\s',  # Ordered lists
            r'\[.*\]\(.*\)',  # Links
            r'^\s*```',  # Code blocks
            r'^\s*---',  # Horizontal rules
            r'^\s*>\s',  # Blockquotes
            r'^\s*[-*+]\s',  # List items
        ]
        return any(re.search(pattern, text, re.MULTILINE) for pattern in patterns)
    except:
        return False

def get_attachment_data(attachment_path: str) -> tuple[bytes, str]:
    """Get file data and mime type from a file path"""
    with open(attachment_path, 'rb') as attachment:
        path = Path(attachment_path)
        
        # Read content for content-based detection
        content = attachment.read()
        attachment.seek(0)  # Reset file pointer
        
        # Try to get MIME type from extension first
        mime_type, _ = mimetypes.guess_type(str(path))
        
        # If no MIME type found or it's octet-stream, try content-based detection
        if mime_type is None or mime_type == 'application/octet-stream':
            # Check for Markdown content
            if path.suffix.lower() in ['.md', '.markdown', '.mdown'] or is_markdown_content(content):
                mime_type = 'text/markdown'
            # Check for shell script content
            elif path.suffix.lower() in ['.sh', '.bash', '.zsh'] or content.startswith(b'#!/bin/') or content.startswith(b'#!/usr/bin/'):
                mime_type = 'text/x-shellscript'
            # Check for HTML content
            elif path.suffix.lower() in ['.html', '.htm', '.xhtml'] or content.startswith(b'<!DOCTYPE') or content.startswith(b'<html'):
                mime_type = 'text/html'
            # Check for other text content
            elif content.startswith(b'#') or content.startswith(b'<!') or content.startswith(b'<?xml'):
                mime_type = 'text/plain'
            else:
                mime_type = 'application/octet-stream'
        
        return content, mime_type 