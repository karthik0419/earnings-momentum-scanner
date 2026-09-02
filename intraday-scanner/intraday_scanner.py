"""
NSE Intraday Scanner -- LIVE market data for intraday options trading.

Separate from scanner-v3 (swing). This is for INTRADAY options only.

Pulls real data that intraday traders use:
  1. Index snapshot (NIFTY/BANKNIFTY/etc) -- overall market direction
  2. Sectoral index performance -- which sectors are strong/weak TODAY
  3. Sector rotation ranking -- strongest to weakest sectors (intraday)
  4. Top F&O gainers/losers filtered by TODAY's strong/weak sectors
  5. Volume toppers (institutional activity)
  6. Pre-open session data (morning sentiment)

Does NOT predict. Presents factual live data for YOUR trading decisions.

Usage:
    python intraday_scanner.py
    python intraday_scanner.py --top 20
    python intraday_scanner.py --no-sectors   # skip sector breakdown
"""
import os
import sys
import time
import argparse
import requests
import pandas as pd
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

NSE_BASE = "https://www.nseindia.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
    "X-Requested-With": "XMLHttpRequest",
}

_session = None


def get_session():
    global _session
    if _session is not None:
        return _session
    s = requests.Session()
    s.headers.update(HEADERS)
    try:
        s.get(NSE_BASE, timeout=10)
        time.sleep(1)
    except Exception as e:
        print(f"  [WARN] NSE homepage fetch failed: {e}")
    _session = s
    return s


