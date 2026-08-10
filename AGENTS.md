# AGENTS.md — Workspace Map

Workspace root: `F:\projects\claude`
Owner: Kartik Bandewar (DevOps/SRE engineer, Pune, India)
Platform: Windows (PowerShell). Python projects use `python` (not `python3`).

This workspace holds **16 projects across 3 domains**:
1. Stock trading screeners (Python)
2. Job-hunting automation (Python + Chrome extension)
3. Restaurant POS SaaS — TableFlow (Node.js microservices)

> **Workspace layout (2026-07-18):** The root `F:\projects\claude` is a clean container — only `AGENTS.md`, `interview-prep.md`, and per-project subfolders live here. No loose project files at root. The root `.git` tracks the `earnings-momentum-scanner/` subfolder (commit `4430bda` restructured loose root files into that subfolder). The duplicate `earnings-scanner/` clone was removed (byte-identical to `earnings-momentum-scanner/`). All other project subfolders are untracked.

---

## Quick Navigation

| Project | Domain | Stack | Status |
|---|---|---|---|
| `scanner/` | Trading | Python | Active (v6.0+) |
| `scanner-v2/` | Trading | Python | Active (enhanced C&H) |
| `scanner-v3/` | Trading | Python | **Active (v3 production)** |
| `weekly-swing-setup-scanner/` | Trading | Python | Redundant — candidate for archival |
| `earnings-momentum-scanner/` | Trading | Python | Active (PEAD strategy) — tracked by root git |
| `scanner-training/` | Trading | Python | Support (validation/tuning) |
| `chart-visualizer/` | Trading | Python | Support (charts from v2 output) |
| `intraday-scanner/` | Trading | Python | **Active (intraday options — separate from swing scanners)** |
| `_old-scanner/`, `_archived/` | Trading | Python | Archived (v5.0 / v6.0 frozen) |
| `job-hunter/` | Career | Python + Chrome ext | Active (personal tool) |
| `tableflow/` | SaaS | Node.js + Docker | Flagship — 9/14 services production-ready |
| `auth-service/` | SaaS | TypeScript + Express | Standalone (may supersede tableflow's) |
| `notification-service/` | SaaS | JS + Express + Bull | Standalone (may supersede tableflow's) |
| `portfolio/` | Personal | Next.js 14 | Static site |
| `scanner-dashboard/` | Trading | Python + Next.js + Docker | **Active (v3 production dashboard)** |

---

## Domain 1 — Stock Scanners (NSE India)

All scanners target NSE (Indian stock market) swing trading setups. Data source is `jugaad-data` (NSE native) with `yfinance` fallback. Output: CSV in `results/` + optional charts + optional Telegram alerts.

### Shared conventions
- Python projects. Run from project root.
- `.env` files (90 bytes) in scanner projects contain Telegram bot tokens — **do not commit**.
- Cache: 8-hour TTL disk cache in `cache/`.
- Stock universe files: `backbone50.txt` (62 curated), `nifty500.txt`, `nifty200.txt`, or full NSE EQ list via `data/nse_eq.py`.
- Most projects **lack `requirements.txt`** — see per-project notes.

### `scanner/` — Main swing screener (v6.0+)
Modular: `engine/`, `patterns/`, `scoring/`, `portfolio/`, `utils/`, `data/`, `backtester/`.
Patterns: Cup & Handle (D/W/M), Double Bottom, Darvas Box, Flags, Breakout, Retest, Compression, Wedge, Break & Retest, Triangle, S&R, Channel. Multi-timeframe (D/W/M/4H). Sector rotation engine in `utils/sector_rotation.py`.

```powershell
# No .bat in this project — run engine directly
python engine/scanner.py
python backtest.py
python backtest_historical.py
python backtest_optimize.py
```

### `scanner-v2/` — Enhanced scanner (diagonal neckline, monthly TF, T1/T2)
Streamlined: `scanner.py`, `daily_scan.py`, `gen_charts.py`, `telegram_notify.py`, `check_perf.py`.
C&H hit rate improved 52% → 95% on 204-sample ground truth. Status tiers: WATCH / NEAR / BREAKOUT. Two targets (T1=60% of move, T2=full move).

```powershell
# Daily morning scan (sector heat + backbone 50 + hot sectors)
.\Daily Scan.bat            # runs: python daily_scan.py --top 15

# Weekly scan
.\run_weekly.bat            # runs scanner.py + gen_charts.py + telegram_notify.py

# Performance check
python check_perf.py
```

### `scanner-v3/` — Production swing scanner (v3)
Built on scanner-v2 (proven +2.7% expectancy/trade, 35% win rate, 3:1 R:R over 97 closed trades). Production swing scanner targeting NSE. **GitHub: https://github.com/karthik0419/scanner-v3**
Has `requirements.txt`, `backbone50.txt`, `nifty500.txt`, `COMPARISON_REPORT.md`. Improvements driven by performance verification of 414 picks (May-Jul 2026).

**9 key improvements over v2:**
1. **ATR-based stop loss (default)** — v2 avg SL loss was -6.5%; earnings-scanner proved -3% stops work. Tighter stops = smaller losses. (`--sl-mode atr`, original v2 stops available via `--sl-mode original`.)
2. **Double Bottom promoted** — 100% win rate (11W/0L) across scanners; score bonus 18 → 28.
3. **Channel Breakout tightened** — 24% win rate was dragging performance; volume gate 1.3x → 1.5x, RSI < 75, R:R >= 1.5.
4. **Cup & Handle (Weekly) promoted** — 50% win rate in `scanner/`; score bonus 25 → 28.
5. **Price range filter** — retail-friendly high-momentum stocks; `--min-price 100 --max-price 400`.
6. **Self-contained sector rotation** — no dependency on `scanner/`; `utils/sector_rotation_v3.py` with 568+ stock-to-sector mappings from NSE official index constituents.
7. **Bearish / short mode** — NSE Heat Map strategy: find weak sectors, short weakest stocks; `--bearish` flag.
8. **`requirements.txt`** — was missing in v2; now reproducible installs.
9. **C&H Weekly detector fixed (2026-07-17)** — was -0.56% avg P&L (losing money). Root cause: handle_bars=12 allowed 3-month downtrends as "handles". Fixed to Bulkowski's classical definition: handle_bars=4, max_depth=0.50, near_pct=0.08/0.15, handle_depth_ratio=0.50, volume_lookback=52. Now +0.76% avg P&L on 746 out-of-sample trades. Parameterized so daily/monthly detectors are unaffected.

**Additional improvements (2026-07-18):**
10. **Sector classification fixed** — was 47% wrong (14/30 scan picks misclassified). Now uses 3-layer lookup: NSE official index constituents (568 stocks) → yfinance `industry` field (granular, 80+ mappings) → yfinance `sector` field (coarse fallback). 30/30 correct on test picks. Run `python utils/build_sector_map.py` to refresh.
11. **Daily scan smart universe** — was only scanning ~600 stocks (Nifty 500 + hardcoded ~15/sector). Now scans Backbone 50 + Nifty 500 + weekly picks + ALL stocks in today's hot sectors (50-100+ per sector from NSE sector map). `--full` flag scans complete NSE EQ (~2000+). Parallel thread pool (`--workers 8`, 4-8x faster).
12. **Timeframe tracking + filter** — every pattern result now includes `timeframe` column (Daily/Weekly/Monthly). `--timeframe daily|weekly|monthly` flag filters to one timeframe for manual chart verification.
13. **Automated Telegram notifications** — scanner.py and daily_scan.py auto-send Telegram on completion. `--no-notify` to opt out.

**Backtest results (post-v3.1 fix, validated on nifty200, 2 years):**

| Version | Trades | Win rate | Avg win | Avg loss | Expectancy | PF | Max DD |
|---|---|---|---|---|---|---|---|
| v3.1 (2.0x ATR + re-entry) | 3012 | 40.6% | +7.6% | -3.0% | +1.30% | 1.73 | -60.1% |
| v3.0 (1.5x ATR, old) | 2389 | 38.0% | +9.1% | -3.4% | +1.32% | 1.62 | -73.9% |
| v2 (original stops) | 1888 | 45.4% | +6.6% | -3.4% | +1.17% | 1.64 | -61.5% |

- **v3.1 beats v2** on profit factor (1.73 vs 1.64), expectancy (+1.30 vs +1.17), and avg loss (-3.0% vs -3.4%)
- **v3.1 beats v3.0** on profit factor (1.73 vs 1.62), max drawdown (-60.1% vs -73.9%), win rate (40.6% vs 38.0%)
- v2 has higher win rate (45.4%) but lower expectancy — fewer trades, wider stops, bigger losses
- Re-entry feature: 691 trades, 49.2% win rate (highest of any pattern), +0.58% avg P&L

**v3.1 improvements (2026-07-29):**
14. **ATR multiplier 1.5x → 2.0x** — ATR sweep on backbone50 showed 2.0x has best PF (2.03 vs 1.80) and best max DD (-46.8% vs -66.7%). 1.5x was too tight, causing whipsaws without reducing losses.
15. **8% max stop cap for ALL patterns** — structural stops (C&H handle low, wedge low) can be 15-25% below entry on monthly patterns. Now capped at 8% max risk; if structural stop is wider, ATR stop used; if ATR also too wide, hard cap at 8%.
16. **Monthly C&H NEAR threshold 20% → 5%** — was surfacing stocks 20% below breakout as "NEAR" (actionable). Now only within 5% of breakout. WATCH threshold 35% → 10%. Daily/weekly already at 5%/15%.
17. **T1 target 60% → 50% of measured move** — full measured-move target is too ambitious for swing trades (often 20-50% away). 50% is more realistic.
18. **Max risk filter (10%)** — picks with >10% stop loss from CMP are rejected entirely.
19. **Max distance filter (8%)** — NEAR/WATCH picks >8% from breakout are rejected (only BREAKOUT picks exempt).
20. **R:R from breakout entry, not CMP** — R:R now calculated from the breakout price (where you'd actually enter), not CMP (which may be below breakout for NEAR picks). Prevents misleading R:R ratios.
21. **Wide-stop R:R penalty** — R:R halved for >8% risk, 20% penalty for >6% risk.
22. **Re-entry after whipsaw** — if a trade hits SL but the stock recovers above the breakout level within 30 days, re-enter with a tight 2% stop. 49.2% win rate on re-entries (highest of any pattern). In paper tracker, stopped-out trades auto-check for re-entry on each update.
23. **Paper tracker: NEAR picks wait for breakout** — NEAR picks no longer entered at CMP (below breakout). They start as WAITING_BREAKOUT and only enter when price crosses the breakout level. This was the root cause of the 83% stop-out rate on the 2026-07-17 batch.
24. **`--stocks` flag** — scan a custom stock list file (e.g. `--stocks nifty200.txt`) instead of full NSE EQ universe. Faster for testing.
25. **Whipsaw analysis tool** (`whipsaw_analysis.py`) — checks how many SL exits would have hit target if held. Finding: 16.3% of SL exits are whipsaws (stock hit SL, then reached T1 within 30 days). 81% went lower before recovering (wider stop wouldn't help).

```powershell
pip install -r requirements.txt

# Full weekly scan (top 30 setups)
python scanner.py

# Top 50, min score 50
python scanner.py --top 50 --min-score 50

# Retail filter: only stocks between 100-400 Rs
python scanner.py --min-price 100 --max-price 400

# Custom stock list (faster than full universe)
python scanner.py --stocks nifty200.txt --min-price 100 --max-price 400

# Original v2 stop loss (wider, for comparison)
python scanner.py --sl-mode original

# Bearish scan: find short setups in weak sectors
python scanner.py --bearish

# Quick test (50 stocks only)
python scanner.py --test

# Daily morning scan (smart universe: Backbone + Nifty500 + hot sector stocks)
python daily_scan.py --top 15

# Daily scan - full NSE EQ universe (~2000+ stocks, ~10-15 min)
python daily_scan.py --full --workers 10

# Daily scan with price filter
python daily_scan.py --min-price 100 --max-price 400

# Daily bearish scan
python daily_scan.py --bearish

# Scan by timeframe (for manual chart verification)
python scanner.py --timeframe weekly    # weekly patterns only
python scanner.py --timeframe daily     # daily patterns only
python scanner.py --timeframe monthly   # monthly patterns only

# Refresh sector mapping (run monthly to pick up new IPOs)
python utils/build_sector_map.py

# Weekly scan + charts + Telegram
.\run_weekly.bat

# Daily scan
.\Daily Scan.bat

# Backtest v3 vs v2 comparison (backbone50, ~5 min)
python compare_backtest.py --stocks backbone50.txt --years 2 --min-score 40

# Backtest on nifty200 (out-of-sample, ~15 min)
python compare_backtest.py --stocks nifty200.txt --years 2 --min-score 40

# Paper tracker — track live picks vs backtest expectancy
python paper_tracker.py init                              # init from latest scan CSV
python paper_tracker.py update                            # fetch prices, update status, auto re-entry check
python paper_tracker.py update --price NATCOPHARM.NS=980  # manual price override
python paper_tracker.py status                            # full status + closed trades summary
python paper_tracker.py summary                           # one-line summary
python paper_tracker.py reset                             # delete tracker (careful)

# Analysis tools (v3.1)
python whipsaw_analysis.py                                # find SL exits that would have hit target
python sweep_atr.py                                       # ATR multiplier sweep (1.0x-3.0x)
python final_comparison.py                                # v3.1 vs v3.0 vs v2 comparison
```

**Paper tracker statuses (v3.1):**
- `WAITING_BREAKOUT` — NEAR pick, not yet entered. Waiting for price to cross breakout level.
- `OPEN` — active trade (BREAKOUT pick entered at CMP, or NEAR pick entered after breakout confirmed).
- `WIN_T1` — price hit Target 1, position still open for T2.
- `WIN_T2` — price hit Target 2, trade closed.
- `LOSS` — stop loss hit, trade closed. Tracker auto-checks for re-entry on next update.
- `RE_ENTERED` — stock recovered above breakout after SL hit, re-entered with tight 2% stop.
- `TIME_EXIT` — held 45 days without hitting SL or target, closed at current price.
- `WATCH` — WATCH status pick, not traded (too far from breakout at scan time).

**Re-entry feature:**
When a trade hits stop loss, the tracker remembers the breakout level. On each `update`, it checks if the stock has recovered above that breakout level within 30 days. If yes, it re-enters the trade with a tight 2% stop (below the breakout level). This captures whipsaw recoveries — stocks that got shaken out then continued to target. Backtest shows 49.2% win rate on re-entries (highest of any pattern).

```
Example paper tracker update output:
  [BREAKOUT] SCI.NS broke out to 281.50 >= 280.50 — entered
  [RE-ENTRY] BANDHANBNK.NS recovered to 248.20 >= breakout 246.00
  Updated 18 open trades.
```

**Key files:**
- `scanner.py` — main weekly scanner (v3.1 engine, 2.0x ATR, 8% stop cap, re-entry)
- `daily_scan.py` — daily morning scanner (volume + sectors, 2.0x ATR, 8% stop cap)
- `gen_charts.py` — chart generator (daily/weekly/monthly per pick)
- `telegram_notify.py` — Telegram alerts (top 10 picks)
- `paper_tracker.py` — paper trade tracker (NEAR waits for breakout, auto re-entry after SL)
- `compare_backtest.py` — v3.1 vs v2 side-by-side backtest comparison
- `backtest.py` — standalone v3.1 backtest (with re-entry logic)
- `whipsaw_analysis.py` — find SL exits that would have hit target if held
- `sweep_atr.py` — ATR multiplier sweep (1.0x, 1.5x, 2.0x, 2.5x, 3.0x)
- `final_comparison.py` — v3.1 vs v3.0 vs v2 comparison report
- `COMPARISON_REPORT.md` — full backtest results + pattern breakdown
- `backbone50.txt` — 51 curated momentum stocks (in-sample)
- `nifty200.txt` — 200 large-cap stocks (out-of-sample test set)
- `config/settings.py` — configuration constants
- `utils/sector_rotation_v3.py` — self-contained sector rotation (bullish + bearish)

**Momentum continuation strategy — NOT RECOMMENDED (validated 2026-08-03):**
A "momentum continuation" strategy (uptrend 30%+ in 6mo, pullback 5-10% from 50-day high, volume surge 2-10x, daily gain 2%+, entry at next-day open, 2x ATR stop capped at 8%, target = 50-day high) was backtested and rejected after full validation. Files: `backtest_momentum.py`, `portfolio_sim.py`, `analyze_sector_momentum.py`, `analyze_regime_filter.py`. Results across 60 months / 5 years on full NSE EQ (~2000 stocks) with Rs 50,000 capital, realistic fees (0.03% brokerage + 0.025% STT + 0.1% slippage), next-day entry, liquidity filter:

| Config | Trades | Final | Return | CAGR |
|---|---|---|---|---|
| MULTI (4 positions, no filter) | 673 | Rs 19,089 | **-61.8%** | -17.5% |
| ALL-IN (1 stock at a time) | 197 | Rs 9,385 | **-81.2%** | -28.5% |
| Top 5 sectors + BULL regime (SMA50+200) | 93 | Rs 63,482 | +27.0% | +4.9% |
| **Bank FD (7% annual)** | — | **Rs 67,500** | **+35.0%** | **+7.0%** |

The 6-month test showed +15.9% (MULTI) / +49.7% (ALL-IN) — but this was regime luck. Over 5 years the strategy loses money. Root cause: avg loss (-7.7%) > avg win (+6.2%), 51.3% win rate (barely above coin flip). Sector filtering (Auto/Media/Telecom/Energy/Chemicals profitable; Infra/Realty/Textiles/Banking bleeders) and regime filtering (Nifty > SMA50+SMA200, real-time no look-ahead) save it from blowing up but still underperform a bank FD. **Do NOT implement. v3.1 (pattern-based, +1.30% expectancy, PF 1.73, avg loss -3.0%) remains the production edge.**

**Position sizing + regime/sector filter backtest (2026-08-05):**
3-year backtest on 181 stocks (backbone50 + nifty200) with REAL v3.1 engine (all 15 pattern detectors, ATR stops, re-entry) testing 4 filter combinations × 8 position sizing strategies = 32 configurations. Files: `_backtest_sizing_3yr.py`, `_backtest_full_3yr.py`, `_backtest_winning_detailed.py`, `_optimize_sizing.py`, `_portfolio_sim_10lakh.py`.

Key lesson: **Simplified patterns (3 detectors) lose -47.7%; full v3.1 (15 detectors) gains +15.4%.** The 12 additional pattern detectors (channels, triangles, Darvas, flags, S&R, break-retest, compression) provide the real edge. Never backtest with simplified patterns.

WINNING STRATEGY: **Regime filter (Nifty > SMA50+SMA200) + Sector filter (top 5 hot sectors) + Equal weight sizing + 17 max positions.**

| Config | Trades | Win% | Return | CAGR | Max DD | PF | Sharpe |
|---|---|---|---|---|---|---|---|
| **Regime+Sector + Equal** | 431 | 37.8% | **+16.5%** | **+5.2%** | **-2.7%** | **1.56** | — |
| Baseline (no filter) + Equal | 1192 | 36.7% | +15.4% | +4.9% | -13.4% | 1.49 | — |
| Regime only + Equal | 607 | 35.3% | +5.7% | +1.9% | -6.0% | 1.42 | — |
| Sector only + Top8 | 710 | 35.5% | +14.6% | +4.6% | -10.6% | 1.35 | — |

Detailed breakdown of winning strategy (431 trades, 3 years):
- Year-by-year: 2024 +7.4% (226 trades), 2025 +15.9% (173 trades), 2026 +16.5% (32 trades) — profitable every year
- Best month: Jun 2025 +7.0% (76.5% win rate); Worst: Mar 2024 -1.82%
- By pattern: Cup & Handle 78% of trades, +Rs 19,847 profit (workhorse); Re-entry 13 trades, 46.2% WR, +1.43% avg
- By exit: Time Exit (45d) +8.13% avg (93.8% WR), Target 1 +5.92% (89.2% WR), Target 2 +4.34% (80% WR), Stop Loss -3.2% avg
- By sector: Infra +Rs 5,289, Auto +Rs 3,746, Pharma +Rs 3,557 (best); PSU Bank -Rs 1,120 (worst, 22% WR)
- Max drawdown only -2.7% (43-day period Apr-Jun 2025); 6 DD periods >1% in 3 years
- Avg win +7.5%, avg loss -2.8% (2.7x asymmetric R:R); avg days held 15; best trade BEL.NS +34.8%

Position sizing findings:
- **Equal weight is BEST** (+16.5% with regime+sector). Fancy sizing (score-weighted, R:R-weighted, momentum-weighted) all performed WORSE.
- **Concentration (Top 5/8/10) does NOT help** — more concentration = bigger drawdowns, no return improvement.
- **Risk-parity has lowest drawdown** (-1.5% with regime+sector) but lower return (+9.0%). Use for capital preservation.
- **R:R-weighting is the WORST** — it over-allocates to high-risk setups that often stop out.
- **Momentum-weighting (4-day test "winner") is misleading** — over 3 years it's 5th worst (-46.9% without filters). Chasing recent winners = buying at peaks.

**Current regime: BEAR** (Nifty 24,625 below SMA200 24,772 as of Aug 5, 2026). Backtest shows regime filter is critical — BEAR regime trades have lower returns and higher drawdowns. Consider smaller position sizes or wait for Nifty to recover above 24,772.

**Paper tracker status (Aug 5, 2026):** 31 picks total, 23 open trades (20 in profit, 0 losses), 7 waiting breakout, 1 win (SPANDANA at T1). Avg P&L +2.72%, best NAZARA +10.73%, GENESYS re-entry +10.03% in 2 days (validates whipsaw recovery). TECHM.NS added (real buy at Rs 1,589, now +3.84%, 20 shares). Waiting list: TATAPOWER (-0.62% from BO), KANSAINER (-1.11%, +5.76% today on 4.6x vol), SAPPHIRE (-1.24%, +5.31% today on 6.1x vol) — closest to breakout.

**Chart image analysis — vision model (2026-08-05):**
Claude Sonnet 4.6 1M (current Devin CLI model) supports image viewing via the `read` tool on local image files. Save screenshots to disk, provide the file path. For other vision models: Claude 3.5 Sonnet / Opus (claude.ai), GPT-4o (ChatGPT), Gemini 1.5 Pro (Google AI Studio).

**Lessons learned from 8 TradingView chart screenshots (2026-08-05) — techniques NOT yet in v3.1:**

1. **"% of measured move done" progress tracker** — chart author annotates "20% Move Done, 20% Left" / "15% Move Done 15% Left" / "35% Up From Our Zone". For every open trade and NEAR pick, calculate: `pct_done = (cmp - breakout) / measured_move * 100` and `pct_left = 100 - pct_done`. This tells you how much upside remains. **TODO: add to paper tracker update output and Telegram alerts.**

2. **Historical resistance as target (not just measured move math)** — Deep Industries target was "600 to 640" = prior resistance zone from Nov 2024 highs, NOT the formula `breakout + (breakout - cup_low)`. When prior resistance is clearly visible, use it as the target instead. **TODO: in scoring, check if a prior resistance zone exists near the measured-move target — if yes, use the zone as T2 (more realistic); if resistance is BELOW measured move, use resistance as T1.**

3. **Double confirmation — Channel + S&R zone breakout simultaneously** — Tilaknagar broke above BOTH the descending channel upper trendline AND a flat horizontal S&R zone (440 band) on the same candle. This is a stronger signal than either alone. Current v3.1 only returns the first matched pattern. **TODO: detect when channel + S&R breakout coincide (within 2% of each other) and add a "double breakout" bonus (+15 score) to both.**

4. **"Breakout Sustained" confirmation** — Tilaknagar chart explicitly labeled "Breakout Sustained" after the stock held above the breakout zone for 2+ weeks. Current v3.1 enters on the breakout candle. **TODO: in paper tracker, add a SUSTAINED flag when an OPEN trade has been above its breakout level for ≥10 trading days — these have higher follow-through probability.**

5. **Nested / multi-scale cup patterns** — Deep Industries shows a large weekly cup (Nov 2025 - May 2026, ~320 bottom) with a smaller secondary cup (handle region) forming within the right side of the larger cup. This nested structure means the smaller cup breakout is the actual entry trigger for the larger cup's measured move. Current v3.1 sweeps multiple cup lengths but doesn't explicitly detect nesting. **TODO: if two cup lengths are detected on the same stock (e.g., 120-bar and 40-bar), flag as NESTED and boost score +10.**

6. **Monthly C&H neckline = horizontal flat line at prior ATH** — Nazara and Thyrocare both show the neckline drawn as a FLAT horizontal line at the prior cycle peak, not a diagonal. This is the classical Bulkowski definition. v3.1's monthly C&H already uses linear regression on left/right thirds — verify the neckline approximates horizontal for monthly patterns. A near-horizontal neckline (slope < 5%) should add +5 score.

7. **Target annotation style for Telegram** — The charts annotate targets as "X to Y" range (e.g., "600 To 640", "264.15 To 330.95") showing both T1 and T2 together. Current Telegram output shows T1 and T2 separately. **TODO: format Telegram alerts as "Target: Rs 595 to Rs 679" on one line.**

8. **Upside % remaining drives conviction** — "20% Left" vs "35% Up From Zone" changes the decision (enter vs hold vs skip). Stocks with >15% remaining measured move = more conviction to enter. Stocks with <8% remaining = skip or hold only. **TODO: add `upside_remaining_pct` to scanner output and filter: skip NEAR picks if upside remaining < 10%.**

Stocks from charts: NAZARA (tracker, hold), THYROCARE (near BO at 617, weekly C&H, Pharma RISING), TI/Tilaknagar (near BO at 511, daily C&H score 72, double confirmation), FSL/Firstsource (already ran +27%), DEEPIND (already ran +35% — case study). TI.NS ticker = `TI.NS` on Yahoo Finance.

### `weekly-swing-setup-scanner/` — Simplified weekly scanner
Subset of scanner-v2: no monthly TF, no WATCH tier, no diagonal neckline, single target. **Candidate for archival** — no unique features vs scanner-v2.

```powershell
.\run_weekly.bat            # runs scanner.py + gen_charts.py + telegram_notify.py
```

### `earnings-momentum-scanner/` — PEAD / post-earnings momentum (v3)
Different strategy: scans for post-earnings pullback entries. Uses `screener.in` for earnings data + `scipy` for profit projection. Modes: weekly (588 stocks), discovery (2131 stocks, ~90 min), daily (top sectors + backbone). **Has `requirements.txt`.** This is the project tracked by the root git repo (remote: `karthik0419/earnings-momentum-scanner`).

**F&O options backtest (2026-07-22, see `OPTIONS_PEAD_REPORT.md`):** PEAD edge VALIDATED on the optionable F&O universe — 112 trades, +2.02%/trade, PF 2.20, **t=3.21 (significant)**, ~28 trades/quarter, 12.4-day avg hold. Options translation (ATM monthly calls, BS-repriced, 7% premium friction): +17.3% of premium avg but t=1.43 (not significant), median trade -48%, stops cost -67% of premium, max ~8 consecutive losses. **Capital verdict: ATM options need ≥₹3-5L to survive variance (median premium ₹26k/lot, avg losing lot -₹18k). Below that capital: trade PEAD in cash equity only.** OTM test ("cheap lots"): ATM lots under ₹15k don't exist (NSE lot normalization) — cheap lots are OTM strikes. OTM 5%/10% keep PF (1.4-1.6, convexity monetizes PEAD's fat right tail) but median trade loses 64-82% and win rate drops to ~30%; viable bankroll drops to ~₹1.5-2L. Sanctioned small-capital experiment rules in the report (OTM 5% monthly, 1 lot, R:R≥2.5 only, ₹12-15k/month cap, 4-loss kill switch). Key files: `fetch_fno_list.py` (F&O universe + lot sizes), `fno_list.txt`, `fno_lots.csv`, `analyze_options_pead.py` (ATM economics), `analyze_cheap_options.py` (ATM vs OTM).

```powershell
cd earnings-momentum-scanner
.\run_scanner.bat           # interactive: 1=weekly, 2=discovery, 3=daily
python scanner.py --mode weekly --top 30 --min-score 35 --delay 2.0 --workers 6
python scanner.py --mode discovery --top 50 --min-score 40 --delay 2.5 --workers 4
python scanner.py --mode daily --top 20 --min-score 40 --delay 1.0 --workers 8

.\run_backtest.bat          # backtester
python test_pipeline.py     # end-to-end smoke test

pip install -r requirements.txt
```

### `scanner-training/` — Pattern validation & tuning
Parses Telegram trade-chat HTML export (`E:/TRADE TEam CHAT`) into ground truth, validates tuned detectors vs production, gap analysis. Tuned patterns in `tuned_patterns/` feed back into `scanner/` and `scanner-v2/`. Sector rotation engine was built here.

```powershell
python scripts/parse_telegram.py
python scripts/extract_setups.py
python scripts/validate_tuned.py
```

### `chart-visualizer/` — Standalone chart generator
Reads scanner-v2 CSV output, produces annotated candlestick charts (Daily 120 bars / Weekly 60 bars) with pattern overlays. **Has `requirements.txt`.**

```powershell
.\run_visualizer.bat
python visualize.py
pip install -r requirements.txt
```

### `intraday-scanner/` — Intraday options scanner (separate from swing)
**Different purpose from scanner-v3.** This pulls LIVE NSE market data for intraday OPTIONS trading, not swing setups. No daily/weekly pattern detection — just real-time market data + sector rotation + F&O gainers/losers for intraday decisions.

Pulls from NSE official API (`https://www.nseindia.com/api/...`):
1. Broad market indices (NIFTY/BANKNIFTY/MIDCAP/IT/AUTO) with advance/decline
2. **Sectoral indices (19 sectors) ranked by % change** — intraday sector rotation
3. Top F&O gainers/losers (filtered to stocks with exchange-traded options)
4. Volume toppers (institutional activity)
5. Pre-open session data (morning sentiment)
6. **Trade plan** — combines sector strength with stock gainers/losers to highlight high-conviction call/put candidates

Does NOT predict. Surfaces the same data intraday traders look at on NSE's website, in one place + filtered to F&O stocks.

```powershell
cd intraday-scanner
python intraday_scanner.py                  # top 15 per category
python intraday_scanner.py --top 20         # top 20 per category
python intraday_scanner.py --no-sectors     # skip sector breakdown
```

**How to use:**
- Check market sentiment (NIFTY A/D ratio) — bearish = put bias, bullish = call bias
- Check sector rotation — strongest sectors = call option bias, weakest = put bias
- High-conviction calls = gainers in STRONG sectors with turnover >100cr
- High-conviction puts = losers in WEAK sectors with turnover >100cr
- ALWAYS check option chain OI before entering
- Strict stop losses (2-3% max for intraday options)
- Exit before 3:15 PM

**⚠️ BACKTESTED 2026-07-22 — STRATEGY DOES NOT WORK FOR TRADING (see `BACKTEST_REPORT.md`):**
365-day backtest (241 days, 116 F&O stocks, hourly bars, no lookahead): every configuration LOSES money after stops+costs (best: -3.6%, strategy config: -9.0%, Sharpe -1.02). Key findings: (1) the sector filter SUBTRACTS alpha intraday, (2) 2% stops are inside the noise band and destroy the weak edge, (3) raw momentum continuation exists (+0.1%/trade, t≈2) but is smaller than option friction (~0.3-0.6% underlying-equivalent), (4) NIFTY/BANKNIFTY first-hour momentum has zero edge (PF 0.64/0.74). **Use as an information dashboard only — do NOT trade its output with options. Swing scanner-v3 has 15-20x the per-trade edge.**

**Key files:**
- `intraday_scanner.py` — main scanner (single file, no dependencies beyond requests/pandas)
- `backtest_intraday.py` — 365-day backtest (variants A/B/C + indices), 24h data cache
- `diag_raw_signal.py` — raw signal diagnostic (no stops/costs, t-stats)
- `BACKTEST_REPORT.md` — full verdict with numbers
- `README.md` — usage guide

### `_old-scanner/`, `_archived/` — Archived versions
Frozen v6.0 and v5.0. Reference only. Do not modify.

---

### `scanner-dashboard/` — Full-stack web dashboard for scanner-v3 (production)

Built on scanner-v3 (proven +1.30% expectancy/trade engine). Full-stack web app: FastAPI backend + Next.js frontend + arq worker + PostgreSQL + Redis, fully containerized with Docker Compose. **GitHub: https://github.com/karthik0419/scanner-dashboard**

**Architecture (5 Docker containers):**

| Container | Image | Port | Purpose |
|---|---|---|---|
| `postgres` | postgres:16-alpine | 5433 | Database (scans, picks, users, alerts, tracker) |
| `redis` | redis:7-alpine | 6380 | Task queue (arq jobs) |
| `backend` | scanner-dashboard-backend | 8000 | FastAPI REST API (auth, scans, picks, screens, tracker, market, charts) |
| `worker` | scanner-dashboard-worker | — | arq worker (runs scanner.py as subprocess, killable) |
| `frontend` | scanner-dashboard-frontend | 3001 | Next.js 14 dashboard (light theme, Stripe/Notion style) |

**Key features:**
- **7 one-click scan presets** (matching .bat menu): Smart Daily, Full + Price Filter, Full NSE, Daily Patterns, Weekly Patterns, Bearish, Quick Test
- **PEAD scanner** — Post-Earnings Announcement Drift scanner integrated (4 presets: Weekly, Daily, Discovery, High Conviction). Scans screener.in for earnings setups. Separate API at `/api/pead/`.
- **Custom scan form** — top, min score, SL mode (ATR/original), price range, stock list (Backbone 50, Nifty 500), timeframe, smart/bearish/test toggles
- **Kill/cancel running scans** — kills scanner.py subprocess without killing the worker (fixed `taskkill /F /PID` without `/T`)
- **Scan results** — same picks as local .bat (verified identical: same stocks, scores, patterns, R:R, targets)
- **Paper tracker** — track live picks, auto-update prices, re-entry after whipsaw
- **Saved screens** — save/load custom filter combinations
- **Market overview** — sector heat map, breadth indicators
- **Collapsible sidebar** — click chevron to expand/collapse, persists to localStorage, hover to reveal toggle
- **Per-page instructions** — collapsible/dismissible help banners on all 7 dashboard pages (Overview, Scans, PEAD, Screens, Tracker, Market, Settings). Persists dismissal to localStorage.
- **Guest login** — auto-created guest user (guest@guest.com / guest) on backend startup. "Try as Guest" button on login page for anyone to explore without registering.
- **Auth** — JWT-based, register/login, per-user data isolation
- **Light theme UI** — white backgrounds, indigo accents, accessible (aria-labels, keyboard nav, focus rings)
- **Auto-restart** — all 3 app containers have `restart: unless-stopped`
- **Worker health endpoint** — `GET /api/scans/health/worker` checks if arq worker is alive via Redis
- **scanner-v3 + earnings-momentum-scanner baked into image** — no external folder mount needed, fully self-contained

**Scanner engine integration:**
- Backend runs `scanner.py` as a subprocess (same as .bat files)
- `--no-notify --no-sync` flags added (dashboard handles notifications/tracker separately)
- `--sl-mode atr` explicitly passed (same as scanner-v3 default)
- scanner-v3 source code is copied into the Docker image at build time (`COPY scanner-v3 /scanner-v3`)
- Results CSV parsed and stored in PostgreSQL as individual Pick records

**Docker Compose commands:**
```powershell
cd F:\projects\claude\scanner-dashboard

docker compose up -d              # Start all 5 containers
docker compose down               # Stop all 5 containers
docker compose restart            # Restart all containers
docker compose logs -f backend    # Watch backend logs
docker compose logs -f worker     # Watch worker logs
docker compose ps                 # See running containers
docker compose build              # Rebuild images after code changes
docker compose up -d --build      # Rebuild + restart
```

**Or just double-click `start-all.bat`** — runs `docker compose up -d` and shows status.

**To deploy on another laptop:**
1. Install Docker Desktop
2. Copy `scanner-dashboard/` folder
3. Run `docker compose up -d`
4. Open `http://localhost:3001/login`

**Login:** `kartik@scanner.io` / `kartik` (or register a new account)

**Key files:**
- `docker-compose.yml` — 5-container orchestration (postgres, redis, backend, worker, frontend)
- `backend/Dockerfile` — Python 3.11 + FastAPI + scanner-v3 + earnings-momentum-scanner baked in
- `frontend/Dockerfile` — Node 20 + Next.js 14 (multi-stage build)
- `backend/app/main.py` — FastAPI app entry point
- `backend/app/routers/scans.py` — scan trigger, list, detail, cancel, worker health
- `backend/app/routers/pead.py` — PEAD scan trigger, list, detail, cancel, picks
- `backend/app/routers/picks.py` — pick listing + stats
- `backend/app/routers/tracker.py` — paper trade tracker
- `backend/app/routers/screens.py` — saved screens
- `backend/app/routers/market.py` — market overview
- `backend/app/routers/charts.py` — chart generation
- `backend/app/routers/auth.py` — JWT auth
- `backend/app/services/scanner_service.py` — scanner.py + PEAD scanner.py subprocess runner
- `backend/app/services/worker.py` — arq worker (run_scan_job + run_pead_scan_job)
- `backend/app/models.py` — SQLAlchemy models (Scan, Pick, PeadScan, PeadPick, User, Alert, SavedScreen, PaperTrade)
- `frontend/app/dashboard/layout.tsx` — collapsible sidebar layout
- `frontend/app/dashboard/scans/page.tsx` — scans page with 7 presets + custom form + kill button
- `frontend/app/dashboard/pead/page.tsx` — PEAD scanner page with 4 presets + picks table
- `frontend/lib/api.ts` — API client (typed, all endpoints including PEAD)
- `frontend/tailwind.config.ts` — light theme design system
- `start-all.bat` — one-click Docker Compose startup

**Tech stack:**
- Backend: Python 3.11, FastAPI, SQLAlchemy, arq, PostgreSQL, Redis, JWT, bcrypt
- Frontend: Next.js 14, TypeScript, Tailwind CSS, Lucide icons, Sonner toasts
- Infra: Docker Compose, 5 containers, auto-restart, health checks
- Scanner: scanner-v3 (v3.1 engine, 2.0x ATR, 8% stop cap, re-entry)

**Docker image optimization (2026-08-07):**
- Frontend: 709MB → 224MB (68% smaller) — Next.js standalone output mode, multi-stage build, no node_modules in runtime
- Backend/Worker: 1.15GB → 784MB each (32% smaller) — multi-stage build, Python venv copied from builder, no gcc/g++/dev headers in runtime
- Total: 3.0GB → 1.79GB (40% reduction)
- Health checks on all 5 containers (backend /api/health, worker arq import check, frontend node http check, postgres pg_isready, redis ping)
- Memory limits: postgres 512M, redis 128M, backend 512M, worker 1G, frontend 256M
- Frontend depends_on backend with `condition: service_healthy`

**Disk cleanup (2026-08-07):**
- Docker WSL2 disk moved to D:\DockerData (via symlink from C: → D:)
- Downloads folder moved to D:\Downloads (via junction point)
- Android SDK deleted (not in use)
- Docker build cache cleaned (12.3 GB freed)
- C: drive freed: 40.8 GB → 75.5 GB free (+34.7 GB)

**Paper tracker status (2026-08-07):**
- 31 total picks, 21 open trades, 7 waiting for breakout
- 17/21 in profit, avg P&L +2.48%, total P&L +52.05%
- Best: NAZARA.NS +12.02%, Worst: FEDERALBNK.NS -1.44%
- 1 win (SPANDANA.NS T1 hit), 2 losses (RECLTD -2.41%, GENESYS -3.86%)
- Closest to breakout: KANSAINER.NS (-0.76%), TATAPOWER.NS (-1.76%), ZOMATO.NS (-2.27%)

**Phone/LAN login fix (2026-08-09):**
- **Symptom:** login from phone (same WiFi, PC LAN IP `192.168.1.10:3001`) failed; appeared to work on desktop only.
- **Root cause:** Next.js bakes `rewrites()` into `routes-manifest.json` at **build** time. `frontend/next.config.js` resolves the `/api/*` proxy destination as `process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`. During `docker build`, only `NEXT_PUBLIC_API_URL` was a build arg — `API_URL` was unset in the builder stage, so the fallback `http://localhost:8000` got frozen into the manifest. At runtime the compose `environment:` sets `API_URL=http://backend:8000`, but that's too late. Every proxied `/api/*` call hit `localhost:8000` inside the container → `ECONNREFUSED 127.0.0.1:8000` → 500. This actually broke login from **all** devices (desktop too); the phone was just where it was first noticed.
- **Fix:** `frontend/Dockerfile` — added `ARG API_URL=http://backend:8000` + `ENV API_URL=$API_URL` in the **builder** stage so `next.config.js` reads it during `next build`. Removed the stale runtime `ENV NEXT_PUBLIC_API_URL=http://localhost:8000` (no-op for the client bundle; only caused confusion). `docker-compose.yml` — added `API_URL: http://backend:8000` to the frontend service's `build.args`.
- **Verified:** `routes-manifest.json` now shows `destination: http://backend:8000/api/:path*`. Login 200 from both `localhost:3001` and `192.168.1.10:3001`; `/api/auth/me` with bearer token 200 from LAN IP. Frontend logs clean (no ECONNREFUSED).
- **Reusable lesson:** Next.js `rewrites()` destinations are baked at **build** time. Any env var the `rewrites()` function reads must be a Docker `ARG`/`ENV` in the **builder** stage — compose `environment:` at runtime is too late. A baked `localhost` destination is the classic "works on desktop, breaks on phone/LAN" trap.
- **Session log:** `scanner-dashboard/SESSION_LOG.md` (full investigation trace).

---

## SwingIQ Naming Map (2026-08-09)

**SwingIQ** is the product/channel name. The code projects still use their
original folder/repo names (`scanner-v3`, `earnings-momentum-scanner`,
`scanner-dashboard`). This map clarifies which project does what, which
Telegram bot each uses, and where to make changes.

### Two Telegram bots

| Bot | .env file | Chat ID | Purpose |
|---|---|---|---|
| **SwingU** | `scanner-v3/.env` (default) | `1121884245` (private chat) | **Testing** — manual CLI runs (`python daily_scan.py`) |
| **SwingIQ** | `scanner-v3/.env.swingiq` | `-1004275742331` (channel) | **Production** — automated cron scans (Task Scheduler) |

`auto_daily_scan.bat` / `auto_weekly_scan.bat` swap `.env` → SwingIQ before
running, then restore SwingU after. So:
- You typing in terminal → message goes to **SwingU** (private)
- Cron/Task Scheduler → message goes to **SwingIQ** (channel)

### Where each project fits

| Project | Folder | What it does | Telegram header | Bot | Rebranded? |
|---|---|---|---|---|---|
| scanner-v3 (daily) | `scanner-v3/` | Daily morning scan (volume + sectors) | `📊 SwingIQ Daily Scan` | SwingU/SwingIQ (swapped) | **Yes** (2026-08-09) |
| scanner-v3 (weekly) | `scanner-v3/` | Weekly swing setup scan (patterns) | `📊 SCANNER v3.1` | SwingU/SwingIQ (swapped) | **No** — still old name |
| earnings-momentum-scanner | `earnings-momentum-scanner/` | PEAD scanner (post-earnings drift) | `EARNINGS MOMENTUM SCANNER` | Unknown (separate .env?) | **No** |
| scanner-dashboard | `scanner-dashboard/` | Web UI (Next.js + FastAPI + Docker) | N/A (has own Telegram settings) | N/A | **No** (no SwingIQ branding in UI) |

### Where to make changes (cheat sheet)

| You want to change... | Edit this file | In this project |
|---|---|---|
| Daily scan Telegram format | `scanner-v3/daily_scan.py` (`_fmt_pick`, `_build_telegram_summary`) | scanner-v3 |
| Daily scan header text | `scanner-v3/daily_scan.py` (line ~826, `header = f"📊 SwingIQ Daily Scan..."`) | scanner-v3 |
| Weekly scan Telegram format | `scanner-v3/telegram_notify.py` (`format_message`) | scanner-v3 |
| Weekly scan header text | `scanner-v3/telegram_notify.py` (line ~98, `SCANNER v3.1`) | scanner-v3 |
| Which bot the cron uses | `scanner-v3/.env.swingiq` (token + chat ID) | scanner-v3 |
| Which bot manual CLI uses | `scanner-v3/.env` (token + chat ID) | scanner-v3 |
| Cron schedule | Windows Task Scheduler → see cron table below | scanner-v3 |
| Dashboard web UI | `scanner-dashboard/frontend/app/` (Next.js pages) | scanner-dashboard |
| Dashboard API | `scanner-dashboard/backend/app/` (FastAPI routers) | scanner-dashboard |
| Dashboard Telegram settings | `scanner-dashboard/frontend/app/dashboard/settings/page.tsx` | scanner-dashboard |
| PEAD scanner format | `earnings-momentum-scanner/scanner.py` | earnings-momentum-scanner |

### Cron jobs (Windows Task Scheduler)

| Task name | Schedule | Runs | Bot | Status |
|---|---|---|---|---|
| `SwingIQ_DailyScan` | Daily 08:30 IST | `scanner-v3\auto_daily_scan.bat` → `python daily_scan.py --top 15` | SwingIQ (swapped via .bat) | **Active** — last ran 10 Aug, result 0 (success) |
| `SwingIQ_WeeklyScan` | Saturdays 09:00 IST | `scanner-v3\auto_weekly_scan.bat` → `python scanner.py` | SwingIQ (swapped via .bat) | **Active** — first run Sat 15 Aug |

**Deleted (2026-08-09):** `NSE Swing Screener` (Mon-Fri 08:30) — stale task
from May 2026 pointing to dead path
`C:\Users\91814\Desktop\claude\enhanced-swing-trading-screener\run_screener.bat`
(workspace migrated to `F:\projects\claude\` in Jul 2026). Was failing silently
every weekday with result code 1 (file not found). Fully replaced by
`SwingIQ_DailyScan`.

**Power management note:** Both tasks have "Stop On Battery Mode, No Start On
Batteries" enabled — they will NOT run if the laptop is on battery. Keep it
plugged in for the 08:30 daily scan to fire.

**To manage cron jobs:**
```powershell
# View tasks
schtasks /query /tn "\SwingIQ_DailyScan" /fo LIST /v
schtasks /query /tn "\SwingIQ_WeeklyScan" /fo LIST /v

# Run a task manually (test)
schtasks /run /tn "\SwingIQ_DailyScan"

# Disable/enable a task
schtasks /change /tn "\SwingIQ_DailyScan" /disable
schtasks /change /tn "\SwingIQ_DailyScan" /enable

# Check last result (0 = success, 1 = failed)
schtasks /query /tn "\SwingIQ_DailyScan" /fo LIST /v | findstr "Last Result"
```

### Key distinction: scanner-v3 vs scanner-dashboard

- **scanner-v3** (`F:\projects\claude\scanner-v3`) = the CLI tool. Runs via
  terminal or cron. Generates Telegram alerts directly. This is where the
  SwingIQ daily/weekly message format lives.
- **scanner-dashboard** (`F:\projects\claude\scanner-dashboard`) = the web app.
  Has its own embedded copy of scanner-v3 (baked into Docker image). Triggers
  scans from the browser. Has its own Telegram settings (per-user chat ID in
  the Settings page). Does NOT use the SwingIQ bot — it uses whatever token
  is in its own `backend/.env`.

**Do not conflate the two.** Changes to `scanner-v3/daily_scan.py` affect the
cron-generated Telegram alerts. They do NOT affect the dashboard unless you
also rebuild the dashboard's Docker images (which bake in their own copy of
scanner-v3). The dashboard's Telegram notifications are separate.

---

## Domain 2 — Job Hunter

Automated job application system for Kartik's DevOps/SRE profile. Scrapes LinkedIn, Naukri, Indeed, Instahyre, + 24 Finnish companies → scores → applies via Workday/LinkedIn Easy Apply/Oracle ORC → SQLite tracker → Telegram alerts.

### ⚠️ Security notes
- `.env` contains real credentials (Telegram bot token, LinkedIn/Naukri/Workday passwords). **Never commit, never share publicly.**
- Phone `8149927963` is hardcoded in multiple files.
- Two different emails appear in profile (`bandewarkarthik@gmail.com` vs `kartikbandewar1911@gmail.com`).
- Chrome extension `content.js` reportedly has a password in default profile.

### ⚠️ Security notes
- `.env` contains real credentials (Telegram bot token, LinkedIn/Naukri/Workday/Instahyre passwords). **Never commit, never share publicly.**
- Phone `8149927963` is hardcoded in multiple files.
- Two different emails appear in profile (`bandewarkarthik@gmail.com` vs `kartikbandewar1911@gmail.com`).
- Chrome extension `content.js` reportedly has a password in default profile.

### Quick Start (EASIEST WAY)
```powershell
# Option 1: Double-click desktop shortcut "Job Auto-Apply"
# Option 2: Run the batch file
.\apply.bat

# Option 3: Command line
python apply.py                  # 5 jobs on LinkedIn + 5 on Instahyre (10 total)
python apply.py --limit 10       # 10 jobs on each platform (20 total)
python apply.py --linkedin       # LinkedIn only
python apply.py --instahyre      # Instahyre only
python export_jobs.py            # Export applied jobs to Excel (tracker/applied_jobs.xlsx)
```

### Commands
```powershell
pip install -r requirements.txt

# ── Simple auto-apply (RECOMMENDED) ──
python apply.py                  # LinkedIn + Instahyre, 5 jobs each
python apply.py --limit 10       # 10 jobs each platform
python apply.py --linkedin       # LinkedIn Easy Apply only
python apply.py --instahyre      # Instahyre only
python export_jobs.py            # Export to Excel + auto-open
.\apply.bat                      # Interactive menu (double-click or run)

# ── Legacy commands ──
python main.py                   # Manual run with Telegram approval workflow
python automate.py --limit 15    # Fully automated (auto-apply at score >=70)
python apply_now.py <url>        # Apply to a specific job URL

# Install Windows Task Scheduler job (daily 9 AM)
python scheduler_setup.py
# Manual trigger:  schtasks /Run /TN "JobHunterAutoApply"
# Remove:          schtasks /Delete /TN "JobHunterAutoApply" /F

.\run_daily.bat                  # runs automate.py
```

### How it works (apply.py)
1. Opens visible Chrome browser
2. **LinkedIn**: Logs in via saved cookies → searches 14 countries (Pune, Remote, UAE, Singapore, Germany, UK, Canada, Australia, etc.) → finds Easy Apply jobs → navigates to apply URL → fills dialog form (resume, phone, email, salary, experience, radio buttons, dropdowns) → submits
3. **Instahyre**: Logs in via cookies/email/Google SSO → searches 4 keywords (DevOps, SRE, Cloud, Platform Engineer) → clicks "Apply to {Company}" (one-click apply using candidate profile)
4. Saves all applied jobs to SQLite tracker → export to Excel with `python export_jobs.py`
5. Cookies saved for both platforms — no manual login needed on future runs

### Excel export (tracker/applied_jobs.xlsx)
- Sheet 1: "Applied Jobs" — color-coded by source (LinkedIn=blue, Instahyre=orange) and score (green≥70, yellow≥60, red<60)
- Sheet 2: "Summary" — breakdown by platform, company, date
- Sheet 3: "All Jobs" — all 2000+ scraped jobs with status (applied/skipped/found)

### Structure
- `apply.py` — **Main entry point** — LinkedIn Easy Apply + Instahyre auto-apply
- `apply.bat` — Interactive menu launcher (also desktop shortcut)
- `export_jobs.py` — Export applied jobs to Excel
- `_show_applied.py` — Print applied jobs list to console
- `scrapers/` — LinkedIn, Naukri, Indeed, Instahyre, Finland
- `engine/scorer.py` — role/skills/location/experience scoring (max 100)
- `applicator/` — Workday, LinkedIn Easy Apply, Oracle ORC
- `applicator/linkedin_apply.py` — Easy Apply dialog handler (resume upload, form fill, submit)
- `applicator/session.py` — Cookie-based session management
- `notifier/telegram_bot.py` — inline buttons: Apply/Skip/Shortlist
- `tracker/tracker.py` — SQLite (`jobs` table, dedup by job_id)
- `tracker/applied_jobs.xlsx` — Excel export of all applied jobs
- `chrome-extension/` — Manifest V3, manual form-fill for 9 ATS platforms
- `profile/profile.py` — target roles, locations, skills, exclusions
- `linkedin_cookies.pkl` / `instahyre_cookies.pkl` — Saved session cookies

---

## Domain 3 — TableFlow (Restaurant POS SaaS)

Microservices architecture: 14 services + PostgreSQL + Redis + RabbitMQ + nginx + Prometheus/Grafana. Two deploy modes: Docker Compose, or Windows installer (Inno Setup, bundles Node.js + PostgreSQL + nginx).

### ⚠️ Known issues (re-verified 2026-07-22 via full codebase audit)
- **`DATABASE_SCHEMA_COMPLETE.sql`** — was a 0-byte placeholder; now regenerated via `pg_dump --schema-only` (123KB of real schema). ✅ Fixed 2026-07-22.
- **Customer Service** — was in-memory Map storage; now uses PostgreSQL (`pg` installed, `customer_orders` table to avoid conflict with main `orders` table). ✅ Fixed 2026-07-22.
- **Report Service** — was returning FAKE data from `dataGenerator.js`; all 10 route files (sales, dashboard, items, payment, customer, inventory, staff, financial, analytics, export) rewritten to use real PostgreSQL queries. ✅ Fixed 2026-07-22.
- **Auth on order-service and billing-service** — JWT middleware added; order-service allows guest POST/GET for QR self-ordering, all other endpoints require Bearer token; billing-service requires auth on all endpoints. ✅ Fixed 2026-07-22.
- **MySQL syntax in PostgreSQL schemas** — `billing-service/schema.sql` rewritten to PG syntax (removed `ON UPDATE CURRENT_TIMESTAMP`, `LONGTEXT`, inline `INDEX`); `menu-service/src/db/schema.sql` rewritten to match actual `menu_items` table (was using `items` with `FULLTEXT INDEX`). ✅ Fixed 2026-07-22.
- **5 services had no schema file** — created `schema.sql` for delivery, aggregator, online-ordering, staff, notification; all applied to DB successfully. ✅ Fixed 2026-07-22.
- **Hardcoded fallback secrets** — all 14 instances removed across auth, order, billing, menu, delivery, aggregator, online-ordering, staff, notification, report, pm2.config.js; services now fail fast (`process.exit(1)`) if `JWT_SECRET` or `DB_PASSWORD` not set. ✅ Fixed 2026-07-22.
- **Frontend customer page** — now sends `Authorization: Bearer` header when token available (from URL param or localStorage); guest mode still works for QR ordering. ✅ Fixed 2026-07-22.
- **Billing GST calculation** — `calculateGST()` in `bills.js` crashed with `toFixed` on NaN when `GST_CGST_RATE`/`GST_SGST_RATE` env vars unset; now defaults to 0. ✅ Fixed 2026-07-22.
- **Frontend uses in-browser Babel** (React via CDN, no build step) — fine for demo/LAN POS, slow for production web. (Unchanged — by design for zero-build deployment.)
- **Service readiness (actual)**: ✅ production-grade: auth, order, menu, table, billing, report (6/14). ⚠️ partial: delivery, online-ordering, staff, notification, inventory, kds (6/14). ❌ stubbed: aggregator (stubbed Zomato/Swiggy), customer (basic CRUD). E2E test: 12/12 passed (login → tables → menu → order → bill → payment → reports).

### Commands — Docker (full stack)
```powershell
cd tableflow
docker-compose up -d                          # start all 18 containers
docker-compose down                           # stop
docker-compose logs -f auth-service           # tail logs
# Frontend:      http://localhost:8080
# Grafana:       http://localhost:3000
# Prometheus:    http://localhost:9090
# RabbitMQ Mgmt: http://localhost:15672
```

### Commands — Windows native
```powershell
cd tableflow
.\install.bat                                 # one-click installer
.\Start TableFlow.bat                         # start all services
.\Stop TableFlow.bat                          # stop
.\Backup TableFlow.bat                        # DB backup
.\Restore TableFlow.bat                       # DB restore
.\Update TableFlow.bat                        # update
.\Add Waiter Account.bat                      # create staff account
.\Network Info.bat                            # show LAN IP for waiter app

# E2E test (requires all 6 core services running)
node e2e_test.js                              # 12-step: login → tables → menu → order → bill → payment → reports

# Individual service launchers (load .env, set PATH to bundled Node)
run_auth.bat                                  # auth-service on :5001
run_order.bat                                 # order-service on :5002
run_menu.bat                                  # menu-service on :5003
run_billing.bat                               # billing-service on :5005
run_report.bat                                # report-service on :5010
run_customer.bat                              # customer-service on :5009
```

### Service ports
| Port | Service | Status |
|---|---|---|
| 5001 | Auth | ✅ Production-ready |
| 5002 | Order (state machine + WebSocket) | ✅ Production-ready |
| 5003 | Menu (full-text search, image upload) | ✅ Production-ready |
| 5004 | Inventory (ledger, FIFO/LIFO) | ✅ Production-ready |
| 5005 | Billing (GST, double-entry accounting) | ✅ Production-ready |
| 5006 | Table (floors, reservations, QR) | ✅ Production-ready |
| 5007 | KDS (kitchen display, WebSocket) | ✅ Production-ready |
| 5008 | Delivery | ⚠️ Partial (skeleton controllers, MySQL `?` placeholders) |
| 5009 | Customer (CRM, loyalty, RFM) | ✅ PostgreSQL (fixed 2026-07-22) |
| 5010 | Report (PDF/Excel/CSV export) | ✅ Real DB queries (fixed 2026-07-22) |
| 5011 | Aggregator (Zomato/Swiggy/UberEats) | ❌ Skeleton |
| 5012 | Online Ordering | ❌ Skeleton |
| 5013 | Staff | ❌ Skeleton |
| 5014 | Notification | ❌ Skeleton |
| 8080 | nginx (frontend gateway) | ✅ |
| 5432 | PostgreSQL | ✅ |
| 6379 | Redis | ✅ |
| 5672/15672 | RabbitMQ | ✅ |
| 9090/3000 | Prometheus / Grafana | ✅ |

### Standalone services (workspace root — may supersede tableflow-internal versions)
These are **more polished, TypeScript/Sequelize** versions vs the JS/raw-pg ones inside `tableflow/`. Decide which to keep and delete the other to avoid divergence.

#### `auth-service/` (TypeScript, Express, Sequelize, Redis, JWT, MFA, OAuth2)
```powershell
cd auth-service
npm install
npm run dev          # ts-node src/index.ts
npm run build        # tsc -> dist/
npm start            # node dist/index.js
npm test             # jest
npm run lint         # eslint
npm run migrate      # node scripts/migrate.js
# Docker: docker-compose up  (brings up Postgres + Redis + auth)
```

#### `notification-service/` (JS, Express, Bull, Redis, Twilio, SendGrid, Firebase)
```powershell
cd notification-service
npm install
npm run dev          # nodemon src/server.js
npm start            # node src/server.js
npm test             # jest --coverage
npm run lint         # eslint src --fix
npm run queue:stats  # view Bull queue stats
npm run queue:clean  # clean failed jobs
```

---

## Domain 4 — Portfolio

Static Next.js 14 site (App Router, Tailwind, dark/terminal theme). Static export — no backend.

```powershell
cd portfolio
npm install
npm run dev          # http://localhost:3000
npm run build
npm run export       # static export to out/
```

---

## Cross-Cutting Notes

### Secrets hygiene
- Scanner `.env` files (Telegram tokens) and `job-hunter/.env` (platform credentials) are on disk. Root `.gitignore` excludes `.env` but the files exist locally.
- Before publishing any of this: scrub hardcoded phone numbers, emails, passwords, and tokens.

### Code duplication (highest-priority refactor)
- Pattern detectors, data loaders, chart generators, and Telegram notifiers are copy-pasted across `scanner/`, `scanner-v2/`, `scanner-v3/`, `weekly-swing-setup-scanner/`. `scanner-v3/` is the canonical version — others should be archived or refactored to import from it.
- `auth-service` and `notification-service` exist both at workspace root (TypeScript) and inside `tableflow/` (JS). Pick one of each.

### Missing tests
- Only `earnings-scanner/test_pipeline.py`, `auth-service/__tests__/`, and `notification-service/tests/` have any tests. Everything else is untested.

### Missing dependency manifests
- `scanner/`, `scanner-v2/`, `weekly-swing-setup-scanner/`, `scanner-training/` have no `requirements.txt`. Add one per project.

### Suggested cleanup order
1. ~~Fix TableFlow Customer Service storage (in-memory → PostgreSQL) — critical bug.~~ ✅ Done 2026-07-22.
2. ~~Remove dead `DATABASE_SCHEMA_COMPLETE.sql` reference from `tableflow/docker-compose.yml`.~~ ✅ Done 2026-07-22 (regenerated real schema).
3. Consolidate scanners into `scanner-v3/` as the canonical scanner package with shared modules; archive `_old-scanner`, `_archived`, `weekly-swing-setup-scanner`.
4. Pick one `auth-service` and one `notification-service`; delete the other.
5. Scrub secrets from `job-hunter/` and scanner `.env` files.
6. Convert delivery-service MySQL `?` placeholders to PostgreSQL `$1` syntax (models use `pool.getConnection()` + `connection.execute()` which is mysql2 API, not pg).
6. Add `requirements.txt` to all Python projects.
