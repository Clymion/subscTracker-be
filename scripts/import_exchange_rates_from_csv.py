"""
Import historical exchange rates from a CSV file into the local SQLite DB.

Expected CSV format (example header):
UTC,Open,High,Low,Close,Volume
01.06.2025 00:00:00 UTC,163.157,163.418,163.117,163.246,11290.27

Filename should contain the currency pair in the form `FROM-TO_...`, for example:
`USD-JPY_Day_2025-06-01_to_2025-11-23_UTC.csv` -> from_currency=USD, to_currency=JPY

The script will insert/update rows into the `exchange_rates` table. It will also
optionally create same-currency synthetic rates (rate=1.0) for both currencies
for each date present in the CSV to avoid missing-parent FK issues.

This script follows the project's existing scripts style and talks directly to
the sqlite database file (no Flask app context needed).
"""

from __future__ import annotations

import argparse
import csv
import datetime
import logging
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "instance" / "app.db"


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
        header = next(reader, None)
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


def insert_rates(
    db_path: str,
    from_currency: str,
    to_currency: str,
    rates: list[tuple[datetime.date, float]],
    source: str = "csv-import",
    create_synthetic: bool = True,
) -> None:
    """Insert exchange rates into the database."""
    import sqlite3

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Prepare inserts for the pair
    pair_rows = [
        (
            from_currency,
            to_currency,
            rate,
            source,
            d.isoformat(),
            now,
            now,
        )
        for d, rate in rates
    ]

    # Insert SQL (UPSERT)
    sql = """
        INSERT INTO exchange_rates (
            from_currency, to_currency, rate, source, date,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(from_currency, to_currency, date) DO UPDATE SET
            rate = excluded.rate,
            source = excluded.source,
            updated_at = excluded.updated_at
    """

    try:
        if pair_rows:
            cursor.executemany(sql, pair_rows)
            logging.info(
                "Inserted/updated %d rows for %s->%s",
                len(pair_rows),
                from_currency,
                to_currency,
            )

        # Optionally create same-currency synthetic rates for both currencies seen in the CSV
        if create_synthetic and rates:
            dates = {d for d, _ in rates}
            synthetic_rows: list[tuple[Any, ...]] = []
            for d in sorted(dates):
                iso = d.isoformat()
                synthetic_rows.append(
                    (
                        from_currency,
                        from_currency,
                        1.0,
                        "synthetic-import",
                        iso,
                        now,
                        now,
                    ),
                )
                synthetic_rows.append(
                    (to_currency, to_currency, 1.0, "synthetic-import", iso, now, now),
                )
            cursor.executemany(sql, synthetic_rows)
            logging.info(
                "Inserted/updated %d synthetic same-currency rows",
                len(synthetic_rows),
            )

        conn.commit()
    except sqlite3.Error:
        logging.exception("Database error while inserting exchange rates")
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Import exchange rate history from CSV into the DB",
    )
    parser.add_argument("--file", "-f", required=True, help="Path to CSV file")
    parser.add_argument(
        "--db-path",
        default=str(DB_PATH),
        help="Path to sqlite DB file",
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
        insert_rates(
            args.db_path,
            from_currency,
            to_currency,
            rows,
            source=f"csv:{csv_path.name}",
            create_synthetic=args.create_synthetic,
        )
        logging.info(
            "Import complete for %s->%s (%d rows)",
            from_currency,
            to_currency,
            len(rows),
        )
    except Exception:
        logging.exception("Import failed")
        sys.exit(1)


if __name__ == "__main__":
    # Make project importable if needed by other scripts
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    main()
