#!/bin/bash
# 本番環境の SQLite データベースを開発環境にコピーするスクリプト
# 実行例: ./scripts/dev/pull_prd_sqlite.sh [TARGET_PATH]

set -e

# デフォルトの復元先を prd_repro.db に変更
TARGET_PATH="${1:-instance/prd_repro.db}"
DB_BACKUP_DIR="instance/dev-backup"
# litestream.yml で定義されている「本物のパス」
# ※ litestream.yml の dbs.path と一致させる必要があります
CONFIG_DB_PATH="/workspace/instance/app.db"
CONFIG_FILE="/etc/litestream.yml"

# ディレクトリの準備
mkdir -p "$(dirname "$TARGET_PATH")"
mkdir -p "$DB_BACKUP_DIR"

# 既存のターゲットファイルがある場合はバックアップ
if [ -f "${TARGET_PATH}" ]; then
    BACKUP_FILE="${DB_BACKUP_DIR}/$(basename "$TARGET_PATH").$(date +%Y%m%d_%H%M%S)"
    cp "${TARGET_PATH}" "${BACKUP_FILE}"
    echo "✅ Backed up existing file to ${BACKUP_FILE}"
fi

# 本番環境の SQLite データベースを復元
echo "🚀 Restoring production database from GCS to ${TARGET_PATH}..."

# Litestream restore を実行
# 設定ファイルにある元のパス (CONFIG_DB_PATH) を指定し、
# 出力先 (-o) だけを TARGET_PATH に変えるのが最も安全な方法です。
if litestream restore -config "${CONFIG_FILE}" -o "${TARGET_PATH}" "${CONFIG_DB_PATH}"; then
    # SQLiteの不整合を防ぐために .recover を試行
    if command -v sqlite3 >/dev/null 2>&1; then
        echo "修正中: SQLite .recover を実行しています..."
        mv "${TARGET_PATH}" "${TARGET_PATH}.tmp"
        sqlite3 "${TARGET_PATH}.tmp" ".recover" | sqlite3 "${TARGET_PATH}"
        rm "${TARGET_PATH}.tmp"
    fi
    echo "✅ Production database restored to ${TARGET_PATH}."
else
    echo "⚠️  Failed to restore database. Please check your GCS credentials and litestream.yml."
    exit 1
fi
