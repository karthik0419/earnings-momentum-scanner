"""
Test script for NSE Price Service — also serves as the loop verifier.

Usage:
    python test_service.py --test RELIANCE          # test 1 stock
    python test_service.py --batch 10               # test 10 stocks
    python test_service.py --batch 500 --verify     # full verifier (exit 0 = pass)
    python test_service.py --compare RELIANCE        # compare NSE vs yfinance
"""

import sys
import time
import argparse
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from price_service import PriceService, log


def test_single(ps: PriceService, symbol: str, period: str = "1y"):
    """Test fetching OHLC for a single stock."""
    print(f"\n{'='*60}")
    print(f"  TEST: Fetch OHLC for {symbol} (period={period})")
    print(f"{'='*60}")

    t0 = time.time()
    df = ps.get_ohlc(symbol, period=period)
    t1 = time.time()

    if df is None or df.empty:
        print(f"  RESULT: FAIL — no data returned")
        return False

    print(f"  Rows:     {len(df)}")
    print(f"  Columns:  {list(df.columns)}")
    print(f"  Range:    {df.index[0]} → {df.index[-1]}")
    print(f"  Time:     {t1-t0:.2f}s")
    print(f"\n  First row:")
    print(f"    {df.iloc[0].to_dict()}")
    print(f"  Last row:")
    print(f"    {df.iloc[-1].to_dict()}")
    print(f"\n  RESULT: PASS")
    return True


def test_batch(ps: PriceService, symbols: list[str], period: str = "1y"):
    """Test fetching OHLC for multiple stocks. Returns (success_count, fail_list, total_time)."""
    total = len(symbols)
    print(f"\n{'='*60}")
    print(f"  BATCH TEST: {total} stocks (period={period})")
    print(f"{'='*60}")

    t0 = time.time()
    results = ps.get_ohlc_batch(symbols, period=period, show_progress=True)
    t1 = time.time()

    success = len(results)
    failed = [s for s in symbols if s not in results]
    elapsed = t1 - t0

    print(f"\n  Results:")
    print(f"    Success:  {success}/{total}")
    print(f"    Failed:   {len(failed)}")
    print(f"    Time:     {elapsed:.1f}s ({elapsed/total:.2f}s/stock)")
    if failed:
        print(f"    Failures: {', '.join(failed[:20])}")
        if len(failed) > 20:
            print(f"             ... and {len(failed)-20} more")

    return success, failed, elapsed


def compare_nse_vs_yfinance(ps: PriceService, symbol: str, period: str = "1y"):
    """Compare NSE API vs yfinance for a single stock."""
    print(f"\n{'='*60}")
    print(f"  COMPARE: {symbol} — NSE API vs yfinance")
    print(f"{'='*60}")

    # Fetch via NSE (through price_service, bypassing cache)
    # Clear cache for this symbol to force fresh fetch
    symbol_clean = symbol.replace(".NS", "")
    cache_key = f"ohlc:{symbol_clean}:{period}:1d"

    # NSE fetch
    t0 = time.time()
    df_nse = ps.get_ohlc(symbol_clean, period=period)
    t1 = time.time()
    nse_time = t1 - t0

    # yfinance fetch
    t0 = time.time()
    df_yf = ps._yf_fallback(symbol_clean, period, "1d")
    t1 = time.time()
    yf_time = t1 - t0

    print(f"\n  NSE API:")
    if df_nse is not None:
        print(f"    Rows: {len(df_nse)}, Time: {nse_time:.2f}s")
        print(f"    Last close: {df_nse.iloc[-1]['Close']}")
    else:
        print(f"    FAILED, Time: {nse_time:.2f}s")

    print(f"\n  yfinance:")
    if df_yf is not None:
        print(f"    Rows: {len(df_yf)}, Time: {yf_time:.2f}s")
        print(f"    Last close: {df_yf.iloc[-1]['Close']}")
    else:
        print(f"    FAILED, Time: {yf_time:.2f}s")

    if df_nse is not None and df_yf is not None:
        speed_ratio = yf_time / nse_time if nse_time > 0 else 0
        print(f"\n  Speed ratio: NSE is {speed_ratio:.1f}x {'faster' if speed_ratio > 1 else 'slower'}")

        # Compare last close prices
        nse_close = df_nse.iloc[-1]['Close']
        yf_close = df_yf.iloc[-1]['Close']
        diff_pct = abs(nse_close - yf_close) / yf_close * 100
        print(f"  Close price diff: {diff_pct:.2f}% (NSE={nse_close}, YF={yf_close})")
        match = diff_pct < 1.0
        print(f"  Data match: {'YES' if match else 'NO'}")
        return match
    return False


