"""
為替レート取得スクリプト.

1日1回実行し、ExchangeRate-API.comから主要通貨の為替レートを取得して、
データベースに保存します。
"""

import datetime
import logging
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from google.api_core import exceptions
from google.cloud import secretmanager

# --- ロギング設定 ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

# --- 定数定義 ---
# プロジェクトのルートディレクトリ
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# 開発環境のデータベースパス
DB_PATH = PROJECT_ROOT / "instance" / "app.db"

# 為替レート取得API
API_URL_TEMPLATE = "https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"
# 取得対象の通貨リスト
TARGET_CURRENCIES = ["JPY", "USD", "EUR", "CNY"]
# APIのソース名
EXCHANGE_RATE_SOURCE = "exchangerate-api.com"

REQUEST_TIMEOUT = 15

# Google Cloud関連
logging.info(PROJECT_ROOT)
SERVICE_ACCOUNT_FILE = PROJECT_ROOT / "service_account_key.json"
GCP_PROJECT_ID = "subscmanager"
SECRET_ID_EXCHANGERATE_API_KEY = "EXCHANGERATE_API_KEY"  # noqa: S105
VERSION = "1"


def get_api_key() -> str | None:
    """
    APIキーを環境変数またはSecret Managerから取得します。

    優先順位:
    1. 環境変数 `EXCHANGERATE_API_KEY`
    2. Google Cloud Secret Manager

    Returns:
        APIキーの文字列。見つからない場合はNone。
    """
    api_key = os.environ.get("EXCHANGERATE_API_KEY")
    if api_key:
        logging.info("環境変数からAPIキーを取得しました。")
        return api_key

    logging.info(
        "環境変数にAPIキーが見つからないため、Secret Managerから取得を試みます。",
    )
    gcp_project_id = os.environ.get("GCP_PROJECT_ID") or GCP_PROJECT_ID
    secret_id = (
        os.environ.get("SECRET_ID_EXCHANGERATE_API_KEY")
        or SECRET_ID_EXCHANGERATE_API_KEY
    )
    version = os.environ.get("SECRET_VERSION", VERSION)

    if not gcp_project_id or not secret_id:
        logging.error(
            "環境変数 'GCP_PROJECT_ID' or 'SECRET_ID_EXCHANGERATE_API_KEY' が設定されていません。",
        )
        return None

    try:
        if SERVICE_ACCOUNT_FILE.exists():
            client = secretmanager.SecretManagerServiceClient.from_service_account_file(
                str(SERVICE_ACCOUNT_FILE),
            )
        else:
            client = secretmanager.SecretManagerServiceClient()
        name = client.secret_version_path(gcp_project_id, secret_id, version)
        response = client.access_secret_version(request={"name": name})
        api_key = response.payload.data.decode("UTF-8")
        logging.info("Secret ManagerからAPIキーを正常に取得しました。")
        return api_key  # noqa: TRY300
    except exceptions.GoogleAPICallError:
        logging.exception("Secret ManagerからのAPIキー取得に失敗しました。")
        return None


def get_db_connection() -> sqlite3.Connection:
    """データベース接続を取得します."""
    # 本番環境ではGCS上のファイルパスが環境変数経由で渡されることを想定
    db_path_str = os.environ.get("DATABASE_URL", str(DB_PATH))
    try:
        conn = sqlite3.connect(db_path_str)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error:
        logging.exception("データベース接続エラー")
        sys.exit(1)
    return conn