def fetch_nse_api(path):
    s = get_session()
    url = f"{NSE_BASE}{path}"
    for attempt in range(3):
        try:
            r = s.get(url, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == 2:
                print(f"  [WARN] {path} failed: {e}")
                return None
            time.sleep(2)
    return None


# -- F&O stock list --------------------------------------------------
FNO_FALLBACK = {
    "NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY",
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN",
    "BHARTIARTL", "ITC", "LT", "AXISBANK", "KOTAKBANK",
    "HINDUNILVR", "MARUTI", "ASIANPAINT", "WIPRO", "HCLTECH",
    "TECHM", "TATAMOTORS", "TATASTEEL", "TATACONSUM", "JSWSTEEL",
    "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP",
    "ADANIENT", "ADANIPORTS", "BAJFINANCE", "BAJAJFINSV", "BAJAJ-AUTO",
    "HEROMOTOCO", "EICHERMOT", "M&M", "VEDL", "HINDALCO",
    "COALINDIA", "NTPC", "POWERGRID", "ONGC", "GAIL",
    "DLF", "GODREJPROP", "ULTRACEMCO", "GRASIM", "SHREECEM",
    "BRITANNIA", "TITAN", "SIEMENS", "ABB", "BEL",
    "BHEL", "INDIGO", "PIDILITIND", "IOC", "BPCL",
    "AMBUJACEM", "ACC", "DABUR", "MARICO", "COLPAL",
    "PNB", "BANKBARODA", "CANBK", "UNIONBANK", "INDIANB",
    "MOTHERSON", "BOSCHLTD", "MCDOWELL-N", "UNITEDSPIRITS", "JINDALSTEL",
    "SAIL", "NMDC", "ATUL", "PIIND", "SRF",
    "LALPATHLAB", "FEDERALBNK", "IDFCFIRSTB", "YESBANK", "RBLBANK",
    "BANDHANBNK", "AUBANK", "ICICIPRULI", "SBILIFE", "HDFCLIFE",
    "ICICIGI", "CHOLAFIN", "MUTHOOTFIN", "BAJAJHLDNG", "MAXFINANCIAL",
}


def get_fno_list():
    """Try to get F&O list from the FOSec gainers endpoint."""
    data = fetch_nse_api("/api/live-analysis-variations?index=FOSec")
    if data and "FOSec" in data:
        items = data["FOSec"].get("data", []) if isinstance(data.get("FOSec"), dict) else []
        syms = {d.get("symbol") for d in items if d.get("symbol")}
        if syms:
            return syms
    return FNO_FALLBACK


# -- Sectoral indices (intraday sector rotation) ---------------------
# Map NSE sectoral index name -> our short sector label
SECTORAL_INDICES = {
    "NIFTY AUTO": "AUTO",
    "NIFTY BANK": "BANK",
    "NIFTY FINANCIAL SERVICES 25/50": "FIN",
    "NIFTY FINANCIAL SERVICES EX-BANK": "FIN-EX-BANK",
    "NIFTY FMCG": "FMCG",
    "NIFTY IT": "IT",
    "NIFTY MEDIA": "MEDIA",
    "NIFTY METAL": "METAL",
    "NIFTY PHARMA": "PHARMA",
    "NIFTY PSU BANK": "PSU BANK",
    "NIFTY PRIVATE BANK": "PVT BANK",
    "NIFTY REALTY": "REALTY",
    "NIFTY HEALTHCARE INDEX": "HEALTHCARE",
    "NIFTY CONSUMER DURABLES": "CONSUMER DUR",
    "NIFTY OIL & GAS": "OIL & GAS",
    "NIFTY CHEMICALS": "CHEMICALS",
    "NIFTY CEMENT": "CEMENT",
    "NIFTY ENERGY": "ENERGY",
    "NIFTY INFRASTRUCTURE": "INFRA",
    "NIFTY TELECOM": "TELECOM",
}

# Map F&O stock symbols to sector (for filtering gainers/losers by sector)
# This is a simplified mapping -- covers the most liquid F&O stocks
STOCK_SECTOR_MAP = {
    # AUTO
    "MARUTI": "AUTO", "BAJAJ-AUTO": "AUTO", "HEROMOTOCO": "AUTO", "EICHERMOT": "AUTO",
    "M&M": "AUTO", "TATAMOTORS": "AUTO", "TVSMOTOR": "AUTO", "ASHOKLEY": "AUTO",
    # BANK
    "HDFCBANK": "BANK", "ICICIBANK": "BANK", "SBIN": "BANK", "AXISBANK": "BANK",
    "KOTAKBANK": "BANK", "INDUSINDBK": "BANK", "FEDERALBNK": "BANK", "IDFCFIRSTB": "BANK",
    "YESBANK": "BANK", "RBLBANK": "BANK", "BANDHANBNK": "BANK", "AUBANK": "BANK",
    "PNB": "BANK", "BANKBARODA": "BANK", "CANBK": "BANK", "UNIONBANK": "BANK", "INDIANB": "BANK",
    # PSU BANK (subset of BANK, but tracked separately for sector rotation)
    # FIN
    "BAJFINANCE": "FIN", "BAJAJFINSV": "FIN", "ICICIPRULI": "FIN", "SBILIFE": "FIN",
    "HDFCLIFE": "FIN", "ICICIGI": "FIN", "CHOLAFIN": "FIN", "MUTHOOTFIN": "FIN",
    "BAJAJHLDNG": "FIN", "MAXFINANCIAL": "FIN",
    # IT
    "TCS": "IT", "INFY": "IT", "WIPRO": "IT", "HCLTECH": "IT", "TECHM": "IT",
    "LTIM": "IT", "PERSISTENT": "IT", "COFORGE": "IT",
    # PHARMA / HEALTHCARE
    "SUNPHARMA": "PHARMA", "DRREDDY": "PHARMA", "CIPLA": "PHARMA", "DIVISLAB": "PHARMA",
    "APOLLOHOSP": "PHARMA", "LUPIN": "PHARMA", "AUROPHARMA": "PHARMA", "ALKEM": "PHARMA",
    "ZYDUSLIFE": "PHARMA", "GLENMARK": "PHARMA", "BIOCON": "PHARMA", "CADILAHC": "PHARMA",
    # METAL
    "TATASTEEL": "METAL", "JSWSTEEL": "METAL", "VEDL": "METAL", "HINDALCO": "METAL",
    "SAIL": "METAL", "NMDC": "METAL", "JINDALSTEL": "METAL", "APLAPOLLO": "METAL",
    # FMCG
    "HINDUNILVR": "FMCG", "ITC": "FMCG", "NESTLEIND": "FMCG", "BRITANNIA": "FMCG",
    "DABUR": "FMCG", "MARICO": "FMCG", "COLPAL": "FMCG", "GODREJCP": "FMCG",
    # REALTY
    "DLF": "REALTY", "GODREJPROP": "REALTY", "LODHA": "REALTY", "OBEROIRLTY": "REALTY",
    # OIL & GAS / ENERGY
    "ONGC": "OIL & GAS", "GAIL": "OIL & GAS", "IOC": "OIL & GAS", "BPCL": "OIL & GAS",
    "RELIANCE": "OIL & GAS", "COALINDIA": "ENERGY", "NTPC": "ENERGY", "POWERGRID": "ENERGY",
    "POWERINDIA": "ENERGY",
    # TELECOM
    "BHARTIARTL": "TELECOM", "IDEA": "TELECOM",
    # MEDIA
    # CHEMICALS
    "PIIND": "CHEMICALS", "SRF": "CHEMICALS", "ATUL": "CHEMICALS", "UPL": "CHEMICALS",
    # CEMENT
    "ULTRACEMCO": "CEMENT", "GRASIM": "CEMENT", "SHREECEM": "CEMENT", "AMBUJACEM": "CEMENT", "ACC": "CEMENT",
    # CONSUMER DUR / RETAIL
    "TITAN": "CONSUMER DUR", "ASIANPAINT": "CONSUMER DUR", "PIDILITIND": "CONSUMER DUR",
    "KALYANKJIL": "CONSUMER DUR", "NYKAA": "CONSUMER DUR",
    # INFRA / CAPITAL GOODS
    "LT": "INFRA", "SIEMENS": "INFRA", "ABB": "INFRA", "BEL": "INFRA", "BHEL": "INFRA",
    "CGPOWER": "INFRA",
    # CONSUMER SERVICES
    "INDIGO": "CONSUMER DUR", "CONCOR": "INFRA",
    # MISC
    "ADANIENT": "INFRA", "ADANIPORTS": "INFRA", "MOTHERSON": "AUTO",
    "BOSCHLTD": "AUTO", "MCDOWELL-N": "FMCG", "UNITEDSPIRITS": "FMCG",
    "TATACONSUM": "FMCG", "GODFRYPHLP": "FMCG", "VOLTAS": "CONSUMER DUR",
    "PREMIERENE": "REALTY", "PGEL": "ENERGY", "OIL": "OIL & GAS", "HINDZINC": "METAL",
    "LALPATHLAB": "PHARMA",
}


def get_sectoral_indices():
    """Fetch all sectoral indices and return ranked DataFrame."""
    data = fetch_nse_api("/api/allIndices")
    if not data or "data" not in data:
        return None
    rows = []
    for d in data["data"]:
        idx_name = d.get("index", "")
        if idx_name in SECTORAL_INDICES:
            rows.append({
                "sector": SECTORAL_INDICES[idx_name],
                "nse_index": idx_name,
                "ltp": d.get("last", 0) or 0,
                "prev_close": d.get("previousClose", 0) or 0,
                "change_pct": d.get("percentChange", 0) or 0,
                "advances": d.get("advances", "?"),
                "declines": d.get("declines", "?"),
            })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("change_pct", ascending=False).reset_index(drop=True)
    return df


# -- Index data (broad market) ---------------------------------------
def get_indices():
    data = fetch_nse_api("/api/allIndices")
    if not data or "data" not in data:
        return None
    want = {"NIFTY 50", "NIFTY BANK", "NIFTY FIN SERVICE", "NIFTY MIDCAP 50", "NIFTY IT", "NIFTY AUTO"}
    rows = []
    for d in data["data"]:
        if d.get("index") in want:
            rows.append({
                "index": d.get("index", ""),
                "ltp": d.get("last", 0) or 0,
                "prev_close": d.get("previousClose", 0) or 0,
                "change_pct": d.get("percentChange", 0) or 0,
                "advances": d.get("advances", "?"),
                "declines": d.get("declines", "?"),
            })
    return pd.DataFrame(rows) if rows else None


# -- Top gainers/losers (live) ---------------------------------------
def get_variations(category="gainers"):
    """category = 'gainers' or 'loosers' (NSE spelling)."""
    data = fetch_nse_api(f"/api/live-analysis-variations?index={category}")
    if not data:
        return None, None, None

    def parse_block(key):
        block = data.get(key, {})
        if isinstance(block, dict):
            items = block.get("data", [])
        else:
            items = block or []
        rows = []
        for d in items:
            sym = d.get("symbol", "")
            rows.append({
                "symbol": sym,
                "ltp": d.get("ltp", 0) or 0,
                "open": d.get("open_price", 0) or 0,
                "high": d.get("high_price", 0) or 0,
                "low": d.get("low_price", 0) or 0,
                "prev_close": d.get("prev_price", 0) or 0,
                "change_pct": d.get("perChange", 0) or 0,
                "volume": d.get("trade_quantity", 0) or 0,
                "turnover_cr": round((d.get("turnover", 0) or 0) / 100, 2),
                "sector": STOCK_SECTOR_MAP.get(sym, "OTHER"),
            })
        return pd.DataFrame(rows) if rows else None

    return parse_block("NIFTY"), parse_block("FOSec"), parse_block("allSec")


# -- Volume toppers --------------------------------------------------
def get_volume_toppers():
    data = fetch_nse_api("/api/live-analysis-volume-gainers")
    if not data or "data" not in data:
        return None
    inner = data.get("data", {})
    if isinstance(inner, dict):
        items = inner.get("data", [])
    else:
        items = inner or []
    rows = []
    for d in items:
        sym = d.get("symbol", "")
        rows.append({
            "symbol": sym,
            "ltp": d.get("ltp", 0) or d.get("last_price", 0) or 0,
            "prev_close": d.get("prev_price", 0) or d.get("prevPrice", 0) or 0,
            "change_pct": d.get("perChange", 0) or 0,
            "volume": d.get("trade_quantity", 0) or d.get("trdQty", 0) or 0,
            "sector": STOCK_SECTOR_MAP.get(sym, "OTHER"),
        })
    return pd.DataFrame(rows) if rows else None


# -- Pre-open session data -------------------------------------------
def get_preopen():
    data = fetch_nse_api("/api/market-data-pre-open?key=NIFTY")
    if not data or "data" not in data:
        return None
    rows = []
    for d in data["data"]:
        m = d.get("metadata", {})
        prev = m.get("prevPrice", 0) or 0
        final = m.get("finalPrice", 0) or 0
        chg = m.get("perChange", 0) or 0
        if not chg and prev:
            chg = (final - prev) / prev * 100
        sym = m.get("symbol", "")
        rows.append({
            "symbol": sym,
            "preopen_price": final,
            "prev_close": prev,
            "change_pct": round(chg, 2),
            "volume": m.get("totalQty", 0) or 0,
            "sector": STOCK_SECTOR_MAP.get(sym, "OTHER"),
        })
    return pd.DataFrame(rows) if rows else None


# -- Main ------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="NSE Intraday Scanner -- live data for options trading")
    parser.add_argument("--top", type=int, default=15, help="Top N stocks to show per category")
    parser.add_argument("--no-sectors", action="store_true", help="Skip sector breakdown")
    args = parser.parse_args()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 90)
    print(f"  NSE INTRADAY SCANNER -- {now}")
    print("  Live data for intraday options trading decisions")
    print("  NOTE: This is DATA, not predictions. Trade at your own risk.")
    print("=" * 90)

    # 1. Indices
    print("\n  [1/5] Fetching index snapshot...")
    idx = get_indices()
    if idx is not None and not idx.empty:
        print("\n  -- BROAD MARKET INDICES --")
        print(idx.to_string(index=False, justify="left"))
        nifty_row = idx[idx["index"] == "NIFTY 50"]
        if not nifty_row.empty:
            chg = nifty_row.iloc[0]["change_pct"]
            adv = nifty_row.iloc[0]["advances"]
            dec = nifty_row.iloc[0]["declines"]
            sentiment = "BULLISH" if chg > 0.3 else ("BEARISH" if chg < -0.3 else "NEUTRAL")
            print(f"\n  >> Market sentiment: {sentiment} (NIFTY {chg:+.2f}%, A/D: {adv}/{dec})")
    else:
        print("  [WARN] Index data unavailable")

    # 2. Sectoral indices (intraday sector rotation)
    print("\n  [2/5] Fetching sectoral indices (intraday sector rotation)...")
    sectors = get_sectoral_indices()
    if sectors is not None and not sectors.empty:
        print(f"\n  -- SECTOR ROTATION (ranked by % change, live) --")
        print(sectors[["sector", "change_pct", "advances", "declines", "ltp"]].to_string(index=False, justify="left"))

        # Identify strongest and weakest sectors
        strong = sectors.head(3)
        weak = sectors.tail(3)
        print(f"\n  >> STRONGEST SECTORS TODAY (call option bias):")
        for _, r in strong.iterrows():
            if r["change_pct"] > 0:
                print(f"     {r['sector']:15} {r['change_pct']:+.2f}%  (A/D: {r['advances']}/{r['declines']})")
        print(f"\n  >> WEAKEST SECTORS TODAY (put option bias):")
        for _, r in weak.iterrows():
            if r["change_pct"] < 0:
                print(f"     {r['sector']:15} {r['change_pct']:+.2f}%  (A/D: {r['advances']}/{r['declines']})")

        strong_sectors = set(strong["sector"].tolist())
        weak_sectors = set(weak["sector"].tolist())
    else:
        print("  [WARN] Sectoral data unavailable")
        strong_sectors = set()
        weak_sectors = set()

    # 3. F&O list
    print("\n  [3/5] Fetching F&O stock list...")
    fno = get_fno_list()
    print(f"  F&O stocks tracked: {len(fno)}")

    # 4. Gainers + Losers (F&O filtered, with sector)
    print(f"\n  [4/5] Fetching top gainers & losers (live)...")
    g_nifty, g_fo, g_all = get_variations("gainers")
    l_nifty, l_fo, l_all = get_variations("loosers")

    if g_fo is not None and not g_fo.empty:
        g_display = g_fo.sort_values("change_pct", ascending=False).head(args.top)
        g_source = "F&O Securities"
    elif g_nifty is not None and not g_nifty.empty:
        g_display = g_nifty[g_nifty["symbol"].isin(fno)].sort_values("change_pct", ascending=False).head(args.top)
        g_source = "NIFTY (F&O filtered)"
    else:
        g_display = None
        g_source = None

    if g_display is not None and not g_display.empty:
        print(f"\n  -- TOP {len(g_display)} F&O GAINERS (live, source: {g_source}) --")
        print("  [Call option candidates -- momentum buying]")
        print(g_display[["symbol", "sector", "ltp", "prev_close", "change_pct", "volume", "turnover_cr"]].to_string(index=False, justify="left"))

        # Highlight gainers in strong sectors (highest probability calls)
        if strong_sectors and not args.no_sectors:
            strong_gainers = g_display[g_display["sector"].isin(strong_sectors)]
            if not strong_gainers.empty:
                print(f"\n  >> HIGH-CONVICTION CALL CANDIDATES (gainers in STRONG sectors):")
                for _, r in strong_gainers.iterrows():
                    if r["change_pct"] > 0:
                        print(f"     {r['symbol']:15} [{r['sector']:12}] {r['change_pct']:+.2f}%  turnover={r['turnover_cr']}cr")
    else:
        print("  [WARN] Gainers data unavailable")

    if l_fo is not None and not l_fo.empty:
        l_display = l_fo.sort_values("change_pct", ascending=True).head(args.top)
        l_source = "F&O Securities"
    elif l_nifty is not None and not l_nifty.empty:
        l_display = l_nifty[l_nifty["symbol"].isin(fno)].sort_values("change_pct", ascending=True).head(args.top)
        l_source = "NIFTY (F&O filtered)"
    else:
        l_display = None
        l_source = None

    if l_display is not None and not l_display.empty:
        print(f"\n  -- TOP {len(l_display)} F&O LOSERS (live, source: {l_source}) --")
        print("  [Put option candidates -- momentum selling]")
        print(l_display[["symbol", "sector", "ltp", "prev_close", "change_pct", "volume", "turnover_cr"]].to_string(index=False, justify="left"))

        # Highlight losers in weak sectors (highest probability puts)
        if weak_sectors and not args.no_sectors:
            weak_losers = l_display[l_display["sector"].isin(weak_sectors)]
            if not weak_losers.empty:
                print(f"\n  >> HIGH-CONVICTION PUT CANDIDATES (losers in WEAK sectors):")
                for _, r in weak_losers.iterrows():
                    if r["change_pct"] < 0:
                        print(f"     {r['symbol']:15} [{r['sector']:12}] {r['change_pct']:+.2f}%  turnover={r['turnover_cr']}cr")
    else:
        print("  [WARN] Losers data unavailable")

    # 5. Volume toppers
    print(f"\n  [5/5] Fetching volume toppers (live)...")
    v = get_volume_toppers()
    if v is not None and not v.empty:
        v_fno = v[v["symbol"].isin(fno)].copy()
        v_fno = v_fno.sort_values("volume", ascending=False).head(args.top)
        print(f"\n  -- TOP {len(v_fno)} F&O VOLUME TOPPERS (live) --")
        print("  [High institutional activity -- breakout/breakdown candidates]")
        if not v_fno.empty:
            print(v_fno[["symbol", "sector", "ltp", "prev_close", "change_pct", "volume"]].to_string(index=False, justify="left"))
        else:
            print("  No F&O stocks in volume list")
    else:
        print("  [WARN] Volume data unavailable")

    # Pre-open (bonus)
    print(f"\n  [BONUS] Fetching pre-open session data...")
    po = get_preopen()
    if po is not None and not po.empty:
        po_fno = po[po["symbol"].isin(fno)].copy()
        po_fno = po_fno[po_fno["change_pct"] != 0].sort_values("change_pct", ascending=False).head(args.top)
        if not po_fno.empty:
            print(f"\n  -- PRE-OPEN TOP {len(po_fno)} F&O STOCKS (by % change) --")
            print(po_fno[["symbol", "sector", "preopen_price", "prev_close", "change_pct", "volume"]].to_string(index=False, justify="left"))
        else:
            print("  Pre-open data available but no F&O stocks with non-zero change")
    else:
        print("  [INFO] Pre-open data unavailable (market is past pre-open session)")

    # Trade plan summary
    print("\n" + "=" * 90)
    print("  INTRADAY TRADE PLAN (based on today's sector + stock data):")
    print("  ----------------------------------------------------------------")
    if strong_sectors:
        print(f"  CALL OPTION BIAS (trade with strong sectors):")
        for s in strong_sectors:
            row = sectors[sectors["sector"] == s].iloc[0]
            if row["change_pct"] > 0:
                print(f"    -> {s} sector is UP {row['change_pct']:+.2f}% -- look for call options on its stocks")
    if weak_sectors:
        print(f"  PUT OPTION BIAS (trade with weak sectors):")
        for s in weak_sectors:
            row = sectors[sectors["sector"] == s].iloc[0]
            if row["change_pct"] < 0:
                print(f"    -> {s} sector is DOWN {row['change_pct']:+.2f}% -- look for put options on its stocks")
    print()
    print("  RULES:")
    print("  - Trade WITH the sector trend (calls on strong sectors, puts on weak)")
    print("  - High turnover (>100cr) = institutional participation = more reliable")
    print("  - Low turnover + high % change = retail-driven = avoid (fake move)")
    print("  - ALWAYS check option chain OI before entering -- high OI = strong levels")
    print("  - Intraday options are HIGH RISK -- use strict stop losses (2-3% max)")
    print("  - Exit before 3:15 PM -- don't let options expire in the red")
    print()
    print("  DISCLAIMER: This is live market DATA, not trading advice.")
    print("=" * 90)


if __name__ == "__main__":
    main()
