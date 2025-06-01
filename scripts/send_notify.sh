#!/bin/bash

# Check if description is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <description> [details] [attachment_path]"
    echo "Example: $0 'System backup completed' 'Backup size: 1.2GB' '/path/to/backup.log'"
    exit 1
fi

# Get the arguments
DESCRIPTION="$1"
DETAILS="${2:-}"
ATTACHMENT_PATH="${3:-}"

# Base URL for the API (adjust if needed)
API_URL="http://192.168.10.10:4800/api"

# Prepare the JSON payload
JSON_PAYLOAD=$(cat <<EOF
{
    "type": "notification",
    "sub_type": "email",
    "status": "success",
    "description": "$DESCRIPTION",
    "details": "$DETAILS"
}
EOF
)

# Function to send the request
send_request() {
    if [ -n "$ATTACHMENT_PATH" ]; then
        # Send with attachment
        curl -X POST "${API_URL}/events/" \
            -H "Content-Type: application/json" \
            -d "$JSON_PAYLOAD" \
            -F "attachment=@${ATTACHMENT_PATH}"
    else
        # Send without attachment
        curl -X POST "${API_URL}/events/" \
            -H "Content-Type: application/json" \
            -d "$JSON_PAYLOAD"
    fi
}

# Send the request and capture the response
RESPONSE=$(send_request)

# Check if the request was successful
if [ $? -eq 0 ]; then
    echo "Notification sent successfully"
    echo "Response: $RESPONSE"
else
    echo "Failed to send notification"
    exit 1
fi 