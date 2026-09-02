#!/usr/bin/env bash
# verify_nse_price_test.sh — Verifier for NSE price service test loop
#
# Checks:
#   1. All 500 Nifty stocks fetch with 0 errors
#   2. NSE fetch time < yfinance fetch time / 2
#
# Exit codes:
#   0 = goal met (loop can stop)
#   1 = goal not met (loop should continue)
#   2 = error (loop should stop and alert)

set -euo pipefail

cd "$(dirname "$0")/.."

echo "Running verifier: test_service.py --batch 500"
python test_service.py --batch 500 --verify
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "PASS: all 500 stocks fetched, speed goal met"
  exit 0
else
  echo "FAIL: verifier returned exit code $EXIT_CODE"
  exit 1
fi
