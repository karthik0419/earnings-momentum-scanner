# AGENTS.md — Workspace Map

Workspace root: `F:\projects\claude`
Owner: Kartik Bandewar (DevOps/SRE engineer, Pune, India)
Platform: Windows (PowerShell). Python projects use `python` (not `python3`).

This workspace holds **18 projects across 5 domains**:
1. Stock trading screeners (Python)
2. Job-hunting automation (Python + Chrome extension)
3. Restaurant POS SaaS — TableFlow (Node.js microservices)
4. E-commerce automation (Python + AI)
5. KDP publishing (Python + AI)

> **Workspace layout (2026-07-18):** The root `F:\projects\claude` is a clean container — only `AGENTS.md`, `interview-prep.md`, and per-project subfolders live here. No loose project files at root. The root `.git` tracks the `earnings-momentum-scanner/` subfolder (commit `4430bda` restructured loose root files into that subfolder). The duplicate `earnings-scanner/` clone was removed (byte-identical to `earnings-momentum-scanner/`). All other project subfolders are untracked.

> **Front-end development (2026-08-24):** 5 custom skills installed in `C:\Users\91814\.claude\skills\` for building professional web pages. These skills are **auto-invoked** - whenever building any web page, all best practices (responsive, accessible, modern design, Tailwind CSS, React) are applied automatically without mentioning them. User just says "build X" and gets production-ready code.

---

## Quick Navigation

| Project | Domain | Stack | Status |
|---|---|---|---|
| `scanner/` | Trading | Python | Active (v6.0+) |
| `scanner-v2/` | Trading | Python | Active (enhanced C&H) |
| `scanner-v3/` | Trading | Python | **Active (v3 production)** |
| `scanner-us/` | Trading | Python | **Active (US market — v2.0 MTF confirmation)** |
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
| `amazon-image-agent/` | E-commerce | Python + Krea AI MCP | Paused (Krea is paid) |
| `kdp-coloring-pipeline/` | KDP Publishing | Python + AI | **Active (Book #1 ready)** |

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
| **SwingU** | `scanner-v3/.env` (default) | `TELEGRAM_CHAT_ID_REDACTED` (private chat) | **Testing** — manual CLI runs (`python daily_scan.py`) |
| **SwingIQ** | `scanner-v3/.env.swingiq` | `-1004275742331` (channel) | **Production** — automated cron scans (Task Scheduler) |

`auto_daily_scan.bat` / `auto_weekly_scan.bat` use `--env-file .env.swingiq`
flag (no .env swapping needed). So:
- You typing in terminal → message goes to **SwingU** (private, default `.env`)
- Cron/Task Scheduler → message goes to **SwingIQ** (channel, `.env.swingiq`)

**Bat files in scanner-v3/ (2026-08-12 cleanup):**
- `auto_daily_scan.bat` — cron daily scan (SwingIQ, Task Scheduler). Shows
  header on screen + full output to log. No pause (cron job).
- `auto_weekly_scan.bat` — cron weekly scan (SwingIQ, Task Scheduler). Same.
- `daily_scan_test.bat` — manual daily scan (SwingU, private chat). Shows
  full real-time output on screen + `pause` at end. (Fixed: was blank when
  double-clicked — all output was redirected to log only.)
- `weekly_scan_test.bat` — manual weekly scan (SwingU, private chat). Same fix.
- `Daily Scan.bat` — interactive menu (22 options, SwingU)
- `run_weekly.bat` — interactive menu (24 options, SwingU)
- **Deleted:** `daily_scan_prod.bat`, `weekly_scan_prod.bat` (duplicates of
  `auto_*` versions), `.env.swingu_backup` (leftover from old swap approach)
- **Restored from `_archive/`:** `_daily_scan_enhanced.py`,
  `_tracker_status.py` (were missing — menu options 20-21 / 22-23 were broken)

**Bug fixes (2026-08-12):**
- `paper_tracker.py` — added `sys.stdout.reconfigure(encoding='utf-8')` (was
  missing — em-dash in output broke UTF-8 consumers on Windows when piped)
- `rank_2week.py` — was hardcoded to `v3_2026-07-29.csv` (stale). Now uses
  `glob` to find latest `v3_*.csv` and latest `backtest_v3*.csv` dynamically.
  Hardcoded summary section replaced with dynamic generation from ranked data.
  Also added UTF-8 encoding fix.

**Stale files cleaned up (2026-08-12):**
- 28 files moved to `_archive/stale_2026-08-12/`: `test_*.txt` (11 test
  captures), `*_today.txt` / `*_output.txt` / `*_results.txt` (stale output
  captures), `SESSION_2026-07-19.md` (old session notes), `inkling_*.md`
  (3 one-off AI review files), `COMMIT_MSG.txt`, `vedl_*.txt`, etc.
- Root directory now has only: `backbone50.txt`, `nifty200.txt`,
  `nifty500.txt`, `requirements.txt`, `COMPARISON_REPORT.md`, `README.md`,
  `VERSION.md` (+ Python scripts + bat files + dirs)

**End-to-end test results (2026-08-12, all 14 scripts tested):**

| Script | Status | Notes |
|---|---|---|
| `daily_scan.py` | PASS | 507 stocks, 8 volume surges, ~30s |
| `scanner.py --test` | PASS | 44 stocks, 20 setups, ~1 min |
| `paper_tracker.py status` | PASS | 144 picks, 53 open, 6 closed (encoding fixed) |
| `paper_tracker.py summary` | PASS | 0% win rate, -1.63% expectancy on closed |
| `_tracker_status.py` | PASS | Telegram sent to SwingU, 53 open, 75 waiting |
| `gen_charts.py` | PASS | 30 charts (10 stocks × 3 timeframes) |
| `rank_2week.py` | PASS | Now loads latest CSV dynamically (was hardcoded) |
| `_daily_scan_enhanced.py` | PASS | 181 stocks, 111 picks, ~5 min, Telegram sent |
| `backtest.py` | PASS | 376 trades, 46% WR, PF 3.05, Exp +3.26%, ~2 min |
| `compare_backtest.py` | PASS | v3 vs v2: v3 better DD (-32% vs -43%), ~4 min |
| `sweep_atr.py` | PASS | 2.0x ATR best (PF 2.22, DD -50.8%), ~5 min |
| `whipsaw_analysis.py` | PASS | 27.1% whipsaw rate, 82.9% went lower, ~3 min |
| `sector_rotation_v3` | PASS | Auto BOOM, Energy/FMCG/Infra weak |
| `telegram_notify.py` | PASS | Sent via SwingU bot from .env |

**Automated test suite (`test_fixes.py`):**
```powershell
cd F:\projects\claude\scanner-v3
python test_fixes.py              # run all 65 tests (validates all 2026-08-12 fixes)
python test_fixes.py --verbose    # show full output
```
Validates: bat files not blank, encoding fix, rank_2week dynamic CSV, restored
scripts, deleted files, stale files archived, cron battery restrictions, Telegram
bot wiring, all imports, menu bat options, daily cron 2-step flow, freshness
tracking. Exit code 0 = all pass.

**Daily cron 2-step flow (2026-08-12):**
The daily cron (`auto_daily_scan.bat`) now runs TWO steps instead of one:
1. `scanner.py --smart --no-notify` — fresh pattern scan on smart universe
   (Backbone50 + Nifty500 + hot sector stocks, ~500-800 stocks, 5-8 min).
   Generates `results/v3_YYYY-MM-DD.csv` with today's fresh picks.
2. `daily_scan.py` — volume movers + loads the fresh CSV from step 1 (30 sec).
   Posts combined message to SwingIQ Telegram channel.

This means **pattern setups are now fresh every day**, not stale from last
Saturday's weekly scan. Total cron time: ~6-9 min (within 8:30-9:15 AM window).
The `daily_scan_test.bat` (manual, SwingU) also uses this 2-step flow.

**Freshness tracking (2026-08-12):**
Each pattern setup in the Telegram message now shows a freshness badge:
- `🆕 NEW` — stock appears for the first time in recent scans (not in previous
  7 CSVs)
- `🔁 Day N` — stock has appeared in N consecutive daily scans (including today)

The PATTERN SETUPS header also shows a count: `(6 new, 4 repeating)`.
This makes it easy to see which picks are fresh opportunities vs which are
being tracked from previous days. Implementation: `_compute_freshness()` in
`daily_scan.py` compares the current CSV against previous `v3_*.csv` files.

**Why daily scan messages looked similar across days (FIXED 2026-08-12):**
**Root cause:** The PATTERN SETUPS section loaded from a weekly scan CSV that
only updated on Saturdays. Mon-Fri showed the same 10 stocks.
**Fix:** The daily cron now runs `scanner.py --smart` before `daily_scan.py`,
generating fresh pattern picks every day. Additionally, each pick shows a
freshness badge (🆕 NEW / 🔁 Day N) so you can see which stocks are new today
vs repeating from previous days.

### Where each project fits

| Project | Folder | What it does | Telegram header | Bot | Rebranded? |
|---|---|---|---|---|---|
| scanner-v3 (daily) | `scanner-v3/` | Daily morning scan (volume + sectors) | `📊 SwingIQ Daily Scan` | SwingU/SwingIQ (via --env-file) | **Yes** (2026-08-09) |
| scanner-v3 (weekly) | `scanner-v3/` | Weekly swing setup scan (patterns) | `📊 SCANNER v3.1` | SwingU/SwingIQ (via --env-file) | **No** — still old name |
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
| `SwingIQ_DailyScan` | Daily 08:30 IST | `scanner-v3\auto_daily_scan.bat` → `python daily_scan.py --top 15 --max-price 5000 --env-file .env.swingiq` | SwingIQ (via --env-file) | **Active** — last ran 12 Aug, result 0 (success) |
| `SwingIQ_WeeklyScan` | Saturdays 09:00 IST | `scanner-v3\auto_weekly_scan.bat` → `python scanner.py --max-price 5000 --env-file .env.swingiq` | SwingIQ (via --env-file) | **Active** — first run Sat 15 Aug |
| `SwingIQ_TrackerUpdate` | Daily 09:15 IST | `scanner-v3\auto_tracker_update.bat` → `python paper_tracker.py update` + `python tracker_alert.py --env-file .env.swingiq` | SwingIQ (via --env-file) | **Active** — created 28 Aug 2026 |

**Deleted (2026-08-09):** `NSE Swing Screener` (Mon-Fri 08:30) — stale task
from May 2026 pointing to dead path
`C:\Users\91814\Desktop\claude\enhanced-swing-trading-screener\run_screener.bat`
(workspace migrated to `F:\projects\claude\` in Jul 2026). Was failing silently
every weekday with result code 1 (file not found). Fully replaced by
`SwingIQ_DailyScan`.

**Power management note (updated 2026-08-12):** Battery restrictions
(`Stop On Battery Mode`, `No Start On Batteries`) have been **removed** from
both tasks — they will now run even if the laptop is unplugged. The laptop
must still be **awake** (not in sleep/hibernate) at the scheduled time.

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

### `scanner-us/` — US Stock Swing Scanner (v2.0)

Adapted from scanner-v3 (India/NSE) for US markets (NYSE/NASDAQ). Same proven patterns (Cup & Handle, Double Bottom), same risk management (2.0x ATR, 8% cap), new market. **GitHub: https://github.com/karthik0419/scanner-us**. **Targeting YouTube Shorts monetization for US audience (10-20x higher CPM than India).**

**v2.0 improvements (2026-08-29):**
1. **Multi-timeframe confirmation** — Daily pattern confirmed by weekly trend (50-week SMA). MTF-confirmed setups get +15 score bonus, non-MTF get -10 penalty. `--mtf-only` flag.
2. **Risk from ENTRY (not CMP)** — v1 calculated risk from current price (wrong). v2 calculates from breakout level (where you actually enter).
3. **Double Bottom spacing** — Min 15 bars between bottoms (was 7). Prevents detecting downtrends as double bottoms.
4. **Momentum check for NEAR** — 5D close must be > 10D close (stock rising toward breakout). Prevents flagging crashing stocks as NEAR.
5. **Handle validation** — Handle must be within 15% of right rim (not a crash).
6. **Recovery check** — Current price must be above bottom 2 (stock recovering, not falling).
7. **C&H Weekly/Monthly timeframe fix (CRITICAL, 2026-08-29)** — Was passing daily df to all timeframes. Now each timeframe uses its own resampled data (daily/weekly/monthly bars). This was hiding C&H Weekly as a profitable pattern (52.2% WR, +1.65% exp).
8. **Auto-refresh S&P 500 list** — `refresh_sp500.py` fetches current constituents from Wikipedia. Scanner auto-refreshes before each scan (unless `--no-refresh`).
9. **Incremental cache refresh** — `--refresh-cache` flag downloads only NEW stocks (after sp500.txt update), merges into existing cache. No full re-download.
10. **Quality filters** — `--best-only` (1 setup per stock, no duplicates), `--db-only` (Double Bottom only, the 70.7% WR pattern).
11. **Paper tracker** — `paper_tracker.py` tracks live picks. NEAR picks wait for breakout, auto-checks SL/T1/T2, 45-day time exit.
12. **NaN bug fixes** — Drop NaN Close rows (incomplete trading day) in sector_rotation, scanner, chart_generator, paper_tracker.

**Stock universes:**
- `sp500.txt` — 503 S&P 500 stocks (DEFAULT, auto-refreshable from Wikipedia)
- `backbone_us.txt` — 50 curated momentum stocks (quick scan, ~2 min)
- `sp500_sectors.json` — Symbol → GICS sector mapping (from Wikipedia)

**Sector rotation:** 11 S&P sector ETFs (XLK, XLV, XLF, XLE, XLY, XLP, XLI, XLB, XLU, XLRE, XLC). Same BOOM/RISING/COOLING/WEAK signals as scanner-v3.

**Backtest results (S&P 500, 5-year, 293 trades, post C&H Weekly fix):**

| Pattern | Trades | Win Rate | Expectancy | PF | Verdict |
|---|---|---|---|---|---|
| **Double Bottom** | 259 | **71.0%** | **+1.73%** | **2.46** | ✅ Star pattern |
| **C&H Weekly** | 23 | **52.2%** | **+1.65%** | **1.56** | ✅ Good (2nd best) |
| C&H Daily | 11 | 36.4% | -0.37% | 0.84 | ❌ Loser |
| C&H Monthly | 0 | — | — | — | Not detected (rare) |

Overall: 69.0% WR, +1.62% expectancy, 2.20 PF, +442.1% return, +40.2% CAGR.

**Files:**
- `scanner_us.py` — main scanner (v2.0, MTF confirmation, correct timeframe data, auto-refresh)
- `visual_backtest.py` — cached backtest engine (incremental refresh, monthly data)
- `chart_generator_v3.py` — chart generator with pattern overlay
- `verify_picks.py` — validate entry/SL/targets correctness
- `refresh_sp500.py` — auto-refresh S&P 500 list from Wikipedia
- `paper_tracker.py` — paper trade tracker (NEAR waits for breakout, auto SL/T1/T2)
- `analyze_patterns.py` — pattern stats by timeframe
- `upgrade_cache.py` — add monthly data to existing cache (in-place)
- `utils/sector_rotation_us.py` — S&P sector rotation
- `Scanner.bat` — main menu (18 options)
- `Daily Scan.bat` — one-click daily scan (S&P 500, MTF, best-only)
- `Weekly Scan.bat` — one-click weekly S&P 500 scan (best-only)
- `Backtest.bat` — backtest menu (3yr/5yr/test)

```powershell
# Daily scan (S&P 500, best-only, ~10 min) — DEFAULT
python scanner_us.py --mtf-only --best-only

