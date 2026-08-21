#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "official" / "moe-cedar-bud-2025.csv"
OUT = ROOT / "api" / "v1"

REGIONS = {
"01":"北海道","02":"東北","03":"東北","04":"東北","05":"東北","06":"東北","07":"東北",
"08":"関東","09":"関東","10":"関東","11":"関東","12":"関東","13":"関東","14":"関東",
"15":"中部","16":"中部","17":"中部","18":"中部","19":"中部","20":"中部","21":"中部","22":"中部","23":"中部",
"24":"近畿","25":"近畿","26":"近畿","27":"近畿","28":"近畿","29":"近畿","30":"近畿",
"31":"中国","32":"中国","33":"中国","34":"中国","35":"中国",
"36":"四国","37":"四国","38":"四国","39":"四国",
"40":"九州・沖縄","41":"九州・沖縄","42":"九州・沖縄","43":"九州・沖縄","44":"九州・沖縄","45":"九州・沖縄","46":"九州・沖縄","47":"九州・沖縄",
}
UNIT = "個/m2"
SOURCE_LOCATOR = "資料1 都道府県別表"

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def json_bytes(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))+"\n").encode()

def load_rows() -> list[dict]:
    with SOURCE.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 47:
        raise ValueError(f"expected 47 prefectures, got {len(rows)}")
    seen=set()
    result=[]
    for row in rows:
        code=row["prefecture_code"]
        if code in seen or code not in REGIONS:
            raise ValueError(f"invalid or duplicate prefecture_code: {code}")
        seen.add(code)
        obs=int(row["observation_count_per_m2"])
        base=int(row["baseline_average_count_per_m2"]) if row["baseline_average_count_per_m2"] else None
        ratio=int(row["official_comparison_percent"]) if row["official_comparison_percent"] else None
        if obs < 0 or (base is not None and base <= 0):
            raise ValueError(f"invalid observation/baseline: {code}")
        if base is None and ratio is not None:
            raise ValueError(f"ratio without baseline: {code}")
        if base is not None and ratio is None:
            raise ValueError(f"baseline without ratio: {code}")
        if base is not None and abs(round(obs/base*100)-ratio) > 1:
            raise ValueError(f"official ratio mismatch: {code}")
        comparison_status = "comparable" if ratio is not None else "not_comparable"
        reason = None if ratio is not None else row["baseline_note"] or "historical baseline unavailable"
        result.append({**row,"region":REGIONS[code],"observation":obs,"baseline":base,"ratio":ratio,"comparison_status":comparison_status,"not_comparable_reason":reason})
    return result

def public_records(rows: list[dict], source_sha256: str) -> list[dict]:
    records=[]
    for r in rows:
        source={
            "publisher":r["publisher"],
            "document_url":r["source_url"],
            "published_date":r["published_date"],
            "retrieved_at":r["retrieved_at"],
            "locator":SOURCE_LOCATOR,
            "sha256":source_sha256,
        }
        records.append({
            "record_id":f"moe-cedar-bud-{r['survey_year']}-{r['prefecture_code']}-observation",
            "prefecture_code":r["prefecture_code"],
            "prefecture_name_ja":r["prefecture_name_ja"],
            "survey_year":int(r["survey_year"]),
            "metric_type":"official_flower_bud_observation",
            "value":r["observation"],
            "unit":UNIT,
            "baseline":None if r["baseline"] is None else {
                "start_year":2015 if "10-year" in r["baseline_note"] else int(r["survey_year"])-int(r["baseline_note"].split("-")[0]),
                "end_year":2024,
                "value":r["baseline"],
                "unit":UNIT,
            },
            "comparison_status":r["comparison_status"],
            "not_comparable_reason":r["not_comparable_reason"],
            "source":source,
            "transformation":None,
        })
    return records

def main() -> int:
    source_bytes=SOURCE.read_bytes()
    source_sha256=sha256_bytes(source_bytes)
    rows=load_rows()
    OUT.mkdir(parents=True, exist_ok=True)
    comparable=[r for r in rows if r["comparison_status"] == "comparable"]
    records=public_records(rows, source_sha256)
    latest={
        "schema_version":"1.0.0","survey_year":2025,"prefecture_count":len(rows),"comparable_prefecture_count":len(comparable),
        "max_official_comparison":max(({"prefecture_code":r["prefecture_code"],"prefecture_name_ja":r["prefecture_name_ja"],"percent":r["ratio"]} for r in comparable),key=lambda x:x["percent"]),
        "min_official_comparison":min(({"prefecture_code":r["prefecture_code"],"prefecture_name_ja":r["prefecture_name_ja"],"percent":r["ratio"]} for r in comparable),key=lambda x:x["percent"]),
        "source_published_date":"2025-12-23","source_url":"https://www.env.go.jp/content/000365031.pdf"}
    region_counts={}; baseline_types={}; comparison_statuses={}
    for r in rows:
        region_counts[r["region"]]=region_counts.get(r["region"],0)+1
        note=r["baseline_note"] or "no baseline"
        baseline_types[note]=baseline_types.get(note,0)+1
        comparison_statuses[r["comparison_status"]]=comparison_statuses.get(r["comparison_status"],0)+1
    facets={"schema_version":"1.0.0","regions":dict(sorted(region_counts.items())),"baseline_types":dict(sorted(baseline_types.items())),"comparison_statuses":dict(sorted(comparison_statuses.items()))}
    payloads={
        "observations.csv":source_bytes,
        "records.json":json_bytes(records),
        "latest.json":json_bytes(latest),
        "facets.json":json_bytes(facets),
    }
    for name,data in payloads.items():
        (OUT/name).write_bytes(data)
    manifest={
        "schema_version":"1.0.0","dataset":"moe_cedar_male_flower_bud_survey",
        "record_schema":"/cedar-pollen-bi/schemas/cedar-pollen-record.schema.json",
        "source":{"path":str(SOURCE.relative_to(ROOT)),"sha256":source_sha256,"publisher":"Ministry of the Environment, Japan","published_date":"2025-12-23","retrieved_at":"2026-08-07T17:14:09Z","document_url":"https://www.env.go.jp/content/000365031.pdf","terms":{"name":"公共データ利用規約（第1.0版）","url":"https://www.env.go.jp/mail.html","attribution_required":True,"processing_disclosure_required":True}},
        "counts":{"prefectures":len(rows),"comparable":len(comparable),"not_comparable":len(rows)-len(comparable)},
        "files":{name:{"bytes":len(data),"sha256":sha256_bytes(data)} for name,data in payloads.items()},
        "cache_control_hint":"max-age=3600, must-revalidate"}
    (OUT/"manifest.json").write_bytes(json_bytes(manifest))
    print(json.dumps({"prefectures":len(rows),"comparable":len(comparable),"not_comparable":len(rows)-len(comparable),"output":str(OUT)},ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
