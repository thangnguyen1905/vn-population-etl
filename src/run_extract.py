import argparse
import hashlib
import json
import logging
import sys

from datetime import datetime, timezone
from pathlib import Path

from extractors.local_csv import inspect_nso, inspect_un
from extractors.world_bank import extract_world_bank

BASE_DIR = Path(__file__).resolve().parent.parent


# 1. Current UTC time
def utc_now():
    return datetime.now(timezone.utc).isoformat()


# 2. Calculate file checksum
def sha256_file(file_path: Path):
    digest = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b""
        ):
            digest.update(chunk)

    return digest.hexdigest()


# 3. Add source metadata to manifest
def add_files(manifest, records):
    for record in records:
        file_path = record["path"]

        manifest["files"].append({
            **{
                key: value
                for key, value in record.items()
                if key != "path"
            },
            "path": file_path.relative_to(BASE_DIR).as_posix(),
            "sha256": sha256_file(file_path),
        })


# 4. Save extraction manifest
def save_manifest(manifest):
    folder = BASE_DIR / "data" / "manifests"
    folder.mkdir(parents=True, exist_ok=True)

    content = json.dumps(
        manifest,
        indent=2,
        ensure_ascii=False
    )

    run_path = (
        folder / f"extract_{manifest['run_id']}.json"
    )
    latest_path = folder / "latest_extract.json"

    run_path.write_text(content, encoding="utf-8")

    # Update latest manifest safely
    tmp = folder / "latest_extract.json.tmp"
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(latest_path)

    return latest_path


# 5. Pipeline orchestrator
def main():
    parser = argparse.ArgumentParser(
        description="Vietnam population extract pipeline"
    )

    parser.add_argument(
        "--offline",
        action="store_true",
        help="Reuse existing World Bank JSON files"
    )

    args = parser.parse_args()

    # Initialize logging
    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                logs_dir / "extract.log",
                encoding="utf-8"
            )
        ],
    )

    # Pipeline execution metadata
    manifest = {
        "run_id": datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%S%fZ"
        ),
        "started_at_utc": utc_now(),
        "status": "running",
        "world_bank_mode": (
            "cache" if args.offline else "api"
        ),
        "files": [],
    }

    exit_code = 0

    try:
        logging.info(
            "=== Begin population extraction ==="
        )

        # Extract World Bank data
        add_files(
            manifest,
            extract_world_bank(
                BASE_DIR / "data/raw/world_bank",
                args.offline
            )
        )

        # Inspect United Nations CSV files
        add_files(
            manifest,
            inspect_un(BASE_DIR / "data/raw/un")
        )

        # Inspect Vietnam NSO CSV file
        add_files(
            manifest,
            inspect_nso(BASE_DIR / "data/raw/nso")
        )

        manifest["status"] = "success"

    except Exception as exc:
        logging.exception("Pipeline failed")

        manifest["status"] = "failed"
        manifest["error"] = str(exc)
        exit_code = 1

    finally:
        manifest["finished_at_utc"] = utc_now()

        manifest["selected_rows_total"] = sum(
            row["selected_rows"]
            for row in manifest["files"]
        )

        manifest_path = save_manifest(manifest)

        logging.info(
            "Status: %s | Files: %d | Selected rows: %d",
            manifest["status"],
            len(manifest["files"]),
            manifest["selected_rows_total"]
        )

        logging.info("Manifest: %s", manifest_path)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())