#!/usr/bin/env python3
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT/"scripts"/"build_public_api.py")], check=True)
api=ROOT/"api"/"v1"
with (api/"observations.csv").open(encoding="utf-8", newline="") as f:
    rows=list(csv.DictReader(f))
latest=json.loads((api/"latest.json").read_text(encoding="utf-8"))
manifest=json.loads((api/"manifest.json").read_text(encoding="utf-8"))
assert len(rows) == 47
assert len({r["prefecture_code"] for r in rows}) == 47
assert next(r for r in rows if r["prefecture_code"] == "47")["official_comparison_percent"] == ""
assert manifest["counts"]["prefectures"] == 47
assert manifest["counts"]["comparable"] == 46
assert latest["max_official_comparison"] == {"percent":328,"prefecture_code":"01","prefecture_name_ja":"北海道"}
assert latest["min_official_comparison"] == {"percent":44,"prefecture_code":"02","prefecture_name_ja":"青森県"}
for name, meta in manifest["files"].items():
    data=(api/name).read_bytes()
    assert len(data) == meta["bytes"]
    assert hashlib.sha256(data).hexdigest() == meta["sha256"]
print("API smoke test passed: 47 prefectures, 46 comparable records")
