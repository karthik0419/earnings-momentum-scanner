# NSE Price Service

> **Status:** Experimental — building and testing in isolation before porting to scanner-v3.

---

## Why this exists

The scanner-v3 and scanner-dashboard currently rely on two external data sources:

| Source | Used for | Problem |
|--------|----------|---------|
| **yfinance** | Historical OHLC (daily/weekly/monthly) for pattern scanning | US-based servers, slow for Indian stocks, rate-limited, sometimes returns NaN, breaks on stock splits/delistings |
| **jugaad-data** | NSE stock universe, live quotes for paper tracker | Wrapper around NSE website, breaks when NSE changes their HTML/API structure, no real-time tick data |
| **screener.in** | PEAD scanner (earnings data) | Very slow (2s/stock), no official API, HTML scraping |

These are the **weakest links** in the entire system. They're third-party, uncontrollable, and break without warning.

### The goal

Build a **self-contained NSE price service** that:
1. Fetches historical OHLC directly from NSE's public JSON API (no yfinance)
2. Fetches real-time quotes directly from NSE's quote API (no jugaad-data)
3. Caches everything in Redis (fast, shared, production-grade)
4. Falls back to disk cache when Redis is unavailable (local .bat usage)
5. Falls back to yfinance only if NSE API is completely down
6. Rate-limits itself to avoid NSE IP bans (max 10 req/s)
7. Handles NSE's cookie/session flow automatically

### Why a separate project (not in scanner-v3 directly)

1. **Isolation** — debug and test the NSE API without touching working scanner code
2. **Speed** — iterate fast, break things, no risk to the production scanner
3. **Reusable** — once proven, copy `price_service.py` into scanner-v3, earnings-momentum-scanner, or any future project
4. **Testable** — standalone CLI (`python price_service.py --test RELIANCE`) to verify each function
5. **Clean** — no scanner logic, no pattern detection, no dashboard — just data fetching + caching

Once stable, the single `price_service.py` file gets copied into scanner-v3 and replaces yfinance/jugaad-data imports. This repo stays as the test/playground.

---

## Architecture

```
                    ┌──────────────────────────┐
                    │    price_service.py       │
                    │                          │
  scanner.py ──────→│  get_ohlc()              │──── NSE Historical API
  daily_scan.py ───→│  get_quote()             │──── NSE Quote API
  paper_tracker ───→│  get_stock_universe()    │──── NSE Stock Names API
                    │  get_index_constituents() │──── NSE Index API
                    │                          │
                    │  ┌─────────────────────┐ │
                    │  │  Cache Layer        │ │
                    │  │  - Redis (primary)  │ │
                    │  │  - Disk (fallback)  │ │
                    │  └─────────────────────┘ │
                    │                          │
                    │  ┌─────────────────────┐ │
                    │  │  Fallback           │ │
                    │  │  - yfinance (if     │ │
                    │  │    NSE is down)     │ │
                    │  └─────────────────────┘ │
                    └──────────────────────────┘
```

### Cache strategy

| Data | Cache TTL (market hours) | Cache TTL (after hours) | Cache backend |
|------|--------------------------|-------------------------|---------------|
| Historical OHLC | 8 hours | 24 hours | Redis or disk |
| Real-time quote | 1 minute | 1 hour | Redis or disk |
| Stock universe | 24 hours | 24 hours | Redis or disk |
| Index constituents | 24 hours | 24 hours | Redis or disk |

### Rate limiting

- Max 10 requests/sec to NSE (they block at ~15/s)
- Exponential backoff on HTTP 429 (Too Many Requests) and 503 (Service Unavailable)
- Retry 3 times before falling back to yfinance
- Session cookies refreshed every 100 requests

---

## NSE API endpoints used

### 1. Historical OHLC
```
GET https://www.nseindia.com/api/historical/cm-equity
    ?symbol=RELIANCE
    &from=2025-08-09
    &to=2026-08-09
    &series=EQ

Headers:
  User-Agent: Mozilla/5.0 ...
  Cookie: <from initial nseindia.com visit>

Response: JSON array of:
  { fhDate: "09-Aug-2026", open, high, low, close, tottrdqty, ... }
```

### 2. Real-time quote
```
GET https://www.nseindia.com/api/quote-equity?symbol=RELIANCE

Response:
  { priceInfo: { lastPrice, close, open, high, low, ... },
    metadata: { series, pdSectorInd, ... } }
```

### 3. Stock universe (all NSE EQ)
```
GET https://www.nseindia.com/api/equity-stock-names?index=equities

Response: JSON array of:
  { symbol: "RELIANCE", name: "Reliance Industries", ... }
```

