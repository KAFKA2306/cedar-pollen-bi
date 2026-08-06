#!/usr/bin/env python3
"""Validate cedar-pollen JSON records before publication.

The validator intentionally uses only the Python standard library so it can run
in CI and local environments without dependency resolution.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

PREFECTURE_CODE = re.compile(r"^(0[1-9]|[1-3][0-9]|4[0-7])$")
RECORD_ID = re.compile(r"^[a-z0-9][a-z0-9._:-]{5,127}$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
METRICS = {"official_flower_bud_observation", "calculated_baseline_ratio"}
STATUSES = {"comparable", "not_comparable", "unknown"}
REQUIRED = {
    "record_id",
    "prefecture_code",
    "prefecture_name_ja",
    "survey_year",
    "metric_type",
    "value",
    "unit",
    "comparison_status",
    "source",
}


def fail(errors: list[str], path: Path, index: int, message: str) -> None:
    errors.append(f"{path}:{index}: {message}")


def valid_https(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def valid_iso(value: object, *, date_only: bool) -> bool:
    if not isinstance(value, str):
        return False
    try:
        if date_only:
            datetime.strptime(value, "%Y-%m-%d")
        else:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate_record(record: object, path: Path, index: int, seen: set[str]) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        fail(errors, path, index, "record must be an object")
        return errors

    missing = sorted(REQUIRED - record.keys())
    if missing:
        fail(errors, path, index, f"missing required fields: {', '.join(missing)}")

    record_id = record.get("record_id")
    if not isinstance(record_id, str) or not RECORD_ID.fullmatch(record_id):
        fail(errors, path, index, "record_id has an invalid format")
    elif record_id in seen:
        fail(errors, path, index, f"duplicate record_id: {record_id}")
    else:
        seen.add(record_id)

    if not isinstance(record.get("prefecture_code"), str) or not PREFECTURE_CODE.fullmatch(record["prefecture_code"]):
        fail(errors, path, index, "prefecture_code must be 01..47")
    if not isinstance(record.get("prefecture_name_ja"), str) or len(record["prefecture_name_ja"].strip()) < 2:
        fail(errors, path, index, "prefecture_name_ja is required")
    if not isinstance(record.get("survey_year"), int) or not 2000 <= record["survey_year"] <= 2100:
        fail(errors, path, index, "survey_year must be an integer from 2000 to 2100")
    if record.get("metric_type") not in METRICS:
        fail(errors, path, index, f"metric_type must be one of {sorted(METRICS)}")

    value = record.get("value")
    if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0):
        fail(errors, path, index, "value must be null or a non-negative number")
    if not isinstance(record.get("unit"), str) or not record["unit"].strip():
        fail(errors, path, index, "unit is required")

    status = record.get("comparison_status")
    if status not in STATUSES:
        fail(errors, path, index, f"comparison_status must be one of {sorted(STATUSES)}")
    if status == "comparable" and not isinstance(record.get("baseline"), dict):
        fail(errors, path, index, "comparable records require baseline")
    if status == "not_comparable" and not str(record.get("not_comparable_reason") or "").strip():
        fail(errors, path, index, "not_comparable records require not_comparable_reason")

    source = record.get("source")
    if not isinstance(source, dict):
        fail(errors, path, index, "source must be an object")
    else:
        for field in ("publisher", "locator"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                fail(errors, path, index, f"source.{field} is required")
        if not valid_https(source.get("document_url")):
            fail(errors, path, index, "source.document_url must be an HTTPS URL")
        if not valid_iso(source.get("published_date"), date_only=True):
            fail(errors, path, index, "source.published_date must be YYYY-MM-DD")
        if not valid_iso(source.get("retrieved_at"), date_only=False):
            fail(errors, path, index, "source.retrieved_at must be ISO-8601 datetime")
        checksum = source.get("sha256")
        if checksum is not None and (not isinstance(checksum, str) or not SHA256.fullmatch(checksum)):
            fail(errors, path, index, "source.sha256 must be 64 lowercase hexadecimal characters")

    if record.get("metric_type") == "calculated_baseline_ratio":
        transformation = record.get("transformation")
        if not isinstance(transformation, dict):
            fail(errors, path, index, "calculated records require transformation lineage")
        elif not transformation.get("input_record_ids"):
            fail(errors, path, index, "transformation.input_record_ids must not be empty")

    return errors


def iter_json_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(path.rglob("*.json")))
        elif path.suffix == ".json":
            files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    files = iter_json_files(args.paths)
    if not files:
        print("No JSON data files found; refusing a false-positive validation.", file=sys.stderr)
        return 2

    errors: list[str] = []
    seen: set[str] = set()
    count = 0
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: unreadable JSON: {exc}")
            continue
        records = payload if isinstance(payload, list) else payload.get("records") if isinstance(payload, dict) else None
        if not isinstance(records, list):
            errors.append(f"{path}: root must be an array or an object with a records array")
            continue
        for index, record in enumerate(records):
            errors.extend(validate_record(record, path, index, seen))
            count += 1

    if errors:
        print("\n".join(errors), file=sys.stderr)
        print(f"Validation failed: {len(errors)} error(s), {count} record(s).", file=sys.stderr)
        return 1
    print(f"Validation passed: {count} record(s) across {len(files)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
