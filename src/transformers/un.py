from pathlib import Path

import pandas as pd

from transformers.common import (
    POPULATION_INDICATORS,
    YEARS,
    to_standard_frame
)

# UN input filenames
UN_FILES = {
    "Estimates": (
        "WPP2024_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT_VN_Estimates.csv"
    ),
    "Medium": (
        "WPP2024_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT_VN_Medium_variant.csv"
    )
}

# Map original UN columns to common indicators
UN_COLUMNS = {
    "Total Population, as of 1 July (thousands)":
        "total_population",

    "Male Population, as of 1 July (thousands)":
        "male_population",

    "Female Population, as of 1 July (thousands)":
        "female_population",

    "Population Growth Rate (percentage)":
        "population_growth_rate"
}


def transform_un(base_dir: Path):
    """
    Transform UN Estimates (2015-2023) and
    Medium variant (2024) into long format.
    """
    frames = []

    original_names = {
        value: key
        for key, value in UN_COLUMNS.items()
    }

    for variant, filename in UN_FILES.items():

        relative_path = Path("data/raw/un") / filename
        file_path = base_dir / relative_path

        # Read prepared CSV
        df = pd.read_csv(
            file_path,
            dtype=str,
            encoding="utf-8-sig"
        )

        required_columns = [
            "Year",
            "Variant",
            "ISO3 Alpha-code",
            *UN_COLUMNS
        ]

        if any(
            col not in df.columns
            for col in required_columns
        ):
            raise ValueError(
                f"Missing UN columns: {filename}"
            )

        # Convert Year to integer
        df["Year"] = pd.to_numeric(
            df["Year"],
            errors="raise"
        ).astype(int)

        # Select project years
        selected = df[
            df["Year"].isin(YEARS)
        ].copy()

        expected_years = (
            set(range(2015, 2024))
            if variant == "Estimates"
            else {2024}
        )

        # Validate source identity and coverage
        if (
            len(selected) != len(expected_years)
            or set(selected["Year"]) != expected_years
            or not selected["Variant"]
                .str.strip().eq(variant).all()
            or not selected["ISO3 Alpha-code"]
                .str.strip().eq("VNM").all()
        ):
            raise ValueError(
                f"Unexpected UN data: {filename}"
            )

        # Rename the required indicator columns
        wide = selected[
            ["Year", *UN_COLUMNS]
        ].rename(columns=UN_COLUMNS)

        # Convert Wide -> Long
        long = wide.melt(
            id_vars="Year",
            var_name="indicator",
            value_name="raw_value"
        )

        # Remove spaces and convert to numeric
        long["value"] = pd.to_numeric(
            long["raw_value"].str.replace(
                r"\s+", "", regex=True
            ),
            errors="raise"
        )

        # Convert thousand persons -> persons
        population_mask = long[
            "indicator"
        ].isin(POPULATION_INDICATORS)

        long.loc[
            population_mask, "value"
        ] *= 1000

        # Add metadata
        long["country_code"] = "VNM"
        long["year"] = long["Year"]
        long["source"] = "United Nations"
        long["dataset"] = "WPP2024"

        long["unit"] = "percent"
        long.loc[
            population_mask, "unit"
        ] = "persons"

        long["data_status"] = (
            "estimate"
            if variant == "Estimates"
            else "projection"
        )

        long["variant"] = variant

        long["reference_period"] = "annual_growth_rate"
        long.loc[
            population_mask, "reference_period"
        ] = "july_1"

        long["source_indicator"] = (
            long["indicator"].map(original_names)
        )

        long["source_file"] = (
            relative_path.as_posix()
        )

        frames.append(
            to_standard_frame(long)
        )

    return pd.concat(
        frames,
        ignore_index=True
    )