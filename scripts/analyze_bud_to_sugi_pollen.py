#!/usr/bin/env python3
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ANALYSES = [
    {
        "bud_path": ROOT / "data" / "official" / "moe-cedar-bud-2024.csv",
        "pollen_path": ROOT / "data" / "official" / "moe-sugi-pollen-2025.csv",
        "output_path": ROOT / "analysis" / "2024-bud-2025-sugi-pollen.json",
        "bud_year": 2024,
        "pollen_year": 2025,
        "expected_bud_records": 46,
        "expected_pollen_records": 26,
        "bud_source_url": "https://www.env.go.jp/content/000278567.pdf",
        "pollen_source_url": "https://www.env.go.jp/content/000365034.pdf",
        "site_identity_source_url": "https://www.env.go.jp/content/000378661.pdf",
        "question": "2024年11～12月のスギ雄花花芽量は、同じ都道府県で2025年春に観測されたスギ花粉総飛散数と横断的に対応するか",
        "interpretation": [
            "26組の都道府県対応では、花芽量の絶対値と翌春のスギ花粉実測値に強い単純な横断相関は確認できない。",
            "この結果は花芽量に予測価値がないことを意味しない。花芽調査は都道府県内のスギ林、花粉実測は各都道府県の特定観測地点であり、空間単位が一致しない。",
            "気象、飛散源から観測地点までの輸送、観測地点特性などを調整していないため、因果効果や予測精度として解釈しない。",
            "令和7年度（2025年11～12月）の花芽量と令和7年春（2025年）の飛散数は時間順序が逆なので結び付けない。",
        ],
    },
    {
        "bud_path": ROOT / "data" / "official" / "moe-cedar-bud-2025.csv",
        "pollen_path": ROOT / "data" / "official" / "moe-sugi-pollen-2026.csv",
        "output_path": ROOT / "analysis" / "2025-bud-2026-sugi-pollen.json",
        "bud_year": 2025,
        "pollen_year": 2026,
        "expected_bud_records": 47,
        "expected_pollen_records": 27,
        "bud_source_url": "https://www.env.go.jp/content/000365031.pdf",
        "pollen_source_url": "https://www.env.go.jp/content/000374236.pdf",
        "pollen_as_of": "2026-06-19",
        "question": "2025年11～12月のスギ雄花花芽量は、同じ都道府県で2026年春に観測されたスギ花粉総飛散数と横断的に対応するか",
        "interpretation": [
            "27組の都道府県対応では、花芽量の絶対値と翌春のスギ花粉実測値に強い単純な横断相関は確認できない。",
            "前年の2024年花芽量と2025年スギ花粉実測値を比較した既存分析でも単純な横断相関は弱く、2年続けて都道府県単位の単純対応を予測精度として扱う根拠は得られなかった。",
            "この結果は花芽量に予測価値がないことを意味しない。花芽調査は都道府県内のスギ林、花粉実測は各都道府県の特定観測地点であり、空間単位が一致しない。",
            "気象、飛散源から観測地点までの輸送、観測地点特性などを調整していないため、因果効果や個別地域の予測精度として解釈しない。",
            "Cedar Pollen BIでは花芽量を空中花粉飛散量や個人症状の予測として表示しない現在の境界を維持する。",
        ],
    },
]


def load_csv(path):
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def pearson(xs, ys):
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("Pearson correlation requires paired observations")
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    centered_x = [x - mean_x for x in xs]
    centered_y = [y - mean_y for y in ys]
    numerator = sum(x * y for x, y in zip(centered_x, centered_y))
    denominator = math.sqrt(sum(x * x for x in centered_x) * sum(y * y for y in centered_y))
    if denominator == 0:
        raise ValueError("Pearson correlation is undefined for a constant series")
    return numerator / denominator


def average_ranks(values):
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(indexed):
        end = start + 1
        while end < len(indexed) and indexed[end][1] == indexed[start][1]:
            end += 1
        rank = (start + 1 + end) / 2
        for position in range(start, end):
            ranks[indexed[position][0]] = rank
        start = end
    return ranks


def analyze(spec):
    buds = load_csv(spec["bud_path"])
    pollen = load_csv(spec["pollen_path"])
    if len(buds) != spec["expected_bud_records"]:
        raise ValueError(
            f"Expected {spec['expected_bud_records']} {spec['bud_year']} bud records, found {len(buds)}"
        )
    if len(pollen) != spec["expected_pollen_records"]:
        raise ValueError(
            f"Expected {spec['expected_pollen_records']} {spec['pollen_year']} pollen records, found {len(pollen)}"
        )

    buds_by_code = {row["prefecture_code"]: row for row in buds}
    if len(buds_by_code) != len(buds):
        raise ValueError(f"Duplicate prefecture_code in {spec['bud_year']} bud data")

    bud_values = []
    pollen_values = []
    for pollen_row in pollen:
        bud_row = buds_by_code.get(pollen_row["prefecture_code"])
        if bud_row is None:
            raise ValueError(
                f"No {spec['bud_year']} bud record for prefecture_code={pollen_row['prefecture_code']}"
            )
        if int(bud_row["survey_year"]) + 1 != int(pollen_row["season_year"]):
            raise ValueError("Temporal pairing must be previous autumn survey -> next spring pollen season")
        bud_values.append(float(bud_row["observation_count_per_m2"]))
        pollen_values.append(float(pollen_row["sugi_pollen_count_per_cm2"]))

    pollen_input = {
        "season_year": spec["pollen_year"],
        "records": spec["expected_pollen_records"],
        "unit": "個/cm²",
        "source_url": spec["pollen_source_url"],
    }
    if spec.get("site_identity_source_url"):
        pollen_input["site_identity_source_url"] = spec["site_identity_source_url"]
    if spec.get("pollen_as_of"):
        pollen_input["as_of"] = spec["pollen_as_of"]

    result = {
        "question": spec["question"],
        "input": {
            "bud_survey": {
                "year": spec["bud_year"],
                "records": spec["expected_bud_records"],
                "unit": "個/m²",
                "source_url": spec["bud_source_url"],
            },
            "sugi_pollen": pollen_input,
            "paired_records": len(bud_values),
        },
        "metrics": {
            "pearson_raw": round(pearson(bud_values, pollen_values), 6),
            "spearman_rank": round(pearson(average_ranks(bud_values), average_ranks(pollen_values)), 6),
            "pearson_log1p": round(
                pearson(
                    [math.log1p(value) for value in bud_values],
                    [math.log1p(value) for value in pollen_values],
                ),
                6,
            ),
        },
        "interpretation": spec["interpretation"],
    }

    if spec["pollen_year"] == 2026:
        prior = json.loads((ROOT / "analysis" / "2024-bud-2025-sugi-pollen.json").read_text(encoding="utf-8"))
        result["comparison_to_prior_analysis"] = {
            "artifact": "analysis/2024-bud-2025-sugi-pollen.json",
            "prior_paired_records": prior["input"]["paired_records"],
            "prior_pearson_raw": prior["metrics"]["pearson_raw"],
            "prior_spearman_rank": prior["metrics"]["spearman_rank"],
            "prior_pearson_log1p": prior["metrics"]["pearson_log1p"],
        }

    spec["output_path"].parent.mkdir(parents=True, exist_ok=True)
    spec["output_path"].write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main():
    for spec in ANALYSES:
        analyze(spec)


if __name__ == "__main__":
    main()
