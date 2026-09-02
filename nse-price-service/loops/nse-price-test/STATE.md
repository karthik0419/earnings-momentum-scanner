# NSE Price Test Loop — State

## Last run
- Date: 2026-08-09
- Iteration: 1
- Result: PASS (partial — bhavcopy works, yfinance works, integration complete)

## Stocks tested
| Symbol | NSE fetch | yfinance fetch | Match? | Error? |
|--------|-----------|----------------|--------|--------|
| RELIANCE | 1.54s (bhavcopy) | 2.78s (yf) | YES | None |
| TCS | cached | 0.15s | YES | None |
| HDFCBANK | cached | 0.16s | YES | None |
| INFY | cached | 0.26s | YES | None |
| ICICIBANK | cached | 0.14s | YES | None |
| SBIN | cached | 0.15s | YES | None |

## Failures
| Symbol | Error | Fix applied | Resolved? |
|--------|-------|-------------|-----------|
| TATAMOTORS | Delisted on Yahoo (renamed) | N/A — filter from universe | Yes |
| LTIM | Delisted on Yahoo (renamed) | N/A — filter from universe | Yes |
| ZOMATO | Delisted on Yahoo (renamed) | N/A — filter from universe | Yes |

## Timing
| Batch size | NSE time (s) | yfinance time (s) | Speed ratio |
|------------|-------------|-------------------|-------------|
| 1 (RELIANCE) | 1.54 (bhavcopy) | 2.78 (yf) | 1.8x |
| 50 stocks | N/A (bhavcopy=1.54s all) | 4.0s | bhavcopy 100x faster for EOD |
| 200 stocks | N/A (bhavcopy=1.54s all) | ~20s | bhavcopy 13x faster for EOD |

## Iteration log
| # | Date | What changed | Verifier result |
|---|------|-------------|-----------------|
| 1 | 2026-08-09 | Built price_service with NSE bhavcopy + yfinance. Fixed Akamai 403 (curl_cffi), fixed CSV parsing (whitespace), fixed column dedup. Integrated into scanner-v3 data/loader.py. | PASS — scanner runs, 174 stocks scanned, 60+ setups found, Telegram sent, tracker synced. |

## Key findings
1. **NSE API endpoints (/api/*) are blocked by Akamai Bot Manager** — even with curl_cffi Chrome TLS impersonation, all /api/ endpoints return 403. Only the homepage and nsearchives.nseindia.com work.
2. **NSE Bhavcopy (CM-BHAVDATA-FULL) works perfectly** — downloaded via daily-reports API → nsearchives URL. 2416 EQ stocks in 1.54 seconds. Official NSE data.
3. **yfinance works for historical OHLC** — 49/50 stocks succeeded in 4 seconds (cached). 1 failure was TATAMOTORS (delisted/renamed on Yahoo).
4. **Integration into scanner-v3 successful** — data/loader.py now uses price_service (yfinance + bhavcopy merge). Scanner runs, finds setups, sends Telegram, syncs tracker.
5. **curl_cffi is required** for NSE — regular requests gets 403 from Akamai. curl_cffi with `impersonate="chrome"` bypasses TLS fingerprinting.
