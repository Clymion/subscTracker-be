# Implementation Plan: history-payment-api (TDD)

- [x] 1. データベースのセットアップ
- [x] 1.1 `PaymentHistory`モデルの作成
  - `app/models/payment_history.py` を新規作成します。
  - 設計書に従い、`payment_histories`テーブルに対応するSQLAlchemyモデルを定義します。
  - _Requirements: 1.3, 1.4_

- [x] 1.2 データベースマイグレーションの実行
  - Alembicを使用して、`payment_histories`テーブルを作成するための新しいマイグレーションスクリプトを生成・実行します。
  - _Requirements: 全ての要件の基礎_

- [ ] 2. Repository層の実装 (TDD)
- [ ] 2.1 `PaymentHistoryRepository`のユニットテストを作成 (Red)
  - `tests/unit/test_payment_history_repository.py` を新規作成します。
  - フィルタ、ソート、ページネーションが正しく機能することを検証するための、失敗するテストケースを記述します。
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4_

- [ ] 2.2 `PaymentHistoryRepository`の実装 (Green)
  - `app/repositories/payment_history_repository.py` を新規作成します。
  - タスク2.1で作成したユニットテストをパスさせるために、`find_all_by_user_id`および`count_all_by_user_id`メソッドを実装します。
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4_

- [ ] 3. Service層の実装 (TDD)
- [ ] 3.1 `PaymentHistoryService`のユニットテストを作成 (Red)
  - `tests/unit/test_payment_history_service.py` を新規作成します。
  - `PaymentHistoryRepository`をモック化し、`get_payment_history`サービスがリポジトリを正しく呼び出すことを検証する、失敗するテストケースを記述します。
  - _Requirements: 1.1, 1.2_

- [ ] 3.2 `PaymentHistoryService`の実装 (Green)
  - `app/services/payment_history_service.py` を新規作成します。
  - タスク3.1で作成したユニットテストをパスさせるために、`get_payment_history`メソッドを実装します。
  - _Requirements: 1.1, 1.2_

- [ ] 4. API層の実装 (TDD/BDD)
- [ ] 4.1 `GET /api/v1/payments`エンドポイントの統合テストを作成 (Red)
  - `tests/integration/test_payment_history_api.py` を新規作成します。
  - APIにリクエストを送信し、期待されるJSONレスポンスが返却されることを検証する、失敗するテストケース（最初は404 Not Foundで失敗させる）を記述します。
  - 認証、フィルタ、ページネーション、ソートの各パターンをテストケースに含めます。
  - _Requirements: 全ての要件_

- [ ] 4.2 APIエンドポイントの実装 (Green)
  - `app/api/v1/payment_history.py` を新規作成し、Flask Blueprintと`GET /api/v1/payments`のエンドポイントを定義します。
  - クエリパラメータを解釈し、`PaymentHistoryService`を呼び出し、結果をJSONレスポンスとして返却するロジックを実装し、タスク4.1の統合テストをパスさせます。
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4_