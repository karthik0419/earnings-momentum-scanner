# Intraday Scanner

NSE intraday scanner for OPTIONS trading. Separate from scanner-v3 (swing trading).

## What it does

Pulls LIVE NSE market data and presents it for intraday options decisions:
1. **Broad market indices** -- NIFTY/BANKNIFTY/MIDCAP/IT/AUTO with advance/decline
2. **Sector rotation (intraday)** -- 19 sectoral indices ranked strongest to weakest
3. **Top F&O gainers** -- filtered to F&O stocks (these have exchange-traded options)
4. **Top F&O losers** -- put option candidates
5. **Volume toppers** -- where institutional money is flowing
6. **Pre-open session data** -- morning sentiment (when available)
7. **Trade plan** -- combines sector strength with stock gainers/losers to highlight high-conviction candidates

## Does NOT predict

This is DATA, not predictions. It surfaces the same information intraday traders look at on NSE's website, but in one place and filtered to F&O stocks (which have options).

## Usage

```powershell
python intraday_scanner.py                  # top 15 per category
python intraday_scanner.py --top 20         # top 20 per category
python intraday_scanner.py --no-sectors     # skip sector breakdown
```

## How to use the output

1. **Check market sentiment** -- if NIFTY is down >0.3% with 40+ declines, bias toward PUTS
2. **Check sector rotation** -- strongest sectors = call option bias, weakest = put option bias
3. **High-conviction calls** = gainers in STRONG sectors with high turnover (>100cr)
4. **High-conviction puts** = losers in WEAK sectors with high turnover (>100cr)
5. **Always check option chain OI** before entering -- high OI = strong support/resistance levels
6. **Use strict stop losses** (2-3% max for intraday options)
7. **Exit before 3:15 PM** -- don't let options expire in the red

## Data source

NSE India official API (`https://www.nseindia.com/api/...`). No API key required but needs cookie session (handled automatically).

## Files

- `intraday_scanner.py` -- main scanner
- `results/` -- output CSVs (future: save scan results for tracking)
