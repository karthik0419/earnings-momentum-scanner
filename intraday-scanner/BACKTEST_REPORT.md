# INTRADAY STRATEGY BACKTEST REPORT — VERDICT: DO NOT TRADE

**Date:** 2026-07-22 | **Period:** 365 days (241 trading days, Jul 2025 – Jul 2026)
**Universe:** 116 NSE F&O stocks (hourly bars) + NIFTY/BANKNIFTY
**Method:** Signal at 10:15 (first-hour return vs prev close + sector strength), entry 10:15, exit 15:15, 2% stop, 0.10% round-trip cost. No lookahead. Corporate-action guard at |12%|.

---

## Headline numbers (with stops + costs — the tradeable version)

| Variant | Trades | Win% | Avg/trade | PF | Equity (6 slots) | MaxDD | Sharpe |
|---|---|---|---|---|---|---|---|
| **B thr=1% (sector filter)** | 1262 | 43.8% | -0.103% | 0.83 | **-19.8%** | -21.5% | -2.23 |
| **B thr=2% (sector filter) — THE STRATEGY** | 861 | 45.8% | -0.063% | 0.90 | **-9.0%** | -13.7% | -1.02 |
| **B thr=3% (sector filter)** | 476 | 46.4% | -0.043% | 0.94 | **-3.6%** | -7.8% | -0.52 |
| A thr=2% (no sector filter) | 1024 | 47.2% | -0.040% | 0.94 | -7.1% | -14.2% | -0.66 |
| C (contrarian fade) | 1024 | 42.3% | -0.225% | 0.68 | **-32.1%** | -32.2% | -4.84 |
| NIFTY first-hour momentum | 160 | 46.9% | -0.092% | 0.64 | -2.4% | — | -2.87 |
| BANKNIFTY first-hour momentum | 150 | 44.7% | -0.072% | 0.74 | -1.8% | — | -1.89 |

**Every single configuration loses money.** Every one.

## Raw signal diagnostic (no stops, no costs)

| Config | n | Avg | Win% | t-stat |
|---|---|---|---|---|
| B thr=2% sector ALL | 861 | +0.106% | 51.1% | 1.82 (not significant) |
| **A thr=2% NO sector ALL** | 1024 | **+0.136%** | 52.6% | **2.50 (marginal)** |
| A thr=5% extreme ALL | 167 | +0.364% | 55.1% | 2.02 |
| SHORT side (all configs) | — | consistently better than LONG | — | — |

## The five brutal findings

1. **The sector rotation filter SUBTRACTS value.** A (no filter, +0.136%) beats B (with filter, +0.106%) on raw signal AND t-stat. The centerpiece of the strategy is negative alpha. Sector strength at 10:15 is already priced in by 10:15.

2. **The 2% stop loss is a wealth-destruction machine.** Raw signal +0.136% → net -0.040% after stop+cost. The stop alone costs ~8bps/trade because 2% is *inside the noise band* of these stocks (hourly ATR ~0.8-1.2%). You get stopped on noise (17-21% stop rate), then the stock finishes in your direction.

3. **Momentum direction is right, but the edge is microscopic.** The fade (Variant C) loses -0.225%/trade — worst of all — so morning moves DO continue. But +0.10-0.14% per trade is nothing. One month (Apr 2026: -26.9% trade-sum) erases three good months.

4. **Index first-hour momentum is dead on arrival.** NIFTY PF 0.64, BANKNIFTY PF 0.74. Both directions. The most liquid, popular intraday options trades (NIFTY/BANKNIFTY weeklies on morning momentum) had **zero** edge over the last year.

5. **The only whiff of signal: extreme movers (≥5%), no sector filter, no tight stop, SHORT side.** +0.364%/trade, but only 167 trades/year (0.7/day) and t=2.02 — one standard error from zero. Not a business.

## Options translation (why it's even worse than the table shows)

The table is the **underlying**. You want to trade OPTIONS on this. Add:

- **Stock option spreads on NSE: 1-5% of premium per side** (illiquid beyond the top 20 names)
- **Theta for a 5-hour hold:** 2-5% of premium (weeklies near expiry: up to 10%+)
- **STT + brokerage on premium**
- Total option friction ≈ **0.3-0.6% of underlying-equivalent per round trip**

Your best raw edge was +0.364% (extreme config). Friction eats **all of it**. The realistic strategy config (+0.106% raw) doesn't even cover the bid-ask spread. Buying options on this signal is paying the market maker for the privilege of donating theta.

## What survives (barely) — if you insist on intraday

- Drop the sector filter (it's negative alpha intraday)
- Only extreme movers ≥5% first-hour, prefer SHORT side
- No 2% stop — use 4%+ or time-stop only
- Trade FUTURES not options (friction ~0.03% vs ~0.5%)
- Expect ~+0.2-0.3%/trade, 0.7 trades/day, with -25%+ trade-sum months. Marginal at best.

## Final verdict

| Question | Answer |
|---|---|
| Does the intraday scanner strategy make money? | **NO. -9% over the year (thr=2% config).** |
| Does the sector filter help? | **NO. It subtracts alpha.** |
| Is there any raw signal? | Weak momentum continuation (+0.1%, t≈2). Not tradeable through option friction. |
| Should you buy options on morning gainers/losers? | **NO. Friction > edge, guaranteed bleed.** |
| What should you trade instead? | **Your swing scanner (v3): proven +1.4-2.0% expectancy/trade — 15-20x the intraday edge, with 1/10th the friction.** |

**Keep the intraday scanner as an information dashboard** (market sentiment, sector context, watching your swing positions). **Do not trade its output with options.**

---
*Trade logs: `results/backtest_variant_*.csv` | Backtest: `backtest_intraday.py` | Raw diagnostic: `diag_raw_signal.py`*
*Caveats: survivorship bias (today's F&O list), yfinance hourly close ≈ but ≠ official close, no half-day handling beyond bar-count filter. None of these change the sign of the result.*
