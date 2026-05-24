#!/bin/bash
set -euo pipefail

DATE_ARG=""
if [ -n "${1:-}" ]; then
  DATE_ARG="--date $1"
fi

python scripts/fetch_exchange_rates.py ${DATE_ARG}
