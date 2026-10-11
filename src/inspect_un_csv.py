from pathlib import Path
import pandas as pd

# 1. Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "un"

# 2. Two CSV input files
FILES = {
    "Estimates": "WPP2024_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT_VN_Estimates.csv",
    "Medium variant": "WPP2024_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT_VN_Medium_variant.csv"
}

# 3. Required columns
COLUMNS = [
    "Year",
    "Total Population, as of 1 July (thousands)",
    "Male Population, as of 1 July (thousands)",
    "Female Population, as of 1 July (thousands)",
    "Population Growth Rate (percentage)"
]


def inspect_csv(source, filename):
    file_path = RAW_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(file_path)

    # Read the original CSV content
    df = pd.read_csv(
        file_path,
        header=0,
        dtype=str,
        encoding="utf-8-sig"
    )

    df.columns = df.columns.str.strip()

    # Validate required columns
    required_columns = ["ISO3 Alpha-code"] + COLUMNS

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    # Validate country
    countries = set(
        df["ISO3 Alpha-code"].str.strip()
    )

    if countries != {"VNM"}:
        raise ValueError(
            f"Unexpected countries: {countries}"
        )

    # Filter required years in memory
    df["Year"] = pd.to_numeric(
        df["Year"],
        errors="raise"
    ).astype(int)

    selected = df[
        df["Year"].between(2015, 2024)
    ].copy()

    # Check for duplicate years
    if selected["Year"].duplicated().any():
        raise ValueError("Duplicate years detected")

    print(f"\n===== {source} =====")
    print("Source records:", len(df))
    print("Columns:", len(df.columns))
    print("Selected records:", len(selected))

    print("\nSelected data:")
    print(
        selected[COLUMNS].to_string(index=False)
    )

    return selected


def main():
    datasets = []

    for source, filename in FILES.items():
        df = inspect_csv(source, filename)
        datasets.append(df)

    # Combine the two datasets in memory
    combined = pd.concat(
        datasets,
        ignore_index=True
    )

    years = sorted(combined["Year"].tolist())

    if years != list(range(2015, 2025)):
        raise ValueError(
            f"Unexpected year coverage: {years}"
        )

    print("\n===== UN DATA SUMMARY =====")
    print("Total selected records:", len(combined))
    print("Year range:", min(years), "-", max(years))
    print("Population indicators:", 4)
    print("UN data inspection completed!")


if __name__ == "__main__":
    main()