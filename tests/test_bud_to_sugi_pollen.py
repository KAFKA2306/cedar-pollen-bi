#!/usr/bin/env python3
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "scripts" / "analyze_bud_to_sugi_pollen.py")], check=True)

with (ROOT / "data" / "official" / "moe-cedar-bud-2024.csv").open(encoding="utf-8", newline="") as file:
    buds = list(csv.DictReader(file))
with (ROOT / "data" / "official" / "moe-sugi-pollen-2025.csv").open(encoding="utf-8", newline="") as file:
    pollen = list(csv.DictReader(file))
result = json.loads((ROOT / "analysis" / "2024-bud-2025-sugi-pollen.json").read_text(encoding="utf-8"))

assert len(buds) == 46
assert len({row["prefecture_code"] for row in buds}) == 46
assert all(row["survey_year"] == "2024" for row in buds)
assert all(row["source_url"] == "https://www.env.go.jp/content/000278567.pdf" for row in buds)
assert next(row for row in buds if row["prefecture_code"] == "27")["observation_count_per_m2"] == "18932"

assert len(pollen) == 26
assert len({row["prefecture_code"] for row in pollen}) == 26
assert all(row["season_year"] == "2025" for row in pollen)
assert all(row["source_url"] == "https://www.env.go.jp/content/000365034.pdf" for row in pollen)
assert all(row["site_source_url"] == "https://www.env.go.jp/content/000378661.pdf" for row in pollen)
osaka = next(row for row in pollen if row["prefecture_code"] == "27")
assert osaka["site_name_ja"] == "泉佐野市"
assert osaka["sugi_pollen_count_per_cm2"] == "1586"
assert osaka["total_pollen_count_per_cm2"] == "2114"

assert result["input"]["paired_records"] == 26
assert result["metrics"] == {
    "pearson_raw": -0.07043,
    "spearman_rank": 0.074872,
    "pearson_log1p": 0.269677,
}
assert any("時間順序が逆" in note for note in result["interpretation"])
assert any("空間単位が一致しない" in note for note in result["interpretation"])

print("2024 autumn bud -> 2025 spring sugi pollen validation passed: 46 bud records, 26 measured sites, 26 temporal pairs")
