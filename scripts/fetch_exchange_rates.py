"""
為替レート取得スクリプト.

1日1回実行し、ExchangeRate-API.comから主要通貨の為替レートを取得して、
データベースに保存します。
"""

import argparse
import datetime
import logging
import os
import sys
from pathlib import Path
from typing import Any

import requests
from db import build_upsert_sql, get_db_connection
from google.api_core import exceptions
from google.cloud import secretmanager

# --- ロギング設定 ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

# --- 定数定義 ---
# 為替レート取得API
API_URL_LATEST_TEMPLATE = "https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"
API_URL_HISTORY_TEMPLATE = "https://v6.exchangerate-api.com/v6/{api_key}/history/{base_currency}/{year}/{month}/{day}"
# 取得対象の通貨リスト
TARGET_CURRENCIES = ["JPY", "USD", "EUR"]
# APIのソース名
EXCHANGE_RATE_SOURCE = "exchangerate-api.com"

REQUEST_TIMEOUT = 15

# Google Cloud関連
SERVICE_ACCOUNT_FILE = Path("service_account_key.json")
GCP_PROJECT_ID = "subscmanager"
SECRET_ID_EXCHANGERATE_API_KEY = "EXCHANGERATE_API_KEY"  # noqa: S105
VERSION = "1"

# UPSERT用カラム定義
_EXCHANGE_RATE_COLUMNS = [
    "from_currency",
    "to_currency",
    "rate",
    "source",
    "date",
    "created_at",
    "updated_at",
]
_EXCHANGE_RATE_CONFLICT_KEYS = ["from_currency", "to_currency", "date"]


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


def fetch_exchange_rates(
    date: str,
    api_key: str,
) -> list[dict[str, Any]]:
    """
    指定された日付の為替レートをAPIから取得します。`TARGET_CURRENCIES`の全ての通貨を基準として為替レートを取得します。

    Args:
        date: 'YYYY-MM-DD'形式の日付文字列
        api_key: 為替レート取得APIのキー

    Returns:
        'insert_rates_to_db'が期待する形式の辞書データのリスト
    """
    rates_data_list: list[dict[str, Any]] = []

    # 日付の妥当性チェック
    try:
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        today = datetime.datetime.now(datetime.timezone.utc).date()
        if date_obj > today:
            logging.error("未来の日付の為替レートは取得できません。: %s", date)
            return []
    except ValueError:
        logging.error("日付のフォーマットが不正です: %s。YYYY-MM-DD形式で指定してください。", date)
        return []

    is_today = date_obj == today

    for base_currency in TARGET_CURRENCIES:
        logging.info("%s を基準通貨として %s のレートを取得します。", base_currency, date)

        if is_today:
            url = API_URL_LATEST_TEMPLATE.format(
                api_key=api_key, base_currency=base_currency
            )
        else:
            year, month, day = date.split("-")
            url = API_URL_HISTORY_TEMPLATE.format(
                api_key=api_key,
                base_currency=base_currency,
                year=year,
                month=month,
                day=day,
            )

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
            # 自分自身へのレートも含める (Identity Rate)
            filtered_rates = {
                currency: all_rates[currency]
                for currency in TARGET_CURRENCIES
                if currency in all_rates
            }
            # APIがbase_currencyを返さない場合は手動で追加
            if base_currency in TARGET_CURRENCIES and base_currency not in filtered_rates:
                filtered_rates[base_currency] = 1.0

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
    conn: Any,
    driver: str,
    rates_data: dict[str, Any],
) -> None:
    """
    取得した為替レートをデータベースに挿入します。

    同じ日の同じ通貨ペアのレートが存在する場合は更新します。

    Args:
        conn: データベース接続オブジェクト
        driver: "sqlite" または "mysql"
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

    sql = build_upsert_sql(
        driver,
        table="exchange_rates",
        columns=_EXCHANGE_RATE_COLUMNS,
        conflict_keys=_EXCHANGE_RATE_CONFLICT_KEYS,
    )
    try:
        cursor.executemany(sql, rates_to_insert)
        conn.commit()
        logging.info(
            "%d件のレート(基準通貨: %s)をデータベースに保存/更新しました。",
            len(rates_to_insert),
            base,
        )
    except Exception:
        logging.exception("データベース挿入エラー")
        conn.rollback()
        sys.exit(1)


def main() -> None:
    """
    メイン処理。

    為替レートを取得し、データベースに保存します。
    cronやCloud Run Jobで実行されることを想定しています。
    """
    # --- 引数パーサーの設定 ---
    parser = argparse.ArgumentParser(description="為替レート取得スクリプト")
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
        help="取得対象の日付 (YYYY-MM-DD形式)。指定しない場合は実行当日の日付になります。",
    )
    args = parser.parse_args()
    date_to_fetch = args.date

    # 1. APIキーを取得
    api_key = get_api_key()
    if not api_key:
        logging.error("APIキーを取得できませんでした。処理を終了します。")
        sys.exit(1)

    # 2. 為替レートを取得
    logging.info("%s の為替レートを取得します...", date_to_fetch)
    all_rates_data = fetch_exchange_rates(date_to_fetch, api_key)

    if not all_rates_data:
        logging.warning("APIからレート情報を取得できませんでした。処理を終了します。")
        sys.exit(0)  # 異常終了ではなく、警告として正常終了する

    logging.info(
        "APIから %d 通貨を基準とするレート情報を取得しました。", len(all_rates_data),
    )

    # 3. データベースに接続
    try:
        conn, driver = get_db_connection()
    except Exception:
        logging.exception("データベース接続に失敗しました")
        sys.exit(1)
    logging.info("データベースに接続しました。(driver=%s)", driver)

    # 4. 取得したレートをDBに保存
    try:
        for rates_data in all_rates_data:
            insert_rates_to_db(conn, driver, rates_data)
    finally:
        conn.close()

    logging.info("処理が完了しました。")


if __name__ == "__main__":
    main()
