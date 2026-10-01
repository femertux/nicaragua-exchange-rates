from datetime import datetime, timezone
from decimal import Decimal
from src.utils.time_utils import (
    nicaragua_today,
)
import json

import requests
from bs4 import BeautifulSoup

from src.models.exchange_rate import ExchangeRate


BANPRO_URL = (
    "https://www.banprogrupopromerica.com.ni/"
    "umbraco/surface/tipocambio/Run"
)

BANPRO_PARAMS = {
    "json": '{"operacion":2}'
}


def fetch_banpro_rates() -> list[ExchangeRate]:
    response = requests.get(
        BANPRO_URL,
        params=BANPRO_PARAMS,
        timeout=30,
    )

    response.raise_for_status()

    outer_json = response.json()

    value = outer_json.get("value")

    if not value:
        raise ValueError(
            "Banpro response does not contain value"
        )

    inner_json = json.loads(value)

    # En algunas respuestas viene serializado
    # una segunda vez como string.
    if isinstance(inner_json, str):
        inner_json = json.loads(inner_json)

    html = inner_json.get(
        "obtieneTipoCambioCajaResult"
    )

    if not html:
        raise ValueError(
            "Banpro response does not contain exchange rate HTML"
        )

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    rows = soup.find_all("tr")

    rates = {}

    for row in rows:
        columns = [
            column.get_text(
                strip=True
            )
            for column in row.find_all("td")
        ]

        if len(columns) < 3:
            continue

        currency = columns[0].rstrip(":")

        if currency not in ("Dólar", "Euro"):
            continue

        rates[currency] = {
            "buying": Decimal(columns[1]),
            "selling": Decimal(columns[2]),
        }

    if "Dólar" not in rates:
        raise ValueError(
            "USD exchange rate not found in Banpro response"
        )

    fetched_at = datetime.now(timezone.utc)

    result = [
        ExchangeRate(
            bank="BANPRO",
            currency="USD",
            base_currency="NIO",
            buying=rates["Dólar"]["buying"],
            selling=rates["Dólar"]["selling"],
            rate_date=nicaragua_today(),
            fetched_at=fetched_at,
        )
    ]

    # Por ahora NO agregamos EUR al modelo común.
    # Banpro publica valores para Euro, pero todavía
    # debemos confirmar contra qué moneda están expresados.

    return result