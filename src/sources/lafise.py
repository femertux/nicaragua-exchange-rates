from datetime import datetime, timezone
from decimal import Decimal

import requests

from src.models.exchange_rate import ExchangeRate
from src.utils.time_utils import (
    nicaragua_today,
)


LAFISE_URL = (
    "https://www.lafise.com/"
    "OpenBankingProxy/obl/v1/banks/BLNI/rates"
)


def fetch_lafise_rates() -> list[ExchangeRate]:
    response = requests.get(
        LAFISE_URL,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    base_currency = data.get("base")

    if base_currency != "NIO":
        raise ValueError(
            f"Unexpected LAFISE base currency: {base_currency}"
        )

    rates = data.get("rates")

    if not rates:
        raise ValueError(
            "LAFISE response does not contain rates"
        )

    fetched_at = datetime.now(timezone.utc)

    result = []

    for currency in ("USD", "EUR"):
        currency_data = rates.get(currency)

        if not currency_data:
            raise ValueError(
                f"{currency} not found in LAFISE response"
            )

        buying = currency_data.get("buying")
        selling = currency_data.get("selling")

        if buying is None or selling is None:
            raise ValueError(
                f"Invalid {currency} rate in LAFISE response"
            )

        result.append(
            ExchangeRate(
                bank="LAFISE",
                currency=currency,
                base_currency=base_currency,
                buying=Decimal(str(buying)),
                selling=Decimal(str(selling)),
                rate_date=nicaragua_today(),
                fetched_at=fetched_at,
            )
        )

    return result