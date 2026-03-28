# Implementation Plan

## Overview

本ドキュメントは、SQLiteからTiDBへの移行機能を実装するためのタスク一覧である。設計書に基づき、設定層、インフラ層、テスト層、スクリプト層の順で実装を進める。

---

## Tasks

### Phase 1: Configuration Layer

- [ ] 1. TiDB接続設定の実装 (P)
- [x] 1.1 (P) AppConfigにTiDB接続URL生成機能を追加
  - `DB_DRIVER`環境変数に基づいて接続URLを生成するプロパティを実装
  - `sqlite`の場合は既存のSQLite接続URLを生成
  - `mysql`の場合は`mysql+pymysql`ドライバーを使用してTiDB接続URLを生成
  - 環境変数から`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`を読み込み
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 1.2 (P) TiDB必須設定のバリデーション実装
  - `DB_DRIVER=mysql`の場合に必須フィールドが設定されているか検証
  - 欠落しているフィールドがある場合、起動時に明確なエラーメッセージを表示
  - SQLiteの場合はバリデーションをスキップ
  - _Requirements: 1.5_

- [x] 1.3 (P) 接続プール設定の実装
  - `to_flask_config`メソッドでTiDB接続用のプール設定を提供
  - `pool_size`, `pool_recycle`, `pool_pre_ping`を適切に設定
  - SQLite接続時はプール設定をスキップ
  - _Requirements: 7.1, 7.2, 7.4_

- [x] 1.4 (P) 再接続試行機能の確認
  - SQLAlchemyの`pool_pre_ping`による接続健全性確認が動作することを確認
  - 接続失敗時のエラーハンドリングを確認
  - _Requirements: 7.3_

### Phase 2: Docker Environment

- [x] 2. Docker環境でのTiDB設定 (P)
- [x] 2.1 (P) compose.ymlのTiDBサービス構成確認
  - TiDBコンテナが正常に起動することを確認
  - ヘルスチェックが正しく設定されていることを確認
  - データ永続ボリュームが適切に設定されていることを確認
  - _Requirements: 6.1, 6.2, 6.4_

- [x] 2.2 (P) backend-apiサービスの依存関係設定
  - backend-apiがTiDBのヘルスチェック完了後に起動することを確認
  - `depends_on`の`condition: service_healthy`が正しく動作することを確認
  - _Requirements: 6.3_

### Phase 3: Migration & Compatibility

- [x] 3. SQLite互換性とマイグレーション設定
- [x] 3.1 SQLite PRAGMA条件分岐の動作確認
  - 既存の`set_sqlite_pragma`イベントリスナーが正しく動作することを確認
  - SQLite接続時のみPRAGMAが実行されることを確認
  - TiDB/MySQL接続時はPRAGMAがスキップされることを確認
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 3.2 Alembic環境設定のTiDB対応
  - `migrations/env.py`が環境変数からTiDB接続URLを読み込むことを確認
  - SQLAlchemyがTiDB互換のDDLを生成することを確認
  - `DATABASE_URL`環境変数の処理を確認
  - _Requirements: 4.1, 4.2_

- [x] 3.3 マイグレーション実行とロールバック検証
  - TiDB環境でAlembicマイグレーションが正常に実行されることを確認
  - マイグレーションのロールバックが正常に動作することを確認
  - 既存データを保持したままスキーマ更新ができることを確認
  - _Requirements: 4.3, 4.4_

- [x] 3.4 データ型とスキーマ互換性の確認
  - SQLAlchemyモデルがTiDB互換のデータ型を使用していることを確認
  - 複合主キー（ExchangeRate等）が正常に動作することを確認
  - 外部キー制約（`ON DELETE CASCADE`, `ON DELETE SET NULL`）が動作することを確認
  - インデックス定義がTiDBで正常に作成されることを確認
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

### Phase 4: Test Environment

