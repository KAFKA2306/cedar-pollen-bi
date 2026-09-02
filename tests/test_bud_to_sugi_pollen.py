#!/usr/bin/env python3
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "scripts" / "analyze_bud_to_sugi_pollen.py")], check=True)

with (ROOT / "data" / "official" / "moe-cedar-bud-2024.csv").open(encoding="utf-8", newline="") as file:
    buds_2024 = list(csv.DictReader(file))
with (ROOT / "data" / "official" / "moe-sugi-pollen-2025.csv").open(encoding="utf-8", newline="") as file:
    pollen_2025 = list(csv.DictReader(file))
with (ROOT / "data" / "official" / "moe-cedar-bud-2025.csv").open(encoding="utf-8", newline="") as file:
    buds_2025 = list(csv.DictReader(file))
with (ROOT / "data" / "official" / "moe-sugi-pollen-2026.csv").open(encoding="utf-8", newline="") as file:
    pollen_2026 = list(csv.DictReader(file))

result_2025 = json.loads((ROOT / "analysis" / "2024-bud-2025-sugi-pollen.json").read_text(encoding="utf-8"))
result_2026 = json.loads((ROOT / "analysis" / "2025-bud-2026-sugi-pollen.json").read_text(encoding="utf-8"))

assert len(buds_2024) == 46
assert len({row["prefecture_code"] for row in buds_2024}) == 46
assert all(row["survey_year"] == "2024" for row in buds_2024)
assert all(row["source_url"] == "https://www.env.go.jp/content/000278567.pdf" for row in buds_2024)
assert next(row for row in buds_2024 if row["prefecture_code"] == "27")["observation_count_per_m2"] == "18932"

assert len(pollen_2025) == 26
assert len({row["prefecture_code"] for row in pollen_2025}) == 26
assert all(row["season_year"] == "2025" for row in pollen_2025)
assert all(row["source_url"] == "https://www.env.go.jp/content/000365034.pdf" for row in pollen_2025)
assert all(row["site_source_url"] == "https://www.env.go.jp/content/000378661.pdf" for row in pollen_2025)
osaka_2025 = next(row for row in pollen_2025 if row["prefecture_code"] == "27")
assert osaka_2025["site_name_ja"] == "泉佐野市"
assert osaka_2025["sugi_pollen_count_per_cm2"] == "1586"
assert osaka_2025["total_pollen_count_per_cm2"] == "2114"

assert result_2025["input"]["paired_records"] == 26
assert result_2025["metrics"] == {
    "pearson_raw": -0.07043,
    "spearman_rank": 0.074872,
    "pearson_log1p": 0.269677,
}
assert any("時間順序が逆" in note for note in result_2025["interpretation"])
assert any("空間単位が一致しない" in note for note in result_2025["interpretation"])

assert len(buds_2025) == 47
assert len({row["prefecture_code"] for row in buds_2025}) == 47
assert all(row["survey_year"] == "2025" for row in buds_2025)
assert all(row["source_url"] == "https://www.env.go.jp/content/000365031.pdf" for row in buds_2025)

assert len(pollen_2026) == 27
assert len({row["prefecture_code"] for row in pollen_2026}) == 27
assert all(row["season_year"] == "2026" for row in pollen_2026)
assert all(row["source_url"] == "https://www.env.go.jp/content/000374236.pdf" for row in pollen_2026)
assert all(row["site_source_url"] == "https://www.env.go.jp/content/000374236.pdf" for row in pollen_2026)
assert all(row["published_date"] == "2026-06-19" for row in pollen_2026)
assert all(row["hinoki_pollen_count_per_cm2"] == "" for row in pollen_2026)
assert all(row["total_pollen_count_per_cm2"] == "" for row in pollen_2026)
osaka_2026 = next(row for row in pollen_2026 if row["prefecture_code"] == "27")
assert osaka_2026["site_name_ja"] == "泉佐野市"
assert osaka_2026["sugi_pollen_count_per_cm2"] == "1105.0"

assert result_2026["input"]["paired_records"] == 27
assert result_2026["input"]["sugi_pollen"]["as_of"] == "2026-06-19"
assert result_2026["metrics"] == {
    "pearson_raw": -0.215298,
    "spearman_rank": -0.064713,
    "pearson_log1p": 0.000388,
}
assert result_2026["comparison_to_prior_analysis"]["prior_paired_records"] == 26
assert any("2年続けて" in note for note in result_2026["interpretation"])
assert any("空間単位が一致しない" in note for note in result_2026["interpretation"])
assert any("個人症状の予測として表示しない" in note for note in result_2026["interpretation"])

print("bud -> next spring sugi pollen validation passed: 2024->2025 26 pairs; 2025->2026 27 pairs")
