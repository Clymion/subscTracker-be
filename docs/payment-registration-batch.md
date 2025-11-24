# 支払履歴登録バッチ — 手動実行と運用メモ

このドキュメントは `scripts/register_payment_histories.py` を手動で実行する際の手順、注意点、運用上のメモをまとめたものです。

**対象スクリプト**: `scripts/register_payment_histories.py`

## 概要
- 本スクリプトは、アクティブなサブスクリプションの支払期日に基づき `PaymentHistory` レコードを作成します。
- 日次のスケジュール実行（運用 cron）または手動起動の両方に対応します。
- 同時実行は簡易ファイルロックで防止しています（`/tmp/register_payment_histories.lock` を使用）。

## 前提（初回実行前に必須）
1. マイグレーションを適用して `next_payment_date` 等のスキーマ変更が DB に反映されていること。
   - プロジェクトでは `scripts/apply_migrations.sh` などでマイグレーションを実行できます。
     ```bash
     ./scripts/apply_migrations.sh
     ```
2. 為替レートが必要な通貨については、事前に `ExchangeRate` レコードが準備されていること（同通貨は合成レートを内部で作成します）。
   - 例: 開発環境でサンプルレートを取得する場合
     ```bash
     python scripts/fetch_exchange_rates.py
     ```
3. （推奨）テスト環境やステージングで一度手動実行して影響範囲を確認すること。

## 手動実行コマンド
- リポジトリのルートで実行します。

1) すべての支払対象サブスクリプションを処理（通常実行）
```bash
python scripts/register_payment_histories.py
```

1) 特定のサブスクリプションのみ処理（カンマ区切りID指定）
```bash
python scripts/register_payment_histories.py --subscription-ids 101,102,203
```

1) テスト / CI で実行する場合（統合テスト）
```bash
pytest tests/integration/test_payment_registration_batch.py -q
```

## 実行結果とログ
- スクリプトは標準出力へ INFO/ERROR ログを出力します。運用ではログをファイルへリダイレクトしてください。
  ```bash
  python scripts/register_payment_histories.py >> /var/log/payment_registration_batch.log 2>&1
  ```
- 終了コード: `0`=成功、`1`=失敗（未処理の致命的エラー等）。
- ログには処理したサブスクリプション数、成功数、失敗数のサマリが含まれます。

## 初回（バックフィル）実行時の注意
- 新規に登録されたサブスクリプションで支払履歴が全くない場合、バッチは `initial_payment_date` から現在までの過去支払日をまとめて生成します。大量に履歴が生成される可能性があるため、初回実行はステージングで影響を確かめてから本番で行ってください。
- 初回大量バックフィルを行う際は、以下を検討してください:
  - 実行時間・DB負荷を分散するために時間帯を選ぶ（深夜など）。
  - 必要に応じて `--subscription-ids` で分割実行する。

## 同時実行とロック
- 現行実装はファイルロック(`/tmp/register_payment_histories.lock`) による簡易排他を実装しています。複数プロセスが同時に実行されると先に起動したプロセスのみが処理を行い、後続は終了します。
- 運用環境が Postgres の場合は、より堅牢な Postgres advisory lock への移行を推奨します（このドキュメントの末尾にサンプルを記載）。

## Cron例（毎日 01:00 JST に実行）
※システムのタイムゾーンに依存します。サーバが JST の場合:
```cron
0 1 * * * /usr/bin/python /path/to/repo/scripts/register_payment_histories.py >> /var/log/payment_registration_batch.log 2>&1
```

もしサーバタイムゾーンが UTC の場合、JST 01:00 は前日の16:00 UTCなので cron を調整してください。

## トラブルシューティング
- 為替レートが見つからない場合: スクリプトはそのサブスクリプションをスキップしエラーログに記録します。該当レートを追加して再実行してください。
- FK や DB エラーが発生した場合: ログのスタックトレースを確認の上、該当サブスクリプションを限定して手動で再実行してください。

## 補足（改善案）
- 運用では以下の改善を推奨します:
  - Postgres の advisory lock を使った排他処理（より確実）。
  - 実行前の dry-run オプション（現在未実装） — 生成予定の件数と日付を確認できると安全。
  - モニタリング/メトリクス（処理件数、失敗件数）をログだけでなく Prometheus 等へ送る。

## 連絡先 / 追加作業
- このドキュメントの修正や、advisory lock への変更等が必要であれば教えてください。サンプルパッチを作成します。