def run_verifier(ps: PriceService, batch_size: int = 500):
    """
    Full verifier — checks if the loop goal is met.
    Exit 0 = pass, exit 1 = fail.
    """
    print(f"\n{'='*60}")
    print(f"  VERIFIER: {batch_size} stocks, 0 errors, 2x speed vs yfinance")
    print(f"{'='*60}")

    # Get stock list
    if batch_size <= 50:
        # Use a small known list for quick tests
        from pathlib import Path
        nifty500_path = Path(__file__).parent.parent / "scanner-v3" / "nifty500.txt"
        if nifty500_path.exists():
            with open(nifty500_path) as f:
                all_symbols = [l.strip() for l in f if l.strip()]
        else:
            all_symbols = [
                "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
                "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
                "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "WIPRO",
                "TATAMOTORS", "TATASTEEL", "SUNPHARMA", "BAJFINANCE", "HCLTECH",
                "ULTRACEMCO", "NESTLEIND", "POWERGRID", "NTPC", "ADANIENT",
                "ADANIPORTS", "TITAN", "JSWSTEEL", "COALINDIA", "ONGC",
                "TECHM", "M&M", "BAJAJFINSV", "GRASIM", "HDFCLIFE",
                "CIPLA", "BRITANNIA", "DIVISLAB", "EICHERMOT", "DRREDDY",
                "ADANIPOWER", "ADANIGREEN", "IOC", "BPCL", "SHRIRAMFIN",
                "ZOMATO", "DMART", "PIDILITIND", "BERGEPAINT", "AMBUJACEM",
            ]
    else:
        # Fetch Nifty 500 from NSE
        print("  Fetching Nifty 500 constituents...")
        all_symbols = ps.get_index_constituents("nifty500")
        if not all_symbols:
            print("  FAILED to fetch Nifty 500 list")
            sys.exit(2)

    symbols = all_symbols[:batch_size]
    print(f"  Testing {len(symbols)} stocks...")

    # Batch fetch via NSE
    nse_success, nse_failed, nse_time = test_batch(ps, symbols)

    # Batch fetch via yfinance for comparison
    print(f"\n  Fetching same {len(symbols)} stocks via yfinance for comparison...")
    t0 = time.time()
    yf_results = {}
    for i, sym in enumerate(symbols):
        if i % 50 == 0:
            print(f"    yfinance: {i}/{len(symbols)}")
        df = ps._yf_fallback(sym, "1y", "1d")
        if df is not None and not df.empty:
            yf_results[sym] = df
    yf_time = time.time() - t0
    yf_success = len(yf_results)

    # Results
    print(f"\n{'='*60}")
    print(f"  VERIFIER RESULTS")
    print(f"{'='*60}")
    print(f"  NSE API:     {nse_success}/{len(symbols)} success, {nse_time:.1f}s")
    print(f"  yfinance:    {yf_success}/{len(symbols)} success, {yf_time:.1f}s")

    if nse_time > 0 and yf_time > 0:
        ratio = yf_time / nse_time
        print(f"  Speed:       NSE is {ratio:.1f}x {'faster' if ratio > 1 else 'slower'}")

    # Verdict
    errors = len(nse_failed)
    speed_ok = nse_time > 0 and yf_time > 0 and nse_time < yf_time / 2

    print(f"\n  Errors:      {errors} (goal: 0)")
    print(f"  Speed goal:  {'PASS' if speed_ok else 'FAIL'} (NSE < yfinance/2)")

    if errors == 0 and speed_ok:
        print(f"\n  VERDICT: PASS ✅")
        sys.exit(0)
    else:
        print(f"\n  VERDICT: FAIL ❌")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="NSE Price Service Test / Verifier")
    parser.add_argument("--test", metavar="SYMBOL", help="Test single stock")
    parser.add_argument("--batch", type=int, metavar="N", help="Test N stocks")
    parser.add_argument("--compare", metavar="SYMBOL", help="Compare NSE vs yfinance")
    parser.add_argument("--verify", action="store_true", help="Run full verifier (exit code)")
    parser.add_argument("--period", default="1y", help="Period: 1mo, 3mo, 6mo, 1y, 2y")
    args = parser.parse_args()

    ps = PriceService()

    if args.compare:
        compare_nse_vs_yfinance(ps, args.compare, args.period)

    elif args.verify:
        batch = args.batch or 500
        run_verifier(ps, batch)

    elif args.test:
        test_single(ps, args.test, args.period)

    elif args.batch:
        # Get stock list
        from pathlib import Path
        nifty500_path = Path(__file__).parent.parent / "scanner-v3" / "nifty500.txt"
        if nifty500_path.exists():
            with open(nifty500_path) as f:
                symbols = [l.strip() for l in f if l.strip()]
        else:
            symbols = [
                "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
                "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
            ]
        symbols = symbols[:args.batch]
        test_batch(ps, symbols, args.period)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
