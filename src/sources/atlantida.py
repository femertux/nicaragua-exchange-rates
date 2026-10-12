import re
from decimal import Decimal

import requests
from bs4 import BeautifulSoup

from src.models.exchange_rate import ExchangeRate
from src.utils.time_utils import (
    nicaragua_today,
    utc_now,
)


ATLANTIDA_URL = "https://bancoatlantida.com.ni/"


def parse_rate(
    text: str,
    label: str,
) -> Decimal:
    pattern = rf"{label}:\s*C\$\s*([\d.,]+)"

    match = re.search(
        pattern,
        text,
        re.IGNORECASE,
    )

    if match is None:
        raise ValueError(
            f"Atlantida {label} exchange rate not found"
        )

    return Decimal(
        match.group(1).replace(",", ".")
    )


def fetch_atlantida_rates() -> list[ExchangeRate]:
    response = requests.get(
        ATLANTIDA_URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html",
        },
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    container = soup.select_one(
        "div.moneda"
    )

    if container is None:
        raise ValueError(
            "Atlantida exchange rate container not found"
        )

    text = container.get_text(
        " ",
        strip=True,
    )

    buying = parse_rate(
        text,
        "Compra",
    )

    selling = parse_rate(
        text,
        "Venta",
    )

    if buying <= 0 or selling <= 0 or selling < buying:
        raise ValueError(
            "Invalid Atlantida exchange rates"
        )

    return [
        ExchangeRate(
            bank="ATLANTIDA",
            currency="USD",
            base_currency="NIO",
            buying=buying,
            selling=selling,
            rate_date=nicaragua_today(),
            fetched_at=utc_now(),
        )
    ]