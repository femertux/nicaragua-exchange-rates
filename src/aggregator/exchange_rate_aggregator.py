from dataclasses import dataclass, field

from src.models.exchange_rate import ExchangeRate
from src.models.official_rate import OfficialRate
from src.sources.avanz import fetch_avanz_rates
from src.sources.bac import fetch_bac_rates
from src.sources.banpro import fetch_banpro_rates
from src.sources.bcn import fetch_bcn_rate
from src.sources.bdf import fetch_bdf_rates
from src.sources.lafise import fetch_lafise_rates


@dataclass
class AggregationResult:
    exchange_rates: list[ExchangeRate] = field(
        default_factory=list
    )
    official_rates: list[OfficialRate] = field(
        default_factory=list
    )
    errors: dict[str, str] = field(
        default_factory=dict
    )


def validate_exchange_rate(
    rate: ExchangeRate,
) -> None:
    if rate.buying <= 0:
        raise ValueError(
            f"{rate.bank} {rate.currency}: "
            "buying must be greater than zero"
        )

    if rate.selling <= 0:
        raise ValueError(
            f"{rate.bank} {rate.currency}: "
            "selling must be greater than zero"
        )

    if rate.selling < rate.buying:
        raise ValueError(
            f"{rate.bank} {rate.currency}: "
            "selling cannot be lower than buying"
        )


def aggregate_rates() -> AggregationResult:
    result = AggregationResult()

    sources = {
        "BAC": fetch_bac_rates,
        "BANPRO": fetch_banpro_rates,
        "LAFISE": fetch_lafise_rates,
        "BDF": fetch_bdf_rates,
        "AVANZ": fetch_avanz_rates,
    }

    for source_name, fetcher in sources.items():
        try:
            rates = fetcher()

            for rate in rates:
                validate_exchange_rate(rate)

            result.exchange_rates.extend(rates)

        except Exception as error:
            result.errors[source_name] = str(error)

    try:
        official_rate = fetch_bcn_rate()

        if official_rate.rate <= 0:
            raise ValueError(
                "Official rate must be greater than zero"
            )

        result.official_rates.append(
            official_rate
        )

    except Exception as error:
        result.errors["BCN"] = str(error)

    return result