# Quick scan (backbone 50, ~2 min)
python scanner_us.py --stocks backbone_us.txt --mtf-only --best-only --no-refresh

# Double Bottom only (70.7% WR pattern)
python scanner_us.py --mtf-only --db-only

# Test mode (10 stocks)
python scanner_us.py --test --mtf-only --no-refresh

# Refresh S&P 500 list from Wikipedia
python refresh_sp500.py --check    # dry run
python refresh_sp500.py            # apply

# Backtest (cached, ~5 min)
python visual_backtest.py --stocks sp500.txt --years 5 --visual

# Incremental cache refresh (after sp500.txt update)
python visual_backtest.py --stocks sp500.txt --years 5 --refresh-cache --visual

# Paper tracker
python paper_tracker.py init       # init from latest scan
python paper_tracker.py update     # fetch prices, check breakouts/SL/T1/T2
python paper_tracker.py status     # show all trades
python paper_tracker.py summary    # one-line summary

# Verify picks
python verify_picks.py

# Generate charts
python chart_generator_v3.py MSFT
python chart_generator_v3.py --batch results_us_2026-08-29.csv --top 5

# Analyze backtest patterns by timeframe
python analyze_patterns.py backtest_results/sp500_5yr_295trades.csv
```

---

## Domain 2 — Job Hunter

**ZERO INTERVENTION JOB HUNTER** — Fully automated job application system targeting Australia + International + Visa Sponsorship opportunities. Scrapes Australia (Seek, LinkedIn AU, Indeed AU) + International (LinkedIn, WeWorkRemotely, RemoteOK) + India (LinkedIn, Naukri, Indeed, Instahyre, Jobringer) → auto-scores (0-100) → auto-approves (NO manual Telegram clicks!) → AI form filling (GPT-4) → AI cover letters → applies via Workday/LinkedIn Easy Apply/Oracle ORC → SQLite tracker → Telegram summary.

**Latest improvements (2026-08-27):**
- ✅ **Auto-approval system** — Score >= 80 = instant apply, >= 70 = 30s delay, >= 60 = 60s delay. NO manual Telegram approvals!
- ✅ **AI form filling** — GPT-4 answers application questions ("Why do you want to work here?", salary expectations, behavioral questions)
- ✅ **AI cover letters** — Personalized per job, emphasizes visa sponsorship for international roles
- ✅ **Australia job scraper** — Seek.com.au, LinkedIn AU, Indeed AU with visa sponsor detection
- ✅ **Jobringer scraper** — jobringer.com (India jobs, Selenium-based, 30 jobs per run)
- ✅ **Location boosting** — Australia +20 points, International/Remote +10, Visa Sponsorship +15
- ✅ **Smart pacing** — Respects daily limits (LinkedIn 15/day, Naukri 50/day), auto-queues excess for next day
- ✅ **Error recovery** — Auto-retry with exponential backoff (3 attempts)
- ✅ **Session management** — Auto-relogin when LinkedIn cookies expire, handles 2FA with Telegram alerts
- ✅ **LinkedIn Easy Apply bug fix** — Fixed dialog disappearing issue (changed to `visibility_of_element_located`, added 3s stabilization delay)
- ✅ **Windows encoding fix** — UTF-8 wrapper for emoji support

**Cost:** $20/month (OpenAI GPT-4 for AI features). Expected results: 70-105 applications/week, 5-15 interview requests/week, 0 manual interventions (except 2FA).

### ⚠️ Security notes
- `.env` contains real credentials (Telegram bot token, LinkedIn/Naukri/Workday/Instahyre passwords, OpenAI API key). **Never commit, never share publicly.**
- Phone `8149927963` is hardcoded in multiple files.
- Two different emails appear in profile (`bandewarkarthik@gmail.com` vs `kartikbandewar1911@gmail.com`).
- Chrome extension `content.js` reportedly has a password in default profile.

### Quick Start (ZERO INTERVENTION)
```powershell
# ── ONE CLICK (EASIEST - RECOMMENDED) ──
# Double-click desktop shortcut "JOB APPLY" (created by create_shortcut.bat)
# OR run:
.\ONE_CLICK_APPLY.bat              # Interactive menu: 5/10/20/30 jobs, dry run, export, stats

