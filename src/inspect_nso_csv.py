from pathlib import Path
import pandas as pd

# 1. Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

FILE_PATH = (
    BASE_DIR / "data" / "raw" / "nso" / "V02.02.csv"
)

# 2. Read CSV
# Skip the existing header and assign unambiguous names
df = pd.read_csv(
    FILE_PATH,
    skiprows=1,
    header=None,
    names=[
        "calculation_type",
        "year",
        "total_population",
        "male_population",
        "female_population"
    ],
    encoding="utf-8"
)

# 3. Validate the year column
df["year"] = pd.to_numeric(
    df["year"], errors="raise"
).astype(int)

expected_years = list(range(2015, 2025))
actual_years = sorted(df["year"].tolist())

if actual_years != expected_years:
    raise ValueError("Invalid year coverage")

# 4. Validate population columns
population_columns = [
    "total_population",
    "male_population",
    "female_population"
]

for column in population_columns:
    df[column] = pd.to_numeric(
        df[column], errors="raise"
    )

if df.isna().any().any():
    raise ValueError("Missing values detected")

if (df[population_columns] < 0).any().any():
    raise ValueError("Negative population detected")

if not df["calculation_type"].eq(
    "Tong so (Nghin nguoi)"
).all():
    raise ValueError("Unexpected calculation type")

# 5. Check demographic consistency
df["population_difference"] = (
    df["total_population"]
    - df["male_population"]
    - df["female_population"]
).round(2)

# Allow small rounding differences (thousand persons)
if (df["population_difference"].abs() > 0.1).any():
    raise ValueError(
        "Population consistency check failed"
    )

# 6. Display results
print("\n========== NSO POPULATION DATA ==========")

print(df.to_string(index=False))

print("\n========== SUMMARY ==========")
print("Total records:", len(df))
print("Year range:", df["year"].min(), "-", df["year"].max())
print("Missing values:", df.isna().sum().sum())
print("Duplicate years:", df["year"].duplicated().sum())
print("Unit: Thousand persons")

print("\nNSO data inspection completed!")