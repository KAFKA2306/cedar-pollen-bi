# 公開データ API v1

環境省「令和7年度スギ雄花花芽調査」の都道府県別表を、出典と比較可否を保持した機械可読データとして配布します。

公開先:

https://kafka2306.github.io/cedar-pollen-bi/api/v1/

## 配布ファイル

- `observations.csv` — 47都道府県の観測値、過去平均、環境省公表比較率、出典
- `comparability.json` — 過去平均と比較できるか、その理由
- `editorial-pack.json` — 編集・広報用途で再利用しやすい都道府県別データ
- `latest.json` — 調査年、件数、比較率の最大・最小
- `facets.json` — 地域別件数、比較基準期間別件数
- `manifest.json` — 出典、取得日時、件数、各配布ファイルのbyte数・SHA-256、利用条件

## 正準ソース

- 報道発表: https://www.env.go.jp/press/press_02181.html
- 都道府県別表（資料1）: https://www.env.go.jp/content/000365031.pdf
- 公表日: 2025-12-23
- 調査年: 2025（令和7年度）

`data/official/moe-cedar-bud-2025.csv` は資料1の表を転記・構造化した加工データです。原資料そのものではありません。取得日時、利用条件などの出典情報は `data/official/moe-source-metadata.json` に保持します。

## 欠損値と比較可否

沖縄県は資料1で新規調査地点として掲載され、過去平均と比較率が空欄です。APIでも推測せず空欄を維持し、`comparability.json` で比較不能として分離します。

## 利用条件

環境省ホームページは、特記または権利表記がないコンテンツについて「公共データ利用規約（第1.0版）」を適用し、利用時の出典記載、編集・加工した場合の加工主体・加工事実の明示を求めています。

https://www.env.go.jp/mail.html

本リポジトリでは出典URL、公表日、取得日時、加工データである旨を `manifest.json` と正準メタデータに保持します。

## 差分確認

配布ファイルが更新されたか確認する場合は、`manifest.json` の各ファイルの `sha256` を比較できます。再取得頻度は利用側の要件に合わせて決めてください。

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
