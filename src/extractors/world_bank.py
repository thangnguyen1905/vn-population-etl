import json
import logging
import time
from pathlib import Path

import requests

# 1. World Bank indicators
INDICATORS = {
    "SP.POP.TOTL": "Total Population",
    "SP.POP.TOTL.MA.IN": "Male Population",
    "SP.POP.TOTL.FE.IN": "Female Population",
    "SP.POP.GROW": "Population Growth",
}

API_ROOT = "https://api.worldbank.org/v2/country/VNM/indicator"
YEARS = set(range(2015, 2025))


# 2. HTTP request with retry
def request_with_retry(url, params, attempts=3):
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(
                url,
                params=params,
                timeout=(10, 45)
            )

            response.raise_for_status()
            return response

        except (
            requests.Timeout,
            requests.ConnectionError,
            requests.HTTPError
        ) as exc:

            retryable = isinstance(
                exc,
                (requests.Timeout, requests.ConnectionError)
            )

            if isinstance(exc, requests.HTTPError):
                retryable = (
                    exc.response is not None
                    and exc.response.status_code
                    in (429, 500, 502, 503, 504)
                )

            if not retryable or attempt == attempts:
                raise

            delay = 2 ** attempt

            logging.warning(
                "World Bank request failed (%s/%s): %s. "
                "Retry in %ss",
                attempt, attempts, exc, delay
            )

            time.sleep(delay)

    raise RuntimeError("World Bank API retries exhausted")


# 3. Validate API response
def validate_payload(payload, code):
    if not isinstance(payload, list) or len(payload) != 2:
        raise ValueError(f"Unexpected JSON structure: {code}")

    metadata, records = payload

    if not isinstance(metadata, dict) or not isinstance(records, list):
        raise ValueError(f"Invalid World Bank data: {code}")

    if int(metadata.get("pages", 0)) != 1:
        raise ValueError(f"Pagination not supported yet: {code}")

    years = []

    for record in records:
        if record.get("indicator", {}).get("id") != code:
            raise ValueError(f"Wrong indicator in {code}")

        if record.get("country", {}).get("id") != "VN":
            raise ValueError(f"Wrong country in {code}")

        years.append(int(record["date"]))

    if len(years) != len(YEARS) or set(years) != YEARS:
        raise ValueError(
            f"Unexpected or duplicate years in {code}: {years}"
        )

    return records


# 4. Extract the 4 indicators
def extract_world_bank(raw_dir: Path, offline: bool = False):
    raw_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for code, name in INDICATORS.items():
        target = raw_dir / f"{code}.json"
        url = f"{API_ROOT}/{code}"

        if offline:
            # Reuse existing JSON
            if not target.exists():
                raise FileNotFoundError(
                    f"Missing cached file: {target}"
                )

            payload = json.loads(
                target.read_text(encoding="utf-8-sig")
            )

            mode = "cache"

        else:
            # Download from the World Bank API
            response = request_with_retry(
                url,
                {
                    "format": "json",
                    "date": "2015:2024",
                    "per_page": 200,
                    "source": 2,
                }
            )

            payload = response.json()
            mode = "api"

        records = validate_payload(payload, code)

        # Save only after validation succeeds
        if not offline:
            temporary = target.with_suffix(".json.tmp")
            temporary.write_bytes(response.content)
            temporary.replace(target)

        result = {
            "source": "World Bank",
            "dataset": code,
            "indicator_name": name,
            "mode": mode,
            "url": url,
            "raw_rows": len(records),
            "selected_rows": len(records),
            "non_null_rows": sum(
                record.get("value") is not None
                for record in records
            ),
            "path": target,
        }

        logging.info(
            "World Bank %-20s: %d rows (%s)",
            code, len(records), mode
        )

        results.append(result)

    return results