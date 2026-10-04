import os
from decimal import Decimal

import requests
from dotenv import load_dotenv

from src.models.exchange_rate import ExchangeRate
from src.utils.time_utils import (
    nicaragua_today,
    utc_now,
)


load_dotenv()


BAC_API_URL = os.getenv("BAC_API_URL")


def fetch_bac_rates() -> list[ExchangeRate]:
    if not BAC_API_URL:
        raise ValueError(
            "BAC_API_URL environment variable is missing"
        )

    response = requests.get(
        BAC_API_URL,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("bank") != "BAC":
        raise ValueError(
            "Invalid BAC API response"
        )

    rates = data.get("rates")

    if not isinstance(rates, list):
        raise ValueError(
            "BAC rates not found in API response"
        )

    fetched_at = utc_now()
    rate_date = nicaragua_today()

    exchange_rates = []

    for rate in rates:
        currency = rate.get("currency")
        base_currency = rate.get(
            "baseCurrency"
        )
        buying = rate.get("buying")
        selling = rate.get("selling")

        if not all(
            [
                currency,
                base_currency,
                buying,
                selling,
            ]
        ):
            raise ValueError(
                "Incomplete BAC rate"
            )

        exchange_rates.append(
            ExchangeRate(
                bank="BAC",
                currency=currency,
                base_currency=base_currency,
                buying=Decimal(buying),
                selling=Decimal(selling),
                rate_date=rate_date,
                fetched_at=fetched_at,
            )
        )

    if not exchange_rates:
        raise ValueError(
            "BAC API returned no rates"
        )

    return exchange_rates