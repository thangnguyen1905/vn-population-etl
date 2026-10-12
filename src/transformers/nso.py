from pathlib import Path

import pandas as pd

from transformers.common import to_standard_frame

NSO_FILENAME = "V02.02.csv"

NSO_INDICATORS = {
    "total_population": "Tong so",
    "male_population": "Nam",
    "female_population": "Nu"
}


def transform_nso(base_dir: Path):
    """
    Transform NSO population CSV
    from Wide to Long format.
    """
    relative_path = (
        Path("data/raw/nso") / NSO_FILENAME
    )

    file_path = base_dir / relative_path

    # Read prepared NSO CSV
    df = pd.read_csv(
        file_path,
        skiprows=1,
        header=None,
        names=[
            "calculation_type",
            "year",
            *NSO_INDICATORS
        ],
        dtype=str,
        encoding="utf-8-sig"
    )

    # Validate original unit/category
    if not df["calculation_type"].str.strip().eq(
        "Tong so (Nghin nguoi)"
    ).all():
        raise ValueError(
            "Unexpected NSO unit or category"
        )

    # Validate year coverage
    df["year"] = pd.to_numeric(
        df["year"],
        errors="raise"
    ).astype(int)

    expected_years = set(range(2015, 2025))

    if (
        len(df) != 10
        or set(df["year"]) != expected_years
    ):
        raise ValueError(
            "Unexpected or duplicate NSO years"
        )

    # Convert Wide -> Long
    long = df.melt(
        id_vars="year",
        value_vars=list(NSO_INDICATORS),
        var_name="indicator",
        value_name="raw_value"
    )

    # Convert thousand persons -> persons
    long["value"] = pd.to_numeric(
        long["raw_value"],
        errors="raise"
    ) * 1000

    # Add metadata
    long["country_code"] = "VNM"
    long["source"] = "Vietnam NSO"
    long["dataset"] = "V02.02"
    long["unit"] = "persons"

    long["data_status"] = (
        "not_specified_in_prepared_csv"
    )

    long["variant"] = ""
    long["reference_period"] = "annual_average"

    long["source_indicator"] = (
        long["indicator"].map(NSO_INDICATORS)
    )

    long["source_file"] = (
        relative_path.as_posix()
    )

    return to_standard_frame(long)