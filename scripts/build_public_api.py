#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "official" / "moe-cedar-bud-2025.csv"
OUT = ROOT / "api" / "v1"
SAMPLES = ROOT / "samples"

REGIONS = {
"01":"北海道","02":"東北","03":"東北","04":"東北","05":"東北","06":"東北","07":"東北",
"08":"関東","09":"関東","10":"関東","11":"関東","12":"関東","13":"関東","14":"関東",
"15":"中部","16":"中部","17":"中部","18":"中部","19":"中部","20":"中部","21":"中部","22":"中部","23":"中部",
"24":"近畿","25":"近畿","26":"近畿","27":"近畿","28":"近畿","29":"近畿","30":"近畿",
"31":"中国","32":"中国","33":"中国","34":"中国","35":"中国",
"36":"四国","37":"四国","38":"四国","39":"四国",
"40":"九州・沖縄","41":"九州・沖縄","42":"九州・沖縄","43":"九州・沖縄","44":"九州・沖縄","45":"九州・沖縄","46":"九州・沖縄","47":"九州・沖縄",
}

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

def build_editorial_pack(rows: list[dict]) -> dict:
    records=[]
    for row in rows:
        records.append({
            "prefecture_code":row["prefecture_code"],
            "prefecture_name_ja":row["prefecture_name_ja"],
            "region":row["region"],
            "survey_year":2025,
            "observation_count_per_m2":row["observation"],
            "baseline_average_count_per_m2":row["baseline"],
            "official_comparison_percent":row["ratio"],
            "comparison_status":row["comparison_status"],
            "not_comparable_reason":row["not_comparable_reason"],
            "source_url":row["source_url"],
            "source_page":int(row["source_page"]),
            "source_section":row["source_section"],
        })
    return {
        "schema_version":"1.0.0",
        "dataset":"moe_cedar_male_flower_bud_survey",
        "purpose":"地域記事・広報資料で、環境省のスギ雄花花芽調査を出典付きで再利用するためのデータパック",
        "survey_year":2025,
        "unit":"個/m²",
        "records":records,
        "usage_notes":[
            "スギ雄花の花芽量であり、空中花粉飛散量そのものではない。",
            "個人の症状、医療上の危険度、安全性を示す値ではない。",
            "comparison_status が not_comparable の地域を比率ランキングへ含めない。",
            "各値を掲載する場合は source_url、source_page、source_section から環境省一次資料へ遡れる。",
        ],
    }

