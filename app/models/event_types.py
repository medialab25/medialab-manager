from enum import Enum

class EventType(str, Enum):
    NOTIFY = "notification"
    BACKUP = "backup"

class SubEventType(str, Enum):
    EMAIL = "email"
    NTFY = "ntfy" 