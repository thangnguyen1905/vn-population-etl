import json
from pathlib import Path

import pandas as pd

from transformers.common import (
    YEARS,
    POPULATION_INDICATORS,
    to_standard_frame
)

# Map source indicator IDs to common names
WB_INDICATORS = {
    "SP.POP.TOTL": "total_population",
    "SP.POP.TOTL.MA.IN": "male_population",
    "SP.POP.TOTL.FE.IN": "female_population",
    "SP.POP.GROW": "population_growth_rate"
}


def transform_world_bank(base_dir: Path):
    """
    Read four World Bank JSON files and return
    a standardized long-format DataFrame.
    """
    rows = []

    for code, indicator in WB_INDICATORS.items():

        relative_path = (
            Path("data/raw/world_bank") / f"{code}.json"
        )

        file_path = base_dir / relative_path

        payload = json.loads(
            file_path.read_text(encoding="utf-8-sig")
        )

        # Expected API structure: [metadata, records]
        if (
            not isinstance(payload, list)
            or len(payload) != 2
            or not isinstance(payload[1], list)
        ):
            raise ValueError(
                f"Invalid World Bank JSON: {code}"
            )

        records = payload[1]
        years = []

        for record in records:

            if (
                record["indicator"]["id"] != code
                or record["country"]["id"] != "VN"
            ):
                raise ValueError(
                    f"Unexpected indicator/country: {code}"
                )

            year = int(record["date"])
            years.append(year)

            rows.append({
                "country_code": "VNM",
                "year": year,
                "source": "World Bank",
                "dataset": "World Development Indicators",
                "indicator": indicator,
                "value": record["value"],
                "unit": (
                    "persons"
                    if indicator in POPULATION_INDICATORS
                    else "percent"
                ),
                "data_status": "not_specified_in_raw",
                "variant": "",
                "reference_period": "as_published",
                "source_indicator": code,
                "source_file": relative_path.as_posix()
            })

        # Check the 10 expected years
        if len(years) != len(YEARS) or set(years) != YEARS:
            raise ValueError(
                f"Wrong or duplicate years: {code}"
            )

    df = pd.DataFrame(rows)

    return to_standard_frame(df)