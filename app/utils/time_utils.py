from datetime import datetime
from zoneinfo import ZoneInfo

LONDON_TZ = ZoneInfo("Europe/London")

def get_current_time() -> datetime:
    """Get current time in Europe/London timezone"""
    return datetime.now(LONDON_TZ)

def format_datetime(dt: datetime) -> str:
    """Format datetime as YYYY-MM-DD HH:MM:SS in Europe/London timezone"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=LONDON_TZ)
    return dt.astimezone(LONDON_TZ).strftime("%Y-%m-%d %H:%M:%S") 