# ── COMMAND LINE ──
pip install openai  # Required for AI features

# Test (dry run - no actual applications)
python automate_zero_intervention.py --dry-run --limit 5

# Live run (apply to 10 jobs automatically)
python automate_zero_intervention.py --limit 10

# Schedule daily (run as Administrator) - SET & FORGET!
python scheduler_setup_zero.py  # Runs daily at 9 AM, applies to 15 jobs

# ── Legacy commands (manual approval required) ──
python apply.py                  # LinkedIn + Instahyre, 5 jobs each
python apply.py --limit 10       # 10 jobs each platform
python main.py                   # Manual run with Telegram approval workflow
python automate.py --limit 15    # Old auto-apply (no AI features)
python export_jobs.py            # Export to Excel + auto-open
.\apply.bat                      # Interactive menu

.\run_daily.bat                  # runs automate.py
```

### Key Files (Zero Intervention)
- `automate_zero_intervention.py` — Main automation pipeline (scrape → score → auto-approve → AI apply)
- `automation/auto_approve.py` — Auto-approval logic (score thresholds, location boosting)
- `automation/ai_form_filler.py` — GPT-4 form filling (questions, dropdowns, salary)
- `automation/cover_letter_generator.py` — AI cover letter generation
- `scrapers/australia_jobs.py` — Australia-specific scraper (Seek, LinkedIn AU, Indeed AU)
- `scrapers/jobringer.py` — Jobringer.com scraper (Selenium-based, India jobs)
- `applicator/linkedin_apply.py` — LinkedIn Easy Apply automation (FIXED: dialog detection bug)
- `README.md` — Quick start guide
- `ZERO_INTERVENTION_PLAN.md` — Full 10-phase implementation plan
- `SETUP_ZERO_INTERVENTION.md` — Detailed setup guide
- `IMPLEMENTATION_COMPLETE.md` — Implementation summary + bug fixes

### Auto-Approval Logic
| Score | Action | Delay | Example |
|---|---|---|---|
| 80-100 | INSTANT APPLY | 0 sec | Atlassian DevOps Sydney (base 75 + Australia +20 + visa +15 = 110) |
| 70-79 | APPLY | 30 sec | Google SRE Remote (base 70 + international +10 = 80) |
| 60-69 | APPLY | 60 sec | Startup DevOps Pune (base 60) |
| < 60 | SKIP | - | Poor match |

### Known Issues (FIXED)
1. ✅ **LinkedIn Easy Apply dialog disappearing** — Fixed with `visibility_of_element_located` + 3s stabilization delay
2. ✅ **Windows encoding errors** — Fixed with UTF-8 wrapper at top of script
3. ⚠️ **OpenAI API required** — Falls back to template answers if key not provided (less personalized)

### Documentation
See `job-hunter/README.md` for quick start, `ZERO_INTERVENTION_PLAN.md` for full implementation details, `SETUP_ZERO_INTERVENTION.md` for setup guide.
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

---

## Domain 4 — E-commerce Automation

### `amazon-image-agent/` — Autonomous Amazon product image generator

**Purpose**: Automated AI agent that monitors Amazon listings and generates high-quality product images using Krea AI's MCP server. Runs on a daily schedule (Windows Task Scheduler) to continuously improve product listings and track revenue performance.

**Stack**: Python 3.8+, Krea AI MCP server, Windows Task Scheduler

**Status**: Active (2026-08-23) — autonomous loop for revenue generation testing

**Key features**:
- 🤖 Autonomous daily loop via Windows Task Scheduler
- 🎨 AI image generation using Krea AI MCP (5 images per listing: front view, lifestyle, close-up, side angle, packaging)
- 📊 Revenue tracking: conversion rates, orders, ROI, performance vs targets
- 🔄 State management: tracks processed ASINs, avoids duplicates
- 📈 Analytics: top performers, 7/30/90-day reports
- 🎯 Multi-style images: realistic, lifestyle, minimal, artistic variants

**Project structure**:
```
amazon-image-agent/
├── agent.py                    # Main agent loop
├── scheduler.py                # Windows Task Scheduler setup
├── requirements.txt            # Python dependencies (requests, python-dotenv)
├── .env.example               # Environment variables template
├── README.md                  # Full documentation
├── QUICKSTART.md              # 5-minute setup guide
├── config/
│   └── settings.py            # Configuration (images per listing, targets, loop interval)
├── modules/
│   ├── krea_client.py         # Krea AI image generation client
│   ├── amazon_monitor.py      # Amazon listing monitor (mock data, needs SP-API/scraping)
│   └── revenue_tracker.py     # Revenue & analytics tracker
├── logs/
│   └── agent.log              # Agent execution logs
├── state/
│   ├── agent_state.json       # Processed ASINs
│   └── revenue_log.json       # Revenue data (orders, views, conversion rates)
└── results/                   # Generated images & metadata (JSON)
```

**Setup (5 minutes)**:
```powershell
cd F:\projects\claude\amazon-image-agent

