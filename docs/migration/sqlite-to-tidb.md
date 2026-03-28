# SQLiteからTiDBへの移行ガイド

## 概要

本ドキュメントは、サブスクリプション管理バックエンドAPIのデータベースをSQLiteからTiDBへ移行するための手順書である。

## 前提条件

- DockerおよびDocker Composeがインストールされていること
- Python 3.13以上がインストールされていること
- Poetryがインストールされていること

## 移行手順

### Phase 1: 環境設定

#### 1.1 環境変数の設定

`.env`ファイルに以下の環境変数を設定する：

```env
# TiDB接続設定
DB_DRIVER=mysql
DB_HOST=localhost
DB_PORT=4000
DB_USER=root
DB_PASSWORD=
DB_NAME=subsc_tracker

# JWT設定（必須）
JWT_SECRET_KEY=your-secret-key-at-least-16-characters
```

#### 1.2 Docker環境の起動

```bash
# TiDBコンテナを起動
docker-compose up -d tidb

# TiDBのヘルスチェックを確認
docker-compose logs tidb
```

### Phase 2: データベースマイグレーション

#### 2.1 マイグレーションの実行

```bash
# マイグレーションを実行
./scripts/apply_migrations.sh
```

#### 2.2 マイグレーションの確認

```bash
# マイグレーション履歴を確認
poetry run alembic history

# 現在のバージョンを確認
poetry run alembic current
```

### Phase 3: データ移行

#### 3.1 移行スクリプトの実行

```bash
# SQLiteからTiDBへのデータ移行
poetry run python scripts/migrate_data.py \
    --source instance/app.db \
    --dest "mysql+pymysql://root@localhost:4000/subsc_tracker"
```

#### 3.2 データ整合性の確認

移行スクリプトは自動的にデータ整合性を検証する。エラーが発生した場合はログを確認すること。

### Phase 4: アプリケーションの起動

#### 4.1 開発環境での起動

```bash
# Docker Composeで全サービスを起動
docker-compose up --build
```

#### 4.2 ヘルスチェック

```bash
# APIヘルスチェック
curl http://localhost:5000/api/v1/health

# 期待されるレスポンス
# {"status": "healthy", "checks": {"database": "healthy"}}
```

## 設定詳細

### 接続プール設定

TiDB接続時の接続プール設定：

| 設定項目 | 値 | 説明 |
|----------|-----|------|
| `pool_size` | 5 | 接続プールサイズ |
| `pool_recycle` | 3600 | 接続の再利用時間（秒） |
| `pool_pre_ping` | True | 接続健全性チェック |

### SQLite互換性

- SQLite接続時は`PRAGMA foreign_keys=ON`が自動的に実行される
- TiDB接続時はこのPRAGMAはスキップされる

## トラブルシューティング

### 接続エラー

```
Error: Can't connect to MySQL server on 'localhost:4000'
```

**対処法:**
1. TiDBコンテナが起動していることを確認
2. ヘルスチェックが成功していることを確認
3. ファイアウォール設定を確認

### マイグレーションエラー

```
Error: Table 'xxx' already exists
```

**対処法:**
1. データベースをクリーンアップ
2. マイグレーションを再実行

### データ移行エラー

```
Error: Foreign key violation
```

**対処法:**
1. 移行順序を確認（users → exchange_rates → subscriptions → labels → subscription_labels → payment_histories）
2. チェックポイントから再開

## ロールバック手順

TiDBからSQLiteに戻す場合：

1. 環境変数をSQLiteに変更
   ```env
   DB_DRIVER=sqlite
   DB_NAME=instance/app.db
   ```

2. アプリケーションを再起動

## 参照

- [TiDB Documentation](https://docs.pingcap.com/tidb/stable)
- [SQLAlchemy MySQL Dialect](https://docs.sqlalchemy.org/en/20/dialects/mysql.html)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

## 要件カバレッジ

| 要件 | ステータス | テスト |
|------|------------|--------|
| 1.1 MySQL互換接続URL生成 | ✅ | `test_appconfig_provides_pool_settings_for_mysql` |
| 1.2 SQLite接続URL生成 | ✅ | `test_appconfig_skips_pool_settings_for_sqlite` |
| 1.3 mysql+pymysqlドライバー | ✅ | `test_config_database_url_mysql` |
| 1.4 環境変数読み込み | ✅ | `test_config_database_url_sqlite` |
| 1.5 必須情報検証 | ✅ | `test_config_validate_mysql_dependencies` |
| 2.1 SQLite PRAGMA条件分岐 | ✅ | `test_pragma_executes_for_sqlite_connection` |
| 2.2 ドライバー別設定適用 | ✅ | `test_pragma_skipped_for_non_sqlite_connection` |
| 2.3 ドライバー判定 | ✅ | `test_set_sqlite_pragma_function_handles_sqlite` |
| 3.1 TiDB互換データ型 | ✅ | `test_integer_type_maps_to_int` |
| 3.2 複合主キー | ✅ | `test_exchange_rate_has_composite_primary_key` |
| 3.3 外部キー制約 | ✅ | `test_subscription_has_cascade_delete_to_user` |
| 3.4 インデックス定義 | ✅ | `test_subscription_has_composite_indexes` |
| 4.1 Alembic環境変数 | ✅ | `test_migrations_env_reads_database_url_from_environment` |
| 4.2 TiDB互換DDL | ✅ | `test_sqlalchemy_uses_mysql_dialect_for_tidb` |
| 5.1 テスト用DB設定 | ✅ | `TestConfig` tests |
| 5.2 統合テスト用DB | ✅ | `test_tidb_connection` |
| 6.1 Docker TiDB起動 | ✅ | `test_tidb_service_exists` |
| 6.2 ヘルスチェック | ✅ | `test_tidb_has_healthcheck` |
| 6.3 API起動時DB接続 | ✅ | `test_backend_api_depends_on_tidb` |
| 7.1 接続プールサイズ | ✅ | `test_appconfig_provides_pool_settings_for_mysql` |
| 7.2 アイドル接続管理 | ✅ | `test_pool_recycle_configuration` |
| 7.3 再接続試行 | ✅ | `test_pre_ping_handles_stale_connections_gracefully` |
| 7.4 pool_pre_ping | ✅ | `test_pool_pre_ping_enabled` |
| 8.1 データ転送 | ✅ | `test_migrate_users_table` |
| 8.2 データ整合性検証 | ✅ | `test_validate_row_counts_match` |
| 8.3 エラー時ロールバック | ✅ | `test_rollback_on_foreign_key_violation` |
| 8.4 進捗ログ | ✅ | `test_progress_tracker_updates` |
