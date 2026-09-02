"""
INTRADAY SECTOR-MOMENTUM BACKTEST -- 365 days, hourly bars, NSE F&O universe.

Tests the intraday_scanner.py strategy honestly:
  Signal at 10:15 IST (close of first hourly bar):
    - first-hour return r1 = bar1_close / prev_day_close - 1
    - sector strength = mean r1 of sector constituents
  Entry: 10:15 (bar1 close). Exit: 15:15 (bar 14:15 close). Stop: 2% adverse.
  Costs: 0.10% round trip (underlying proxy; options are worse -- see report).

Variants:
  A  momentum, no sector filter   (top 3 long >= thr, bottom 3 short <= -thr)
  B  momentum + sector filter     (longs only in top-3 sectors, shorts only in bottom-3)
  C  contrarian fade of A         (short the gainers, long the losers)
  IDX index first-hour momentum   (NIFTY / BANKNIFTY, thr 0.25%, stop 0.75%)

Guards:
  |r1| > 12% skipped (corporate action / ex-date distortion)
  day needs >= 6 bars, first bar at 09:15 IST
Data: yfinance 60m bars (~245 trading days). Cached in cache/.
"""
import os
import sys
import pickle
import argparse
import numpy as np
import pandas as pd
from datetime import datetime, time as dtime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from intraday_scanner import STOCK_SECTOR_MAP

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
RESULTS = os.path.join(HERE, "results")
os.makedirs(CACHE, exist_ok=True)
os.makedirs(RESULTS, exist_ok=True)

COST_RT = 0.0010          # 0.10% round trip on underlying
STOP_PCT = 0.02           # 2% stop for stocks
IDX_STOP = 0.0075         # 0.75% stop for indices
IDX_THR = 0.0025          # 0.25% first-hour threshold for indices
MAX_LONG = 3
MAX_SHORT = 3
SLOTS = 6                 # capital slots for equity curve
CA_GUARD = 0.12           # skip |r1| > 12% (corporate actions)

IST_OPEN = dtime(9, 15)
EXIT_BAR = dtime(14, 15)  # exit at this bar's close = 15:15 price


# ---------------------------------------------------------------- data
def download_all(tickers, label):
    """Download hourly bars, cache to disk. Returns {sym_without_NS: df}."""
    cpath = os.path.join(CACHE, f"hourly_{label}.pkl")
    if os.path.exists(cpath):
        age_h = (datetime.now().timestamp() - os.path.getmtime(cpath)) / 3600
        if age_h < 24:
            with open(cpath, "rb") as f:
                return pickle.load(f)
    import yfinance as yf
    out = {}
    chunk = 25
    for i in range(0, len(tickers), chunk):
        batch = tickers[i:i + chunk]
        df = yf.download(batch, period="1y", interval="60m", progress=False,
                         auto_adjust=True, group_by="ticker", threads=True)
        for t in batch:
            try:
                sub = df[t].dropna(how="all") if isinstance(df.columns, pd.MultiIndex) else df.dropna(how="all")
                if sub is None or sub.empty:
                    continue
                sub = sub.copy()
                sub.index = sub.index.tz_convert("Asia/Kolkata").tz_localize(None)
                out[t.replace(".NS", "")] = sub[["Open", "High", "Low", "Close"]].dropna()
            except Exception:
                continue
        print(f"    downloaded {min(i+chunk, len(tickers))}/{len(tickers)} tickers, got {len(out)} with data")
    with open(cpath, "wb") as f:
        pickle.dump(out, f)
    return out


def build_day_table(data):
    """{date: {sym: dict(r1, entry, bars_after, exit_px)}}"""
    table = {}
    for sym, df in data.items():
        df = df.sort_index()
        dates = pd.Series(df.index.date, index=df.index)
        prev_close = None
        for d, day_bars in df.groupby(dates.values):
            day_bars = day_bars.sort_index()
            if prev_close is not None and len(day_bars) >= 6 and day_bars.index[0].time() == IST_OPEN:
                b1 = day_bars.iloc[0]
                r1 = b1["Close"] / prev_close - 1.0
                exit_rows = day_bars[day_bars.index.map(lambda x: x.time() == EXIT_BAR)]
                if len(exit_rows) == 1 and abs(r1) <= CA_GUARD:
                    after = day_bars[(day_bars.index > day_bars.index[0]) &
                                     (day_bars.index.map(lambda x: x.time() <= EXIT_BAR))]
                    table.setdefault(d, {})[sym] = {
                        "r1": r1, "entry": float(b1["Close"]),
                        "bars": after[["Open", "High", "Low", "Close"]].values,
                        "exit_px": float(exit_rows.iloc[0]["Close"]),
                    }
            prev_close = float(day_bars.iloc[-1]["Close"])
    return table


