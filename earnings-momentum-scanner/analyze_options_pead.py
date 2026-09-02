"""
PEAD OPTIONS ECONOMICS -- translate stock backtest trades into ATM monthly option trades.

For each backtest trade:
  entry: buy ATM call (strike=entry price), 30 DTE, IV 32% (typical post-crush F&O stock)
  exit:  reprice via Black-Scholes at exit day (spot moved by return_pct, time decayed by days_held)
  friction: 3% of premium spread each side + 1% brokerage/STT = ~7% RT on premium

Also computes lot-size capital requirements from fno_lots.csv.

Usage: python analyze_options_pead.py [--csv results/backtest_2026-07-22.csv] [--iv 0.32]
"""
import os, sys, argparse
import numpy as np
import pandas as pd
from scipy.stats import norm

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))

R_RATE = 0.065
DTE = 30
SPREAD = 0.03      # spread cost each side, fraction of premium
BROKER = 0.01      # brokerage + STT etc, fraction of premium RT


def bs_call(S, K, T, sigma, r=R_RATE):
    if T <= 0:
        return max(S - K, 0.0)
    d1 = (np.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(HERE, "results", "backtest_2026-07-22.csv"))
    ap.add_argument("--iv", type=float, default=0.32)
    args = ap.parse_args()

    tr = pd.read_csv(args.csv)
    lots = pd.read_csv(os.path.join(HERE, "fno_lots.csv"))
    lots["symbol_ns"] = lots["symbol"] + ".NS"
    tr = tr.merge(lots[["symbol_ns", "lot_size"]], left_on="symbol", right_on="symbol_ns", how="left")

    print("=" * 80)
    print(f"  PEAD -> ATM MONTHLY CALL OPTIONS TRANSLATION  (IV={args.iv:.0%}, {DTE} DTE)")
    print(f"  Friction: {SPREAD:.0%} spread/side + {BROKER:.0%} costs = ~{(2*SPREAD+BROKER):.0%} of premium RT")
    print("=" * 80)
    print(f"\n  Stock trades loaded: {len(tr)}")

    recs = []
    for _, t in tr.iterrows():
        S0 = float(t["entry_price"])
        R = float(t["return_pct"]) / 100.0
        d_cal = min(int(min(max(int(t["days_held"]), 1), DTE) * 1.4), DTE - 1)
        prem_in = bs_call(S0, S0, DTE / 365, args.iv)
        prem_out = bs_call(S0 * (1 + R), S0, (DTE - d_cal) / 365, args.iv)
        gross = (prem_out - prem_in) / prem_in
        net = gross - (2 * SPREAD + BROKER)
        lot = t["lot_size"] if pd.notna(t.get("lot_size")) else np.nan
        recs.append({
            "symbol": t["symbol"], "underlying_ret_pct": round(R * 100, 2),
            "days_held": t["days_held"], "exit_reason": t["exit_reason"],
            "prem_pct_of_spot": round(prem_in / S0 * 100, 2),
            "opt_gross_pct": round(gross * 100, 1), "opt_net_pct": round(net * 100, 1),
            "lot_size": lot,
            "prem_per_lot_rs": round(prem_in * lot, 0) if pd.notna(lot) else np.nan,
            "pnl_per_lot_rs": round(net * prem_in * lot, 0) if pd.notna(lot) else np.nan,
        })
    od = pd.DataFrame(recs)

    # ---- underlying vs option comparison
    u = tr["return_pct"]
    o = od["opt_net_pct"]
    print("\n  -- UNDERLYING (stock) --")
    print(f"    win={_wr(u)}%  avg={u.mean():+.2f}%  med={u.median():+.2f}%  "
          f"avgW={u[u>0].mean():+.2f}%  avgL={u[u<=0].mean():+.2f}%  PF={_pf(u):.2f}")
    print("\n  -- OPTIONS (net of friction, on premium) --")
    print(f"    win={_wr(o)}%  avg={o.mean():+.1f}%  med={o.median():+.1f}%  "
          f"avgW={o[o>0].mean():+.1f}%  avgL={o[o<=0].mean():+.1f}%  PF={_pf(o):.2f}")
    t_stat = o.mean() / (o.std() / np.sqrt(len(o))) if o.std() > 0 else 0
    print(f"    t-stat on option expectancy: {t_stat:.2f}")

    # ---- by exit reason
    print("\n  -- OPTION RESULT BY EXIT REASON --")
    print(od.groupby("exit_reason").agg(
        n=("opt_net_pct", "size"), avg_opt=("opt_net_pct", lambda x: round(x.mean(), 1)),
        avg_und=("underlying_ret_pct", lambda x: round(x.mean(), 2)),
        avg_days=("days_held", lambda x: round(x.mean(), 1))).to_string())

    # ---- capital requirements
    ok = od.dropna(subset=["prem_per_lot_rs"])
    print(f"\n  -- CAPITAL REALITY (premium per lot, Rs) -- ({len(ok)} trades with lot data)")
    q = ok["prem_per_lot_rs"].quantile([0.1, 0.25, 0.5, 0.75, 0.9])
    print(f"    p10={q[0.1]:,.0f}  p25={q[0.25]:,.0f}  MEDIAN={q[0.5]:,.0f}  p75={q[0.75]:,.0f}  p90={q[0.9]:,.0f}")
    print(f"    avg loss per losing lot: Rs {ok.loc[ok['pnl_per_lot_rs']<0,'pnl_per_lot_rs'].mean():,.0f}")
    print(f"    worst single-lot loss:   Rs {ok['pnl_per_lot_rs'].min():,.0f}")
    print(f"    best single-lot win:     Rs {ok['pnl_per_lot_rs'].max():,.0f}")
    # losing streak
    seq = (od.sort_values("symbol").reset_index()["opt_net_pct"] <= 0).astype(int)
    max_streak = (seq.groupby((seq != seq.shift()).cumsum()).cumsum()).max()
    print(f"    max consecutive option losses (any order): ~{int(max_streak)}")

    out = os.path.join(HERE, "results", "options_translation.csv")
    od.to_csv(out, index=False)
    print(f"\n  Saved: {out}")


def _wr(x):
    return round((x > 0).mean() * 100, 1)


def _pf(x):
    w, l = x[x > 0].sum(), abs(x[x <= 0].sum())
    return w / l if l > 0 else np.inf


if __name__ == "__main__":
    main()
