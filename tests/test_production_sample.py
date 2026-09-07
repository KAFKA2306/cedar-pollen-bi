import json
import urllib.request
from pathlib import Path

BASE_URL = "https://kafka2306.github.io/cedar-pollen-bi/samples/osaka/"
EXPECTED_JSON = json.loads(Path("samples/osaka/data.json").read_text(encoding="utf-8"))


def fetch(path=""):
    request = urllib.request.Request(BASE_URL + path, headers={"User-Agent": "cedar-pollen-bi-production-contract/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.status, response.headers.get_content_type(), response.read()


def main():
    html_status, html_type, html_body = fetch()
    assert html_status == 200, html_status
    assert html_type == "text/html", html_type
    html = html_body.decode("utf-8")
    assert "大阪府" in html
    assert str(EXPECTED_JSON["observation_count_per_m2"]) in html

    json_status, json_type, json_body = fetch("data.json")
    assert json_status == 200, json_status
    assert json_type == "application/json", json_type
    assert json.loads(json_body) == EXPECTED_JSON

    svg_status, svg_type, svg_body = fetch("chart.svg")
    assert svg_status == 200, svg_status
    assert svg_type == "image/svg+xml", svg_type
    svg = svg_body.decode("utf-8")
    assert "<svg" in svg
    assert "大阪府" in svg

    print("production Osaka sample verified: HTML/JSON/SVG 3/3")


if __name__ == "__main__":
    main()
