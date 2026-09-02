# PEAD + STOCK OPTIONS — BACKTEST REPORT

**Date:** 2026-07-22 | **Universe:** 210 NSE F&O stocks (optionable only) | **Period:** last 4 quarters (Jun 2025 – Jun 2026)
**Engine:** existing `backtester/engine.py` (spike >2% on results → pullback entry → target / -3% stop / D+30 time exit, no lookahead)
**Options model:** ATM monthly call (30 DTE, IV 32% post-crush), Black-Scholes repricing at exit, friction 7% of premium RT (3% spread/side + 1% costs). Lot sizes from NSE `fo_mktlots.csv`.

---

## Result 1 — The PEAD edge on the F&O universe is REAL

| Metric | Original (24 trades) | F&O universe (112 trades) |
|---|---|---|
| Trades | 24 | **112** (4.7x sample) |
| Win rate | 54.2% | 43.8% |
| Avg return | +1.71% | **+2.02%** |
| Avg winner / loser | +5.5% / -2.77% | +8.48% / -3.00% |
| Profit factor | 2.35 | **2.20** |
| **t-stat** | ~1.7 (weak) | **3.21 (SIGNIFICANT)** |
| Avg hold | — | 12.4 days |
| Trade flow | — | ~28/quarter (~2-3/week in season) |

The edge did NOT come from midcaps — it survives on optionable large/mid-caps. Win rate dropped but winners got bigger (+8.5% avg). This is a validated strategy on the underlying. **t=3.21 means this is very unlikely to be luck.**

## Result 2 — The options translation is +EV but statistically fragile

| Metric | Stock | ATM Monthly Call (net) |
|---|---|---|
| Win rate | 43.8% | 38.4% |
| Avg per trade | +2.02% | **+17.3% of premium** |
| Median per trade | -3.00% | **-48.4% of premium** |
| Avg winner / loser | +8.5% / -3.0% | +148% / **-64%** |
| Profit factor | 2.20 | 1.44 |
| **t-stat** | **3.21** | **1.43 (NOT significant)** |

By exit reason (options, net):
- Stop Loss (63 trades, 56%): **-67.3%** of premium each
- Target Hit (32 trades): +148.9%
- Time Exit (16 trades): +84.8%

Options amplify the mean 8.5x but the variance 19x (std 6.7% → 129%). The +EV is real on paper but you cannot statistically distinguish it from zero with a year of trades. The MEDIAN trade loses half its premium.

## Result 3 — The capital math (the killer)

| Item | Rs |
|---|---|
| Premium per lot (median) | **25,800** (p25 23k, p90 36k) |
| Avg loss per losing lot | **-17,762** |
| Worst single-lot loss | -43,153 |
| Best single-lot win | +159,665 |
| Max consecutive losses observed | **~8** |
| Drawdown from an 8-loss streak @ 1 lot | **~-1.4 lakh** |

**Minimum survivable capital at 1 lot/trade: ~₹3-5 lakh** (to absorb an 8-loss streak at <50% drawdown). Proper sizing (risk 2-5%/trade) needs **₹8-15 lakh**.

## Verdict

| Question | Answer |
|---|---|
| Is PEAD real on optionable NSE stocks? | **YES — +2.02%/trade, PF 2.20, t=3.21 over 112 trades** |
| Do options make it more profitable per rupee risked? | On average yes (+17.3% of premium), but t=1.43 — unproven, and median trade -48% |
| Can it be traded with ~₹50k-1L capital? | **NO. One lot = ₹26k premium, one losing streak = ruin** |
| What should be traded TODAY? | **Cash equity on PEAD picks — exactly what the scanner already does** (INDIANB is a live example) |
| When do options become viable? | Capital ≥ ₹3-5L AND another 2-3 quarters of live PEAD tracking confirming the edge |

## Result 4 — The "cheap options" test (ATM vs OTM strikes)

Question asked: some lots cost only ₹10-15k — why not filter for those?
Answer from the data: **ATM monthly lots under ₹15k don't exist (0% of 112 trades)** — NSE lot normalization keeps ATM lots at ₹21-36k. Cheap lots are structurally **OTM strikes**. So the real question is ATM vs OTM, repriced on the same 112 trades:

| Config | Median ₹/lot | Avg % | Median % | Win% | PF | t | Realistic worst streak |
|---|---|---|---|---|---|---|---|
| ATM monthly (3%/side spread) | 25,800 | +17.3 | -48 | 38.4 | 1.44 | 1.43 | 8 losses ≈ -₹1.4L |
| OTM 5% (5%/side spread) | 12,704 | +22.5 | -64 | 33.0 | 1.41 | 1.22 | 9-10 losses ≈ -₹1.1L |
| OTM 10% (6%/side spread) | 5,453 | +36.9 | **-82** | 29.5 | 1.56 | 1.28 | 12-13 losses ≈ -₹75k |

Findings:
- **OTM keeps/improves EV per rupee** (PF 1.4-1.6) — PEAD's fat right tail (+8.5% avg winners) is exactly what OTM convexity monetizes (+233% to +349% per winner)
- **But the typical trade loses 64-82% of premium** and win rate drops to ~30% — a lottery-ticket portfolio. Streaks of 12-13 losses are expected at OTM 10%, and t-stat worsens (variance grows faster than mean)
- **Capital bar drops:** OTM 10% worst-streak ≈ ₹75k → viable bankroll ~₹1.5-2L (vs ₹3-5L for ATM). Still above ~₹50k capital
- OTM stock option books are thin — modeled spreads may be optimistic; many strikes have zero bids

## The sanctioned small-capital experiment (if trying options before ₹3-5L)

The data supports a limited OTM experiment under these exact rules:
1. **OTM 5% monthly** only (not 10% — lottery territory; not weeklies — theta kills 12-day holds), premium ≤ ₹12k/lot
2. **Only R:R ≥ 2.5 setups** from the scanner (big winners fund everything)
3. **1 lot, 1 concurrent position, max ₹12-15k/month** — a tuition budget, not a profit center
4. **Check real bid-ask before entry** — skip if spread > 8% or no bids
5. Enter AFTER results only (post-IV-crush); hard stop = underlying -3% (exit the option, never hold and hope)
6. Exit by 7 DTE regardless (physical settlement + terminal theta)
7. **Kill switch: 4 consecutive losses = stop for the quarter**, log everything, reassess against this report
8. Cash equity PEAD (validated: +2.02%, t=3.21) remains the primary engine — options are the sidecar

## If/when options are used at full size (capital ≥ ₹3-5L)

1. Only Target-rich setups: R:R ≥ 2.5 (the 148% winners pay for everything)
2. ATM monthly (not weekly — theta on stops is already -67%)
3. Enter AFTER results only (post-IV-crush — never before)
4. Max 1 lot, max 2 concurrent positions, hard stop = underlying -3% (exit option, don't hold)
5. Kill switch: stop after 4 consecutive losses, reassess
6. Exit by 7 DTE regardless (physical settlement risk + terminal theta)

---
*Files: `results/backtest_2026-07-22.csv` (112 trades) · `results/options_translation.csv` (per-trade option P&L) · `analyze_options_pead.py` (ATM economics, `--iv 0.40` for high-IV names) · `analyze_cheap_options.py` (ATM vs OTM comparison) · `fno_lots.csv` (lot sizes) · `fetch_fno_list.py` (refresh F&O list)*
*Caveats: IV held constant at 32% (real IVs 25-45% by name); spreads are mid-book estimates, optimistic for illiquid OTM strikes; 4 quarters only — one earnings regime; survivorship on current F&O list.*
