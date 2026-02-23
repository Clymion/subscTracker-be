# セットアップと実行 (DevContainer 環境)

## 📋 前提条件
- VSCode + Dev Containers 拡張機能
- Docker Desktop (ホスト側)
- Google Cloud 認証 (GCSへのアクセス用)

## 🚀 アプリケーションの起動

DevContainer を開いた後、以下の `make` コマンドで起動できます。

1. **通常起動** (instance/app.db を使用)
   ```bash
   make run
   ```

2. **API動作確認** (別のターミナルで実行)
   ```bash
   curl http://localhost:5000/api/v1/health
   ```

## 🔄 本番データの再現 (Production Replication)
本番環境（Cloud Run + Litestream）のSQLiteデータを安全に再現できます。

1. **データの取得**: 最新のバックアップを `instance/prd_repro.db` として保存。
   ```bash
   make db-pull-prd
   ```
2. **再現モードで起動**: `instance/prd_repro.db` を参照してアプリを起動。
   ```bash
   make run-repro
   ```
   *注意: 本番データの書き換えは避け、調査・再現のみに使用することを推奨します。*

## 🛠 その他の開発操作

### 依存関係の管理 (Poetry)
```bash
poetry install
```

### マイグレーションの実行
```bash
./scripts/apply_migrations.sh
```
*Note: CI/CDなどでマイグレーションのみを実行したい場合は `--no-replicate` フラグを使用してください。*

### テストの実行
```bash
# 全テスト実行
make test  # (もしMakefileに定義する場合、または poetry run pytest)
```
