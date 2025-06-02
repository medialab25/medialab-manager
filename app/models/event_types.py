from enum import Enum

class EventType(str, Enum):
    NONE = "None"
    NOTIFY = "Notify"
    BACKUP = "Backup"
    TASK = "Task"

class SubEventType(str, Enum):
    NONE = "None"
    EMAIL = "Email"
    NTFY = "Ntfy"
    SNAPRAID = "Snapraid"
    TASK_RUN = "Task Run"
    
class Status(str, Enum):
    """Status enum for event status values."""
    INFO = "Info"
    SUCCESS = "Success"
    ERROR = "Error" 