- [ ] 4. テスト環境設定
- [ ] 4.1 TestConfigのTiDB対応
  - テスト用データベース設定が適切に機能することを確認
  - デフォルトでSQLiteインメモリDBを使用することを確認
  - 環境変数によるTiDBテスト設定が可能であることを確認
  - _Requirements: 5.1, 5.2_

- [ ] 4.2 テストフィクスチャの確認
  - テスト実行後にデータベースのクリーンアップが行われることを確認
  - テスト間でデータベース状態が分離されていることを確認
  - `conftest.py`のフィクスチャがTiDB環境でも動作することを確認
  - _Requirements: 5.3, 5.4_

- [ ] 4.3 統合テストの実行
  - TiDB環境で既存の統合テストが正常に実行されることを確認
  - CRUD操作がTiDBで正しく動作することを確認
  - 外部キー制約の動作確認テストを実行
  - _Requirements: 5.2, 3.3_

### Phase 5: Data Migration Script

- [ ] 5. データ移行スクリプトの実装
- [ ] 5.1 SQLiteからTiDBへのデータ転送機能
  - 全テーブルデータをSQLiteからTiDBへ転送するスクリプトを実装
  - SQLAlchemyモデルを使用してデータを読み書き
  - バッチ処理による大量データ対応
  - _Requirements: 8.1_

- [ ] 5.2 データ整合性検証機能
  - 移行完了後のデータ整合性を検証する機能を実装
  - 行数比較、外部キー整合性チェックを実装
  - 検証結果をログに出力
  - _Requirements: 8.2_

- [ ] 5.3 エラーハンドリングとロールバック
  - 移行中のエラーを検知しロールバックする機能を実装
  - チェックポイント機能による再開対応
  - エラー詳細をログに記録
  - _Requirements: 8.3_

- [ ] 5.4 進捗ログ機能
  - 移行の進捗をログに記録する機能を実装
  - 処理済み行数、残り行数、推定完了時間を表示
  - _Requirements: 8.4_

### Phase 6: Integration & Validation

- [ ] 6. 統合検証
- [ ] 6.1 Docker環境でのエンドツーエンドテスト
  - `docker-compose up`でTiDB + backend-apiが正常起動することを確認
  - APIエンドポイントが正常に動作することを確認
  - データベース接続が確立していることを確認
  - _Requirements: 6.1, 6.2, 6.3_

- [ ] 6.2 接続プールの負荷テスト
  - 接続プールが適切に動作することを確認
  - 並行クエリに対するパフォーマンスを確認
  - _Requirements: 7.1, 7.2, 7.4_

- [ ] 6.3 最終検証とドキュメント更新
  - 全要件が満たされていることを確認
  - 移行手順のドキュメントを作成
  - _Requirements: 1.1-8.4_

---

## Coverage Matrix

| Requirement | Tasks |
|-------------|-------|
| 1.1 | 1.1 |
| 1.2 | 1.1 |
| 1.3 | 1.1 |
| 1.4 | 1.1 |
| 1.5 | 1.2 |
| 2.1 | 3.1 |
| 2.2 | 3.1 |
| 2.3 | 3.1 |
| 3.1 | 3.4 |
| 3.2 | 3.4 |
| 3.3 | 3.4, 4.3 |
| 3.4 | 3.4 |
| 3.5 | 3.4 |
| 4.1 | 3.2 |
| 4.2 | 3.2 |
| 4.3 | 3.3 |
| 4.4 | 3.3 |
| 5.1 | 4.1 |
| 5.2 | 4.1, 4.3 |
| 5.3 | 4.2 |
| 5.4 | 4.2 |
| 6.1 | 2.1, 6.1 |
| 6.2 | 2.1, 6.1 |
| 6.3 | 2.2, 6.1 |
| 6.4 | 2.1 |
| 7.1 | 1.3, 6.2 |
| 7.2 | 1.3, 6.2 |
| 7.3 | 1.4 |
| 7.4 | 1.3, 6.2 |
| 8.1 | 5.1 |
| 8.2 | 5.2 |
| 8.3 | 5.3 |
| 8.4 | 5.4 |
