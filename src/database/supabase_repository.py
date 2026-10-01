import os

import requests
from dotenv import load_dotenv

from src.models.exchange_rate import ExchangeRate
from src.models.official_rate import OfficialRate


load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv(
    "SUPABASE_SECRET_KEY"
)


def validate_supabase_config() -> None:
    if not SUPABASE_URL:
        raise ValueError(
            "SUPABASE_URL is not configured"
        )

    if not SUPABASE_SECRET_KEY:
        raise ValueError(
            "SUPABASE_SECRET_KEY is not configured"
        )


def get_headers() -> dict[str, str]:
    validate_supabase_config()

    return {
        "apikey": SUPABASE_SECRET_KEY,
        "Content-Type": "application/json",
    }


def get_banks() -> list[dict]:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/banks",
        headers=get_headers(),
        params={
            "select": "id,code,name,active",
            "order": "id.asc",
        },
        timeout=30,
    )

    if not response.ok:
        print(
            "Supabase error:",
            response.status_code,
            response.text,
        )

    response.raise_for_status()

    return response.json()

def upsert_exchange_rates(
    rates: list[ExchangeRate],
    banks: list[dict],
) -> None:
    if not rates:
        return

    bank_ids = {
        bank["code"]: bank["id"]
        for bank in banks
    }

    payload = []

    for rate in rates:
        bank_id = bank_ids.get(
            rate.bank
        )

        if bank_id is None:
            raise ValueError(
                f"Bank not found in Supabase: "
                f"{rate.bank}"
            )

        payload.append(
            {
                "bank_id": bank_id,
                "currency": rate.currency,
                "base_currency": (
                    rate.base_currency
                ),
                "buying": str(rate.buying),
                "selling": str(rate.selling),
                "rate_date": (
                    rate.rate_date.isoformat()
                ),
                "fetched_at": (
                    rate.fetched_at.isoformat()
                ),
            }
        )

    response = requests.post(
        (
            f"{SUPABASE_URL}"
            "/rest/v1/exchange_rates"
        ),
        headers={
            **get_headers(),
            "Prefer": (
                "resolution=merge-duplicates,"
                "return=minimal"
            ),
        },
        params={
            "on_conflict": (
                "bank_id,currency,"
                "base_currency,rate_date"
            )
        },
        json=payload,
        timeout=30,
    )

    response.raise_for_status()


def upsert_official_rates(
    rates: list[OfficialRate],
) -> None:
    if not rates:
        return

    payload = []

    for rate in rates:
        payload.append(
            {
                "source": rate.source,
                "currency": rate.currency,
                "base_currency": (
                    rate.base_currency
                ),
                "rate": str(rate.rate),
                "rate_date": (
                    rate.rate_date.isoformat()
                ),
                "fetched_at": (
                    rate.fetched_at.isoformat()
                ),
            }
        )

    response = requests.post(
        (
            f"{SUPABASE_URL}"
            "/rest/v1/official_rates"
        ),
        headers={
            **get_headers(),
            "Prefer": (
                "resolution=merge-duplicates,"
                "return=minimal"
            ),
        },
        params={
            "on_conflict": (
                "source,currency,"
                "base_currency,rate_date"
            )
        },
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

def save_fetch_run(
    started_at,
    finished_at,
    successful_sources: list[str],
    errors: dict[str, str],
) -> None:
    payload = {
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "successful_sources": successful_sources,
        "failed_sources": list(errors.keys()),
        "errors": errors,
    }

    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/fetch_runs",
        headers={
            **get_headers(),
            "Prefer": "return=minimal",
        },
        json=payload,
        timeout=30,
    )

    response.raise_for_status()