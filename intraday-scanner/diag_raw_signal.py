"""Diagnostic: raw signal quality -- no stops, no costs. 10:15 entry -> 15:15 exit."""
import sys
import numpy as np
import pandas as pd
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import backtest_intraday as bt
from intraday_scanner import STOCK_SECTOR_MAP

data = bt.download_all([s + ".NS" for s in sorted(STOCK_SECTOR_MAP.keys())], "stocks")
table = bt.build_day_table(data)

def raw_run(thr, use_sector):
    rets_l, rets_s = [], []
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
                longs.append(rec)
            elif rec["r1"] <= -thr and (not use_sector or sec in weak):
                shorts.append(rec)
        longs = sorted(longs, key=lambda r: -r["r1"])[:3]
        shorts = sorted(shorts, key=lambda r: r["r1"])[:3]
        rets_l += [r["exit_px"] / r["entry"] - 1 for r in longs]
        rets_s += [1 - r["exit_px"] / r["entry"] for r in shorts]
    return np.array(rets_l), np.array(rets_s)

print("RAW SIGNAL (no stop, no cost): does the 10:15->15:15 move continue the morning direction?")
print(f"{'config':38} {'n':>5} {'avg%':>8} {'med%':>8} {'win%':>6} {'t-stat':>7}")
for thr, sec, label in [(0.01, True, "B thr=1% sector"), (0.02, True, "B thr=2% sector"),
                        (0.03, True, "B thr=3% sector"), (0.02, False, "A thr=2% no-sector"),
                        (0.05, False, "A thr=5% no-sector (extreme)")]:
    l, s = raw_run(thr, sec)
    both = np.concatenate([l, s])
    for arr, name in [(l, "LONG"), (s, "SHORT"), (both, "ALL")]:
        if len(arr) == 0:
            continue
        t = arr.mean() / (arr.std() / np.sqrt(len(arr))) if arr.std() > 0 else 0
        print(f"{label + ' ' + name:38} {len(arr):5} {arr.mean()*100:8.3f} {np.median(arr)*100:8.3f} "
              f"{(arr > 0).mean()*100:6.1f} {t:7.2f}")
    print()
