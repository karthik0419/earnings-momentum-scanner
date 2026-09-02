# NSE Price Test Loop — Skill

## Goal
`price_service.py` fetches OHLC for all 500 Nifty stocks with 0 errors AND is 2x faster than yfinance.

## Pattern
ReAct + deterministic verifier. One workstream, program-checkable goal.

## How to run
```powershell
# Run the verifier (checks if goal is met)
python test_service.py --batch 500

# If failures, fix price_service.py, re-run
# Loop self-terminates when all 500 pass + speed check passes
```

## What "done" means
1. `test_service.py --batch 500` exits with code 0
2. 0 stocks failed to fetch
3. NSE fetch time < yfinance fetch time / 2
4. OHLC data matches yfinance within 0.1% (sanity check)

## Conventions (do not re-derive each run)
- NSE API base: `https://www.nseindia.com/api/`
- Session: first GET to `https://www.nseindia.com` sets cookies, reuse for all API calls
- User-Agent: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36`
- Rate limit: max 10 req/s, exponential backoff on 429/503
- Cache: Redis (if available) or disk (`cache/` directory)
- Cache TTL: 8 hours for historical OHLC, 1 min for quotes
- Fallback: yfinance if NSE API is down
- Symbol format: NSE uses `RELIANCE` (no `.NS` suffix); yfinance uses `RELIANCE.NS`

## NSE API endpoints
- Historical OHLC: `/api/historical/cm-equity?symbol=RELIANCE&from=YYYY-MM-DD&to=YYYY-MM-DD&series=EQ`
- Real-time quote: `/api/quote-equity?symbol=RELIANCE`
- Stock universe: `/api/equity-stock-names?index=equities`
- Index constituents: `/api/equity-stock-names?index=nifty500`

## Budget
- Max 10 iterations per run
- 2 hour wall-clock
- Stop when verifier passes
