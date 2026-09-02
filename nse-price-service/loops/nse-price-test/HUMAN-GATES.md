# Human Gates — NSE Price Test Loop

## Irreversible actions
None. All actions are local file edits and test runs. No network calls beyond
NSE API (read-only) and yfinance (read-only). No deletes, no merges, no sends.

## Budget / stop conditions
- Max 10 iterations per run
- 2 hour wall-clock
- Stop immediately if NSE API is consistently down (3 consecutive failures)
- Stop when verifier passes (all 500 stocks fetch with 0 errors + 2x speed)
