"""Single-stock PEAD scanner for NYKAA.NS."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta
import yfinance as yf
import pandas as pd

from data.fetcher import fetch_cached
from data.earnings import fetch_earnings
from data.result_dates import get_result_date
from engine.earnings_filter import filter_earnings
from engine.price_reactor import measure_reaction, avg_spike
from engine.entry_detector import detect_entry
from engine.profit_estimator import estimate_current_quarter
from engine.scorer import score_stock

SYMBOL = "NYKAA.NS"
POST_RESULT_WINDOW = 45
PRE_RESULT_WINDOW = 15

print("=" * 70)
print("  PEAD SCANNER — Single Stock Analysis")
print("  Symbol: %s" % SYMBOL)
print("=" * 70)
print()

# 1. Fetch earnings data
print("[1/6] Fetching earnings from screener.in...")
quarters = fetch_earnings(SYMBOL)
if not quarters or len(quarters) < 4:
    print("  ERROR: Not enough earnings data (need 4+ quarters, got %d)" % (len(quarters) if quarters else 0))
    sys.exit(1)

print("  Found %d quarters of earnings data" % len(quarters))
for q in quarters[-4:]:
    print("    %s: Revenue=%s  NetProfit=%s  EPS=%s" % (
        q.get('quarter', '?'),
        q.get('revenue', '?'),
        q.get('net_profit', '?'),
        q.get('eps', '?')))

# 2. Filter earnings (growth + consistency)
print()
print("[2/6] Filtering earnings (growth + consistency)...")
ef = filter_earnings(quarters)
print("  Passes filter: %s" % ef["passes"])
print("  Consistency score: %s" % ef.get("consistency_score", "N/A"))
print("  Avg YoY growth: %s%%" % ef.get("avg_yoy_growth", "N/A"))
print("  Growth quarters: %s/%s" % (ef.get("growth_quarters", 0), len(quarters)))

# 3. Fetch price data
print()
print("[3/6] Fetching price data...")
df = fetch_cached(SYMBOL, days=365)
if df is None or len(df) < 60:
    print("  ERROR: Not enough price data")
    sys.exit(1)
print("  Got %d days of price data" % len(df))
print("  Current price: Rs %.2f" % float(df["Close"].iloc[-1]))

# 4. Find last result date
print()
print("[4/6] Finding result date...")
last_q = quarters[-1].get("quarter") if quarters else None
print("  Last quarter: %s" % last_q)

result_date = get_result_date(SYMBOL, last_q, price_df=df) if last_q else None
print("  Result date: %s" % result_date)

today = date.today()
mode = None
days_since = None
if result_date:
    delta = (today - result_date).days
    if 0 <= delta <= POST_RESULT_WINDOW:
        mode = "post"
        days_since = delta
    elif -PRE_RESULT_WINDOW <= delta < 0:
        mode = "pre"
    print("  Days since result: %d" % delta)
    print("  Mode: %s" % (mode or "OUTSIDE_WINDOW (no recent earnings)"))

# 5. Historical reactions (last 4 quarters)
print()
print("[5/6] Historical earnings reactions (last 4 quarters)...")
valid_qs = [q for q in quarters if q.get("quarter")]
last4_qs = valid_qs[-4:]
reactions = []
for q in last4_qs:
    rd = get_result_date(SYMBOL, q["quarter"], price_df=df)
    if rd is None:
        print("  %s: no result date found" % q["quarter"])
        continue
    rx = measure_reaction(SYMBOL, rd, df)
    if rx:
        reactions.append(rx)
        print("  %s: spike=%+.2f%%  d1=%+.2f%%  d5=%+.2f%%  d20=%+.2f%%" % (
            q["quarter"],
            rx.get("spike_pct", 0),
            rx.get("d1_pct", 0),
            rx.get("d5_pct", 0),
            rx.get("d20_pct", 0)))
    else:
        print("  %s: no reaction data" % q["quarter"])

avg_sp = avg_spike(reactions)
print("  Average spike: %+.2f%%" % avg_sp)

# 6. Entry detection (post-result only)
print()
print("[6/6] Entry detection...")
entry_info = None
if mode == "post" and result_date:
    spike_rx = measure_reaction(SYMBOL, result_date, df)
    if spike_rx and spike_rx.get("spike_pct", 0) >= 2:
        entry_info = detect_entry(df, result_date, spike_rx["d0"])
        if entry_info:
            print("  ENTRY DETECTED!")
            print("    Entry:  Rs %.2f" % entry_info["entry"])
            print("    Stop:   Rs %.2f" % entry_info["stop"])
            print("    Target: Rs %.2f" % entry_info["target"])
            print("    R:R:    1:%.2f" % entry_info["rr"])
        else:
            print("  No entry signal (pullback not detected yet)")
    else:
        print("  No spike >= 2%% on result day (spike: %+.2f%%)" % (spike_rx.get("spike_pct", 0) if spike_rx else 0))
else:
    print("  Not in post-result window (mode=%s)" % mode)
    if mode is None:
        print("  Earnings were outside the %d-day post-result window" % POST_RESULT_WINDOW)

# Projection
print()
print("  Profit projection (current quarter):")
projection = estimate_current_quarter(quarters)
print("    Projected net profit: %s" % projection.get("projected_net_profit", "N/A"))
print("    Projected EPS:        %s" % projection.get("projected_eps", "N/A"))
print("    YoY growth:           %s%%" % projection.get("yoy_growth_pct", "N/A"))
print("    Confidence:           %s" % projection.get("confidence", "N/A"))

# Score
print()
score_breakdown = score_stock(ef, reactions, entry_info, sector_rank=1)
total_score = score_breakdown["total"]
print("  PEAD Score: %.1f / 100" % total_score)
print("  Score breakdown:")
for k, v in score_breakdown.items():
    if k != "total" and isinstance(v, (int, float)):
        print("    %s: %.1f" % (k, v))

# Summary
print()
print("=" * 70)
print("  SUMMARY")
print("=" * 70)
cmp = float(df["Close"].iloc[-1])
print("  Stock:          %s" % SYMBOL)
print("  Current price:  Rs %.2f" % cmp)
print("  Last quarter:   %s" % last_q)
print("  Result date:    %s" % result_date)
print("  Mode:           %s" % (mode or "OUTSIDE_WINDOW"))
if days_since is not None:
    print("  Days since:     %d" % days_since)
print("  Avg spike:      %+.2f%%" % avg_sp)
print("  PEAD score:     %.1f / 100" % total_score)
if entry_info:
    print("  ENTRY SIGNAL:   YES")
    print("    Entry:  Rs %.2f" % entry_info["entry"])
    print("    Stop:   Rs %.2f" % entry_info["stop"])
    print("    Target: Rs %.2f" % entry_info["target"])
    print("    R:R:    1:%.2f" % entry_info["rr"])
    # Current vs entry
    dist = ((cmp - entry_info["entry"]) / entry_info["entry"]) * 100
    print("    Current vs entry: %+.2f%%" % dist)
else:
    print("  ENTRY SIGNAL:   NO")
    if mode is None:
        print("  Reason: Earnings outside %d-day post-result window" % POST_RESULT_WINDOW)
    elif mode == "post":
        print("  Reason: No pullback entry detected yet (or spike < 2%%)")

# Recent price action
print()
print("  Recent price action (last 10 days):")
for idx, row in df[['Open', 'High', 'Low', 'Close', 'Volume']].tail(10).iterrows():
    d = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)
    print("    %s  O=%.2f H=%.2f L=%.2f C=%.2f V=%d" % (
        d, row['Open'], row['High'], row['Low'], row['Close'], int(row['Volume'])))

print()
print("=" * 70)

