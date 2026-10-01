from datetime import datetime, timezone
from decimal import Decimal
from xml.etree import ElementTree
from src.utils.time_utils import (
    nicaragua_today,
)

import requests

from src.models.exchange_rate import ExchangeRate


BAC_URL = (
    "https://www.sucursalelectronica.com/"
    "exchangerate/showXmlExchangeRate.do"
)

BAC_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": (
        "es-NI,es-ES;q=0.9,es-US;q=0.8,"
        "es-419;q=0.7,es;q=0.6"
    ),
    "Origin": "https://www.baccredomatic.com",
    "Referer": "https://www.baccredomatic.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/155.0.0.0 Safari/537.36"
    ),
    "sec-ch-ua": (
        '"Google Chrome";v="155", '
        '"Chromium";v="155", '
        '"Not(A:Brand";v="24"'
    ),
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}


def fetch_bac_rates() -> list[ExchangeRate]:
    response = requests.get(
        BAC_URL,
        headers=BAC_HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    root = ElementTree.fromstring(
        response.content
    )

    nicaragua = None

    for country in root.findall("country"):
        name = country.findtext("name")

        if name == "Nicaragua":
            nicaragua = country
            break

    if nicaragua is None:
        raise ValueError(
            "Nicaragua not found in BAC response"
        )

    fetched_at = datetime.now(timezone.utc)

    usd = ExchangeRate(
        bank="BAC",
        currency="USD",
        base_currency="NIO",
        buying=Decimal(
            nicaragua.findtext("buyRateUSD")
        ),
        selling=Decimal(
            nicaragua.findtext("saleRateUSD")
        ),
        rate_date=nicaragua_today(),
        fetched_at=fetched_at,
    )

    eur = ExchangeRate(
        bank="BAC",
        currency="EUR",
        base_currency="NIO",
        buying=Decimal(
            nicaragua.findtext("buyRateEUR")
        ),
        selling=Decimal(
            nicaragua.findtext("saleRateEUR")
        ),
        rate_date=nicaragua_today(),
        fetched_at=fetched_at,
    )

    return [usd, eur]