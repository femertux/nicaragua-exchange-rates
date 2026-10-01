from datetime import date, datetime, timezone
from decimal import Decimal
from xml.etree import ElementTree
import platform
import subprocess

from src.models.official_rate import OfficialRate
from src.utils.time_utils import nicaragua_today


BCN_URL = (
    "https://servicios.bcn.gob.ni/"
    "Tc_Servicio/ServicioTC.asmx"
)

SOAP_ACTION = (
    "http://servicios.bcn.gob.ni/"
    "RecuperaTC_Dia"
)


def fetch_bcn_rate(
    rate_date: date | None = None,
) -> OfficialRate:
    if rate_date is None:
        rate_date = nicaragua_today()

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

    curl_command = [
        "curl",
        "--silent",
        "--show-error",
        "--fail",
        "--max-time",
        "30",
    ]

    # GitHub Actions uses Linux + OpenSSL 3.
    # BCN requires legacy TLS 1.0 compatibility there.
    if platform.system() == "Linux":
        curl_command.extend(
            [
                "--tlsv1.0",
                "--ciphers",
                "DEFAULT:@SECLEVEL=0",
            ]
        )

    curl_command.extend(
        [
            BCN_URL,
            "-H",
            "Content-Type: text/xml; charset=utf-8",
            "-H",
            f'SOAPAction: "{SOAP_ACTION}"',
            "--data-binary",
            "@-",
        ]
    )

    result = subprocess.run(
        curl_command,
        input=soap_body,
        text=True,
        capture_output=True,
        check=True,
    )

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