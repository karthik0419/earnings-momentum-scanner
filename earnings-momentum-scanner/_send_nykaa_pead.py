"""Send NYKAA PEAD scan to Telegram."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scanner-v3'))
from telegram_notify import send_telegram, _get_credentials

token, chat_id = _get_credentials()

msg = """<b>PEAD Scanner — NYKAA.NS</b>
<b>Date: 2026-08-03 | Current: Rs 344.90</b>

━━━━━━━━━━━━━━━━━━━
<b>EARNINGS DATA (13 quarters)</b>
━━━━━━━━━━━━━━━━━━━
Last 4 quarters:
  Jun 2025: NP=24.0 Cr  EPS=0.08
  Sep 2025: NP=33.0 Cr  EPS=0.12
  Dec 2025: NP=68.0 Cr  EPS=0.22
  Mar 2026: NP=79.0 Cr  EPS=0.27

Consistency score: 100/100
Avg YoY growth: +175.7%
Growth quarters: 4/4 (all profitable, all growing)

━━━━━━━━━━━━━━━━━━━
<b>HISTORICAL EARNINGS REACTIONS</b>
━━━━━━━━━━━━━━━━━━━
  Jun 2025: spike +5.08%
  Sep 2025: spike +6.08%
  Dec 2025: spike +7.24%
  Mar 2026: spike +1.00%
  Average spike: +4.85%

NYKAA consistently spikes 5-7% on earnings days.
Last quarter (Mar 2026) was weak — only +1% spike.

━━━━━━━━━━━━━━━━━━━
<b>PEAD ENTRY SIGNAL</b>
━━━━━━━━━━━━━━━━━━━
<b>NO ENTRY — Outside post-result window</b>

Last result date: May 21, 2026 (75 days ago)
Post-result window: 45 days
Current mode: OUTSIDE_WINDOW

The PEAD strategy only enters within 45 days of earnings.
NYKAA's earnings were 75 days ago — too late for a PEAD entry.

━━━━━━━━━━━━━━━━━━━
<b>PROFIT PROJECTION (current quarter)</b>
━━━━━━━━━━━━━━━━━━━
  Projected net profit: 70.28 Cr
  Projected EPS: 0.24
  YoY growth: +162.1%
  Confidence: low (next quarter not yet reported)

━━━━━━━━━━━━━━━━━━━
<b>PEAD SCORE: 70.0 / 100</b>
━━━━━━━━━━━━━━━━━━━
  Earnings quality:    30/30 (perfect)
  Historical reaction: 15/15 (strong)
  Sustained bonus:      0/10 (not in window)
  Entry quality:        0/20 (no entry signal)
  Sector momentum:     15/15 (Services sector hot)
  Profit growth:       10/10 (175% YoY growth)

━━━━━━━━━━━━━━━━━━━
<b>VERDICT</b>
━━━━━━━━━━━━━━━━━━━
NYKAA has EXCELLENT earnings quality (100/100 consistency,
175% YoY growth, profitable every quarter). It spikes 5-7%
on earnings days historically.

<b>BUT — no PEAD entry right now.</b> Earnings were 75 days ago,
outside the 45-day post-result window. The PEAD edge only
works in the first 45 days after results.

The v3 scanner's Cup & Handle breakout (Rs 335 breakout,
T1 Rs 400) is the active trade for NYKAA — not PEAD.

<b>Next earnings:</b> Likely Aug-Sep 2026 (Q1 FY27).
Watch for PEAD entry signal after results announcement.

━━━━━━━━━━━━━━━━━━━
Not financial advice. For research only."""

ok = send_telegram(token, chat_id, msg)
print("Telegram: %s" % ("Sent" if ok else "Failed"))
