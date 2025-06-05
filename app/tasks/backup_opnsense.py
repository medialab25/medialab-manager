#!/usr/bin/env python3

import os
import sys
import logging
import requests
import datetime
from pathlib import Path
from typing import Optional
import shutil
from urllib3.exceptions import InsecureRequestWarning
from app.utils.event_utils import EventManagerUtil
from app.utils.file_utils import AttachDataMimeType

# Disable SSL warnings since we're using self-signed certificates
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Configuration
BACKUP_DIR = "/srv/system-backups/opnsense-remote"
#LOG_FILE = "/var/log/opnsense_backup.log"
API_KEY = "k3EJWEzDM5PvDpIZTlOMn0hYvARuWGNbUDE6lltAipN8i4Xs+2IHzv2/i/PWJ3ts/+YD3bXJpJmZtuTU"
API_SECRET = "CL+zsLuPzz5IY+zFeX9ot6LK96KXK44Oqu024oCbn8dShAkIJtl5+kU4QrbS0nlYK3cQviUiVzDybvJy"
OPNSENSE_HOST = "192.168.2.1"
MAX_BACKUPS = 30

# Configure logging
#logging.basicConfig(
#    level=logging.INFO,
#    format='%(asctime)s - %(message)s',
#    handlers=[
#        logging.FileHandler(LOG_FILE),
#        logging.StreamHandler()
#    ]
#)
logger = logging.getLogger(__name__)

def load_environment_variables() -> None:
    """Load environment variables from services.env file."""
    env_file = "/root/media-stacks/services.env"
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip().strip('"\'')
                    os.environ[key] = value

def test_api_connection() -> bool:
    """Test connectivity to the OPNsense API."""
    logger.info("Testing API connection...")
    
    session = requests.Session()
    session.auth = (API_KEY, API_SECRET)
    session.verify = False
    
    try:
        # Test basic API connectivity
        response = session.get(f"https://{OPNSENSE_HOST}/api/core/system/version")
        response.raise_for_status()
        
        # Test backup API endpoint
        response = session.get(f"https://{OPNSENSE_HOST}/api/core/backup/list")
        response.raise_for_status()
        
        logger.info("API connection test successful")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"ERROR: API connection test failed: {str(e)}")
        return False

def cleanup_old_backups() -> None:
    """Remove old backups, keeping only the last MAX_BACKUPS."""
    logger.info(f"Cleaning up old backups, keeping last {MAX_BACKUPS}...")
    
    backup_dir = Path(BACKUP_DIR)
    if not backup_dir.exists():
        return
    
    # Get list of backup files sorted by modification time
    backup_files = sorted(
        backup_dir.glob("*.xml"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    # Remove excess backups
    for old_file in backup_files[MAX_BACKUPS:]:
        logger.info(f"Removing old backup: {old_file.name}")
        old_file.unlink()

def get_latest_backup() -> bool:
    """Download the latest backup from OPNsense API."""
    logger.info("Getting latest backup from OPNsense API...")
    
    # Create backup directory if it doesn't exist
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Generate backup filename
    backup_name = f"config-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.xml"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    
    session = requests.Session()
    session.auth = (API_KEY, API_SECRET)
    session.verify = False
    
    try:
        response = session.get(
            f"https://{OPNSENSE_HOST}/api/core/backup/download/this",
            stream=True
        )
        response.raise_for_status()
        
        with open(backup_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Successfully downloaded backup to {backup_path}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"ERROR: Failed to download backup: {str(e)}")
        return False

def backup_opnsense() -> str:
    """
    Main function to execute the OPNsense backup process.
    This is the entry point for the task system.
    
    Returns:
        str: Status message about the backup operation
    """
    # Add event before task execution
    with EventManagerUtil.get_event_manager() as event_manager:
        event_manager.add_event(
            type="backup",
            sub_type="opnsense",
            status="info",
            description="Starting OPNsense backup process",
            details="Initiating backup of OPNsense configuration"
        )
    
    # Check if running on Linux
    if sys.platform != "linux":
        error_msg = "This script is designed for Linux"
        logger.error(error_msg)
        with EventManagerUtil.get_event_manager() as event_manager:
            event_manager.add_event(
                type="backup",
                sub_type="opnsense",
                status="error",
                description="Backup failed",
                details=error_msg
            )
        raise Exception(error_msg)
    
    # Load environment variables
    load_environment_variables()
    
    # Test API connection before proceeding
    if not test_api_connection():
        error_msg = "API connection test failed"
        logger.error(f"ERROR: {error_msg}")
        with EventManagerUtil.get_event_manager() as event_manager:
            event_manager.add_event(
                type="backup",
                sub_type="opnsense",
                status="error",
                description="Backup failed",
                details=error_msg
            )
        raise Exception(error_msg)
    
    # Get latest backup from API
    if get_latest_backup():
        success_msg = "Backup completed successfully"
        logger.info(success_msg)
        # Clean up old backups after successful backup
        cleanup_old_backups()
        
        with EventManagerUtil.get_event_manager() as event_manager:
            event_manager.add_event(
                type="backup",
                sub_type="opnsense",
                status="success",
                description="Backup completed",
                details=success_msg
            )
        return success_msg
    else:
        error_msg = "Failed to get latest backup from API"
        logger.error(f"ERROR: {error_msg}")
        with EventManagerUtil.get_event_manager() as event_manager:
            event_manager.add_event(
                type="backup",
                sub_type="opnsense",
                status="error",
                description="Backup failed",
                details=error_msg
            )
        raise Exception(error_msg)

if __name__ == "__main__":
    backup_opnsense() 