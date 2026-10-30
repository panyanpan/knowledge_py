from datetime import datetime, timezone


def utc_now() -> datetime:
    """MySQL DATETIME 无时区，统一存 naive UTC。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)
