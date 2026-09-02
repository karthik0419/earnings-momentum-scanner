# Amazon Image Agent

**Automated AI agent for generating Amazon product listing images using Krea AI**

An autonomous Python agent that monitors Amazon listings, generates high-quality product images using Krea AI's MCP server, and tracks revenue performance. Runs on a schedule (daily loop) to continuously improve your product listings.

---

## Features

- 🤖 **Autonomous Loop**: Runs daily via Windows Task Scheduler
- 🎨 **AI Image Generation**: Uses Krea AI MCP server for professional product images
- 📊 **Revenue Tracking**: Monitors conversion rates, orders, and ROI
- 🔄 **State Management**: Tracks processed listings, avoids duplicates
- 📈 **Performance Analytics**: Reports on top performers and targets
- 🎯 **Multi-style Images**: Generates realistic, lifestyle, minimal, and artistic variants

---

## Project Structure

```
amazon-image-agent/
├── agent.py                    # Main agent loop
├── scheduler.py                # Windows Task Scheduler setup
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── config/
│   └── settings.py            # Configuration constants
├── modules/
│   ├── krea_client.py         # Krea AI image generation
│   ├── amazon_monitor.py      # Amazon listing monitor
│   └── revenue_tracker.py     # Revenue & analytics
├── logs/                      # Agent logs
├── state/                     # State files (processed ASINs, revenue data)
└── results/                   # Generated images & metadata
```

---

## Setup

### 1. Install Dependencies

```powershell
cd F:\projects\claude\amazon-image-agent
pip install -r requirements.txt
```

### 2. Configure Krea AI

The Krea AI MCP server is already configured in your Devin config at:
`C:\Users\91814\.config\devin\config.json`

**Get your Krea API key:**
1. Go to https://krea.ai/app/api/tokens
2. Create a new API token
3. Copy the token

### 3. Set Environment Variables

```powershell
# Copy the example file
cp .env.example .env

# Edit .env and add your credentials
notepad .env
```

Fill in:
- `KREA_API_KEY`: Your Krea AI API token
- `AMAZON_MARKETPLACE`: Your target marketplace (amazon.in, amazon.com, etc.)
- `AMAZON_SELLER_ID`: Your Amazon seller ID (if applicable)

### 4. Configure Amazon Integration

**Option A: Amazon Selling Partner API (Recommended for sellers)**
- Register for SP-API access at https://developer.amazonservices.com
- Add credentials to `.env`
- Uncomment `boto3` and `sp-api` in `requirements.txt`
- Update `amazon_monitor.py` to use SP-API

**Option B: Web Scraping (For research/testing)**
- Uncomment `beautifulsoup4` or `playwright` in `requirements.txt`
- Update `amazon_monitor.py` with scraping logic
- **Note**: Respect Amazon's robots.txt and terms of service

### 5. Test the Agent

```powershell
# Run one cycle manually
python agent.py
```

Check the output in:
- Console: Real-time logs
- `logs/agent.log`: Detailed logs
- `results/`: Generated image metadata
- `state/agent_state.json`: Processed ASINs
- `state/revenue_log.json`: Revenue data

---

## Usage

### Manual Run

```powershell
# Run one agent cycle
python agent.py
```

### Schedule Daily Runs

```powershell
# Create scheduled task (runs daily at 9 AM)
python scheduler.py create

# Custom time (e.g., 6 PM)
python scheduler.py create --time 18:00

# Check task status
python scheduler.py status

# Run task immediately (for testing)
python scheduler.py run

# Delete scheduled task
python scheduler.py delete
```

### Revenue Tracking

```powershell
# The agent automatically tracks listings after image generation
# To manually record orders and views, use the revenue_tracker module:

python -c "
from modules.revenue_tracker import RevenueTracker
tracker = RevenueTracker()

# Update views for a listing
tracker.update_views('B08TEST001', views=1500)

# Record an order
tracker.record_order('B08TEST001', order_value=2999)

# Print 30-day report
tracker.print_report(days=30)
"
```

---

## Configuration

Edit `config/settings.py` to customize:

```python
# Image generation
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024
IMAGES_PER_LISTING = 5  # Generate 5 images per product

# Loop settings
LOOP_INTERVAL_HOURS = 24  # Run once per day
MAX_LISTINGS_PER_RUN = 10  # Process max 10 listings per run

# Revenue targets
CONVERSION_RATE_TARGET = 0.03  # 3% target
AVG_ORDER_VALUE_TARGET = 500  # Rs 500 average order
```

