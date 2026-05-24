"""
scripts/db.py — バッチスクリプト共通のデータベース接続ヘルパー。

使い方:
    from db import get_db_connection

    conn, driver = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(...)
        conn.commit()
    finally:
        conn.close()

接続先の決定ロジック:
    1. AppConfig が読み込め、DB_DRIVER == "mysql" → TiDB/MySQL (pymysql)
    2. それ以外 → SQLite (db_path 引数 or デフォルトの instance/app.db)

SQL プレースホルダ:
    driver == "sqlite" → ?
    driver == "mysql"  → %s

    スクリプト側では upsert_sql(driver) などを使って SQL を切り替えること。
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import sqlite3 as _sqlite3

    import pymysql as _pymysql

    Connection = _sqlite3.Connection | _pymysql.connections.Connection

logger = logging.getLogger(__name__)

# scripts/ の親 = プロジェクトルート
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB_PATH = _PROJECT_ROOT / "instance" / "app.db"

# AppConfig をオプショナルにインポート。
# scripts/ ディレクトリ直下から実行されても動作するよう try/except でガードする。
_app_config: Any = None


def _load_app_config() -> Any:
    """AppConfig インスタンスを返す。読み込めない場合は None。"""
    global _app_config  # noqa: PLW0603
    if _app_config is not None:
        return _app_config

    root = str(_PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)

    try:
        from app.config import AppConfig  # type: ignore[import]

        _app_config = AppConfig()
        logger.debug("AppConfig を読み込みました (DB_DRIVER=%s)", _app_config.DB_DRIVER)
    except Exception as exc:
        logger.debug("AppConfig の読み込みをスキップします: %s", exc)
        _app_config = None

    return _app_config


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_db_connection(db_path: str | None = None) -> tuple[Any, str]:
    """
    データベース接続とドライバ名のタプルを返す。

    Args:
        db_path: SQLite 使用時の DB ファイルパス。
                 AppConfig で mysql が設定されている場合は無視される。
                 None の場合は instance/app.db を使用。

    Returns:
        (connection, driver) のタプル。
        driver は "sqlite" または "mysql"。

    Raises:
        ImportError: mysql ドライバ選択時に pymysql が未インストールの場合。
        pymysql.Error: MySQL/TiDB への接続に失敗した場合。
    """
    cfg = _load_app_config()

    if cfg is not None and getattr(cfg, "DB_DRIVER", "sqlite") == "mysql":
        conn = _connect_mysql(cfg)
        return conn, "mysql"

    return _connect_sqlite(db_path), "sqlite"


def placeholder(driver: str) -> str:
    """
    ドライバに対応する SQL プレースホルダ文字列を返す。

    Args:
        driver: "sqlite" または "mysql"。

    Returns:
        SQLite → "?", MySQL → "%s"

    Example:
        ph = placeholder(driver)
        cursor.execute(f"SELECT * FROM t WHERE id = {ph}", (id_,))
    """
    return "%s" if driver == "mysql" else "?"


def build_upsert_sql(
    driver: str, table: str, columns: list[str], conflict_keys: list[str]
) -> str:
    """
    UPSERT 用 SQL 文字列を生成する。

    Args:
        driver: "sqlite" または "mysql"。
        table: テーブル名。
        columns: INSERT するカラム名のリスト。
        conflict_keys: 競合判定に使うカラム名のリスト。
                       SQLite では ON CONFLICT(...) に、MySQL では実質的に
                       UNIQUE/PK キーとして使われる（SQL 文には含まれない）。

    Returns:
        実行可能な UPSERT SQL 文字列。プレースホルダはドライバに合わせて生成される。

    Example:
        sql = build_upsert_sql(
            driver,
            table="exchange_rates",
            columns=["from_currency", "to_currency", "rate", "source", "date", "created_at", "updated_at"],
            conflict_keys=["from_currency", "to_currency", "date"],
        )
        cursor.executemany(sql, rows)
    """
    ph = placeholder(driver)
    col_list = ", ".join(columns)
    val_list = ", ".join([ph] * len(columns))

    # UPDATE 対象 = conflict_keys 以外のカラム
    update_cols = [c for c in columns if c not in conflict_keys]

    if driver == "mysql":
        updates = ", ".join(f"{c} = VALUES({c})" for c in update_cols)
        return (
            f"INSERT INTO {table} ({col_list}) VALUES ({val_list})\n"
            f"ON DUPLICATE KEY UPDATE {updates}"
        )
    else:
        conflict = ", ".join(conflict_keys)
        updates = ", ".join(f"{c} = excluded.{c}" for c in update_cols)
        return (
            f"INSERT INTO {table} ({col_list}) VALUES ({val_list})\n"
            f"ON CONFLICT({conflict}) DO UPDATE SET {updates}"
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _connect_sqlite(db_path: str | None) -> Any:
    import sqlite3

    path = db_path or str(_DEFAULT_DB_PATH)
    conn = sqlite3.connect(path)
    logger.info("SQLite に接続しました: %s", path)
    return conn


def _connect_mysql(cfg: Any) -> Any:
    try:
        import pymysql  # type: ignore[import]
    except ImportError as exc:
        msg = (
            "pymysql がインストールされていません。"
            "`pip install pymysql` を実行してください。"
        )
        raise ImportError(msg) from exc

    # SSL configuration for TiDB Cloud
    ssl_params = {}
    if getattr(cfg, "DB_SSL_ENABLED", True):
        ssl_ca = getattr(cfg, "DB_SSL_CA", None)
        if ssl_ca:
            ssl_params = {
                "ssl_ca": ssl_ca,
                "ssl_verify_cert": True,
                "ssl_verify_identity": True,
            }

    conn = pymysql.connect(
        host=cfg.DB_HOST,
        port=cfg.DB_PORT or 4000,
        user=cfg.DB_USER,
        password=cfg.DB_PASSWORD or "",
        database=cfg.DB_NAME,
        charset="utf8mb4",
        autocommit=False,
        **ssl_params,
    )
    logger.info(
        "TiDB/MySQL に接続しました: %s:%s/%s (SSL: %s)",
        cfg.DB_HOST,
        cfg.DB_PORT,
        cfg.DB_NAME,
        bool(ssl_params),
    )
    return conn
