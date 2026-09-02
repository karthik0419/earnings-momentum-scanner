"""
"Cheap options" test -- can we filter for low premium-per-lot and trade PEAD that way?

Reprices all 112 backtest trades three ways:
  ATM monthly   (strike = entry)         -- baseline, 3% spread/side
  OTM 5% monthly (strike = entry*1.05)   -- "cheap" version, 5% spread/side (thinner book)
  OTM 10% monthly (strike = entry*1.10)  -- "very cheap", 6% spread/side

Shows premium-per-lot distribution for each + full P&L economics.
"""
import os, sys
import numpy as np
import pandas as pd
from scipy.stats import norm

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
R_RATE, DTE, IV = 0.065, 30, 0.32


def bs_call(S, K, T, sigma, r=R_RATE):
    if T <= 0:
        return max(S - K, 0.0)
    d1 = (np.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)


tr = pd.read_csv(os.path.join(HERE, "results", "backtest_2026-07-22.csv"))
lots = pd.read_csv(os.path.join(HERE, "fno_lots.csv"))
lots["symbol_ns"] = lots["symbol"] + ".NS"
tr = tr.merge(lots[["symbol_ns", "lot_size"]], left_on="symbol", right_on="symbol_ns", how="left")

configs = [("ATM monthly", 1.00, 0.03), ("OTM 5%", 1.05, 0.05), ("OTM 10%", 1.10, 0.06)]

print("=" * 92)
print("  'CHEAP OPTIONS' TEST -- same 112 PEAD trades, repriced ATM vs OTM  (IV 32%, 30 DTE)")
print("=" * 92)

summary = []
for name, k_mult, spread in configs:
    recs = []
    for _, t in tr.iterrows():
        S0 = float(t["entry_price"])
        K = S0 * k_mult
        R = float(t["return_pct"]) / 100.0
        d_cal = min(int(min(max(int(t["days_held"]), 1), DTE) * 1.4), DTE - 1)
        p_in = bs_call(S0, K, DTE / 365, IV)
        p_out = bs_call(S0 * (1 + R), K, (DTE - d_cal) / 365, IV)
        net = (p_out - p_in) / p_in - (2 * spread + 0.01)
        lot = t["lot_size"]
        recs.append({"net": net * 100, "prem_lot": p_in * lot if pd.notna(lot) else np.nan,
                     "pnl_lot": net * p_in * lot if pd.notna(lot) else np.nan})
    d = pd.DataFrame(recs)
    r = d["net"]
    w, l = r[r > 0], r[r <= 0]
    pf = w.sum() / abs(l.sum()) if l.sum() != 0 else np.inf
    tstat = r.mean() / (r.std() / np.sqrt(len(r)))
    pl = d["prem_lot"].dropna()
    print(f"\n  -- {name} (spread {spread:.0%}/side) --")
    print(f"    premium/lot: p10=Rs{pl.quantile(.1):,.0f}  MEDIAN=Rs{pl.median():,.0f}  p90=Rs{pl.quantile(.9):,.0f}"
          f"  |  lots under Rs15k: {(pl <= 15000).mean()*100:.0f}%  under Rs10k: {(pl <= 10000).mean()*100:.0f}%")
    print(f"    win={((r > 0).mean()*100):.1f}%  avg={r.mean():+.1f}%  MEDIAN={r.median():+.1f}%  "
          f"avgW={w.mean():+.1f}%  avgL={l.mean():+.1f}%  PF={pf:.2f}  t={tstat:.2f}")
    print(f"    avg Rs P&L/lot: {d['pnl_lot'].mean():+,.0f}  |  avg losing lot: {d.loc[d['pnl_lot']<0,'pnl_lot'].mean():,.0f}"
          f"  |  8-loss streak damage: Rs {d.loc[d['pnl_lot']<0,'pnl_lot'].mean()*8:,.0f}")
    summary.append((name, pl.median(), r.mean(), r.median(), (r > 0).mean() * 100, pf, tstat,
                    d.loc[d['pnl_lot'] < 0, 'pnl_lot'].mean() * 8))

print("\n" + "=" * 92)
print("  SIDE BY SIDE")
print("=" * 92)
print(f"  {'config':14} {'med prem/lot':>13} {'avg%':>8} {'MEDIAN%':>8} {'win%':>6} {'PF':>6} {'t':>6} {'8-loss dmg':>12}")
for name, med_pl, avg, med, win, pf, t, dmg in summary:
    print(f"  {name:14} {'Rs'+format(med_pl, ',.0f'):>13} {avg:>+8.1f} {med:>+8.1f} {win:>6.1f} {pf:>6.2f} {t:>6.2f} {'Rs'+format(dmg, ',.0f'):>12}")
