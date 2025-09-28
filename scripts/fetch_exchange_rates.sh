#!/bin/bash

DB_PATH="instance/app.db"

echo "🚀 Restoring database from GCS if it does not exist..."
# -if-replica-exists オプションで、バックアップが存在しない場合は何もしない
if ! litestream restore -if-replica-exists "${DB_PATH}"; then
    echo "⚠️ No existing database found in backup. Creating a new one."
    # データベースファイルが存在しない場合のみ新規作成
    if [ ! -f "${DB_PATH}" ]; then
        touch "${DB_PATH}"
        echo "✅ New database file created at ${DB_PATH}."
    fi
else
    echo "Database restore from GCS."
    rm -f "${DB_PATH}"
    litestream restore "${DB_PATH}" >&2
fi

# マイグレーションバージョンの確認
python -m alembic current
python -m alembic upgrade head

DATE_ARG=""
if [ -n "$1" ]; then
  DATE_ARG="--date $1"
fi

# 目的のpythonスクリプトを実行
litestream replicate -exec "python scripts/fetch_exchange_rates.py ${DATE_ARG}"