# 1. Install dependencies
pip install -r requirements.txt

# 2. Get Krea API key from https://krea.ai/app/api/tokens

# 3. Configure
cp .env.example .env
notepad .env  # Add KREA_API_KEY

# 4. Test run
python agent.py

# 5. Schedule daily runs (9 AM default)
python scheduler.py create
```

**Usage**:
```powershell
# Manual run (one cycle)
python agent.py

# Schedule daily runs
python scheduler.py create              # 9 AM default
python scheduler.py create --time 18:00 # Custom time (6 PM)
python scheduler.py status              # Check task status
python scheduler.py run                 # Run immediately (testing)
python scheduler.py delete              # Remove scheduled task

# Revenue tracking (manual)
python -c "from modules.revenue_tracker import RevenueTracker; t = RevenueTracker(); t.update_views('B08TEST001', 1500)"
python -c "from modules.revenue_tracker import RevenueTracker; t = RevenueTracker(); t.record_order('B08TEST001', 2999)"
python -c "from modules.revenue_tracker import RevenueTracker; t = RevenueTracker(); t.print_report(30)"

# Check logs
cat logs\agent.log
Get-Content logs\agent.log -Tail 50 -Wait  # Real-time

# Check state
cat state\agent_state.json      # Processed ASINs
cat state\revenue_log.json      # Revenue data