# ---------------------------------------------------------------- sim
def simulate(rec, side, stop_pct=STOP_PCT):
    """Returns (net_return, stopped). side: +1 long, -1 short."""
    entry = rec["entry"]
    stop = entry * (1 - stop_pct) if side == 1 else entry * (1 + stop_pct)
    for o, h, l, c in rec["bars"]:
        if side == 1:
            if o <= stop:
                return (o / entry - 1) - COST_RT, True
            if l <= stop:
                return (stop / entry - 1) - COST_RT, True
        else:
            if o >= stop:
                return (1 - o / entry) - COST_RT, True
            if h >= stop:
                return (1 - stop / entry) - COST_RT, True
    raw = rec["exit_px"] / entry - 1
    return (raw if side == 1 else -raw) - COST_RT, False


def run_variant(table, thr, use_sector, fade=False):
    trades = []
    for d in sorted(table):
        day = table[d]
        if len(day) < 30:
            continue
        if use_sector:
            sec_r = {}
            for sym, rec in day.items():
                sec_r.setdefault(STOCK_SECTOR_MAP.get(sym, "OTHER"), []).append(rec["r1"])
            sec_avg = {s: np.mean(v) for s, v in sec_r.items() if len(v) >= 2 and s != "OTHER"}
            ranked = sorted(sec_avg, key=sec_avg.get, reverse=True)
            strong = {s for s in ranked[:3] if sec_avg[s] > 0}
            weak = {s for s in ranked[-3:] if sec_avg[s] < 0}
        longs, shorts = [], []
        for sym, rec in day.items():
            sec = STOCK_SECTOR_MAP.get(sym, "OTHER")
            if rec["r1"] >= thr and (not use_sector or sec in strong):
                longs.append((sym, rec))
            elif rec["r1"] <= -thr and (not use_sector or sec in weak):
                shorts.append((sym, rec))
        longs = sorted(longs, key=lambda x: -x[1]["r1"])[:MAX_LONG]
        shorts = sorted(shorts, key=lambda x: x[1]["r1"])[:MAX_SHORT]
        for sym, rec in longs:
            side = -1 if fade else 1
            ret, stopped = simulate(rec, side)
            trades.append({"date": d, "symbol": sym, "sector": STOCK_SECTOR_MAP.get(sym, "OTHER"),
                           "dir": "SHORT" if fade else "LONG", "r1_pct": round(rec["r1"] * 100, 2),
                           "entry": rec["entry"], "net_ret_pct": round(ret * 100, 3), "stopped": stopped})
        for sym, rec in shorts:
            side = 1 if fade else -1
            ret, stopped = simulate(rec, side)
            trades.append({"date": d, "symbol": sym, "sector": STOCK_SECTOR_MAP.get(sym, "OTHER"),
                           "dir": "LONG" if fade else "SHORT", "r1_pct": round(rec["r1"] * 100, 2),
                           "entry": rec["entry"], "net_ret_pct": round(ret * 100, 3), "stopped": stopped})
    return pd.DataFrame(trades)


def run_index(table_idx, sym):
    trades = []
    for d in sorted(table_idx):
        if sym not in table_idx[d]:
            continue
        rec = table_idx[d][sym]
        if rec["r1"] >= IDX_THR:
            side, lbl = 1, "LONG"
        elif rec["r1"] <= -IDX_THR:
            side, lbl = -1, "SHORT"
        else:
            continue
        ret, stopped = simulate(rec, side, stop_pct=IDX_STOP)
        trades.append({"date": d, "symbol": sym, "dir": lbl, "r1_pct": round(rec["r1"] * 100, 2),
                       "net_ret_pct": round(ret * 100, 3), "stopped": stopped})
    return pd.DataFrame(trades)


# ---------------------------------------------------------------- metrics
def metrics(tr, n_days):
    if tr is None or tr.empty:
        return None
    r = tr["net_ret_pct"]
    wins, losses = r[r > 0], r[r <= 0]
    pf = wins.sum() / abs(losses.sum()) if losses.sum() != 0 else np.inf
    day_ret = tr.groupby("date")["net_ret_pct"].sum() / SLOTS / 100
    eq = (1 + day_ret).cumprod()
    dd = ((eq - eq.cummax()) / eq.cummax()).min() * 100
    all_days = pd.Series(0.0, index=range(n_days))
    all_days.iloc[:len(day_ret)] = day_ret.values  # pad zero days for sharpe honesty
    sharpe = day_ret.mean() / day_ret.std() * np.sqrt(252) if day_ret.std() > 0 else 0
    return {
        "trades": len(tr), "trades_per_day": round(len(tr) / max(tr["date"].nunique(), 1), 2),
        "win_rate": round(len(wins) / len(tr) * 100, 1),
        "avg_ret": round(r.mean(), 3), "median_ret": round(r.median(), 3),
        "avg_win": round(wins.mean(), 3) if len(wins) else 0,
        "avg_loss": round(losses.mean(), 3) if len(losses) else 0,
        "profit_factor": round(pf, 2), "stop_rate": round(tr["stopped"].mean() * 100, 1),
        "total_sum_pct": round(r.sum(), 1), "equity_ret_pct": round((eq.iloc[-1] - 1) * 100, 1),
        "max_dd_pct": round(dd, 1), "sharpe": round(sharpe, 2),
    }


