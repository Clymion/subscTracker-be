#!/bin/bash
# 本番環境の SQLite データベースを開発環境にコピーするスクリプト
# 実行例: ./scripts/dev/pull_prd_sqlite.sh

set -e

DB_PATH="instance/app.db"
DB_BACKUP_DIR="instance/dev-backup"
DB_BACKUP_PATH="${DB_BACKUP_DIR}/app.db.$(date +%Y%m%d_%H%M%S)"

# 現在の開発用の SQLite データベースをバックアップ
if [ -f "${DB_PATH}" ]; then
    if [ ! -d "${DB_BACKUP_DIR}" ]; then
        mkdir -p "${DB_BACKUP_DIR}"
    fi
    mv "${DB_PATH}" "${DB_BACKUP_PATH}"
    rm -f "${DB_PATH}"*
    echo "✅ Backed up current development database to ${DB_BACKUP_PATH}."
fi

# 本番環境の SQLite データベースを復元
echo "🚀 Restoring production database from GCS..."
if litestream restore -if-replica-exists "${DB_PATH}"; then
    mv "${DB_PATH}" "${DB_PATH}".tmp
    sqlite3 "${DB_PATH}".tmp ".recover" | sqlite3 ${DB_PATH}
    echo "✅ Production database restored to ${DB_PATH}."
else
    echo "⚠️  No existing production database found in backup.
        Please ensure that the production database has been backed up to GCS."
    exit 1
fi
