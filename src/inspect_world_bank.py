import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "world_bank"

for path in sorted(RAW_DIR.glob("SP.POP.*.json")):
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    records = payload[1]

    print(f"\nIndicator: {path.stem}")
    print(f"Total records: {len(records)}")

    for record in records:
        year = record["date"]
        value = record["value"]

        print(f"Year: {year} | Value: {value}")