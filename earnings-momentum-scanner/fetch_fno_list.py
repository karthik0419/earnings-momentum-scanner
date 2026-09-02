"""Fetch NSE F&O stock list + lot sizes -> fno_list.txt + fno_lots.csv"""
import sys, io, time, requests
import pandas as pd
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://www.nseindia.com/",
}

urls = [
    "https://nsearchives.nseindia.com/content/fo/fo_mktlots.csv",
    "https://archives.nseindia.com/content/fo/fo_mktlots.csv",
]

text = None
s = requests.Session()
s.headers.update(HEADERS)
try:
    s.get("https://www.nseindia.com", timeout=10)
    time.sleep(1)
except Exception:
    pass
for u in urls:
    try:
        r = s.get(u, timeout=20)
        if r.status_code == 200 and "SYMBOL" in r.text.upper():
            text = r.text
            print(f"Fetched: {u}")
            break
        print(f"{u} -> {r.status_code}")
    except Exception as e:
        print(f"{u} -> {e}")

if text is None:
    print("FAILED to fetch lot file")
    sys.exit(1)

rows = []
for line in text.splitlines()[1:]:
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 3 or not parts[1]:
        continue
    sym = parts[1]
    # skip index rows and header repeats
    if sym in ("NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50", "Symbol", "SYMBOL") or "NIFTY" in sym:
        continue
    lot = None
    for p in parts[2:]:
        if p.isdigit():
            lot = int(p)
            break
    if lot:
        rows.append({"symbol": sym, "lot_size": lot})

df = pd.DataFrame(rows).drop_duplicates("symbol").sort_values("symbol")
print(f"F&O stocks: {len(df)}")
df.to_csv("fno_lots.csv", index=False)
with open("fno_list.txt", "w") as f:
    for sym in df["symbol"]:
        f.write(sym + ".NS\n")
print("Wrote fno_list.txt + fno_lots.csv")
print(df.head(10).to_string(index=False))