def print_metrics(name, m):
    if m is None:
        print(f"\n  {name}: NO TRADES")
        return
    print(f"\n  {name}")
    print(f"    trades={m['trades']} ({m['trades_per_day']}/day)  win={m['win_rate']}%  "
          f"avg={m['avg_ret']:+.3f}%  med={m['median_ret']:+.3f}%")
    print(f"    avg_win={m['avg_win']:+.3f}%  avg_loss={m['avg_loss']:+.3f}%  "
          f"PF={m['profit_factor']}  stopped={m['stop_rate']}%")
    print(f"    equity({SLOTS} slots)={m['equity_ret_pct']:+.1f}%  maxDD={m['max_dd_pct']}%  "
          f"sharpe={m['sharpe']}  sum_of_trades={m['total_sum_pct']:+.1f}%")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh", action="store_true", help="ignore cache, redownload")
    args = ap.parse_args()
    if args.fresh:
        for f in os.listdir(CACHE):
            if f.startswith("hourly_"):
                os.remove(os.path.join(CACHE, f))

    print("=" * 88)
    print("  INTRADAY SECTOR-MOMENTUM BACKTEST -- last 365 days, hourly bars, NSE F&O universe")
    print("  Entry 10:15 | Exit 15:15 | Stop 2% | Cost 0.10% RT | Max 3L+3S/day | CA guard 12%")
    print("=" * 88)

    universe = sorted(STOCK_SECTOR_MAP.keys())
    print(f"\n  Universe: {len(universe)} F&O stocks  |  downloading hourly data (cached 24h)...")
    data = download_all([s + ".NS" for s in universe], "stocks")
    print(f"  Got data for {len(data)} stocks")
    table = build_day_table(data)
    n_days = len(table)
    print(f"  Trading days with signals: {n_days}")

    print("\n  Downloading index data...")
    idx_data = download_all(["^NSEI", "^NSEBANK"], "indices")
    idx_table = build_day_table(idx_data)

    # -------- variants
    results = {}
    for thr, tag in [(0.01, "B thr=1%"), (0.02, "B thr=2%"), (0.03, "B thr=3%")]:
        tr = run_variant(table, thr, use_sector=True)
        results[f"VARIANT {tag} (momentum + SECTOR filter -- THE STRATEGY)"] = tr
    results["VARIANT A thr=2% (pure momentum, NO sector filter)"] = run_variant(table, 0.02, use_sector=False)
    results["VARIANT C thr=2% (CONTRARIAN FADE of A)"] = run_variant(table, 0.02, use_sector=False, fade=True)

    print("\n" + "=" * 88)
    print("  RESULTS -- UNDERLYING RETURNS (options translation at the end)")
    print("=" * 88)
    for name, tr in results.items():
        print_metrics(name, metrics(tr, n_days))

    # direction breakdown for the strategy @2%
    strat = results["VARIANT B thr=2% (momentum + SECTOR filter -- THE STRATEGY)"]
    if not strat.empty:
        print("\n  " + "-" * 60)
        print("  STRATEGY (B thr=2%) -- BREAKDOWN BY DIRECTION")
        for dr in ["LONG", "SHORT"]:
            print_metrics(f"  {dr} only", metrics(strat[strat["dir"] == dr], n_days))
        print("\n  STRATEGY (B thr=2%) -- BY SECTOR (top 8 by trade count)")
        sec_stats = strat.groupby("sector").agg(
            trades=("net_ret_pct", "size"), win_rate=("net_ret_pct", lambda x: round((x > 0).mean() * 100, 1)),
            avg_ret=("net_ret_pct", lambda x: round(x.mean(), 3)), total=("net_ret_pct", lambda x: round(x.sum(), 1)),
        ).sort_values("trades", ascending=False).head(8)
        print(sec_stats.to_string())
        print("\n  STRATEGY (B thr=2%) -- MONTHLY SUM OF TRADE RETURNS (%)")
        strat2 = strat.copy()
        strat2["month"] = pd.to_datetime(strat2["date"]).dt.to_period("M")
        monthly = strat2.groupby("month")["net_ret_pct"].agg(["sum", "size", lambda x: round((x > 0).mean() * 100, 0)])
        monthly.columns = ["sum_pct", "trades", "win_%"]
        print(monthly.round(1).to_string())

    # -------- indices
    print("\n" + "=" * 88)
    print(f"  INDEX FIRST-HOUR MOMENTUM (thr {IDX_THR*100:.2f}%, stop {IDX_STOP*100:.2f}%)")
    print("=" * 88)
    for sym in ["^NSEI", "^NSEBANK"]:
        tr = run_index(idx_table, sym)
        print_metrics(f"{sym} first-hour momentum", metrics(tr, n_days))
        if not tr.empty:
            for dr in ["LONG", "SHORT"]:
                print_metrics(f"  {sym} {dr} only", metrics(tr[tr["dir"] == dr], n_days))

    # -------- save trades
    for name, tr in results.items():
        if not tr.empty:
            tag = name.split("(")[0].strip().replace(" ", "_").lower()
            tr.to_csv(os.path.join(RESULTS, f"backtest_{tag}.csv"), index=False)
    print(f"\n  Trade logs saved to {RESULTS}\\backtest_variant_*.csv")


if __name__ == "__main__":
    main()
