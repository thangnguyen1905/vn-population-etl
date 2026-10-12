import argparse
import csv
import json
import logging
import os

from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg
from dotenv import load_dotenv


# 1. Project configuration
BASE_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = (
    BASE_DIR
    / "data/processed/population_long_2015_2024.csv"
)

MANIFEST_PATH = (
    BASE_DIR / "data/manifests/latest_extract.json"
)

EXPECTED_COLUMNS = [
    "country_code",
    "year",
    "source",
    "dataset",
    "indicator",
    "value",
    "unit",
    "data_status",
    "variant",
    "reference_period",
    "source_indicator",
    "source_file",
    "extract_run_id"
]

EXPECTED_COUNTS = {
    "World Bank": 40,
    "United Nations": 40,
    "Vietnam NSO": 30
}

POPULATION_INDICATORS = {
    "total_population",
    "male_population",
    "female_population"
}


# 2. Read database settings
def get_db_config():
    load_dotenv(BASE_DIR / ".env")

    keys = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD"
    ]

    missing = [
        key for key in keys
        if not os.getenv(key)
    ]

    if missing:
        raise ValueError(
            f"Missing environment variables: {missing}"
        )

    return {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT")),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "connect_timeout": 10
    }


# 3. Read and validate Extract Manifest
def get_extract_run_id():
    manifest = json.loads(
        MANIFEST_PATH.read_text(encoding="utf-8")
    )

    if manifest.get("status") != "success":
        raise ValueError(
            "Latest Extract is not successful"
        )

    return manifest["run_id"]


# 4. Read and validate processed CSV
def read_processed_csv(expected_run_id):
    rows = []
    observed_keys = set()

    with CSV_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(
                "Unexpected processed CSV schema"
            )

        for line_number, row in enumerate(
            reader, start=2
        ):

            # Check required text fields
            for column in EXPECTED_COLUMNS:
                if column == "variant":
                    continue

                if (
                    row.get(column) is None
                    or not row[column].strip()
                ):
                    raise ValueError(
                        f"Missing {column} at line {line_number}"
                    )

            # Parse year
            year = int(row["year"])

            if not 2015 <= year <= 2024:
                raise ValueError(
                    f"Invalid year at line {line_number}"
                )

            # Parse decimal without converting to float
            try:
                value = Decimal(row["value"])
            except InvalidOperation as exc:
                raise ValueError(
                    f"Invalid value at line {line_number}"
                ) from exc

            if not value.is_finite():
                raise ValueError(
                    f"Non-finite value at line {line_number}"
                )

            # Check indicator and unit
            indicator = row["indicator"]
            unit = row["unit"]

            if indicator in POPULATION_INDICATORS:
                if unit != "persons" or value < 0:
                    raise ValueError(
                        f"Invalid population at line {line_number}"
                    )

            elif indicator == "population_growth_rate":
                if unit != "percent":
                    raise ValueError(
                        f"Invalid growth unit at line {line_number}"
                    )

            else:
                raise ValueError(
                    f"Unknown indicator at line {line_number}"
                )

            # Validate provenance
            if row["country_code"] != "VNM":
                raise ValueError("Unexpected country")

            if row["extract_run_id"] != expected_run_id:
                raise ValueError(
                    "Processed CSV does not match Extract run. "
                    "Run Transform again."
                )

            # Check business-key duplicates
            business_key = (
                row["country_code"],
                row["source"],
                row["dataset"],
                row["variant"],
                year,
                indicator
            )

            if business_key in observed_keys:
                raise ValueError(
                    f"Duplicate observation at line {line_number}"
                )

            observed_keys.add(business_key)

            row["year"] = year
            row["value"] = value

            rows.append(row)

    # Validate expected row counts
    counts = Counter(
        row["source"] for row in rows
    )

    if (
        len(rows) != 110
        or counts != EXPECTED_COUNTS
    ):
        raise ValueError(
            f"Unexpected row counts: {dict(counts)}"
        )

    return rows


# 5. PostgreSQL UPSERT statement
UPSERT_SQL = """
INSERT INTO public.population_observations AS existing
(
    country_code,
    year,
    source,
    dataset,
    indicator,
    value,
    unit,
    data_status,
    variant,
    reference_period,
    source_indicator,
    source_file,
    extract_run_id
)
VALUES (
    %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s
)
ON CONFLICT ON CONSTRAINT uq_population_observation
DO UPDATE SET
    value = EXCLUDED.value,
    unit = EXCLUDED.unit,
    data_status = EXCLUDED.data_status,
    reference_period = EXCLUDED.reference_period,
    source_indicator = EXCLUDED.source_indicator,
    source_file = EXCLUDED.source_file,
    extract_run_id = EXCLUDED.extract_run_id,
    updated_at = CURRENT_TIMESTAMP
WHERE (
    existing.value,
    existing.unit,
    existing.data_status,
    existing.reference_period,
    existing.source_indicator,
    existing.source_file,
    existing.extract_run_id
) IS DISTINCT FROM (
    EXCLUDED.value,
    EXCLUDED.unit,
    EXCLUDED.data_status,
    EXCLUDED.reference_period,
    EXCLUDED.source_indicator,
    EXCLUDED.source_file,
    EXCLUDED.extract_run_id
)
"""


# 6. Execute loading in a transaction
def load_to_postgres(rows, simulate_failure=False):
    affected_rows = 0

    # This context commits on success
    # and rolls back on exception
    with psycopg.connect(**get_db_config()) as conn:

        with conn.cursor() as cursor:

            for index, row in enumerate(rows, start=1):

                values = tuple(
                    row[column]
                    for column in EXPECTED_COLUMNS
                )

                cursor.execute(UPSERT_SQL, values)

                # 1 = inserted/updated, 0 = unchanged
                affected_rows += cursor.rowcount

                # Test transaction rollback
                if simulate_failure and index == 10:
                    raise RuntimeError(
                        "Simulated failure after 10 rows"
                    )

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM public.population_observations
                """
            )

            total_rows = cursor.fetchone()[0]

    # Reached only when transaction succeeds
    return affected_rows, total_rows


# 7. Main program
def main():
    parser = argparse.ArgumentParser(
        description="Load standardized population data"
    )

    parser.add_argument(
        "--simulate-failure",
        action="store_true",
        help="Test transaction rollback after 10 rows"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s"
    )

    try:
        run_id = get_extract_run_id()

        rows = read_processed_csv(run_id)

        logging.info(
            "Validated %d processed records",
            len(rows)
        )

        affected, total = load_to_postgres(
            rows,
            simulate_failure=args.simulate_failure
        )

        logging.info(
            "LOAD SUCCESS | Affected: %d | Total in DB: %d",
            affected,
            total
        )

    except Exception:
        logging.exception("LOAD FAILED")
        raise SystemExit(1)


if __name__ == "__main__":
    main()