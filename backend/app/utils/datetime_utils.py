from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """Returns current UTC datetime as offset-naive for consistent database storage and comparison."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ensure_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Converts offset-aware datetime to UTC and removes tzinfo for safe SQLite comparisons."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
