#!/bin/bash

# Default values
SERVER_URL="http://192.168.10.10:4800"
ATTACHMENT=""
ATTACHMENT_NAME=""

# Help message
show_help() {
    echo "Usage: $0 -t <to> -s <subject> -b <body> [-a <attachment>] [-n <attachment_name>] [-u <server_url>]"
    echo ""
    echo "Required arguments:"
    echo "  -t <to>              Recipient email address"
    echo "  -s <subject>         Email subject"
    echo "  -b <body>            Email body"
    echo ""
    echo "Optional arguments:"
    echo "  -a <attachment>      Path to attachment file"
    echo "  -n <attachment_name> Custom name for the attachment"
    echo "  -u <server_url>      Server URL (default: $SERVER_URL)"
    echo "  -h                   Show this help message"
    exit 1
}

# Parse command line arguments
while getopts "t:s:b:a:n:u:h" opt; do
    case $opt in
        t) TO="$OPTARG" ;;
        s) SUBJECT="$OPTARG" ;;
        b) BODY="$OPTARG" ;;
        a) ATTACHMENT="$OPTARG" ;;
        n) ATTACHMENT_NAME="$OPTARG" ;;
        u) SERVER_URL="$OPTARG" ;;
        h) show_help ;;
        ?) show_help ;;
    esac
done

# Check required arguments
if [ -z "$TO" ] || [ -z "$SUBJECT" ] || [ -z "$BODY" ]; then
    echo "Error: Missing required arguments"
    show_help
fi

# Add http:// to server URL if protocol is missing
if [[ ! $SERVER_URL =~ ^https?:// ]]; then
    SERVER_URL="http://$SERVER_URL"
fi

# Build the curl command
CURL_ARGS=(
    "-s"
    "-X" "POST"
    "-F" "to=$TO"
    "-F" "subject=$SUBJECT"
    "-F" "body=$BODY"
)

# Add attachment if provided
if [ ! -z "$ATTACHMENT" ]; then
    if [ ! -f "$ATTACHMENT" ]; then
        echo "Error: Attachment file not found: $ATTACHMENT"
        exit 1
    fi
    CURL_ARGS+=("-F" "attachment=@$ATTACHMENT")
    
    # Add attachment name if provided
    if [ ! -z "$ATTACHMENT_NAME" ]; then
        CURL_ARGS+=("-F" "attachment_name=$ATTACHMENT_NAME")
    fi
fi

# Add the server URL with the correct endpoint path
CURL_ARGS+=("$SERVER_URL/api/notify/mail")

# Execute the command
echo "Sending email..."
curl "${CURL_ARGS[@]}"
CURL_EXIT_CODE=$?

if [ $CURL_EXIT_CODE -ne 0 ]; then
    echo "Error: Failed to send email"
    exit 1
fi

echo "Email sent successfully" 