def build_prefecture_sample(row: dict) -> dict[str, bytes]:
    name=row["prefecture_name_ja"]
    obs=row["observation"]
    base=row["baseline"]
    ratio=row["ratio"]
    source=row["source_url"]
    page=int(row["source_page"])
    section=row["source_section"]
    comparable=row["comparison_status"] == "comparable"
    note="スギ雄花の花芽量であり、空中花粉飛散量そのものや個人の症状を予測する値ではありません。"
    data={
        "prefecture_code":row["prefecture_code"],
        "prefecture_name_ja":name,
        "survey_year":2025,
        "unit":"個/m²",
        "observation_count_per_m2":obs,
        "baseline_average_count_per_m2":base,
        "official_comparison_percent":ratio,
        "comparison_status":row["comparison_status"],
        "not_comparable_reason":row["not_comparable_reason"],
        "source_url":source,
        "source_page":page,
        "source_section":section,
        "note":note,
    }
    if comparable:
        comparison_html=f"<dt>過去平均</dt><dd>{base:,} 個/m²</dd>\n<dt>公式比較率</dt><dd>{ratio}%</dd>\n<dt>比較可否</dt><dd>比較可能</dd>"
        comparison_summary=f"花芽量 {obs:,} 個/m² / 過去平均 {base:,} 個/m² / 公式比較率 {ratio}%"
        comparison_desc=f"花芽量{obs}個毎平方メートル、過去平均{base}個毎平方メートル、公式比較率{ratio}パーセント。"
        baseline_width=round(508 * base / max(obs, base))
        observation_width=round(508 * obs / max(obs, base))
        comparison_svg=f'''<text x="48" y="215" font-family="sans-serif" font-size="16">過去平均</text><rect x="180" y="195" width="{baseline_width}" height="28" fill="#999"/><text x="700" y="216" font-family="sans-serif" font-size="16">{base:,}</text>'''
    else:
        reason=row["not_comparable_reason"] or "過去平均なし"
        comparison_html=f"<dt>過去平均</dt><dd>なし</dd>\n<dt>公式比較率</dt><dd>なし</dd>\n<dt>比較可否</dt><dd>比較不能（{reason}）</dd>"
        comparison_summary=f"花芽量 {obs:,} 個/m² / 過去平均なし / 比較不能"
        comparison_desc=f"花芽量{obs}個毎平方メートル。過去平均がないため比較不能。"
        observation_width=508
        comparison_svg=f'''<text x="48" y="215" font-family="sans-serif" font-size="16">過去平均なしのため比率比較は行いません</text>'''
    html=f'''<!doctype html>
<html lang="ja">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{name} スギ雄花花芽量 2025</title></head>
<body>
<main>
<h1>{name} スギ雄花花芽量 2025</h1>
<p>環境省「令和7年度スギ雄花花芽調査」{section}の{name}の観測値です。</p>
<dl>
<dt>花芽量</dt><dd>{obs:,} 個/m²</dd>
{comparison_html}
</dl>
<p><strong>注意:</strong> {note}</p>
<p>出典: <a href="{source}">環境省「令和7年度スギ雄花花芽調査」{section}、{page}ページ</a></p>
<p><a href="data.json">JSON</a> / <a href="chart.svg">SVG図表</a></p>
</main>
</body>
</html>
'''
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 420" role="img" aria-labelledby="title desc">
<title id="title">{name} スギ雄花花芽量 2025</title>
<desc id="desc">{comparison_desc}</desc>
<rect width="800" height="420" fill="white"/>
<text x="48" y="55" font-family="sans-serif" font-size="28">{name} スギ雄花花芽量 2025</text>
<text x="48" y="100" font-family="sans-serif" font-size="18">{comparison_summary}</text>
<text x="48" y="155" font-family="sans-serif" font-size="16">花芽量</text><rect x="180" y="135" width="{observation_width}" height="28" fill="#555"/><text x="700" y="156" font-family="sans-serif" font-size="16">{obs:,}</text>
{comparison_svg}
<text x="48" y="285" font-family="sans-serif" font-size="15">{note}</text>
<text x="48" y="330" font-family="sans-serif" font-size="14">出典: 環境省「令和7年度スギ雄花花芽調査」{section}、{page}ページ</text>
<text x="48" y="360" font-family="sans-serif" font-size="14">{source}</text>
</svg>
'''
    return {
        "data.json":(json.dumps(data, ensure_ascii=False, indent=2)+"\n").encode(),
        "index.html":html.encode(),
        "chart.svg":svg.encode(),
    }

def parse_args() -> argparse.Namespace:
    parser=argparse.ArgumentParser(description="環境省の正準データから公開APIと地域サンプルを生成します。")
    parser.add_argument("--sample-prefecture-code", default="27", choices=sorted(REGIONS), help="生成する地域サンプルの都道府県コード（既定: 27 大阪府）")
    parser.add_argument("--sample-output", type=Path, default=SAMPLES / "osaka", help="地域サンプルの出力先（既定: samples/osaka）")
    return parser.parse_args()

def main() -> int:
    args=parse_args()
    rows=load_rows()
    OUT.mkdir(parents=True, exist_ok=True)
    comparable=[r for r in rows if r["comparison_status"] == "comparable"]
    latest={
        "schema_version":"1.0.0","survey_year":2025,"prefecture_count":len(rows),"comparable_prefecture_count":len(comparable),
        "max_official_comparison":max(({"prefecture_code":r["prefecture_code"],"prefecture_name_ja":r["prefecture_name_ja"],"percent":r["ratio"]} for r in comparable),key=lambda x:x["percent"]),
        "min_official_comparison":min(({"prefecture_code":r["prefecture_code"],"prefecture_name_ja":r["prefecture_name_ja"],"percent":r["ratio"]} for r in comparable),key=lambda x:x["percent"]),
        "source_published_date":"2025-12-23","source_url":"https://www.env.go.jp/content/000365031.pdf"}
    region_counts={}; baseline_types={}
    for r in rows:
        region_counts[r["region"]]=region_counts.get(r["region"],0)+1
        note=r["baseline_note"] or "no baseline"
        baseline_types[note]=baseline_types.get(note,0)+1
    facets={"schema_version":"1.0.0","regions":dict(sorted(region_counts.items())),"baseline_types":dict(sorted(baseline_types.items()))}
    comparability={
        "schema_version":"1.0.0",
        "records":[{
            "prefecture_code":r["prefecture_code"],
            "comparison_status":r["comparison_status"],
            "not_comparable_reason":r["not_comparable_reason"],
        } for r in rows],
    }
    payloads={
        "observations.csv":SOURCE.read_bytes(),
        "comparability.json":json_bytes(comparability),
        "editorial-pack.json":json_bytes(build_editorial_pack(rows)),
        "latest.json":json_bytes(latest),
        "facets.json":json_bytes(facets),
    }
    for name,data in payloads.items():
        (OUT/name).write_bytes(data)
    manifest={
        "schema_version":"1.0.0","dataset":"moe_cedar_male_flower_bud_survey",
        "source":{"path":str(SOURCE.relative_to(ROOT)),"sha256":sha256_bytes(SOURCE.read_bytes()),"publisher":"Ministry of the Environment, Japan","published_date":"2025-12-23","retrieved_at":"2026-08-07T17:14:09Z","document_url":"https://www.env.go.jp/content/000365031.pdf","terms":{"name":"公共データ利用規約（第1.0版）","url":"https://www.env.go.jp/mail.html","attribution_required":True,"processing_disclosure_required":True}},
        "counts":{"prefectures":len(rows),"comparable":len(comparable)},
        "files":{name:{"bytes":len(data),"sha256":sha256_bytes(data)} for name,data in payloads.items()},
        "cache_control_hint":"max-age=3600, must-revalidate"
    }
    (OUT/"manifest.json").write_bytes(json_bytes(manifest))

    sample=next(r for r in rows if r["prefecture_code"] == args.sample_prefecture_code)
    sample_dir=args.sample_output if args.sample_output.is_absolute() else ROOT / args.sample_output
    sample_dir.mkdir(parents=True, exist_ok=True)
    for name,data in build_prefecture_sample(sample).items():
        (sample_dir/name).write_bytes(data)

    print(json.dumps({"prefectures":len(rows),"comparable":len(comparable),"output":str(OUT),"sample_prefecture_code":sample["prefecture_code"],"sample":str(sample_dir)},ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
