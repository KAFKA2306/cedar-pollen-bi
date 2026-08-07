#!/usr/bin/env python3
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT/"scripts"/"build_public_api.py")], check=True)
api=ROOT/"api"/"v1"
obs=json.loads((api/"observations.json").read_text(encoding="utf-8"))
latest=json.loads((api/"latest.json").read_text(encoding="utf-8"))
manifest=json.loads((api/"manifest.json").read_text(encoding="utf-8"))
assert obs["count"] == 47
assert len(obs["records"]) == 47
assert len({r["prefecture_code"] for r in obs["records"]}) == 47
assert manifest["counts"]["prefectures"] == 47
assert manifest["counts"]["comparable"] == 46
assert latest["max_official_comparison"]["prefecture_name_ja"] == "北海道"
assert latest["max_official_comparison"]["percent"] == 328
assert latest["min_official_comparison"]["prefecture_name_ja"] == "青森県"
assert latest["min_official_comparison"]["percent"] == 44
for name, meta in manifest["files"].items():
    data=(api/name).read_bytes()
    assert len(data) == meta["bytes"]
    assert hashlib.sha256(data).hexdigest() == meta["sha256"]
print("API smoke test passed: 47 prefectures, 46 comparable records")