def fetch_exchange_rates(
    date: str,
    api_key: str,
) -> list[dict[str, Any]]:
    """
    TARGET_CURRENCIESの全ての通貨を基準として為替レートをAPIから取得します。

    Args:
        date: 'YYYY-MM-DD'形式の日付文字列（DB保存用）
        api_key: 為替レート取得APIのキー

    Returns:
        'insert_rates_to_db'が期待する形式の辞書データのリスト
    """
    rates_data_list: list[dict[str, Any]] = []
    for base_currency in TARGET_CURRENCIES:
        logging.info("%s を基準通貨としてレートを取得します。", base_currency)
        url = API_URL_TEMPLATE.format(api_key=api_key, base_currency=base_currency)
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if data.get("result") != "success":
                error_type = data.get("error-type", "unknown")
                logging.error("APIエラー (%s): %s", base_currency, error_type)
                continue  # 次の通貨へ

            # 'insert_rates_to_db'が期待する形式にレスポンスを整形
            all_rates = data.get("conversion_rates", {})
            # 自分自身へのレートは不要なので除外
            filtered_rates = {
                currency: all_rates[currency]
                for currency in TARGET_CURRENCIES
                if currency in all_rates and currency != base_currency
            }

            rates_data_list.append(
                {
                    "date": date,
                    "base": data.get("base_code"),
                    "rates": filtered_rates,
                },
            )

        except requests.exceptions.RequestException:
            logging.exception("APIリクエストエラー (%s)", base_currency)
            # エラーが発生しても他の通貨の取得は続ける
            continue

    if not rates_data_list:
        logging.error("すべての通貨のレート取得に失敗しました。")
        # 呼び出し元でハンドリングするため、ここでは終了しない

    return rates_data_list


def insert_rates_to_db(
    conn: sqlite3.Connection,
    rates_data: dict[str, Any],
) -> None:
    """
    取得した為替レートをデータベースに挿入します。

    同じ日の同じ通貨ペアのレートが存在する場合は更新します。

    Args:
        conn: データベース接続オブジェクト
        rates_data: APIから取得した為替レートデータ
    """
    cursor = conn.cursor()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    date = rates_data["date"]
    base = rates_data["base"]

    if not base or not date or "rates" not in rates_data:
        logging.error("レートデータが不正です。処理を中断します。")
        return

    rates_to_insert: list[tuple] = []
    for to_currency, rate in rates_data["rates"].items():
        # 基準通貨 -> 対象通貨 のレート
        rates_to_insert.append(
            (base, to_currency, rate, EXCHANGE_RATE_SOURCE, date, now, now),
        )

    if not rates_to_insert:
        logging.info("挿入するレートがありませんでした。(Base: %s)", base)
        return

    # 同じ日、同じ通貨ペアが重複した場合は更新する
    sql = """
        INSERT INTO EXCHANGE_RATES (
            from_currency, to_currency, rate, source, date,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(from_currency, to_currency, date) DO UPDATE SET
            rate = excluded.rate,
            source = excluded.source,
            updated_at = excluded.updated_at
    """
    try:
        cursor.executemany(sql, rates_to_insert)
        conn.commit()
        logging.info(
            "%d件のレート(基準通貨: %s)をデータベースに保存/更新しました。",
            len(rates_to_insert),
            base,
        )
    except sqlite3.Error:
        logging.exception("データベース挿入エラー")
        conn.rollback()
        sys.exit(1)


def main() -> None:
    """
    メイン処理。

    為替レートを取得し、データベースに保存します。
    cronやCloud Run Jobで実行されることを想定しています。
    """
    # 1. APIキーを取得
    api_key = get_api_key()
    if not api_key:
        logging.error("APIキーを取得できませんでした。処理を終了します。")
        sys.exit(1)

    # 2. 為替レートを取得
    date_to_fetch = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    logging.info("%s の為替レートを取得します...", date_to_fetch)
    all_rates_data = fetch_exchange_rates(date_to_fetch, api_key)

    if not all_rates_data:
        logging.warning("APIからレート情報を取得できませんでした。処理を終了します。")
        sys.exit(0)  # 異常終了ではなく、警告として正常終了する

    logging.info(
        "APIから %d 通貨を基準とするレート情報を取得しました。", len(all_rates_data),
    )

    # 3. データベースに接続
    conn = get_db_connection()
    logging.info("データベースに接続しました。")

    # 4. 取得したレートをDBに保存
    for rates_data in all_rates_data:
        insert_rates_to_db(conn, rates_data)

    # 5. 接続を閉じる
    conn.close()
    logging.info("処理が完了しました。")


if __name__ == "__main__":
    # .envファイルから環境変数を読み込む
    load_dotenv()

    # sys.pathにプロジェクトルートを追加して、appモジュールをインポート可能にする
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    main()
