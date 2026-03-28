#!/bin/bash

# スクリプトのいずれかのコマンドが失敗した場合、直ちにスクリプトを終了する
set -e

# データベースマイグレーションの実行
echo "🚀 Running database migrations..."
python -m alembic upgrade head
echo "✅ Database migrations completed."

# Gunicornサーバーの起動
echo "🚀 Starting Gunicorn server..."
python -m gunicorn --bind :$PORT --workers 1 --threads 8 'app:create_app()'
