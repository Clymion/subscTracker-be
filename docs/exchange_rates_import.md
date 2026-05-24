**為替レート CSV インポート**

- **目的**: CSV ファイルから過去の為替レートをローカルの `exchange_rates` テーブルへインポートします。1つのファイルに複数の通貨ペアが含まれていても対応可能です。必要に応じて同通貨の合成レート（rate=1.0）も作成し、支払履歴登録時の親レコード欠損による FOREIGN KEY エラーを防ぎます。
- **スクリプト**: `scripts/import_exchange_rates_from_csv.py`
- **データ取得元**: https://www.tfx.co.jp/historical/fx/

**前準備**
1. ファイルエンコードをsjisからutf-8に変換する
2. 中国人民元の`CNH`は`CNY`に、csvファイル内で置換する
3. 最初の2行を削除する

使用例:

```bash
# ファイル内の全通貨ペアをインポート
poetry run python scripts/import_exchange_rates_from_csv.py --file tmp/fx_result.csv

# 特定の通貨ペアのみインポート
poetry run python scripts/import_exchange_rates_from_csv.py --file tmp/fx_result.csv --from-to USD-JPY

# 同通貨の合成レートを作成したくない場合
poetry run python scripts/import_exchange_rates_from_csv.py --file tmp/fx_result.csv --no-synthetic
```

- **CSV の想定フォーマット**:
  - ヘッダ: `商品名,商品タイプ,取引日,当日清算価格`
  - 1つのファイルに複数通貨ペアが混在可能（例: USD/JPY, EUR/JPY, CNH/JPY）
  - 日付形式: `YYYY/MM/DD`（例: `2026/03/23`）
  - レート: `当日清算価格` 列を使用

- **注意点 / 補足**:
  - 本スクリプトは `exchange_rates` テーブルに対して UPSERT（ON CONFLICT DO UPDATE）で挿入・更新を行います。
  - デフォルトで CSV に含まれる各日付について、同通貨（例: `USD->USD` / `JPY->JPY`）の合成レート（rate=1.0、`source`=`synthetic-import`）を作成します。これにより、支払履歴登録時に同通貨の為替レート参照が見つからず FK エラーになる事象を回避します。
  - インポート元の `source` カラムには `csv:<filename>` が設定され、合成レートは `synthetic-import` となります。

- **いつ実行するか**:
  - 過去日付の為替レートが見つからず `payment_histories` 挿入で FK エラーが発生する場合、支払履歴登録バッチを実行する前に本スクリプトで履歴を投入してください。
