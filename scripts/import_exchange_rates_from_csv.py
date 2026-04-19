"""
Import historical exchange rates from a CSV file into the DB.

Expected CSV format (example header):
UTC,Open,High,Low,Close,Volume
01.06.2025 00:00:00 UTC,163.157,163.418,163.117,163.246,11290.27

Filename should contain the currency pair in the form `FROM-TO_...`, for example:
`USD-JPY_Day_2025-06-01_to_2025-11-23_UTC.csv` -> from_currency=USD, to_currency=JPY

The script will insert/update rows into the `exchange_rates` table. It will also
optionally create same-currency synthetic rates (rate=1.0) for both currencies
for each date present in the CSV to avoid missing-parent FK issues.
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


def infer_pair_from_filename(filename: str) -> tuple[str, str] | None:
    """
    Infer FROM and TO currency codes from the filename.

    Expects pattern like `USD-JPY_...` at start of name.
    Returns (from_currency, to_currency) or None if not found.
    """
    name = Path(filename).name
    parts = name.split("_")
    if not parts:
        return None
    first = parts[0]
    if "-" not in first:
        return None
    from_cur, to_cur = first.split("-", 1)
    if (
        len(from_cur) == 3
        and len(to_cur) == 3
        and from_cur.isalpha()
        and to_cur.isalpha()
    ):
        return from_cur.upper(), to_cur.upper()
    return None


def parse_csv_rows(path: Path) -> list[tuple[datetime.date, float]]:
    """
    Parse CSV and return list of (date, close_rate).

    Assumes the timestamp format in the provided CSV is like: '01.06.2025 00:00:00 UTC'
    and that the `Close` column is the 5th column (index 4).
    """
    rows: list[tuple[datetime.date, float]] = []
    with path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        next(reader, None)  # skip header
        for r in reader:
            if not r or len(r) < 5:
                continue
            date_str = r[0].strip()
            close_str = r[4].strip()
            try:
                dt = datetime.datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S UTC")
                d = dt.date()
            except ValueError:
                logging.warning("Skipping row with unparsable date: %s", date_str)
                continue
            try:
                rate = float(close_str.replace(",", ""))
            except ValueError:
                logging.warning("Skipping row with unparsable rate: %s", close_str)
                continue
            rows.append((d, rate))
    return rows


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
        help="Optional override for FROM-TO pair (e.g. USD-JPY)",
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

    pair = None
    if args.from_to:
        if "-" in args.from_to:
            a, b = args.from_to.split("-", 1)
            pair = (a.upper(), b.upper())
        else:
            logging.error("--from-to must be in the form FROM-TO, e.g. USD-JPY")
            sys.exit(1)
    else:
        pair = infer_pair_from_filename(csv_path.name)

    if not pair:
        logging.error(
            "Could not infer currency pair from filename. Use --from-to to specify.",
        )
        sys.exit(1)

    from_currency, to_currency = pair
    rows = parse_csv_rows(csv_path)
    if not rows:
        logging.error("No valid rows parsed from CSV: %s", csv_path)
        sys.exit(1)

    try:
        conn, driver = get_db_connection(db_path=args.db_path)
    except Exception:
        logging.exception("データベース接続に失敗しました")
        sys.exit(1)

    try:
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
