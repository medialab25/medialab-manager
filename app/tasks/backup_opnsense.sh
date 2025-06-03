#!/usr/bin/env bash

set -euo pipefail

# Import environment variables from services.env
if [ -f "/root/media-stacks/services.env" ]; then
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        case "$key" in
            \#*|"") continue ;;
        esac
        # Remove any quotes from the value
        value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
        # Export the variable
        export "$key=$value"
    done < "/root/media-stacks/services.env"
fi

# Configuration
BACKUP_DIR="/srv/system-backups/opnsense-remote"
LOG_FILE="/var/log/opnsense_backup.log"

API_KEY="k3EJWEzDM5PvDpIZTlOMn0hYvARuWGNbUDE6lltAipN8i4Xs+2IHzv2/i/PWJ3ts/+YD3bXJpJmZtuTU"
API_SECRET="CL+zsLuPzz5IY+zFeX9ot6LK96KXK44Oqu024oCbn8dShAkIJtl5+kU4QrbS0nlYK3cQviUiVzDybvJy"

OPNSENSE_HOST="192.168.2.1"
MAX_BACKUPS=30

# Check if running on Linux
if [ "$(uname)" != "Linux" ]; then
    echo "This script is designed for Linux"
    exit 1
fi

# Function to log messages
log_message() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ${message}" | tee -a "${LOG_FILE}"
}

# Function to test API connectivity
test_api_connection() {
    log_message "Testing API connection..."
    
    # Test basic API connectivity
    if ! curl -s -k -u "${API_KEY}:${API_SECRET}" "https://${OPNSENSE_HOST}/api/core/system/version" > /dev/null; then
        log_message "ERROR: Failed to connect to API"
        return 1
    fi
    
    # Test backup API endpoint
    if ! curl -s -k -u "${API_KEY}:${API_SECRET}" "https://${OPNSENSE_HOST}/api/core/backup/list" > /dev/null; then
        log_message "ERROR: Backup API endpoint not accessible"
        return 1
    fi
    
    log_message "API connection test successful"
    return 0
}

# Function to clean up old backups
cleanup_old_backups() {
    log_message "Cleaning up old backups, keeping last ${MAX_BACKUPS}..."
    
    # Get list of backups sorted by modification time (newest first)
    # and remove all but the last MAX_BACKUPS
    find "${BACKUP_DIR}" -type f -name "*.xml" -printf "%T@ %p\n" | \
    sort -nr | \
    tail -n +$((MAX_BACKUPS + 1)) | \
    cut -d' ' -f2- | \
    while read -r file; do
        log_message "Removing old backup: $(basename "${file}")"
        rm -f "${file}"
    done
}

# Create backup directory if it doesn't exist
if [ ! -d "${BACKUP_DIR}" ]; then
    mkdir -p "${BACKUP_DIR}"
    log_message "Created backup directory: ${BACKUP_DIR}"
fi

# Function to get latest backup from OPNsense API
get_latest_backup() {
    log_message "Getting latest backup from OPNsense API..."
    
    # Download the latest backup
    local backup_name="config-$(date +%Y%m%d-%H%M%S).xml"    
    log_message "Downloading backup: ${backup_name}"
    
    if ! curl -s -k -u "${API_KEY}:${API_SECRET}" "https://${OPNSENSE_HOST}/api/core/backup/download/this" -o "${BACKUP_DIR}/${backup_name}"; then
        log_message "ERROR: Failed to download backup"
        return 1
    fi
    
    log_message "Successfully downloaded backup to ${BACKUP_DIR}/${backup_name}"
    return 0
}

# Test API connection before proceeding
if ! test_api_connection; then
    log_message "ERROR: API connection test failed"
    exit 1
fi

# Get latest backup from API
if get_latest_backup; then
    log_message "Backup completed successfully"
    # Clean up old backups after successful backup
    cleanup_old_backups
else
    log_message "ERROR: Failed to get latest backup from API"
    exit 1
fi

log_message "Backup process completed"
exit 0 