---

## How It Works

### Agent Loop (runs daily)

1. **Monitor**: Fetch new Amazon listings that need images
2. **Generate Prompts**: Create diverse image prompts (front view, lifestyle, close-up, etc.)
3. **Generate Images**: Call Krea AI MCP server to generate 5 images per listing
4. **Save Results**: Store images and metadata in `results/`
5. **Track**: Add listing to revenue tracker
6. **State**: Mark ASIN as processed to avoid duplicates

### Image Generation

For each listing, the agent generates 5 images with different styles:
1. **Front view** - Professional product photography, white background
2. **Side angle** - Detailed features visible, studio lighting
3. **Lifestyle shot** - In-use context, natural setting
4. **Close-up detail** - Macro photography, key features highlighted
5. **Packaging** - Unboxing scene, premium presentation

### Revenue Tracking

The agent tracks:
- **Per-listing metrics**: Revenue, orders, views, conversion rate
- **Summary metrics**: Total revenue, avg order value, avg conversion rate
- **Performance vs targets**: Conversion rate and order value targets
- **Top performers**: Best-performing listings by revenue

---

## Krea AI MCP Integration

The agent uses Krea AI's Model Context Protocol (MCP) server for image generation.

**MCP Server Details:**
- URL: `https://api.krea.ai/mcp`
- Transport: Streamable HTTP
- Authentication: OAuth or API token

**Available in your Devin config:**
```json
{
  "mcpServers": {
    "krea-ai": {
      "transport": "streamable-http",
      "url": "https://api.krea.ai/mcp"
    }
  }
}
```

**To use Krea MCP in Python:**
- The `krea_client.py` module handles API calls
- Uses Bearer token authentication
- Generates images with custom prompts and styles

---

## Monitoring & Logs

### Check Logs

```powershell
# View real-time logs
Get-Content logs\agent.log -Tail 50 -Wait

# View full log
cat logs\agent.log
```

### Check State

```powershell
# Processed ASINs
cat state\agent_state.json

# Revenue data
cat state\revenue_log.json
```

### Check Results

```powershell
# List generated images
ls results\

# View image metadata
cat results\B08TEST001_metadata.json
```

---

## Troubleshooting

### "Krea API key not found"
- Make sure `.env` file exists and contains `KREA_API_KEY`
- Verify the key is valid at https://krea.ai/app/api/tokens

### "No new listings found"
- Check `amazon_monitor.py` is correctly fetching listings
- Verify your Amazon credentials (SP-API or scraping setup)
- Check `state/agent_state.json` - listings may already be processed

### "Scheduled task not running"
- Check task status: `python scheduler.py status`
- Verify Python path in task: `schtasks /Query /TN AmazonImageAgent /V /FO LIST`
- Check Windows Event Viewer for task scheduler errors

### "Images not generating"
- Test Krea API manually: `python modules\krea_client.py`
- Check Krea API quota/limits
- Verify MCP server is accessible

---

## Revenue Optimization Tips

1. **A/B Test Image Styles**: Generate different styles and track which converts best
2. **Monitor Top Performers**: Use `get_top_performers()` to identify winning patterns
3. **Adjust Targets**: Update `CONVERSION_RATE_TARGET` based on your category benchmarks
4. **Scale Gradually**: Start with `MAX_LISTINGS_PER_RUN = 5`, increase as you validate ROI
5. **Track Seasonality**: Compare 7-day, 30-day, and 90-day reports

---

## Roadmap

- [ ] Integrate Amazon SP-API for real listing data
- [ ] Add image upload to Amazon Seller Central
- [ ] Multi-marketplace support (US, UK, DE, etc.)
- [ ] A/B testing framework (compare image variants)
- [ ] Slack/Telegram notifications for daily reports
- [ ] Dashboard UI for revenue analytics
- [ ] Auto-optimize prompts based on conversion data

---

## License

This project is for personal/commercial use. Respect Amazon's terms of service and Krea AI's usage policies.

---

## Support

For issues or questions:
1. Check logs: `logs/agent.log`
2. Review state files: `state/`
3. Test modules individually: `python modules/krea_client.py`

---

**Built with:**
- Python 3.8+
- Krea AI MCP Server
- Windows Task Scheduler
- Love for automation ❤️
