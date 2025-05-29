from enum import Enum

class EventType(str, Enum):
    NOTIFY = "notify"
    BACKUP = "backup"

class SubEventType(str, Enum):
    EMAIL = "email"
    NTFY = "ntfy" 