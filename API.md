# MediaLab Manager API Documentation

This document provides examples of how to interact with the MediaLab Manager API using curl commands.

## Base URL

All API endpoints are relative to the base URL:
```
http://localhost:4800
```

## Tasks API

### List All Tasks
```bash
curl -X GET "http://localhost:4800/tasks/"
```

### Toggle Task Status
```bash
# Enable a task
curl -X POST "http://localhost:4800/tasks/{task_id}/toggle" \
     -H "Content-Type: application/json" \
     -d '{"enabled": true}'

# Disable a task
curl -X POST "http://localhost:4800/tasks/{task_id}/toggle" \
     -H "Content-Type: application/json" \
     -d '{"enabled": false}'
```

### Run Task Immediately
```bash
curl -X POST "http://localhost:4800/tasks/{task_id}/run"
```

### Task Notifications

#### Notify Task Start
```bash
curl -X POST "http://localhost:4800/tasks/{task_id}/notify-start"
```

#### Notify Task End (Success)
```bash
curl -X POST "http://localhost:4800/tasks/{task_id}/notify-end"
```

#### Notify Task Error
```bash
# Basic error notification
curl -X POST "http://localhost:4800/tasks/{task_id}/notify-error"

# Error notification with message
curl -X POST "http://localhost:4800/tasks/{task_id}/notify-error?error_message=Failed%20to%20connect%20to%20database"
```

## Events API

### Create Event
```bash
# Basic event creation
curl -X POST "http://localhost:4800/api/events/" \
     -H "Content-Type: application/json" \
     -d '{
           "type": "system",
           "sub_type": "backup",
           "status": "success",
           "description": "Backup completed",
           "details": "Backup completed successfully at 2024-03-20 10:00:00"
         }'

# Create event with attachment
curl -X POST "http://localhost:4800/api/events/" \
     -H "Content-Type: application/json" \
     -d '{
           "type": "system",
           "sub_type": "backup",
           "status": "success",
           "description": "Backup completed",
           "details": "Backup completed successfully at 2024-03-20 10:00:00"
         }' \
     -F "attachment=@/path/to/your/file.txt"
```

The attachment can be any file type. The API will automatically detect the MIME type and store it with the event. You can later retrieve the attachment using the Get Event Attachment endpoint.

### Get Event by ID
```bash
curl -X GET "http://localhost:4800/api/events/{event_id}"
```

### List Events
```bash
# Basic listing (last 100 events)
curl -X GET "http://localhost:4800/api/events/"

# With filtering and sorting
curl -X GET "http://localhost:4800/api/events/?type=system&status=success&sort_by=timestamp&sort_order=desc"

# With pagination
curl -X GET "http://localhost:4800/api/events/?skip=0&limit=10"
```

### Get Event Attachment
```bash
# Get attachment content
curl -X GET "http://localhost:4800/api/events/{event_id}/attachment"
```

### Get Event Details
```bash
# Get formatted event details
curl -X GET "http://localhost:4800/api/events/{event_id}/details"
```

### Event Filter Parameters
- `type`: Filter by event type (e.g., "system", "task", "backup")
- `sub_type`: Filter by event sub-type
- `status`: Filter by status (e.g., "success", "error", "info")
- `description`: Search in event description
- `start_date`: Filter events after this date (ISO format)
- `end_date`: Filter events before this date (ISO format)
- `has_attachment`: Filter events with/without attachments (true/false)
- `parent_id`: Filter events by parent event ID

### Event Sort Parameters
- `sort_by`: Field to sort by (id, timestamp, type, status, description)
- `sort_order`: Sort order (asc or desc)

## CLI Commands

The MediaLab Manager also provides a CLI interface. Here are the main commands:

### Start Server
```bash
./mvm start
```

### Stop Server
```bash
./mvm stop
```

### Check Server Status
```bash
./mvm status
```

### Show Version
```bash
./mvm version
```

### Media Management
```bash
# List media
./mvm media list

# Scan media
./mvm media scan
```

### Event Management
```bash
# List events
./mvm event list

# Clear events
./mvm event clear
```

### Notification Management
```bash
# Send test notification
./mvm notify test
```

## Response Format

All API endpoints return JSON responses in the following format:

### Success Response
```json
{
    "status": "success",
    "message": "Operation completed successfully",
    "data": {} // Optional data field
}
```

### Error Response
```json
{
    "detail": "Error message describing what went wrong"
}
```

## Common HTTP Status Codes

- `200 OK`: Request succeeded
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

## Authentication

Currently, the API does not require authentication. This may change in future versions.

## Rate Limiting

There are no rate limits currently implemented. This may change in future versions.

## Examples

### Complete Task Lifecycle

Here's an example of a complete task lifecycle:

1. Start the task:
```bash
curl -X POST "http://localhost:4800/tasks/backup/notify-start"
```

2. If the task succeeds:
```bash
curl -X POST "http://localhost:4800/tasks/backup/notify-end"
```

3. If the task fails:
```bash
curl -X POST "http://localhost:4800/tasks/backup/notify-error?error_message=Backup%20failed%20due%20to%20disk%20space"
```

### Checking Task Status

To check the current status of all tasks:
```bash
curl -X GET "http://localhost:4800/tasks/" | jq
```

This will return a JSON object with tasks grouped by their group, including their current status, last run time, and other details.

### Event Management Example

Here's an example of creating and retrieving events:

1. Create a new event:
```bash
curl -X POST "http://localhost:4800/api/events/" \
     -H "Content-Type: application/json" \
     -d '{
           "type": "system",
           "sub_type": "backup",
           "status": "success",
           "description": "Backup completed",
           "details": "Backup completed successfully at 2024-03-20 10:00:00"
         }'
```

2. List recent events with filtering:
```bash
curl -X GET "http://localhost:4800/api/events/?type=system&status=success&sort_by=timestamp&sort_order=desc&limit=5" | jq
```

3. Get event details:
```bash
curl -X GET "http://localhost:4800/api/events/1/details" | jq
``` 