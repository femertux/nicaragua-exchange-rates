from decimal import Decimal

import requests
from bs4 import BeautifulSoup

from src.models.exchange_rate import ExchangeRate
from src.utils.time_utils import (
    nicaragua_today,
    utc_now,
)


FICOHSA_URL = "https://www.ficohsa.ni/"


def parse_rate(element) -> Decimal:
    if element is None:
        raise ValueError(
            "Ficohsa exchange rate value not found"
        )

    text = element.get_text(
        " ",
        strip=True,
    )

    value = (
        text.replace("C$", "")
        .replace(" ", "")
        .replace(",", ".")
    )

    return Decimal(value)


def fetch_ficohsa_rates() -> list[ExchangeRate]:
    response = requests.get(
        FICOHSA_URL,
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
        ".gff-indicadores-divisas-ficohsa__container"
    )

    if container is None:
        raise ValueError(
            "Ficohsa exchange rate container not found"
        )

    currencies = {
        "USD": "value-one",
        "EUR": "value-two",
    }

    fetched_at = utc_now()
    rate_date = nicaragua_today()

    rates = []

    for currency, value_class in currencies.items():
        buying_element = container.select_one(
            f".gff-indicadores-divisas-ficohsa__buys-value.{value_class}"
        )

        selling_element = container.select_one(
            f".gff-indicadores-divisas-ficohsa__sale-value.{value_class}"
        )

        buying = parse_rate(
            buying_element
        )

        selling = parse_rate(
            selling_element
        )

        if buying <= 0 or selling <= 0 or selling < buying:
            raise ValueError(
                f"Invalid Ficohsa {currency} exchange rates"
            )

        rates.append(
            ExchangeRate(
                bank="FICOHSA",
                currency=currency,
                base_currency="NIO",
                buying=buying,
                selling=selling,
                rate_date=rate_date,
                fetched_at=fetched_at,
            )
        )

    return rates