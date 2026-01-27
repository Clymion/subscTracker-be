# Implementation Tasks

- [x] 1. 支払履歴削除サービスのTDD実装
  - [x] 1.1 Service削除機能のテスト作成 (Red)
    - `tests/unit/test_payment_history_service.py` に `delete_payment` メソッドのテストケースを追加する
    - 正常系：存在するIDで削除が成功すること（モックを使用）
    - 異常系：存在しないIDで `ResourceNotFoundError` が発生すること
    - 異常系：他人のIDで `ResourceNotFoundError` (セキュリティ要件) が発生すること
    - テストを実行し、失敗することを確認する
    - _Requirements: 1.1, 1.3, 1.4, 2.3_

  - [x] 1.2 Service削除機能の実装 (Green)
    - `PaymentHistoryService` に `delete_payment` メソッドを最小限の実装で追加する
    - IDによる取得、所有権チェック、リポジトリの削除呼び出しを実装する
    - テストを実行し、成功することを確認する
    - _Requirements: 1.1, 1.3, 1.4, 2.3_

  - [x] 1.3 Serviceログ出力の追加とリファクタリング (Refactor)
    - 処理開始、完了、エラー時のログ出力を追加する
    - コードの可読性と構造を見直す
    - テストが引き続き成功することを確認する
    - _Requirements: 3.1, 3.2, 3.3, 1.5_

- [x] 2. 支払履歴削除APIのTDD実装

  - [x] 2.1 API削除機能のテスト作成 (Red)

    - `tests/integration/test_payment_history_api.py` に `DELETE /payments/{id}` のテストケースを追加する

    - 正常系：削除成功時にステータス 204 が返ること

    - 異常系：存在しないIDで 404 が返ること

    - 異常系：他人のIDで 404 が返ること

    - 異常系：未認証で 401 が返ること

    - テストを実行し、失敗することを確認する（404 Not Found または 405 Method Not Allowed）

    - _Requirements: 1.2, 2.1, 2.2_



  - [x] 2.2 API削除機能の実装 (Green)

    - `PaymentHistoryAPI` に `DELETE /payments/{id}` エンドポイントを追加する

    - `jwt_required` で認証し、Serviceを呼び出す処理を実装する

    - 例外を適切なステータスコードにマッピングする

    - テストを実行し、成功することを確認する

    - _Requirements: 1.2, 2.1, 2.2_



  - [x] 2.3 APIのリファクタリング (Refactor)

    - エラーハンドリングやレスポンス処理を共通化・整理する

    - OpenAPI定義との整合性を最終確認する

    - 全テストを実行し、リグレッションがないことを確認する

    - _Requirements: 1.2, 2.1, 2.2_
