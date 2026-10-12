import hashlib
import json
import logging
import math
import sys

from pathlib import Path

import pandas as pd

from transformers.common import (
    COLUMNS,
    POPULATION_INDICATORS,
    YEARS
)

from transformers.world_bank import (
    WB_INDICATORS,
    transform_world_bank
)

from transformers.un import (
    UN_FILES,
    transform_un
)

from transformers.nso import (
    NSO_FILENAME,
    transform_nso
)

BASE_DIR = Path(__file__).resolve().parent.parent


# 1. Calculate checksum
def sha256_file(path: Path):
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b""
        ):
            digest.update(chunk)

    return digest.hexdigest()


# 2. Verify Extract manifest
def verify_extract_manifest():
    manifest_path = (
        BASE_DIR
        / "data/manifests/latest_extract.json"
    )

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    if manifest.get("status") != "success":
        raise ValueError(
            "Latest Extract failed. Run Extract again."
        )

    files = manifest["files"]

    entries = {
        item["path"]: item
        for item in files
    }

    required_paths = (
        [
            f"data/raw/world_bank/{code}.json"
            for code in WB_INDICATORS
        ]
        + [
            f"data/raw/un/{filename}"
            for filename in UN_FILES.values()
        ]
        + [
            f"data/raw/nso/{NSO_FILENAME}"
        ]
    )

    # All 7 expected files must be present
    if (
        len(files) != len(required_paths)
        or set(entries) != set(required_paths)
    ):
        raise ValueError(
            "Extract Manifest does not match source files"
        )

    # Verify each file has not changed
    for relative_path in required_paths:

        file_path = BASE_DIR / relative_path

        current_hash = sha256_file(file_path)
        expected_hash = entries[
            relative_path
        ]["sha256"]

        if current_hash != expected_hash:
            raise ValueError(
                f"Source file changed: {relative_path}"
            )

    return manifest


# 3. Validate transformed data
def validate_transformed(df):

    if len(df) != 110:
        raise ValueError(
            f"Expected 110 rows, got {len(df)}"
        )

    required = [
        "country_code",
        "year",
        "source",
        "dataset",
        "indicator",
        "value",
        "unit",
        "data_status",
        "reference_period",
        "source_indicator",
        "source_file",
        "extract_run_id"
    ]

    if df[required].isna().any().any():
        raise ValueError(
            "Missing mandatory values"
        )

    # Check mandatory metadata is not empty
    text_columns = df[required].select_dtypes(
        include=["object", "str"]
    )

    if text_columns.apply(
        lambda column:
            column.astype(str).str.strip().eq("").any()
    ).any():
        raise ValueError(
            "Empty mandatory metadata"
        )

    # Country and year coverage
    if (
        not df["country_code"].eq("VNM").all()
        or set(df["year"]) != YEARS
    ):
        raise ValueError(
            "Unexpected country or year coverage"
        )

    # Values must be finite numbers
    if not df["value"].map(
        math.isfinite
    ).all():
        raise ValueError(
            "Invalid numeric values"
        )

    # Population cannot be negative
    population_mask = df[
        "indicator"
    ].isin(POPULATION_INDICATORS)

    if (
        df.loc[population_mask, "value"] < 0
    ).any():
        raise ValueError(
            "Negative population detected"
        )

    # Every source/year/indicator should be unique
    if df.duplicated(
        subset=[
            "source",
            "country_code",
            "year",
            "indicator"
        ]
    ).any():
        raise ValueError(
            "Duplicate observations detected"
        )

    # Expected indicators for each source
    indicators_by_source = {
        "World Bank": set(WB_INDICATORS.values()),
        "United Nations": set(WB_INDICATORS.values()),
        "Vietnam NSO": set(POPULATION_INDICATORS)
    }

    for source, indicators in indicators_by_source.items():

        source_rows = df[df["source"] == source]

        expected = {
            (year, indicator)
            for year in YEARS
            for indicator in indicators
        }

        actual = set(
            zip(
                source_rows["year"],
                source_rows["indicator"]
            )
        )

        if (
            len(source_rows) != len(expected)
            or actual != expected
        ):
            raise ValueError(
                f"Incomplete data coverage: {source}"
            )

    # Validate units
    if not df.loc[
        population_mask, "unit"
    ].eq("persons").all():
        raise ValueError(
            "Invalid population unit"
        )

    if not df.loc[
        ~population_mask, "unit"
    ].eq("percent").all():
        raise ValueError(
            "Invalid growth rate unit"
        )

    # Check total ≈ male + female
    pivot = df.loc[population_mask].pivot(
        index=["source", "year"],
        columns="indicator",
        values="value"
    )

    difference = (
        pivot["total_population"]
        - pivot["male_population"]
        - pivot["female_population"]
    )

    # Technical tolerances, in persons
    tolerances = {
        "World Bank": 1,
        "United Nations": 1000,
        "Vietnam NSO": 100
    }

    for source, tolerance in tolerances.items():

        maximum = difference.loc[source].abs().max()

        logging.info(
            "Population difference %-14s: %.0f persons",
            source,
            maximum
        )

        if maximum > tolerance:
            raise ValueError(
                f"Population consistency failed: {source}"
            )


# 4. Main transformation pipeline
def main():

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
        stream=sys.stdout
    )

    # Verify raw data against Extract Manifest
    manifest = verify_extract_manifest()

    logging.info(
        "Verified Extract run: %s",
        manifest["run_id"]
    )

    # Transform each source
    wb = transform_world_bank(BASE_DIR)
    un = transform_un(BASE_DIR)
    nso = transform_nso(BASE_DIR)

    logging.info(
        "Transformed rows: WB=%d, UN=%d, NSO=%d",
        len(wb),
        len(un),
        len(nso)
    )

    # Combine three DataFrames
    combined = pd.concat(
        [wb, un, nso],
        ignore_index=True
    )

    # Preserve Extract run ID
    combined["extract_run_id"] = manifest["run_id"]

    combined = combined[
        COLUMNS + ["extract_run_id"]
    ]

    # Data Quality Checks
    validate_transformed(combined)

    # Consistent output ordering
    combined = combined.sort_values(
        ["source", "year", "indicator"]
    ).reset_index(drop=True)

    # Save processed dataset
    output_path = (
        BASE_DIR
        / "data/processed/population_long_2015_2024.csv"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Write temporary file before replacing output
    temporary = output_path.with_suffix(
        ".csv.tmp"
    )

    combined.to_csv(
        temporary,
        index=False,
        encoding="utf-8"
    )

    temporary.replace(output_path)

    logging.info(
        "Transform SUCCESS: %d rows, %d columns",
        len(combined),
        len(combined.columns)
    )

    logging.info(
        "Output: %s",
        output_path
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.exception("Transform FAILED")
        sys.exit(1)