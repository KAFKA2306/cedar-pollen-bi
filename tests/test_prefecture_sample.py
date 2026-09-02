#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_public_api", ROOT / "scripts" / "build_public_api.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
rows = module.load_rows()

for code in ("13", "47"):
    row = next(item for item in rows if item["prefecture_code"] == code)
    files = module.build_prefecture_sample(row)
    assert set(files) == {"data.json", "index.html", "chart.svg"}
    data = json.loads(files["data.json"].decode("utf-8"))
    assert data["prefecture_code"] == code
    assert data["source_url"] == "https://www.env.go.jp/content/000365031.pdf"
    assert data["source_page"] == 1
    assert data["source_section"] == "資料1"
    assert "空中花粉飛散量そのもの" in files["index.html"].decode("utf-8")
    assert "空中花粉飛散量そのもの" in files["chart.svg"].decode("utf-8")

tokyo = json.loads(module.build_prefecture_sample(next(item for item in rows if item["prefecture_code"] == "13"))["data.json"].decode("utf-8"))
assert tokyo["prefecture_name_ja"] == "東京都"
assert tokyo["comparison_status"] == "comparable"
assert tokyo["baseline_average_count_per_m2"] is not None
assert tokyo["official_comparison_percent"] is not None

okinawa_files = module.build_prefecture_sample(next(item for item in rows if item["prefecture_code"] == "47"))
okinawa = json.loads(okinawa_files["data.json"].decode("utf-8"))
assert okinawa["prefecture_name_ja"] == "沖縄県"
assert okinawa["comparison_status"] == "not_comparable"
assert okinawa["baseline_average_count_per_m2"] is None
assert okinawa["official_comparison_percent"] is None
assert okinawa["not_comparable_reason"] == "new observation; no historical baseline"
assert "過去平均なし" in okinawa_files["index.html"].decode("utf-8")
assert "比率比較は行いません" in okinawa_files["chart.svg"].decode("utf-8")

print("Prefecture sample generation passed for comparable and not-comparable canonical data")
