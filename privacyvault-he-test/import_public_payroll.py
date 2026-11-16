"""Download a bounded public-payroll sample without employee names."""

import csv
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API = "https://data.cityofnewyork.us/resource/k397-673e.json"
SOURCE = (
    "https://data.cityofnewyork.us/City-Government/"
    "Citywide-Payroll-Data-Fiscal-Year-/k397-673e"
)
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "local-experiments" / "nyc-payroll-25"
LIMIT = 25

ELIGIBLE = (
    "agency_name IS NOT NULL "
    "AND agency_name != '' "
    "AND regular_gross_paid > 0 "
    "AND total_ot_paid >= 0 "
    "AND regular_gross_paid <= 1000000000 "
    "AND total_ot_paid <= 1000000000"
)


def fetch(params):
    url = API + "?" + urlencode(params)
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "PrivacyVault-Educational-Importer/1.0",
        },
    )
    with urlopen(request, timeout=90) as response:
        data = json.load(response)
    if not isinstance(data, list):
        raise ValueError("Expected a list from NYC Open Data.")
    return data, url


def main():
    if OUTPUT.exists():
        raise SystemExit(
            "Experiment folder already exists. "
            "Keep it unchanged or choose a new OUTPUT folder."
        )

    years, year_url = fetch({
    
        "$select": "fiscal_year",
        "$where": f"fiscal_year IS NOT NULL AND {ELIGIBLE}",
        "$group": "fiscal_year",
        "$order": "fiscal_year DESC",
        "$limit": 1,
    })
    if not years:
        raise ValueError("No fiscal year was returned.")

    year = str(years[0]["fiscal_year"])
    if not year.isdigit():
        raise ValueError("Unexpected fiscal-year format.")

    year_filter = f"fiscal_year = '{year}'"

    agencies, agency_url = fetch({
        "$select": "agency_name,count(*) AS eligible_records",
        "$where": f"{year_filter} AND {ELIGIBLE}",
        "$group": "agency_name",
        "$order": "eligible_records DESC,agency_name ASC",
        "$limit": 1,
    })
    print("Selected fiscal year:", year)
    print("Agency query URL:", agency_url)
    print("Agency query response:", json.dumps(agencies, indent=2))

    if not agencies or not agencies[0].get("agency_name"):
        raise ValueError(
            "Agency selection failed. Inspect the diagnostic output above."
        )

    agency = agencies[0]["agency_name"]
    escaped_agency = agency.replace("'", "''")
    where = (
        f"{year_filter} AND agency_name = '{escaped_agency}' "
        f"AND {ELIGIBLE}"
    )

    rows, sample_url = fetch({
        "$select": (
            "fiscal_year,agency_name,"
            "regular_gross_paid,total_ot_paid"
        ),
        "$where": where,
        "$order": ":id",
        "$limit": LIMIT,
    })
    if len(rows) != LIMIT:
        raise ValueError(f"Expected {LIMIT} rows; received {len(rows)}.")

    totals = {
        "regular_gross_paid": Decimal("0"),
        "total_ot_paid": Decimal("0"),
    }

    for row in rows:
        if (
            str(row.get("fiscal_year")) != year
            or row.get("agency_name") != agency
        ):
            raise ValueError("Unexpected agency or fiscal year.")

        for field in totals:
            try:
                value = Decimal(row[field])
            except (InvalidOperation, KeyError, TypeError):
                raise ValueError(f"Invalid numeric field: {field}")

            if (
                not value.is_finite()
                or value < 0
                or value > Decimal("1000000000")
            ):
                raise ValueError(f"Out-of-range value: {field}")

            totals[field] += value

    OUTPUT.mkdir(parents=True)
    csv_path = OUTPUT / "payroll-sample.csv"

    with csv_path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "fiscal_year",
                "agency_name",
                "regular_gross_paid",
                "total_ot_paid",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    metadata = {
        "source": SOURCE,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "fiscal_year": year,
        "agency": agency,
        "currency": "USD",
        "period": "fiscal-year",
        "record_count": len(rows),
        "eligible_agency_records": agencies[0]["eligible_records"],
        "selection": (
            "Latest fiscal year with eligible named-agency records; "
            "agency with most eligible records; first 25 eligible "
            "rows ordered by source row ID."
        ),
        "filter": where,
        "limitations": [
            "Non-random sample; not an agency-wide total.",
            "Positive regular pay and nonnegative overtime only.",
            "Records with missing or empty agency names are excluded.",
            "Negative payroll adjustments are excluded.",
            "Public data; this does not create secrecy for source values.",
            "Row IDs and source records may change in later revisions.",
        ],
        "discovery_queries": [year_url, agency_url],
        "sample_query": sample_url,
        "csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "local_reference_totals": {
            field: str(value) for field, value in totals.items()
        },
    }

    with (OUTPUT / "source.local.json").open(
        "x", encoding="utf-8"
    ) as handle:
        json.dump(metadata, handle, indent=2)

    print(f"Fiscal year: {year}")
    print(f"Agency: {agency}")
    print(f"Payroll records: {len(rows)}")
    print(f"Regular pay total: USD {totals['regular_gross_paid']:,.2f}")
    print(f"Overtime total: USD {totals['total_ot_paid']:,.2f}")
    print("Saved payroll-sample.csv and source.local.json")
    print("No employee names were requested.")
    print("Sample only: do not report these as agency-wide totals.")


if __name__ == "__main__":
    main()