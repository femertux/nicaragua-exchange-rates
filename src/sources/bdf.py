from datetime import datetime, timezone
from decimal import Decimal

import requests
from bs4 import BeautifulSoup

from src.models.exchange_rate import ExchangeRate
from src.utils.time_utils import (
    nicaragua_today,
)


BDF_URL = "https://www.bdfnet.com/"


def parse_rate(container) -> tuple[Decimal, Decimal]:
    values = []

    for item in container.find_all("h5"):
        text = item.get_text(
            " ",
            strip=True,
        )

        if ":" not in text:
            continue

        _, value = text.split(":", 1)

        values.append(
            Decimal(value.strip())
        )

    if len(values) < 2:
        raise ValueError(
            "Invalid BDF exchange rate structure"
        )

    return values[0], values[1]


def fetch_bdf_rates() -> list[ExchangeRate]:
    response = requests.get(
        BDF_URL,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    dollar_container = soup.find(
        id="pills-dolar"
    )

    euro_container = soup.find(
        id="pills-euro"
    )

    if dollar_container is None:
        raise ValueError(
            "BDF USD exchange rate not found"
        )

    if euro_container is None:
        raise ValueError(
            "BDF EUR exchange rate not found"
        )

    usd_buying, usd_selling = parse_rate(
        dollar_container
    )

    eur_buying, eur_selling = parse_rate(
        euro_container
    )

    fetched_at = datetime.now(timezone.utc)

    return [
        ExchangeRate(
            bank="BDF",
            currency="USD",
            base_currency="NIO",
            buying=usd_buying,
            selling=usd_selling,
            rate_date=nicaragua_today(),
            fetched_at=fetched_at,
        ),
        ExchangeRate(
            bank="BDF",
            currency="EUR",
            base_currency="NIO",
            buying=eur_buying,
            selling=eur_selling,
            rate_date=nicaragua_today(),
            fetched_at=fetched_at,
        ),
    ]