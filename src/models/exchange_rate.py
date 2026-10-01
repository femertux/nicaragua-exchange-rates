from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class ExchangeRate:
    bank: str
    currency: str
    base_currency: str
    buying: Decimal
    selling: Decimal
    rate_date: date
    fetched_at: datetime