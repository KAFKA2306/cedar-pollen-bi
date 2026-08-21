# Cedar Pollen BI

[![Data contract and public API](https://github.com/KAFKA2306/cedar-pollen-bi/actions/workflows/data-contract.yml/badge.svg)](https://github.com/KAFKA2306/cedar-pollen-bi/actions/workflows/data-contract.yml)
[![pages-build-deployment](https://github.com/KAFKA2306/cedar-pollen-bi/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/KAFKA2306/cedar-pollen-bi/actions/workflows/pages/pages-build-deployment)

**スギ雄花の花芽量は、空中花粉飛散量の実測値でも、個人の症状予測でもありません。**

Cedar Pollen BI は、環境省「令和7年度スギ雄花花芽調査」の都道府県別観測値と、資料1に掲載された過去平均比を表示します。原則は過去10年平均ですが、観測歴が10年未満の地点は実際に観測した年数の平均が使われます。沖縄県は新規観測で過去平均がないため、観測値は保持し、比率比較は行いません。

- **公開サイト:** https://kafka2306.github.io/cedar-pollen-bi/
- **環境省発表:** https://www.env.go.jp/press/press_02181.html
- **資料1（令和7年度観測値・比較値）:** https://www.env.go.jp/content/000365031.pdf
- **資料2（過去の観測値）:** https://www.env.go.jp/content/000365032.pdf

## 読めるもの

- 47都道府県のスギ雄花花芽量
- 資料1に過去平均がある46都道府県の比較比率
- 各都道府県の基準年数に関する注記
- 公式資料への根拠リンク
- 比較できない場合の理由

比率は、その地点の資料上の過去平均を100%とした比較です。したがって、すべての地点が同じ10年間を基準にしているわけではありません。

## データと再現

正準入力は [`data/official/moe-cedar-bud-2025.csv`](data/official/moe-cedar-bud-2025.csv) です。出典・取得日時・利用条件は [`data/official/moe-source-metadata.json`](data/official/moe-source-metadata.json) に保持します。

```text
環境省 資料1
  → data/official/moe-cedar-bud-2025.csv
  → scripts/build_public_api.py で件数・重複・分母・比率を検証
  → api/v1/ の公開データを再生成
  → pollen-bi.js が公開データを読み込んで表示
```

再生成と検証は標準ライブラリだけで実行できます。

```bash
python scripts/build_public_api.py
python tests/test_public_api.py
```

GitHub Actions は同じ処理を実行し、再生成結果がcommit済み `api/v1/` と異なる場合に失敗します。

## 解釈上の境界

- 花芽量と実際の空中花粉飛散量を同一視しません。
- 花芽量から個人の症状や医療上のリスクを推定しません。
- 基準期間・観測年数・単位が異なる値を同条件の測定として扱いません。
- 公式資料に過去平均がない場合、比率を推測で補いません。

プロジェクト内の情報種別の定義は [`ontology/project.yaml`](ontology/project.yaml) を参照してください。
