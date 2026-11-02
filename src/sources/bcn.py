from datetime import date, datetime, timezone
from decimal import Decimal
from xml.etree import ElementTree
import subprocess

from src.models.official_rate import OfficialRate
from src.utils.time_utils import nicaragua_today


# ============================================================
# BCN Configuration
# ============================================================

BCN_URL = (
    "https://servicios.bcn.gob.ni/"
    "Tc_Servicio/ServicioTC.asmx"
)

SOAP_ACTION = (
    "http://servicios.bcn.gob.ni/"
    "RecuperaTC_Dia"
)


# ============================================================
# Fetch Official Exchange Rate
# ============================================================

def fetch_bcn_rate(
    rate_date: date | None = None,
) -> OfficialRate:

    if rate_date is None:
        rate_date = nicaragua_today()

    # --------------------------------------------------------
    # SOAP Request
    # --------------------------------------------------------

    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <RecuperaTC_Dia xmlns="http://servicios.bcn.gob.ni/">
            <Ano>{rate_date.year}</Ano>
            <Mes>{rate_date.month}</Mes>
            <Dia>{rate_date.day}</Dia>
        </RecuperaTC_Dia>
    </soap:Body>
</soap:Envelope>"""

    # --------------------------------------------------------
    # HTTP Request
    # --------------------------------------------------------

    curl_command = [
        "curl",
        "--silent",
        "--show-error",
        "--fail",
        "--max-time",
        "30",
        BCN_URL,
        "-H",
        "Content-Type: text/xml; charset=utf-8",
        "-H",
        f'SOAPAction: "{SOAP_ACTION}"',
        "--data-binary",
        "@-",
    ]

    result = subprocess.run(
        curl_command,
        input=soap_body,
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "BCN request failed "
            f"(curl exit code {result.returncode}): "
            f"{result.stderr.strip()}"
        )

    # --------------------------------------------------------
    # Parse SOAP Response
    # --------------------------------------------------------

    root = ElementTree.fromstring(
        result.stdout
    )

    namespace = {
        "bcn": "http://servicios.bcn.gob.ni/"
    }

    rate_element = root.find(
        ".//bcn:RecuperaTC_DiaResult",
        namespace,
    )

    if (
        rate_element is None
        or not rate_element.text
    ):
        raise ValueError(
            "BCN official exchange rate not found"
        )

    # --------------------------------------------------------
    # Build Official Rate
    # --------------------------------------------------------

    return OfficialRate(
        source="BCN",
        currency="USD",
        base_currency="NIO",
        rate=Decimal(
            rate_element.text.strip()
        ),
        rate_date=rate_date,
        fetched_at=datetime.now(timezone.utc),
    )