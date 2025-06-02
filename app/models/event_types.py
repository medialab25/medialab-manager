from enum import Enum

class EventType(str, Enum):
    NONE = "none"
    NOTIFY = "notify"
    BACKUP = "backup"
    TASK = "task"

class SubEventType(str, Enum):
    NONE = "none"
    EMAIL = "email"
    NTFY = "ntfy"
    SNAPRAID = "snapraid"
    
class Status(str, Enum):
    """Status enum for event status values."""
    INFO = "info"
    SUCCESS = "success"
    ERROR = "error" 