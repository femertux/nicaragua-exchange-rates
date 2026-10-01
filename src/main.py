from src.aggregator.exchange_rate_aggregator import (
    aggregate_rates,
)
from src.database.supabase_repository import (
    get_banks,
    save_fetch_run,
    upsert_exchange_rates,
    upsert_official_rates,
)
from src.utils.time_utils import utc_now


def main():
    print("MobileNi Exchange Rates")
    print("=" * 50)

    started_at = utc_now()

    result = aggregate_rates()

    print()
    print("COMMERCIAL RATES")
    print("-" * 50)

    for rate in result.exchange_rates:
        print(
            f"{rate.bank:<8} | "
            f"{rate.currency}/"
            f"{rate.base_currency} | "
            f"Compra: {rate.buying} | "
            f"Venta: {rate.selling} | "
            f"Fecha: {rate.rate_date}"
        )

    print()
    print("OFFICIAL RATES")
    print("-" * 50)

    for rate in result.official_rates:
        print(
            f"{rate.source:<8} | "
            f"{rate.currency}/"
            f"{rate.base_currency} | "
            f"Oficial: {rate.rate} | "
            f"Fecha: {rate.rate_date}"
        )

    print()
    print("SAVING TO SUPABASE")
    print("-" * 50)

    banks = get_banks()

    upsert_exchange_rates(
        result.exchange_rates,
        banks,
    )

    upsert_official_rates(
        result.official_rates,
    )

    print(
        f"Commercial rates saved: "
        f"{len(result.exchange_rates)}"
    )

    print(
        f"Official rates saved: "
        f"{len(result.official_rates)}"
    )

    successful_sources = sorted(
        {
            rate.bank
            for rate in result.exchange_rates
        }
        | {
            rate.source
            for rate in result.official_rates
        }
    )

    finished_at = utc_now()

    save_fetch_run(
        started_at=started_at,
        finished_at=finished_at,
        successful_sources=successful_sources,
        errors=result.errors,
    )

    print()
    print("SUMMARY")
    print("-" * 50)

    print(
        f"Commercial rates: "
        f"{len(result.exchange_rates)}"
    )

    print(
        f"Official rates: "
        f"{len(result.official_rates)}"
    )

    if result.errors:
        print()
        print("ERRORS")

        for source, error in result.errors.items():
            print(
                f"{source}: {error}"
            )
    else:
        print("Errors: 0")


if __name__ == "__main__":
    main()