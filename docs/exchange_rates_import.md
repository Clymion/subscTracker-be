**為替レート CSV インポート**

- **目的**: CSV ファイルから過去の為替レートをローカルの `exchange_rates` テーブルへインポートします。必要に応じて同通貨の合成レート（rate=1.0）も作成し、支払履歴登録時の親レコード欠損による FOREIGN KEY エラーを防ぎます。
- **スクリプト**: `scripts/import_exchange_rates_from_csv.py`
- **データ取得元**: https://www.dukascopy.com/swiss/english/marketwatch/historical/

使用例:

```
# ファイル名に通貨ペアが含まれている場合 (例: USD-JPY_...)
poetry run python scripts/import_exchange_rates_from_csv.py --file /path/to/USD-JPY_Day_2025-06-01_to_2025-11-23_UTC.csv

# ファイル名に通貨ペアが含まれていない場合は明示的に指定:
poetry run python scripts/import_exchange_rates_from_csv.py --file /path/to/file.csv --from-to USD-JPY

# 同通貨の合成レートを作成したくない場合:
poetry run python scripts/import_exchange_rates_from_csv.py --file /path/to/USD-JPY.csv --no-synthetic
```

- **CSV の想定フォーマット**:
  - ヘッダ: `UTC,Open,High,Low,Close,Volume`（`Close` 列をレートとして使用します）
  - タイムスタンプ形式: `DD.MM.YYYY HH:MM:SS UTC`（例: `01.06.2025 00:00:00 UTC`）

- **注意点 / 補足**:
  - 本スクリプトは `exchange_rates` テーブルに対して UPSERT（ON CONFLICT DO UPDATE）で挿入・更新を行います。
  - デフォルトで CSV に含まれる各日付について、同通貨（例: `USD->USD` / `JPY->JPY`）の合成レート（rate=1.0、`source`=`synthetic-import`）を作成します。これにより、支払履歴登録時に同通貨の為替レート参照が見つからず FK エラーになる事象を回避します。
  - インポート元の `source` カラムには `csv:<filename>` が設定され、合成レートは `synthetic-import` となります。

- **いつ実行するか**:
  - 過去日付の為替レートが見つからず `payment_histories` 挿入で FK エラーが発生する場合、支払履歴登録バッチを実行する前に本スクリプトで履歴を投入してください。