### 4. Index constituents
```
GET https://www.nseindia.com/api/allIndices
→ find index "NIFTY 500" → get its constituents

or

GET https://www.nseindia.com/api/equity-stock-names?index=nifty500
```

### Session handling
NSE requires a session cookie. First request to `https://www.nseindia.com` sets cookies, which must be sent with all subsequent API calls.

```python
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
})
session.get("https://www.nseindia.com")  # sets cookies
# Now session.get("https://www.nseindia.com/api/...") works
```

---

## Project structure

```
nse-price-service/
├── README.md              ← this file
├── price_service.py       ← the main module (single file, portable)
├── test_service.py        ← standalone tests (no pytest, just run it)
├── requirements.txt       ← requests, redis, pandas, yfinance (fallback)
├── docker-compose.yml     ← Redis for local testing
└── .env.example           ← REDIS_URL, CACHE_DIR, etc.
```

---

## Testing plan

### Phase 1: NSE API exploration (no cache)
- [ ] Get session cookie working
- [ ] Fetch historical OHLC for 1 stock (RELIANCE)
- [ ] Fetch real-time quote for 1 stock
- [ ] Fetch stock universe (all NSE EQ)
- [ ] Fetch Nifty 500 constituents
- [ ] Measure response times

### Phase 2: Cache layer
- [ ] Disk cache (no Redis needed)
- [ ] Redis cache (with docker-compose Redis)
- [ ] Auto-detect: use Redis if available, disk otherwise
- [ ] Verify cache hits/misses

### Phase 3: Rate limiting + fallback
- [ ] Rate limiter (10 req/s)
- [ ] Exponential backoff on 429/503
- [ ] yfinance fallback when NSE is down
- [ ] Batch fetch (100 stocks) with rate limiting

### Phase 4: Performance test
- [ ] Fetch OHLC for 500 stocks (Nifty 500) — measure time
- [ ] Compare: NSE API vs yfinance (same 500 stocks)
- [ ] Fetch real-time quotes for 30 tracker stocks — measure time

### Phase 5: Port to scanner-v3
- [ ] Copy `price_service.py` to scanner-v3
- [ ] Update `scanner.py` imports
- [ ] Update `daily_scan.py` imports
- [ ] Update `paper_tracker.py` imports
- [ ] Run full scan end-to-end with new price service
- [ ] Verify results match old yfinance-based scan

---

## Why not just use yfinance?

| Issue | yfinance | NSE Direct |
|-------|----------|------------|
| Server location | US (Illinois) | India (Mumbai) |
| Speed for Indian stocks | 0.5-2s/stock | 0.1-0.3s/stock |
| Reliability | Breaks often (Yahoo changes API) | Stable (NSE's own API) |
| Rate limiting | Aggressive (blocks after ~200 req/min) | Lenient (~10 req/s = 600/min) |
| Data quality | Sometimes NaN, missing days | Clean, official NSE data |
| Stock splits | Often wrong/delayed | Correct same-day |
| Delisted stocks | Returns old data | Returns error (correct) |
| Real-time quotes | 15-min delay | Live during market hours |
| Stock universe | No NSE-specific list | Full NSE EQ list available |
| Dependency | Third-party (Yahoo) | First-party (NSE) |

For a product you're selling, depending on Yahoo's free API is a liability. NSE's API is the official source — it's what every Indian trading platform uses under the hood.

---

## Why Redis?

| Feature | Disk cache (current) | Redis |
|---------|---------------------|-------|
| Speed | ~5ms (file I/O) | ~0.1ms (memory) |
| Shared across processes | No (each scanner reads files) | Yes (scanner + tracker + dashboard all share) |
| TTL expiry | Manual (check file mtime) | Built-in (`SETEX key ttl value`) |
| Concurrent access | File locks needed | Thread-safe by design |
| Dashboard reads | Has to read CSV files | Instant cache hits |
| Production-grade | No | Yes |
| Local .bat usage | Works | Not needed (disk fallback) |

Redis is already running in the scanner-dashboard Docker setup. The price service will auto-detect it and use it when available. For local `.bat` file usage (no Docker), it falls back to disk cache — same as today.

---

## Future: Real-time WebSocket (Phase 6)

NSE doesn't offer a public WebSocket, but once the REST API service is stable, we could:
1. Poll NSE quote API every 5 seconds during market hours
2. Push updates to dashboard via Server-Sent Events (SSE)
3. Dashboard shows live P&L updating in real-time (no manual refresh)

This is a stretch goal — not needed for v1, but the architecture supports it.
