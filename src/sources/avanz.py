from datetime import datetime, timezone
from decimal import Decimal
from src.utils.time_utils import (
    nicaragua_today,
)

import requests
from bs4 import BeautifulSoup

from src.models.exchange_rate import ExchangeRate


AVANZ_URL = (
    "https://www.avanzbanc.com/"
    "Pages/Empresas/ServiciosFinancieros/"
    "MesaCambio.aspx"
)


def fetch_avanz_rates() -> list[ExchangeRate]:
    response = requests.get(
        AVANZ_URL,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    container = soup.find(
        id="avanz-mobile-tipo-cambio"
    )

    if container is None:
        raise ValueError(
            "Avanz exchange rate not found"
        )

    values = container.find_all("strong")

    if len(values) < 2:
        raise ValueError(
            "Invalid Avanz exchange rate structure"
        )

    buying = Decimal(
        values[0].get_text(strip=True)
    )

    selling = Decimal(
        values[1].get_text(strip=True)
    )

    fetched_at = datetime.now(timezone.utc)

    return [
        ExchangeRate(
            bank="AVANZ",
            currency="USD",
            base_currency="NIO",
            buying=buying,
            selling=selling,
            rate_date=nicaragua_today(),
            fetched_at=fetched_at,
        )
    ]