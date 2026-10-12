import logging
from pathlib import Path

import pandas as pd

# 1. UN input files
UN_FILES = {
    "Estimates":
        "WPP2024_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT_VN_Estimates(1).csv",

    "Medium variant":
        "WPP2024_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT_VN_Medium_variant(1).csv",
}

UN_INDICATORS = [
    "Total Population, as of 1 July (thousands)",
    "Male Population, as of 1 July (thousands)",
    "Female Population, as of 1 July (thousands)",
    "Population Growth Rate (percentage)",
]


# 2. Inspect UN files
def inspect_un(raw_dir: Path):
    results = []

    for variant, filename in UN_FILES.items():
        file_path = raw_dir / filename

        if not file_path.is_file():
            raise FileNotFoundError(file_path)

        df = pd.read_csv(
            file_path,
            dtype=str,
            encoding="utf-8-sig"
        )

        df.columns = df.columns.str.strip()

        required = [
            "Year",
            "ISO3 Alpha-code",
            *UN_INDICATORS
        ]

        missing = [
            name for name in required
            if name not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing UN columns: {missing}"
            )

        countries = set(
            df["ISO3 Alpha-code"].dropna().str.strip()
        )

        if countries != {"VNM"} or df["ISO3 Alpha-code"].isna().any():
            raise ValueError(
                f"Unexpected country in {filename}"
            )

        df["Year"] = pd.to_numeric(
            df["Year"],
            errors="raise"
        ).astype(int)

        chosen = df[df["Year"].between(2015, 2024)]

        expected = (
            set(range(2015, 2024))
            if variant == "Estimates"
            else {2024}
        )

        years = chosen["Year"].tolist()

        if len(years) != len(expected) or set(years) != expected:
            raise ValueError(
                f"UN years invalid for {variant}: {years}"
            )

        if (
            chosen[UN_INDICATORS].isna().any().any()
            or chosen[UN_INDICATORS]
                .apply(lambda col: col.str.strip().eq(""))
                .any().any()
        ):
            raise ValueError(
                f"Missing UN indicator values: {variant}"
            )

        logging.info(
            "UN %-16s: %d selected / %d raw rows",
            variant, len(chosen), len(df)
        )

        results.append({
            "source": "United Nations",
            "dataset": variant,
            "mode": "manually_prepared_csv",
            "raw_rows": len(df),
            "selected_rows": len(chosen),
            "path": file_path,
            "data_status": (
                "historical_estimate"
                if variant == "Estimates"
                else "medium_variant_projection"
            ),
        })

    return results


# 3. Inspect NSO file
def inspect_nso(raw_dir: Path):
    file_path = raw_dir / "V02.02.csv"

    if not file_path.is_file():
        raise FileNotFoundError(file_path)

    # Skip original header with duplicate column name "Nam"
    df = pd.read_csv(
        file_path,
        skiprows=1,
        header=None,
        names=[
            "calculation_type",
            "year",
            "total",
            "male",
            "female",
        ],
        dtype=str,
        encoding="utf-8-sig"
    )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="raise"
    ).astype(int)

    years = df["year"].tolist()

    if (
        len(years) != 10
        or set(years) != set(range(2015, 2025))
    ):
        raise ValueError(
            f"Unexpected NSO years: {years}"
        )

    if not df["calculation_type"].str.strip().eq(
        "Tong so (Nghin nguoi)"
    ).all():
        raise ValueError("Unexpected NSO data unit")

    values = df[["total", "male", "female"]].apply(
        pd.to_numeric,
        errors="raise"
    )

    if (
        values.isna().any().any()
        or (values < 0).any().any()
    ):
        raise ValueError(
            "Invalid or missing NSO population values"
        )

    logging.info(
        "NSO V02.02: %d selected rows",
        len(df)
    )

    return [{
        "source": "Vietnam NSO",
        "dataset": "V02.02",
        "mode": "manually_prepared_csv",
        "raw_rows": len(df),
        "selected_rows": len(df),
        "path": file_path,
        "unit": "thousand_persons",
    }]