# View results
ls results\
cat results\B08TEST001_metadata.json
```

**Configuration** (`config/settings.py`):
- `IMAGE_WIDTH`, `IMAGE_HEIGHT`: Image dimensions (default 1024x1024)
- `IMAGES_PER_LISTING`: Number of images per product (default 5)
- `LOOP_INTERVAL_HOURS`: Loop frequency (default 24 = daily)
- `MAX_LISTINGS_PER_RUN`: Max listings per cycle (default 10)
- `CONVERSION_RATE_TARGET`: Target conversion rate (default 3%)
- `AVG_ORDER_VALUE_TARGET`: Target avg order value (default Rs 500)

**Krea AI MCP integration**:
- MCP server configured in `C:\Users\91814\.config\devin\config.json`
- URL: `https://api.krea.ai/mcp`
- Transport: Streamable HTTP
- Authentication: Bearer token (API key from https://krea.ai/app/api/tokens)
- `krea_client.py` handles API calls with custom prompts and styles

**Amazon integration (TODO)**:
Currently uses **mock data** (2 test listings). To connect real Amazon:
- **Option A (sellers)**: Amazon Selling Partner API (SP-API) — register at https://developer.amazonservices.com, add credentials to `.env`, update `amazon_monitor.py`
- **Option B (research)**: Web scraping with `beautifulsoup4` or `playwright` — respect robots.txt and rate limits

**Agent loop workflow**:
1. **Monitor**: Fetch new Amazon listings that need images (`amazon_monitor.get_new_listings()`)
2. **Generate prompts**: Create 5 diverse prompts per listing (front, lifestyle, close-up, side, packaging)
3. **Generate images**: Call Krea AI MCP to generate images with different styles
4. **Save results**: Store images and metadata in `results/`
5. **Track**: Add listing to revenue tracker (`revenue_tracker.track_listing()`)
6. **State**: Mark ASIN as processed to avoid duplicates

**Revenue tracking**:
- **Per-listing metrics**: Total revenue, orders, views, conversion rate, avg order value, days active
- **Summary metrics**: Total revenue, total orders, avg conversion rate, avg order value
- **Performance vs targets**: Conversion rate target (3%), avg order value target (Rs 500)
- **Top performers**: Best listings by revenue (`get_top_performers()`)

**Files**:
- `agent.py` — Main loop orchestrator (run this)
- `scheduler.py` — Windows Task Scheduler setup
- `modules/krea_client.py` — Krea AI image generation (5 styles: realistic, lifestyle, minimal, artistic, packaging)
- `modules/amazon_monitor.py` — Amazon listing monitor (mock data, **edit this** to connect real data)
- `modules/revenue_tracker.py` — Revenue & analytics tracker
- `config/settings.py` — Configuration constants
- `README.md` — Full documentation
- `QUICKSTART.md` — 5-minute setup guide
- `.env.example` — Environment variables template

**Logs & monitoring**:
- `logs/agent.log` — Detailed execution logs (check for errors)
- `state/agent_state.json` — Processed ASINs (prevents duplicates)
- `state/revenue_log.json` — Revenue data (orders, views, conversion rates)
- `results/` — Generated images and metadata (JSON per ASIN)

**Next steps**:
1. Get Krea API key and test image generation
2. Connect real Amazon data (SP-API or scraping)
3. Run first cycle and verify images are generated
4. Schedule daily runs and monitor logs
5. Track revenue (update views/orders as they come in)
6. Optimize: A/B test image styles, adjust targets, scale gradually

**Roadmap**:
- [ ] Integrate Amazon SP-API for real listing data
- [ ] Add image upload to Amazon Seller Central
- [ ] Multi-marketplace support (US, UK, DE, etc.)
- [ ] A/B testing framework (compare image variants)
- [ ] Slack/Telegram notifications for daily reports
- [ ] Dashboard UI for revenue analytics
- [ ] Auto-optimize prompts based on conversion data

**Notes**:
- Project created 2026-08-23 for revenue generation testing
- Krea AI MCP server is hosted (no local setup needed)
- Windows Task Scheduler used for loop (not cron, since Windows)
- Mock data returns 2 test listings; connect real Amazon for production
- Revenue tracking is manual (update views/orders via Python CLI)
- Has `requirements.txt` (requests, python-dotenv)

---

## Domain 5 — KDP Publishing

### `kdp-coloring-pipeline/` — AI-powered kids coloring book generator

**Purpose**: Create and publish kids coloring books on Amazon KDP. Manual validation first (Book #1), then automate proven workflows. Target: $6.99 books, 100 pages, kids ages 3-8.

**Stack**: Python 3.12+, Pillow, ReportLab, AI image APIs (Hugging Face free tier / Replicate / Stability AI)

**Status**: Active (2026-08-23) — Book #1 plan ready, tested with placeholders

**Workflow**:
```
1. PLAN → book_planner.py → 100-page content plan (JSON)
2. GENERATE → image_generator.py → 100 simple line drawings
3. REVIEW → Manual QC, copy to approved_images/
4. BUILD PDF → pdf_builder.py → KDP-ready interior.pdf
5. DESIGN COVER → Canva (dimensions from pdf_builder)
6. PUBLISH → kdp.amazon.com → Upload & set price $6.99
7. TRACK → 30 days → If 5+ sales/day, make Book #2
```

**Book #1 spec**:
- Title: "My First Big Coloring Book"
- Pages: 100 (20 animals, 15 vehicles, 15 fruits/veg, 15 shapes, 10 birds, 10 sea creatures, 10 insects, 5 flowers)
- Target: Kids 3-8 years
- Style: Simple black line drawings, no shading, white background
- Trim: 8.5" x 11"
- Price: $6.99 USD (printing $2.50, royalty $4.49/book)
- Cost to create: $0-2 (free Hugging Face tier or $1 Replicate)

**Project structure**:
```
kdp-coloring-pipeline/
├── book_planner.py          # Generate 100-page content plan
├── image_generator.py       # Generate line drawings (AI)
├── pdf_builder.py           # Assemble KDP-ready PDF
├── config.py                # Book settings, KDP specs, pricing
├── requirements.txt         # Pillow, ReportLab, requests
├── README.md                # Full docs
├── QUICKSTART.md            # 30-min guide
├── book_plans/              # JSON plans
│   └── book_001_plan.json   # 100-page plan (generated)
├── generated_images/        # Raw AI images (100 PNGs)
├── approved_images/         # QC-passed images
└── output/                  # Final PDFs
```

**Usage**:
```powershell
cd F:\projects\claude\kdp-coloring-pipeline

# 1. Generate book plan (already done)
python book_planner.py

# 2. Generate images
python image_generator.py --provider local --test       # Placeholders (5 pages, testing)
python image_generator.py --provider local              # Placeholders (all 100)
python image_generator.py --provider huggingface        # Real AI (free tier, requires API key)
python image_generator.py --provider replicate          # Real AI (paid, $0.01/image)

# 3. Review & approve
cp generated_images\*.png approved_images\

# 4. Build PDF
python pdf_builder.py
python pdf_builder.py --use-generated  # Use generated_images/ instead of approved_images/

# 5. Check output
start output\My_First_Big_Coloring_Book_Interior.pdf
```

**Configuration** (`config.py`):
```python
BOOK_CONFIG = {
    "title": "My First Big Coloring Book",
    "author": "Creative Kids Publishing",  # Change to your pen name
    "total_pages": 100,
    "categories": {
        "Animals": 20, "Vehicles": 15, "Fruits & Vegetables": 15,
        "Shapes & Objects": 15, "Birds": 10, "Sea Creatures": 10,
        "Insects": 10, "Flowers": 5
    }
}

KDP_SPECS = {
    "trim_width_inches": 8.5,
    "trim_height_inches": 11.0,
    "dpi": 300,
    "interior_color": "black_and_white"
}

PRICING = {
    "target_price_usd": 6.99,
    "printing_cost_estimate_usd": 2.50,
    "target_royalty_usd": 4.49
}
```

**Image generation options**:
1. **Local placeholders** (free, testing only) — Simple text placeholders, not suitable for publishing
2. **Hugging Face** (free tier) — Real AI images, good quality, rate-limited (sign up at huggingface.co, get API token)
3. **Replicate** (~$0.01/image = $1 for 100) — High quality, fast (requires credit card)
4. **Stability AI** (~$0.02/image = $2 for 100) — Highest quality (requires credit card)

**Phase 1: Manual validation** (current):
- ✅ Book plan generated (100 pages)
- ✅ Test images created (5 placeholders)
- ⏳ Generate all 100 images (need to set up Hugging Face API or use Replicate)
- ⏳ Build PDF
- ⏳ Design cover (Canva)
- ⏳ Publish on KDP
- ⏳ Track sales for 30 days
- **Decision**: If 5+ sales/day → automate and scale. If not → pivot niche.

**Phase 2: Automation** (after Book #1 success):
- Batch image generation (overnight)
- Auto QC (filter bad images)
- One-click PDF assembly
- Cover templates (reusable)
- Series generator (Book #2, #3 in same niche)

**Economics**:
- **Cost**: $0-2 per book (image generation)
- **Revenue**: $4.49/book sold (after KDP printing)
- **Break-even**: 1 sale
- **Target**: 5 sales/day = $22/day = $674/month per book
- **Scale**: 10 books × $674/month = $6,740/month

**Next steps**:
1. Get Hugging Face API token (free): https://huggingface.co/settings/tokens
2. Add to `config.py`: `IMAGE_API_CONFIG = {"api_key": "hf_..."}`
3. Generate 100 images: `python image_generator.py --provider huggingface`
4. Build PDF: `python pdf_builder.py`
5. Design cover in Canva (use dimensions from pdf_builder output)
6. Publish on KDP: https://kdp.amazon.com/en_US/create
7. Track sales, decide next move

**Files**:
- `book_planner.py` — Generate 100-page content plan with prompts
- `image_generator.py` — Generate line drawings via AI (supports local/HF/Replicate/Stability)
- `pdf_builder.py` — Assemble KDP-ready interior PDF (B&W, 8.5x11, 300 DPI)
- `config.py` — Book settings, KDP specs, pricing, API keys
- `book_plans/book_001_plan.json` — 100-page plan (Dog, Cat, Elephant, Car, Bus, Apple, etc.)
- `README.md` — Full documentation
- `QUICKSTART.md` — 30-minute setup guide

**Notes**:
- Project created 2026-08-23 for KDP revenue testing
- Book #1 plan ready (100 pages, variety theme for kids 3-8)
- Tested with placeholder images (5 pages generated successfully)
- Need to set up Hugging Face API (free) or Replicate (paid) for real images
- Manual validation first — only automate after Book #1 proves profitable
- Has `requirements.txt` (Pillow, ReportLab, requests, python-dotenv)

---

## MCP Servers Configuration

MCP (Model Context Protocol) servers extend Devin's capabilities with third-party integrations. Configuration file: `C:\Users\91814\.config\devin\config.json`

### Active MCP Servers

#### 1. **Krea AI** (Image Generation)
- **Purpose**: Generate product images for Amazon listings
- **Transport**: Streamable HTTP
- **Endpoint**: `https://api.krea.ai/mcp`
- **Used by**: `amazon-image-agent/`
- **Status**: ✅ Active

#### 2. **GLM Vision** (Image Analysis - TradingView Charts)
- **Purpose**: Analyze TradingView chart screenshots for pattern recognition, OCR, and technical analysis
- **Model**: GLM-4.5V (Zhipu AI via OpenRouter)
- **Provider**: OpenRouter (English interface, multi-model aggregator)
- **API Key**: Configured (free tier + pay-as-you-go)
- **Cost**: ~$0.0001 per image analysis (very cheap)
- **Status**: ✅ Active (2026-08-23)

**Capabilities**:
- **Pattern recognition**: Identify Cup & Handle, Double Bottom, Darvas Box, etc.
- **OCR**: Extract text from charts (prices, indicators, RSI values, volume)
- **Technical analysis**: Analyze trend strength, support/resistance levels, breakout confirmation
- **Multi-image comparison**: Compare multiple chart timeframes or stocks side-by-side

**Tools available**:
- `analyze_image(file_path, prompt?)` — Analyze a local TradingView chart screenshot
- `analyze_image_url(url, prompt?)` — Analyze a chart from a URL
- `extract_text(file_path)` — OCR to extract all text/numbers from chart
- `describe_image(file_path)` — Get detailed description of chart setup
- `analyze_multiple_images(file_paths, prompt?)` — Compare up to 10 charts

**Model details**:
- **GLM-4.5V**: 106B params, 12B activated (MoE architecture)
- **Context**: 128K tokens
- **Strengths**: State-of-the-art OCR, document parsing, spatial reasoning, video understanding
- **Thinking mode**: Deep reasoning for complex pattern analysis
- **Languages**: English + Chinese (perfect for NSE stock tickers)

**Configuration** (`C:\Users\91814\.config\devin\config.json`):
```json
{
  "mcpServers": {
    "glm-vision": {
      "command": "python",
      "args": ["-m", "glm_vision_mcp_server"],
      "env": {
        "GLM_API_KEY": "sk-or-v1-***",
        "GLM_API_BASE": "https://openrouter.ai/api/v1",
        "GLM_MODEL": "z-ai/glm-4.5v"
      },
      "startup_timeout_sec": 120
    }
  }
}
```

**Installation**:
```powershell
# Install MCP server (already done)
pip install glm-vision-mcp-server

# Test API key
python -c "import requests; r = requests.post('https://openrouter.ai/api/v1/chat/completions', headers={'Authorization': 'Bearer YOUR_KEY', 'Content-Type': 'application/json'}, json={'model': 'z-ai/glm-4.5v', 'messages': [{'role': 'user', 'content': 'OK'}], 'max_tokens': 100}); print(r.status_code, r.json())"
```

**Usage examples**:
```
# In Devin chat after restart:
"Analyze this TradingView chart: F:\projects\claude\scanner-v3\charts\RELIANCE.NS.png"

"Extract all indicator values from this chart: F:\path\to\chart.png"

"Is this a valid Cup & Handle pattern? F:\path\to\chart.png"

"Compare these two timeframes and tell me which is stronger: 
 F:\daily_chart.png and F:\weekly_chart.png"
```

**OpenRouter account**:
- **Dashboard**: https://openrouter.ai/settings/credits
- **API Keys**: https://openrouter.ai/settings/keys
- **Free tier**: ~$1-5 credits (hundreds of analyses)
- **Pricing**: https://openrouter.ai/z-ai/glm-4.5v (very cheap)
- **Add credits**: $5-10 recommended for heavy use

**Alternative models on OpenRouter** (if you want to switch):
- `z-ai/glm-5v-turbo` — Latest, native multimodal agent model (more expensive, requires credits)
- `z-ai/glm-4.6v` — High-fidelity visual understanding, 128K context
- `openai/gpt-4o` — OpenAI's vision model (more expensive)
- `anthropic/claude-3.5-sonnet` — Claude's vision model (most expensive)

**Use cases for scanner projects**:
1. **Verify scanner picks**: Upload TradingView chart, ask "Is this a valid Cup & Handle?"
2. **Extract chart data**: OCR to read exact RSI, MACD, volume values from screenshots
3. **Pattern confirmation**: Get AI second opinion on pattern quality before entering trade
4. **Multi-timeframe analysis**: Compare daily/weekly/monthly charts side-by-side
5. **Backtest validation**: Analyze historical chart screenshots to verify pattern definitions
6. **Training data**: Generate labeled dataset for pattern recognition ML models

**Notes**:
- Restart Devin after config changes to load MCP servers
- Images must be local files or public URLs (no clipboard support yet)
- Max file size: 5MB per image (TradingView screenshots are typically <500KB)
- Supported formats: PNG, JPG, JPEG, WebP, GIF
- Cost tracking: Check OpenRouter dashboard for usage stats
- Free tier should be enough for 100-500 chart analyses

**Bug Bounty Research** (2026-08-23):
- OpenRouter has an active bug bounty program (`safety@openrouter.ai`)
- Research document: `.devin/openrouter_bug_bounty_research.md`
- Focus areas: TOCTOU race conditions, credit bypass, rate limit manipulation
- Testing tools: Race condition tester, credit monitor, endpoint scanner
- **Always get approval before testing** (red-teaming policy requires it)
- Potential vulnerabilities: Credit system race conditions (most common in API credit systems)
- Responsible disclosure: Report to `safety@openrouter.ai`, wait 5 business days
- See research doc for full testing methodology and report template

---

## 🚀 Quick Start: Using GLM Vision (After Restart)

### **Method 1: Direct in Devin Chat (EASIEST)**
After restarting Devin, just paste the image path:
```
Analyze this chart: F:\projects\claude\scanner-v3\charts\PIRAMALFIN_analysis_2026-07-18.png
```

Or ask specific questions:
```
Is this a Cup & Handle? F:\projects\claude\scanner-v3\charts\STOCK_NAME.png
Extract all indicator values from: F:\path\to\chart.png
```

### **Method 2: Python Script (Multi-Provider Router)**
Uses FREE providers first (Gemini → OpenRouter → GPT4Free):
```powershell
cd F:\projects\claude\.devin
python multi_provider_vision.py "F:\path\to\chart.png"
python multi_provider_vision.py "F:\path\to\chart.png" "Is this a valid Cup & Handle?"
```

### **Method 3: Import in Scanner Code**
```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / ".devin"))
from multi_provider_vision import analyze_chart, extract_chart_text

# Analyze pattern
analysis = analyze_chart("charts/RELIANCE.png", "Is this a valid Cup & Handle?")
print(f"AI Analysis: {analysis}")

# Extract OCR text
ocr_text = extract_chart_text("charts/RELIANCE.png")
print(f"Chart Data: {ocr_text}")
```

### **Where to Find Chart Images:**
- Scanner-v3: `F:\projects\claude\scanner-v3\charts\*.png`
- Scanner-v2: `F:\projects\claude\scanner-v2\charts\*.png`
- Chart Visualizer: `F:\projects\claude\chart-visualizer\output\*.png`
- Any TradingView screenshot you save

### **Speed Optimization:**
Current setup takes 5-10 seconds per analysis (OpenRouter API call).

**To make it 2x faster + FREE forever:**
1. Get Gemini API key: https://aistudio.google.com/apikey (30 seconds)
2. Edit `F:\projects\claude\.devin\multi_provider_vision.py` line 23:
   ```python
   "gemini": {
       "api_key": "YOUR_GEMINI_KEY_HERE",  # Paste your key
       "enabled": True  # Change to True
   }
   ```
3. **Result**: 1500 free analyses/day, PERMANENT, 2x faster

### **Cost Summary:**
- **Gemini (recommended)**: $0 forever, 1500/day
- **OpenRouter (current)**: $0.0001/image (~$0.01 per 100 charts)
- **GPT4Free (backup)**: $0 but unstable

### **Full Documentation:**
- Usage guide: `.devin/VISION_USAGE_GUIDE.md`
- Multi-provider script: `.devin/multi_provider_vision.py`
- Bug bounty research: `.devin/openrouter_bug_bounty_research.md`
- Provider comparison: `.devin/vision_providers.json`

### **Tested & Working:**
✅ Analyzed PIRAMALFIN chart successfully (2026-08-23)
✅ Pattern recognition: Cup & Handle detected with 73.6/100 score
✅ OCR: Extracted price levels, indicators, support/resistance
✅ Cost: $0.004 per analysis with OpenRouter
