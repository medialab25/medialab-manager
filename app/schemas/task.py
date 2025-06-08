from pydantic import BaseModel
from typing import Optional

class TaskToggleAPIRequest(BaseModel):
    enabled: bool

class TaskStartAPIRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    group: str = "other"

class TaskEndAPIRequest(BaseModel):
    status: str = "success"

class TaskCreateAPIRequest(BaseModel):
    name: str
    description: str
    group: str = "other"
    task_type: str = "external"
    enabled: bool = True
    host_url: Optional[str] = None
    hours: Optional[int] = None
    minutes: Optional[int] = None
    seconds: Optional[int] = None
    cron_hour: Optional[str] = None
    cron_minute: Optional[str] = None
    cron_second: Optional[str] = None 