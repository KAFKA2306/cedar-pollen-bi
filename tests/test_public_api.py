#!/usr/bin/env python3
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "scripts" / "build_public_api.py")], check=True)
api = ROOT / "api" / "v1"
with (api / "observations.csv").open(encoding="utf-8", newline="") as file:
    rows = list(csv.DictReader(file))
comparability = json.loads((api / "comparability.json").read_text(encoding="utf-8"))
latest = json.loads((api / "latest.json").read_text(encoding="utf-8"))
manifest = json.loads((api / "manifest.json").read_text(encoding="utf-8"))

assert len(rows) == 47
assert len({row["prefecture_code"] for row in rows}) == 47
assert all(row["source_url"] == "https://www.env.go.jp/content/000365031.pdf" for row in rows)
assert all(row["source_page"] == "1" for row in rows)
assert all(row["source_section"] == "資料1" for row in rows)
for prefecture_code in ("01", "27", "47"):
    evidence = next(row for row in rows if row["prefecture_code"] == prefecture_code)
    assert evidence["source_page"] == "1"
    assert evidence["source_section"] == "資料1"

okinawa = next(row for row in rows if row["prefecture_code"] == "47")
assert okinawa["observation_count_per_m2"] == "668"
assert okinawa["baseline_average_count_per_m2"] == ""
assert okinawa["official_comparison_percent"] == ""
assert okinawa["baseline_note"] == "new observation; no historical baseline"

comparison_records = comparability["records"]
assert len(comparison_records) == 47
assert sum(row["comparison_status"] == "comparable" for row in comparison_records) == 46
okinawa_status = next(row for row in comparison_records if row["prefecture_code"] == "47")
assert okinawa_status == {
    "comparison_status": "not_comparable",
    "not_comparable_reason": "new observation; no historical baseline",
    "prefecture_code": "47",
}
assert all(
    row["not_comparable_reason"] is None
    for row in comparison_records
    if row["comparison_status"] == "comparable"
)

assert manifest["counts"]["prefectures"] == 47
assert manifest["counts"]["comparable"] == 46
assert "comparability.json" in manifest["files"]
assert latest["max_official_comparison"] == {
    "percent": 328,
    "prefecture_code": "01",
    "prefecture_name_ja": "北海道",
}
assert latest["min_official_comparison"] == {
    "percent": 44,
    "prefecture_code": "02",
    "prefecture_name_ja": "青森県",
}
for name, meta in manifest["files"].items():
    data = (api / name).read_bytes()
    assert len(data) == meta["bytes"]
    assert hashlib.sha256(data).hexdigest() == meta["sha256"]

ui_script = (ROOT / "pollen-bi.js").read_text(encoding="utf-8")
assert "/cedar-pollen-bi/api/v1/observations.csv" in ui_script
assert "baselineNote" in ui_script
assert "新規観測のため過去平均なし" in ui_script
assert "環境省 資料1" in ui_script
assert "sourceUrl" in ui_script

root_html = (ROOT / "index.html").read_text(encoding="utf-8")
assert 'id="countLabel">46件 + 比較不能1件<' in root_html
assert "沖縄県は新規観測で過去平均がないため比率比較は行わず" in root_html
assert "<th>根拠</th>" in root_html
assert 'src="/cedar-pollen-bi/pollen-bi.js"' in root_html

legacy_html = (ROOT / "bi" / "index.html").read_text(encoding="utf-8")
assert 'rel="canonical" href="https://kafka2306.github.io/cedar-pollen-bi/"' in legacy_html
assert 'content="0; url=/cedar-pollen-bi/"' in legacy_html
assert 'src="/cedar-pollen-bi/pollen-bi.js"' not in legacy_html
assert "bi.astro_astro_type_script_index_0_lang.BBc-nVcZ.js" not in root_html + legacy_html

print("API and BI smoke test passed: 47 observations with source location, 46 comparable, 1 explicit no-baseline record")
