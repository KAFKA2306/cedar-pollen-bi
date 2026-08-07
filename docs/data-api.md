# 公開データ API v1

環境省「令和7年度スギ雄花花芽調査」の都道府県別表を、出典を保持した機械可読データとして配布します。

## エンドポイント

GitHub Pages のサイトルートを `https://kafka2306.github.io/cedar-pollen-bi/` とした場合:

- `api/v1/observations.csv` — 47都道府県の観測値・過年度平均・環境省公表比較率
- `api/v1/latest.json` — 最新調査の件数と比較率の最大・最小
- `api/v1/facets.json` — 地域別件数・比較基準期間別件数
- `api/v1/manifest.json` — 出典、取得日時、件数、各ファイルのbyte数・SHA-256、利用条件

## 正準ソース

- 報道発表: https://www.env.go.jp/press/press_02181.html
- 都道府県別表（資料1）: https://www.env.go.jp/content/000365031.pdf
- 公表日: 2025-12-23
- 調査年: 2025（令和7年度）
- 取得日時: 2026-08-07T17:14:09Z

`data/official/moe-cedar-bud-2025.csv` は資料1の表を転記・構造化した加工データです。原資料そのものではありません。

## 欠損値

沖縄県は資料1で新規調査地点として掲載され、過年度平均と比較率が空欄です。APIでも推測せず空欄を維持します。

## 利用条件

環境省ホームページは、特記または権利表記がないコンテンツについて「公共データ利用規約（第1.0版）」を適用し、利用時の出典記載、編集・加工した場合の加工主体・加工事実の明示を求めています。

- https://www.env.go.jp/mail.html

本リポジトリでは出典URL、公表日、取得日時、加工データである旨をmanifestとこの文書に保持します。

## 差分同期

最初に `manifest.json` を取得し、各配布物の `sha256` が手元の値と異なる場合だけ対象ファイルを再取得してください。推奨再検証間隔は1時間です。

```python
import csv
import io
import urllib.request

url = "https://kafka2306.github.io/cedar-pollen-bi/api/v1/observations.csv"
text = urllib.request.urlopen(url).read().decode("utf-8")
rows = list(csv.DictReader(io.StringIO(text)))
print(len(rows))
```

## 更新方針

新しい環境省調査を取り込む際は旧年データを上書き・削除せず、年別の正準snapshotを追加します。公開API v1の破壊的変更は行わず、必要な場合は新しいAPIバージョンへ分離します。
