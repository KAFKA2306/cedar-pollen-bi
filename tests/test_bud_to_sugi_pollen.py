#!/usr/bin/env python3
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "scripts" / "analyze_bud_to_sugi_pollen.py")], check=True)

with (ROOT / "data" / "official" / "moe-cedar-bud-2023.csv").open(encoding="utf-8", newline="") as file:
    buds_2023 = list(csv.DictReader(file))
with (ROOT / "data" / "official" / "moe-sugi-pollen-2024.csv").open(encoding="utf-8", newline="") as file:
    pollen_2024 = list(csv.DictReader(file))
with (ROOT / "data" / "official" / "moe-cedar-bud-2024.csv").open(encoding="utf-8", newline="") as file:
    buds_2024 = list(csv.DictReader(file))
with (ROOT / "data" / "official" / "moe-sugi-pollen-2025.csv").open(encoding="utf-8", newline="") as file:
    pollen_2025 = list(csv.DictReader(file))
with (ROOT / "data" / "official" / "moe-cedar-bud-2025.csv").open(encoding="utf-8", newline="") as file:
    buds_2025 = list(csv.DictReader(file))
with (ROOT / "data" / "official" / "moe-sugi-pollen-2026.csv").open(encoding="utf-8", newline="") as file:
    pollen_2026 = list(csv.DictReader(file))

result_2024 = json.loads((ROOT / "analysis" / "2023-bud-2024-sugi-pollen.json").read_text(encoding="utf-8"))
result_2025 = json.loads((ROOT / "analysis" / "2024-bud-2025-sugi-pollen.json").read_text(encoding="utf-8"))
result_2026 = json.loads((ROOT / "analysis" / "2025-bud-2026-sugi-pollen.json").read_text(encoding="utf-8"))
year_over_year_prior = json.loads(
    (ROOT / "analysis" / "2023-2024-bud-change-2024-2025-sugi-pollen-change.json").read_text(encoding="utf-8")
)
year_over_year = json.loads(
    (ROOT / "analysis" / "2024-2025-bud-change-2025-2026-sugi-pollen-change.json").read_text(encoding="utf-8")
)

assert len(buds_2023) == 35
assert len({row["prefecture_code"] for row in buds_2023}) == 35
assert all(row["survey_year"] == "2023" for row in buds_2023)
assert all(row["source_url"] == "https://www.env.go.jp/content/000184013.pdf" for row in buds_2023)
assert next(row for row in buds_2023 if row["prefecture_code"] == "27")["observation_count_per_m2"] == "4083"

assert len(pollen_2024) == 24
assert len({row["prefecture_code"] for row in pollen_2024}) == 24
assert all(row["season_year"] == "2024" for row in pollen_2024)
assert all(row["source_url"] == "https://www.env.go.jp/content/000278280.pdf" for row in pollen_2024)
verified_2024_sites = {row["prefecture_code"]: row for row in pollen_2024 if row["site_name_ja"]}
assert verified_2024_sites == {
    code: next(row for row in pollen_2024 if row["prefecture_code"] == code)
    for code in {"02", "06", "07", "09", "17", "19", "21", "22", "24", "26", "27", "28", "30", "31", "34", "35", "37", "40"}
}
assert all(row["site_source_url"] == "https://www.env.go.jp/content/000378287.pdf" for row in verified_2024_sites.values())
assert next(row for row in pollen_2024 if row["prefecture_code"] == "02")["site_name_ja"] == "弘前市"
assert next(row for row in pollen_2024 if row["prefecture_code"] == "27")["site_name_ja"] == "泉佐野市"
assert next(row for row in pollen_2024 if row["prefecture_code"] == "40")["site_name_ja"] == "福岡市"
assert sum(not row["site_name_ja"] for row in pollen_2024) == 6
osaka_2024 = next(row for row in pollen_2024 if row["prefecture_code"] == "27")
assert osaka_2024["sugi_pollen_count_per_cm2"] == "574"
assert osaka_2024["total_pollen_count_per_cm2"] == "726"

assert result_2024["input"]["paired_records"] == 18
assert {row["prefecture_code"] for row in result_2024["input"]["unpaired_pollen_records_without_bud_survey"]} == {"01", "21", "24", "30", "43", "45"}
assert result_2024["metrics"] == {"pearson_raw": 0.118356, "spearman_rank": 0.155831, "pearson_log1p": 0.097254}
assert any("3シーズン連続" in note for note in result_2024["interpretation"])
assert any("欠損都道府県を推測で補わない" in note for note in result_2024["interpretation"])

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
assert result_2025["metrics"] == {"pearson_raw": -0.07043, "spearman_rank": 0.074872, "pearson_log1p": 0.269677}
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
assert result_2026["metrics"] == {"pearson_raw": -0.215298, "spearman_rank": -0.064713, "pearson_log1p": 0.000388}
assert result_2026["comparison_to_prior_analysis"]["prior_paired_records"] == 26
assert any("2年続けて" in note for note in result_2026["interpretation"])
assert any("空間単位が一致しない" in note for note in result_2026["interpretation"])
assert any("個人症状の予測として表示しない" in note for note in result_2026["interpretation"])

assert year_over_year_prior["input"]["common_prefectures_before_site_check"] == 23
assert year_over_year_prior["input"]["same_site_paired_prefectures"] == 14
assert year_over_year_prior["input"]["excluded_site_changes"] == []
assert {row["prefecture_code"] for row in year_over_year_prior["input"]["excluded_unverified_site_identity"]} == {"01", "13", "14", "38", "43", "45"}
assert {row["prefecture_code"] for row in year_over_year_prior["input"]["excluded_missing_bud_observation"]} == {"21", "24", "30"}
assert year_over_year_prior["metrics"] == {
    "pearson_log_ratio": 0.247175,
    "spearman_log_ratio": 0.16044,
    "same_direction_count": 11,
    "same_direction_fraction": 0.785714,
    "leave_one_out_pearson_min": -0.102251,
    "leave_one_out_pearson_max": 0.372131,
}
assert len(year_over_year_prior["records"]) == 14
assert any("同じ強さで再現しなかった" in note for note in year_over_year_prior["interpretation"])
assert any("推測で補わず除外" in note for note in year_over_year_prior["interpretation"])

assert year_over_year["input"]["common_prefectures_before_site_check"] == 25
assert year_over_year["input"]["same_site_paired_prefectures"] == 23
assert {row["prefecture_code"] for row in year_over_year["input"]["excluded_site_changes"]} == {"35", "38"}
assert year_over_year["metrics"] == {
    "pearson_log_ratio": 0.480092,
    "spearman_log_ratio": 0.327075,
    "same_direction_count": 14,
    "same_direction_fraction": 0.608696,
    "leave_one_out_pearson_min": 0.358103,
    "leave_one_out_pearson_max": 0.545031,
}
assert len(year_over_year["records"]) == 23
assert all(row["prefecture_code"] not in {"35", "38"} for row in year_over_year["records"])
assert any("予測精度や予測式として扱わない" in note for note in year_over_year["interpretation"])
assert any("地点変更" in note for note in year_over_year["interpretation"])

print(
    "bud -> next spring sugi pollen validation passed: "
    "2023->2024 18 pairs; 2024->2025 26 pairs; 2025->2026 27 pairs; "
    "year-over-year same-site periods 14 and 23 pairs"
)
