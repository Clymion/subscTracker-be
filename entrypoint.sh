#!/bin/sh

# スクリプトのいずれかのコマンドが失敗した場合、直ちにスクリプトを終了する
set -e

# --- Litestream設定 ---
# 環境変数から受け取るのが理想ですが、まずは直接記述
GCS_BUCKET="subsc-tracker-sqlite-backup"
DB_PATH="/workspace/instance/app.db"
GCS_REPLICA_URL="gcs://${GCS_BUCKET}/db"

# ディレクトリの存在を確認・作成
mkdir -p /workspace/instance

echo "🚀 Restoring database from GCS if it does not exist..."
# -if-replica-exists オプションで、バックアップが存在しない場合は何もしない
if ! litestream restore -if-replica-exists "${DB_PATH}"; then
    echo "⚠️ No existing database found in backup. Creating a new one."
    # データベースファイルが存在しない場合のみ新規作成
    if [ ! -f "${DB_PATH}" ]; then
        touch "${DB_PATH}"
        echo "✅ New database file created at ${DB_PATH}."
    fi
fi

# ステップ2: データベースマイグレーションの実行
echo "🚀 Running database migrations..."
python -m alembic upgrade head
echo "✅ Database migrations completed."

# ステップ3: LitestreamによるレプリケーションとGunicornサーバーの起動
# LitestreamがGunicornをサブプロセスとして監視し、変更をGCSにリアルタイムでバックアップ
# Gunicornが終了すると、Litestreamも安全に終了
echo "🚀 Starting Gunicorn server with Litestream replication..."
exec litestream replicate -exec "python -m gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 'app:create_app()'"
