"""
Import historical exchange rates from a CSV file into the DB.

Expected CSV format (header):
商品名,商品タイプ,取引日,当日清算価格
USD/JPY,"U.S. Dollar-Japanese Yen",2026/03/23,158.445

A single file may contain multiple currency pairs. The script will insert/update
rows into the `exchange_rates` table for every pair found. It will also optionally
create same-currency synthetic rates (rate=1.0) for both currencies for each date
to avoid missing-parent FK issues.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import logging
import sys
from pathlib import Path
from typing import Any

from db import build_upsert_sql, get_db_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

# Column indices in the new CSV format
_COL_PAIR = 0
_COL_DATE = 2
_COL_RATE = 3


def parse_csv_rows(
    path: Path,
) -> dict[str, list[tuple[datetime.date, float]]]:
    """
    Parse CSV and return dict keyed by pair string (e.g. "USD/JPY")
    mapping to a list of (date, rate) tuples.
    """
    result: dict[str, list[tuple[datetime.date, float]]] = {}
    with path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        next(reader, None)  # skip header
        for r in reader:
            if not r or len(r) < 4:
                continue
            pair = r[_COL_PAIR].strip()
            if not pair or "/" not in pair:
                logging.warning("Skipping row with invalid pair: %s", r[_COL_PAIR])
                continue
            date_str = r[_COL_DATE].strip()
            rate_str = r[_COL_RATE].strip()
            if not date_str or not rate_str:
                continue
            try:
                d = datetime.datetime.strptime(date_str, "%Y/%m/%d").date()
            except ValueError:
                logging.warning("Skipping row with unparsable date: %s", date_str)
                continue
            try:
                rate = float(rate_str.replace(",", ""))
            except ValueError:
                logging.warning("Skipping row with unparsable rate: %s", rate_str)
                continue
            result.setdefault(pair, []).append((d, rate))
    return result


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


def insert_rates(
    conn: Any,
    driver: str,
    from_currency: str,
    to_currency: str,
    rates: list[tuple[datetime.date, float]],
    source: str = "csv-import",
    create_synthetic: bool = True,
) -> None:
    """Insert/upsert exchange rates into the database."""
    sql = build_upsert_sql(
        driver,
        table="exchange_rates",
        columns=_EXCHANGE_RATE_COLUMNS,
        conflict_keys=_EXCHANGE_RATE_CONFLICT_KEYS,
    )
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    pair_rows = [
        (from_currency, to_currency, rate, source, d.isoformat(), now, now)
        for d, rate in rates
    ]

    cursor = conn.cursor()
    try:
        if pair_rows:
            cursor.executemany(sql, pair_rows)
            logging.info(
                "Inserted/updated %d rows for %s->%s",
                len(pair_rows),
                from_currency,
                to_currency,
            )

        if create_synthetic and rates:
            dates = {d for d, _ in rates}
            synthetic_rows: list[tuple[Any, ...]] = [
                row
                for d in sorted(dates)
                for row in (
                    (
                        from_currency,
                        from_currency,
                        1.0,
                        "synthetic-import",
                        d.isoformat(),
                        now,
                        now,
                    ),
                    (
                        to_currency,
                        to_currency,
                        1.0,
                        "synthetic-import",
                        d.isoformat(),
                        now,
                        now,
                    ),
                )
            ]
            cursor.executemany(sql, synthetic_rows)
            logging.info(
                "Inserted/updated %d synthetic same-currency rows",
                len(synthetic_rows),
            )

        conn.commit()
    except Exception:
        logging.exception("Database error while inserting exchange rates")
        conn.rollback()
        raise
    finally:
        cursor.close()


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Import exchange rate history from CSV into the DB",
    )
    parser.add_argument("--file", "-f", required=True, help="Path to CSV file")
    parser.add_argument(
        "--db-path",
        default=None,
        help=(
            "SQLite DB ファイルパス (SQLite 使用時のみ有効。"
            "AppConfig で mysql が設定されている場合は無視されます)"
        ),
    )
    parser.add_argument(
        "--from-to",
        help=(
            "Optional filter for a specific currency pair (e.g. USD-JPY). "
            "Only that pair will be imported."
        ),
    )
    parser.add_argument(
        "--no-synthetic",
        dest="create_synthetic",
        action="store_false",
        help="Do not create same-currency synthetic rates",
    )
    args = parser.parse_args()

    csv_path = Path(args.file)
    if not csv_path.exists():
        logging.error("CSV file not found: %s", csv_path)
        sys.exit(1)

    all_pairs = parse_csv_rows(csv_path)
    if not all_pairs:
        logging.error("No valid rows parsed from CSV: %s", csv_path)
        sys.exit(1)

    # Normalize --from-to filter: accept both "USD-JPY" and "USD/JPY"
    filter_pair: str | None = None
    if args.from_to:
        filter_pair = args.from_to.replace("-", "/").upper()

    filtered_pairs: dict[str, list[tuple[datetime.date, float]]] = {}
    for pair, rows in sorted(all_pairs.items()):
        pair_normalized = pair.replace("/", "/").upper()
        if filter_pair and pair_normalized != filter_pair:
            continue
        filtered_pairs[pair] = rows

    if not filtered_pairs:
        logging.error(
            "No matching pairs found. Available: %s",
            ", ".join(sorted(all_pairs.keys())),
        )
        sys.exit(1)

    try:
        conn, driver = get_db_connection(db_path=args.db_path)
    except Exception:
        logging.exception("データベース接続に失敗しました")
        sys.exit(1)

    try:
        for pair, rows in filtered_pairs.items():
            if "/" not in pair:
                logging.warning("Skipping invalid pair: %s", pair)
                continue
            from_currency, to_currency = (c.strip().upper() for c in pair.split("/", 1))
            insert_rates(
                conn=conn,
                driver=driver,
                from_currency=from_currency,
                to_currency=to_currency,
                rates=rows,
                source=f"csv:{csv_path.name}",
                create_synthetic=args.create_synthetic,
            )
            logging.info(
                "Import complete for %s->%s (%d rows) [driver=%s]",
                from_currency,
                to_currency,
                len(rows),
                driver,
            )
    except Exception:
        logging.exception("Import failed")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
