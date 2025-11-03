# 実装計画: 支払履歴登録バッチ

- [ ] 1. データベースとリポジトリ層の準備 (TDD)
- [ ] 1.1 `Subscription`モデルの拡張とマイグレーション
  - `app/models/subscription.py`に`next_payment_date`フィールド（Date型、nullable）を追加します。
  - Alembicを使用して、データベーススキーマ変更のための新しいマイグレーションスクリプトを生成します。
  - 生成されたスクリプトを手動で確認し、`apply_migrations.sh`を実行してローカルDBに適用します。
  - _Requirements: 3.4_

- [ ] 1.2 `SubscriptionRepository`の拡張
  - `tests/unit/test_subscription_repository.py`に`find_due_subscriptions`メソッドのユニットテストを追加します。`next_payment_date`がNULLの場合と、過去の日付である場合の両方のシナリオをテストします。
  - `app/repositories/subscription_repository.py`に`find_due_subscriptions`メソッドを実装します。
  - `update_next_payment_date`メソッドのユニットテストを追加します。
  - `update_next_payment_date`メソッドを実装します。
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.4_

- [ ] 1.3 `PaymentHistoryRepository`の拡張
  - `tests/unit/test_payment_history_repository.py`に`bulk_save`メソッドのユニットテストを追加します。
  - `app/repositories/payment_history_repository.py`に`bulk_save`メソッドを実装します。
  - _Requirements: 3.1, 3.2_

- [ ] 2. ビジネスロジックの実装 (TDD)
- [ ] 2.1 日付計算ユーティリティの作成
  - `app/common/date_utils.py`のような新しいモジュールを作成します。
  - `payment_frequency`（`monthly`, `yearly`）と開始日に基づいて、次の支払日を計算する関数のユニットテストを作成します。月末やうるう年などのエッジケースを考慮します。
  - 上記関数を実装します。
  - _Requirements: 2.2, 3.2_

- [ ] 2.2 `PaymentRegistrationBatchService`の基本ロジック実装
  - `app/services/payment_registration_batch_service.py`を新規作成します。
  - `tests/unit/`に新しいテストファイルを作成し、`execute`メソッドのユニットテストを記述します。まずは単一の支払い履歴が生成されるシンプルなケースを対象とします。
  - `SubscriptionRepository`と`ExchangeRateService`をモック化し、サービスがリポジトリの各メソッドを正しく呼び出すことを検証します。
  - `execute`メソッドの基本ロジック（単一レコード生成）を実装します。
  - _Requirements: 3.1, 3.3, 3.5, 4.3, 4.4_

- [ ] 2.3 バックフィルロジックの実装
  - `PaymentRegistrationBatchService`のユニットテストを拡張し、サブスクリプションに履歴が全くない場合のバックフィルシナリオを追加します。
  - 複数の支払い履歴が生成され、`bulk_save`が正しい引数で呼び出されることを検証します。
  - `execute`メソッドにバックフィルロジックを実装します。
  - _Requirements: 3.2_

- [ ] 2.4 トランザクション管理の実装
  - `PaymentRegistrationBatchService`のユニットテストを拡張し、`update_next_payment_date`が失敗した場合に`bulk_save`がロールバックされることを検証するテストを追加します。
  - `execute`メソッドに、サブスクリプション単位の処理が単一トランザクション内で実行されるように実装します。
  - _Requirements: (データ整合性のための暗黙要件)_

- [ ] 3. バッチスクリプトの実装と統合
- [ ] 3.1 バッチスクリプトの作成
  - `scripts/register_payment_histories.py`を新規作成します。
  - Flaskアプリケーションコンテキストのセットアップ、ロギング設定、コマンドライン引数（`--subscription-ids`）の解析ロジックを実装します。
  - `PaymentRegistrationBatchService`を呼び出し、結果をログに出力する処理を実装します。
  - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.2_

- [ ] 3.2 統合テストの作成
  - `tests/integration/test_payment_registration_batch.py`を新規作成します。
  - テスト用のDBに複数のシナリオ（バックフィル対象、通常更新対象、対象外）のサブスクリプションを準備します。
  - スクリプトをサブプロセスとして実行し、DBの状態（`PaymentHistory`テーブルと`Subscription`テーブル）が期待通りに更新されていることをアサートします。
  - 引数なしのフル実行と、`--subscription-ids`を指定した部分実行の両方をテストします。
  - _Requirements: 全ての要件_
