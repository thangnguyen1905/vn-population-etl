import pandas as pd

# Years included in the project
YEARS = set(range(2015, 2025))

# Indicators representing population counts
POPULATION_INDICATORS = {
    "total_population",
    "male_population",
    "female_population"
}

# Common output schema
COLUMNS = [
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
    "source_file"
]


def to_standard_frame(df):
    """
    Select common columns and normalize data types.
    """
    result = df.loc[:, COLUMNS].copy()

    result["year"] = pd.to_numeric(
        result["year"],
        errors="raise"
    ).astype("int64")

    result["value"] = pd.to_numeric(
        result["value"],
        errors="raise"
    ).astype("float64")

    return result