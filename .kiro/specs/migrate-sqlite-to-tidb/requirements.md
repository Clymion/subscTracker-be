# Requirements Document

## Introduction

本ドキュメントは、サブスクリプション管理バックエンドAPIにおけるデータベース移行（SQLiteからTiDB）の要件を定義する。現在、本番・開発環境ともにSQLiteを使用しているが、スケーラビリティと可用性の向上を目的としてTiDBへの移行を行う。

## Requirements

### Requirement 1: データベース接続設定

**Objective:** 開発者として、TiDBへの接続設定を柔軟に変更できるようにしたい、環境ごとに適切なデータベースに接続できるようにするため。

#### Acceptance Criteria

1. When `DB_DRIVER`環境変数が`mysql`に設定される場合、the Application shall MySQL互換（TiDB含む）の接続URLを生成する。
2. When `DB_DRIVER`環境変数が`sqlite`に設定される場合、the Application shall SQLiteへの接続URLを生成する。
3. When TiDB接続が設定される場合、the Application shall `mysql+pymysql`ドライバーを使用する（TiDBはMySQL 8.0プロトコル互換）。
4. The Application shall 環境変数からTiDB接続情報（ホスト、ポート、ユーザー、パスワード、データベース名）を読み込む。
5. If 必須のTiDB接続情報が欠落している場合、the Application shall 起動時に明確なエラーメッセージを表示する。

### Requirement 2: SQLite固有コードの互換性

**Objective:** 開発者として、データベース固有のコードを適切に分離・条件分岐したい、複数のデータベースエンジンに対応できるコードベースを維持するため。

#### Acceptance Criteria

1. When SQLite以外のデータベースドライバーが使用される場合、the Application shall SQLite PRAGMA設定を実行しない（既存の`isinstance`チェックで対応済み）。
2. When データベース接続が確立される場合、the Application shall ドライバーの種類に応じて適切な設定を適用する。
3. The Application shall 接続オブジェクトの型判定によりSQLite接続を識別する（既存実装を維持）。

### Requirement 3: データ型とスキーマ互換性

**Objective:** 開発者として、TiDBで動作するデータベーススキーマを維持したい、データ整合性とパフォーマンスを保証するため。

#### Acceptance Criteria

1. When モデルが定義される場合、the Application shall SQLAlchemyを通じてTiDB互換のデータ型を使用する。
2. When 複合主キーが定義される場合（ExchangeRate等）、the Application shall TiDBで正常に動作する主キー制約を使用する。
3. When 外部キー制約が定義される場合、the Application shall `ON DELETE CASCADE`および`ON DELETE SET NULL`を適切にサポートする。
4. When インデックスが定義される場合、the Application shall TiDBで正常に作成されるインデックス定義を使用する。
5. If データ型に互換性の問題がある場合、the Application shall 適切な代替型にマッピングする。

### Requirement 4: マイグレーション管理

**Objective:** 開発者として、TiDB環境でデータベースマイグレーションを実行したい、スキーマ変更を安全に適用するため。

#### Acceptance Criteria

1. When Alembicマイグレーションが実行される場合、the Application shall 環境変数からTiDB接続URLを読み込む。
2. When 新規マイグレーションが作成される場合、the Application shall TiDB互換のDDLステートメントを生成する。
3. When マイグレーションが適用される場合、the Application shall 既存データを保持したままスキーマを更新する。
4. If マイグレーションが失敗する場合、the Application shall ロールバック機能を提供する。

### Requirement 5: テスト環境対応

**Objective:** 開発者として、TiDB環境でもテストを実行したい、本番環境と同等の動作を検証するため。

#### Acceptance Criteria

1. When テスト設定が初期化される場合、the Application shall テスト用のデータベース設定を使用する。
2. When 統合テストが実行される場合、the Application shall テスト用TiDBまたはインメモリデータベースを使用できる。
3. The Application shall テスト実行後にデータベースのクリーンアップを行う。
4. When テストが実行される場合、the Application shall テスト間でデータベース状態を分離する。

### Requirement 6: Docker環境設定

**Objective:** 開発者として、Docker ComposeでTiDB環境を起動したい、開発環境の一貫性を保証するため。

#### Acceptance Criteria

1. When `docker-compose up`が実行される場合、the Application shall TiDBコンテナを正常に起動する。
2. When TiDBコンテナが起動する場合、the Application shall ヘルスチェックが完了するまで待機する。
3. When バックエンドAPIが起動する場合、the Application shall TiDBへの接続が確立していることを確認する。
4. The Application shall TiDBデータ用の永続ボリュームを提供する。

### Requirement 7: 接続プール設定

**Objective:** 運用者として、TiDBへの接続を効率的に管理したい、リソース使用量とパフォーマンスを最適化するため。

#### Acceptance Criteria

1. When TiDB接続が確立される場合、the Application shall 適切な接続プールサイズを設定する。
2. When 接続がアイドル状態になる場合、the Application shall 接続を再利用または解放する。
3. If 接続が失敗する場合、the Application shall 再接続を試行する。
4. When 接続プールが設定される場合、the Application shall `pool_pre_ping`を有効にして接続の健全性を確認する。

### Requirement 8: 既存データ移行

**Objective:** 運用者として、既存のSQLiteデータをTiDBに移行したい、データ損失を防ぎサービス継続性を確保するため。

#### Acceptance Criteria

1. When データ移行が実行される場合、the Application shall 全てのテーブルデータをTiDBに転送する。
2. When 移行が完了する場合、the Application shall データ整合性を検証する。
3. If 移行中にエラーが発生する場合、the Application shall 移行をロールバックする。
4. The Application shall 移行の進捗をログに記録する。

