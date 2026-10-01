from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class OfficialRate:
    source: str
    currency: str
    base_currency: str
    rate: Decimal
    rate_date: date
    fetched_at: datetime