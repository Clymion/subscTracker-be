# 実装タスク: 支払履歴更新API (TDDスタイル)

- [x] 1. 支払履歴サービスのユニットテスト作成 (Red)
  - `tests/unit/test_payment_history_service.py` に `update_payment` メソッドのテストケースを追加する。
  - テストケース: 所有権チェック（他人のデータを更新しようとしてエラーになること）。
  - テストケース: 部分更新（金額のみ変更され、他の値が維持されること）。
  - テストケース: 為替レート再計算（日付/通貨変更時に `ExchangeRateService` が呼ばれ、`converted_amount` が更新されること）。
  - テストケース: サブスクリプション変更（`subscription_name` が更新されること）。
  - _Requirements: 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4_

- [x] 2. 支払履歴サービスの実装とリファクタリング (Green & Refactor)
  - `app/services/payment_history_service.py` に `update_payment` メソッドを実装してテストをパスさせる。
    - ユーザーIDによる所有権検証ロジックを実装する。
    - `subscription_id` 変更時の名前更新ロジックを実装する。
    - `currency` または `payment_date` 変更時の為替レート再計算ロジックを実装する。
    - バリデーション（負の値チェックなど）を実装する。
  - 実装完了後、コードの重複がないか、可読性が高いか（メソッドの抽出など）を確認し、必要に応じてリファクタリングを行う。
  - 再度テストを実行し、リファクタリングで機能が壊れていないことを確認する。
  - _Requirements: 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4_

- [x] 3. 支払履歴APIの結合テスト作成 (Red)
  - `tests/integration/test_payment_history_api.py` に `PATCH /payments/<id>` エンドポイントのテストを追加する。
  - テストケース: 正常系（200 OK、レスポンス内容の検証）。
  - テストケース: バリデーションエラー（不正な型、負の金額 -> 400 Bad Request）。
  - テストケース: 存在しないIDへのリクエスト（404 Not Found）。
  - テストケース: 認証エラー（401 Unauthorized）。
  - _Requirements: 1.1, 1.2, 1.3, 1.6_

- [x] 4. 支払履歴APIの実装とリファクタリング (Green & Refactor)
  - `app/api/v1/payment_history.py` に `PaymentUpdateRequestSchema` を定義し、`PATCH` ルートを実装してテストをパスさせる。
    - `app/api/v1/payment_history.py` に `PaymentUpdateRequestSchema` を定義する（Marshmallow、全フィールド任意）。
    - `PATCH /payments/<int:payment_id>` ルートを実装し、Serviceメソッドを呼び出す。
    - Service層の例外を適切なHTTPステータスコードにマッピングする。
    - 結合テストを実行し、全てパスすることを確認する。
  - エラーハンドリングやバリデーションロジックがクリーンか確認し、リファクタリングを行う。
  - コードフォーマットやLintチェック（ruff, black）を実行し、プロジェクトの規約に準拠させる。
  - 全テストを実行し、機能の回帰がないことを最終確認する。
  - _Requirements: 1.1, 1.2, 1.3, 1.6_
