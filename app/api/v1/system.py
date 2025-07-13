"""
システム監視用のAPIエンドポイントを定義するモジュール
"""

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Literal

import psutil
from flask import Blueprint, jsonify
from flask.wrappers import Response
from sqlalchemy import text

from app.models import db

# プロセス起動時刻を記録
PROCESS_START_TIME = time.time()
PROCESS = psutil.Process(os.getpid())

VERSION = "0.2.0"
JST = timezone(timedelta(hours=9))

# システム監視用のBlueprintを作成
system_bp = Blueprint("system", __name__)


@system_bp.route("/health", methods=["GET"])
def health_check() -> tuple[Response, Literal[200, 503]]:
    """
    ヘルスチェックエンドポイント

    サービスの基本的な稼働状況と依存関係（DB）の状態を返す
    """
    db_status = "healthy"
    try:
        # DB接続を試みて、簡単なクエリを実行する
        db.session.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    # 全てのチェックがhealthyなら全体のステータスもhealthy
    is_healthy = db_status == "healthy"
    overall_status = "healthy" if is_healthy else "unhealthy"

    response_data = {
        "status": overall_status,
        "timestamp": datetime.now(JST).isoformat(),
        "checks": {
            "database": db_status,
            # 他の依存関係もここに追加
        },
    }

    status_code = 200 if is_healthy else 503
    return jsonify(response_data), status_code


@system_bp.route("/version", methods=["GET"])
def get_version() -> tuple[Response, Literal[200]]:
    """
    アプリケーションのバージョン情報を返すエンドポイント

    実際にはビルド時にこれらの情報をファイルや環境変数から読み込むのが一般的
    """
    version_info = {
        "version": VERSION,
        "build": "20250713-local",  # ビルドID
        "commit": "localdev",  # Gitのコミットハッシュ
        "build_date": datetime.now(JST).isoformat(),
    }
    return jsonify(version_info), 200


@system_bp.route("/metrics", methods=["GET"])
def get_metrics() -> tuple[Response, Literal[200]]:
    """
    アプリケーションのパフォーマンス指標（メトリクス）を返すエンドポイント。
    """
    uptime_seconds = time.time() - PROCESS_START_TIME
    memory_info = PROCESS.memory_info()
    cpu_times = PROCESS.cpu_times()

    metrics_data = {
        "uptime_seconds": round(uptime_seconds),
        # 'requests_total' は別途リクエストカウンターを実装する必要がある
        # "requests_total": get_request_count(),
        # 'avg_response_time_ms' も計測が必要
        # "avg_response_time_ms": get_avg_response_time(),
        "memory_usage_mb": round(memory_info.rss / (1024 * 1024), 2),
        "cpu_usage_percent": PROCESS.cpu_percent(interval=0.1),
        "cpu_times": {
            "user": round(cpu_times.user, 2),
            "system": round(cpu_times.system, 2),
        },
        "active_threads": PROCESS.num_threads(),
    }
    return jsonify(metrics_data), 200


@system_bp.route("/status", methods=["GET"])
def get_status() -> tuple[Response, Literal[200]]:
    """
    サービス全体の統合的なステータスを提供するエンドポイント

    healthとversionの情報を組み合わせている
    """
    db_status = "connected"
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    status_data = {
        "service": "substracker-api",
        "status": "operational" if db_status == "connected" else "degraded",
        "version": VERSION,
        "uptime_seconds": round(time.time() - PROCESS_START_TIME),
        "timestamp": datetime.now(JST).isoformat(),
        "dependencies": {
            "database": db_status,
            # 他の依存関係もここに追加
        },
    }
    return jsonify(status_data), 200
