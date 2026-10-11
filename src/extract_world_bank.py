import time
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

# 1. Cấu hình dự án
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "world_bank"

RAW_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.worldbank.org/v2/country/VNM/indicator"

INDICATORS = {
    "SP.POP.TOTL": "Total Population",
    "SP.POP.TOTL.MA.IN": "Male Population",
    "SP.POP.TOTL.FE.IN": "Female Population",
    "SP.POP.GROW": "Population Growth"
}

def get_with_retry(url, params, max_attempts=3):

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Request attempt {attempt}/{max_attempts}")

            response = requests.get(
                url,
                params=params,
                timeout=(10, 45)
            )

            response.raise_for_status()

            return response

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError
        ) as e:

            print(f"Network error: {e}")

            if attempt == max_attempts:
                print("All retry attempts failed.")
                raise

            wait_time = 2 ** attempt

            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)


# 2. Hàm thu thập dữ liệu từ API
def extract_indicator(indicator_code, indicator_name):
    url = f"{BASE_URL}/{indicator_code}"

    params = {
        "format": "json",
        "date": "2015:2024",
        "per_page": 200,
        "source": 2
    }

    print(f"\nExtracting: {indicator_name}")

    # Gửi HTTP GET Request
    response = get_with_retry(url, params)

    # Kiểm tra lỗi HTTP
    response.raise_for_status()

    # Chuyển JSON thành Python object
    payload = response.json()

    # Kiểm tra cấu trúc dữ liệu
    if (
        not isinstance(payload, list)
        or len(payload) != 2
        or not isinstance(payload[0], dict)
        or not isinstance(payload[1], list)
    ):
        raise ValueError(
            f"Unexpected API response: {indicator_code}"
        )

    metadata, records = payload

    # Đảm bảo không bỏ sót trang dữ liệu
    if int(metadata.get("pages", 0)) != 1:
        raise ValueError("Pagination handling required")

    if not records:
        raise ValueError("No records returned")

    # 3. Lưu nguyên phản hồi JSON
    output_path = RAW_DIR / f"{indicator_code}.json"
    output_path.write_bytes(response.content)

    # 4. Thống kê để kiểm tra kết quả
    valid_count = sum(
        record.get("value") is not None
        for record in records
    )

    print(f"Total records: {len(records)}")
    print(f"Non-null records: {valid_count}")
    print(f"Saved to: {output_path}")

    return {
        "indicator": indicator_code,
        "name": indicator_name,
        "url": response.url,
        "retrieved_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "total_records": len(records),
        "non_null_records": valid_count
    }


# 5. Chạy Extract cho 4 chỉ số
def main():
    manifest = []

    for code, name in INDICATORS.items():
        result = extract_indicator(code, name)
        manifest.append(result)

    # Lưu thông tin nguồn và thời điểm lấy dữ liệu
    manifest_path = RAW_DIR / "manifest.json"

    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\nWorld Bank extraction completed!")


if __name__ == "__main__":
    main()