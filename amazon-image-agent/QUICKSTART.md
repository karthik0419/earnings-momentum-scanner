# Quick Start Guide - Amazon Image Agent

Get up and running in 5 minutes.

---

## 1. Install (1 min)

```powershell
cd F:\projects\claude\amazon-image-agent
pip install -r requirements.txt
```

---

## 2. Get Krea API Key (2 min)

1. Go to https://krea.ai/app/api/tokens
2. Sign in / create account
3. Click "Create new token"
4. Copy the token

---

## 3. Configure (1 min)

```powershell
# Create .env file
cp .env.example .env

# Edit and add your Krea API key
notepad .env
```

Paste your key:
```
KREA_API_KEY=your_actual_key_here
```

Save and close.

---

## 4. Test Run (1 min)

```powershell
python agent.py
```

You should see:
```
Amazon Image Agent Starting
Found 2 new listings to process
Generating 5 images via Krea AI...
✓ Completed processing for B08TEST001
Cycle Summary:
  Listings processed: 2
  Images generated: 10
```

Check results:
```powershell
ls results\
cat logs\agent.log
```

---

## 5. Schedule Daily Runs (30 sec)

```powershell
# Run daily at 9 AM
python scheduler.py create

# Or custom time (e.g., 6 PM)
python scheduler.py create --time 18:00
```

Done! The agent will now run automatically every day.

---

## Next Steps

### Connect Real Amazon Data

Right now the agent uses **mock data** (test listings). To connect real Amazon listings:

**Option A: Amazon Selling Partner API (for sellers)**
1. Register at https://developer.amazonservices.com
2. Get SP-API credentials
3. Add to `.env`:
   ```
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   SP_API_REFRESH_TOKEN=your_token
   ```
4. Uncomment `boto3` and `sp-api` in `requirements.txt`
5. Update `modules/amazon_monitor.py` → `get_new_listings()` to use SP-API

**Option B: Web Scraping (for research)**
1. Uncomment `beautifulsoup4` or `playwright` in `requirements.txt`
2. Update `modules/amazon_monitor.py` → `get_new_listings()` with scraping logic
3. **Important**: Respect Amazon's robots.txt and rate limits

### Track Revenue

```powershell
# Update views for a listing
python -c "from modules.revenue_tracker import RevenueTracker; t = RevenueTracker(); t.update_views('B08TEST001', 1000)"

# Record an order
python -c "from modules.revenue_tracker import RevenueTracker; t = RevenueTracker(); t.record_order('B08TEST001', 2999)"

# View 30-day report
python -c "from modules.revenue_tracker import RevenueTracker; t = RevenueTracker(); t.print_report(30)"
```

### Monitor Logs

```powershell
# Real-time logs
Get-Content logs\agent.log -Tail 50 -Wait

# Check scheduled task
python scheduler.py status
```

---

## Troubleshooting

**"No module named 'requests'"**
→ Run `pip install -r requirements.txt`

**"KREA_API_KEY not found"**
→ Make sure `.env` file exists with your key

**"No new listings found"**
→ Expected! Mock data only returns 2 listings once. Connect real Amazon data (see above).

**Scheduled task not running**
→ Check: `python scheduler.py status`
→ Run manually: `python scheduler.py run`

---

## Files to Know

- `agent.py` - Main loop (run this)
- `scheduler.py` - Task scheduler setup
- `config/settings.py` - Configuration (images per listing, targets, etc.)
- `modules/amazon_monitor.py` - **Edit this** to connect real Amazon data
- `logs/agent.log` - Check this for errors
- `state/agent_state.json` - Processed ASINs
- `state/revenue_log.json` - Revenue data
- `results/` - Generated images

---

## Daily Workflow

1. **Morning**: Agent runs automatically (9 AM by default)
2. **Check logs**: `cat logs\agent.log` or `python scheduler.py status`
3. **Review results**: `ls results\` to see new images
4. **Track revenue**: Update views/orders as they come in
5. **Weekly report**: `python -c "from modules.revenue_tracker import RevenueTracker; t = RevenueTracker(); t.print_report(7)"`

---

**That's it! You're now running an autonomous AI agent for Amazon image generation. 🚀**

Questions? Check `README.md` for full documentation.
