# Cedar Pollen BI

環境省のスギ雄花花芽調査を、過去10年平均比として都道府県別に可視化する公開データBIです。

- Deployed site: https://kafka2306.github.io/cedar-pollen-bi/

## 読み取り境界

このダッシュボードが観測するのは、花粉飛散予測へ入力される**スギ雄花花芽量**です。空中花粉の実測値、花粉飛散予測値、予測精度とは同一ではありません。

## 因果・証拠オントロジー

上位システムは `CedarPollenInputObservationSystem` です。

```text
公式調査資料
→ 都道府県別観測値
→ 基準期間との比較
→ 比率計算
→ 表示区分
→ BI公開
```

`OfficialObservation`、`CalculatedValue`、`DerivedClassification`、`Interpretation`、`Forecast`を区別します。公式出典、調査年、基準期間、単位、比較可能性が欠ける値は補完せず、`UNKNOWN` または `mark_not_comparable` とします。

- [プロジェクト・オントロジー](ontology/project.yaml)
- [共通因果・証拠オントロジー](https://github.com/KAFKA2306/know/blob/main/ontology/causal-evidence-core.yaml)