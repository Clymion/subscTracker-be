#!/bin/sh

# スクリプトのいずれかのコマンドが失敗した場合、直ちにスクリプトを終了する
set -e

# --- Litestream設定 ---
# 環境変数から受け取るのが理想ですが、まずは直接記述します。
GCS_BUCKET="subsc-tracker-sqlite-backup"
DB_PATH="/workspace/instance/app.db"
GCS_REPLICA_URL="gcs://${GCS_BUCKET}/db"

# ステップ1: GCSからデータベースをリストア
# ローカルにデータベースファイルが存在しない場合のみ、GCSから復元します。
echo "🚀 Restoring database from GCS if it does not exist..."
litestream restore -if-replica-exists "${DB_PATH}"

# リストアが失敗した場合、またはデータベースが存在しない場合は新規作成します。
if [ $? -ne 0 ]; then
    sqlite3 "${DB_PATH}" "PRAGMA user_version = 0;" || true
    echo "⚠️ Database restore failed or no existing database found. A new database will be created."
fi
echo "✅ Database restored or created successfully at ${DB_PATH}."

# ステップ2: データベースマイグレーションの実行
# リストアされた、あるいは新規作成されたデータベースに対してマイグレーションを適用します。
echo "🚀 Running database migrations..."
# alembicコマンドでデータベースを最新の状態にする
python -m alembic upgrade head
echo "✅ Database migrations completed."

# ステップ3: LitestreamによるレプリケーションとGunicornサーバーの起動
# LitestreamがGunicornをサブプロセスとして監視し、変更をGCSにリアルタイムでバックアップします。
# Gunicornが終了すると、Litestreamも安全に終了します。
echo "🚀 Starting Gunicorn server with Litestream replication..."
exec litestream replicate -exec "python -m gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 'app:create_app()'"
