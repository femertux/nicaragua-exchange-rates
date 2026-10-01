from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo


NICARAGUA_TIMEZONE = ZoneInfo(
    "America/Managua"
)


def nicaragua_today() -> date:
    return datetime.now(
        NICARAGUA_TIMEZONE
    ).date()


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )