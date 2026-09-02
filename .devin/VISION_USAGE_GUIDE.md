# Vision API Usage Guide

## 🎯 Main Goal: Analyze TradingView Charts for FREE/CHEAP

---

## 📋 Quick Start (3 Ways to Use)

### **Method 1: Direct in Devin Chat (After Restart)**

After you restart Devin, just drag & drop or paste the image path:

```
"Analyze this chart: F:\projects\claude\scanner-v3\charts\PIRAMALFIN_analysis_2026-07-18.png"
```

Or:

```
"Is this a Cup & Handle pattern? F:\projects\claude\scanner-v3\charts\PIRAMALFIN_analysis_2026-07-18.png"
```

---

### **Method 2: Python Script (Multi-Provider Router)**

Use the smart router that tries FREE providers first:

```powershell
cd F:\projects\claude\.devin

# Analyze a chart
python multi_provider_vision.py "F:\projects\claude\scanner-v3\charts\PIRAMALFIN_analysis_2026-07-18.png"

# With custom question
python multi_provider_vision.py "F:\path\to\chart.png" "Is this a valid Cup & Handle?"

# Extract all text (OCR)
python multi_provider_vision.py "F:\path\to\chart.png" "Extract all text and numbers from this chart"
```

---

### **Method 3: Import in Your Scanner Code**

Add to your scanner projects:

```python
# In scanner-v3/scanner.py or daily_scan.py
from pathlib import Path
import sys

# Add vision module to path
sys.path.append(str(Path(__file__).parent.parent / ".devin"))
from multi_provider_vision import analyze_chart, extract_chart_text

# After generating chart
chart_path = f"charts/{symbol}_analysis.png"
if Path(chart_path).exists():
    # Analyze pattern
    analysis = analyze_chart(chart_path, "Is this a valid Cup & Handle pattern?")
    print(f"\n🤖 AI Analysis: {analysis}\n")
    
    # Extract indicator values
    ocr_text = extract_chart_text(chart_path)
    print(f"📊 Chart Data: {ocr_text}")
```

---

## 🔑 Setup: Get FREE API Keys

### **Option 1: Google Gemini (BEST - FREE FOREVER)**

1. Visit: https://aistudio.google.com/apikey
2. Click "Create API Key"
3. Copy the key (starts with `AIza...`)
4. Add to `F:\projects\claude\.devin\multi_provider_vision.py`:
   ```python
   "gemini": {
       "api_key": "AIzaSy...",  # Your key here
       "enabled": True  # Change to True
   }
   ```

**Limits**: 1,500 requests/day, PERMANENT, NO CREDIT CARD NEEDED

---

### **Option 2: OpenRouter (Current Setup)**

Already configured! Uses your existing key:
- **Cost**: $0.0001 per image (~1 cent per 100 charts)
- **Free credits**: $1-5 (hundreds of analyses)
- **Add more**: https://openrouter.ai/settings/credits

---

### **Option 3: GPT4Free (Last Resort)**

No setup needed, but unstable:
```python
"gpt4free": {
    "enabled": True  # Change to True in multi_provider_vision.py
}
```

**Warning**: Reverse engineered, may break anytime

---

## 📂 Where to Find Your Chart Images

### Scanner-v3 Charts:
```
F:\projects\claude\scanner-v3\charts\
```

### Scanner-v2 Charts:
```
F:\projects\claude\scanner-v2\charts\
```

### Chart Visualizer:
```
F:\projects\claude\chart-visualizer\output\
```

---

## 💡 Common Use Cases

### 1. **Verify Scanner Picks**
```python
# After scanner.py generates picks
for symbol in top_picks:
    chart_path = f"charts/{symbol}_analysis.png"
    analysis = analyze_chart(chart_path, 
        "Rate this Cup & Handle pattern from 1-10. Is it tradeable?")
    print(f"{symbol}: {analysis}")
```

### 2. **Extract Exact Values from Chart Screenshots**
```python
# Get RSI, MACD, Volume from screenshot
ocr_text = extract_chart_text("screenshot.png")
# Parse the text to extract indicator values
```

### 3. **Compare Multiple Timeframes**
```python
from multi_provider_vision import compare_charts

result = compare_charts([
    "charts/RELIANCE_daily.png",
    "charts/RELIANCE_weekly.png"
], "Which timeframe shows a stronger breakout setup?")
print(result)
```

### 4. **Batch Analyze All Scanner Results**
```python
import glob
from multi_provider_vision import analyze_chart

charts = glob.glob("charts/*.png")
for chart in charts[:10]:  # First 10 only
    symbol = Path(chart).stem.split("_")[0]
    analysis = analyze_chart(chart, "Is this a valid breakout?")
    print(f"{symbol}: {analysis}\n")
```

---

## 🎨 Example Prompts

### Pattern Recognition:
```
"Is this a Cup & Handle pattern? Rate it 1-10."
"Identify the chart pattern. Is it bullish or bearish?"
"Is this a valid Double Bottom formation?"
```

### Technical Analysis:
```
"What are the key support and resistance levels?"
"Is this a breakout or a fakeout?"
"What is the risk-reward ratio for entering here?"
```

### OCR / Data Extraction:
```
"Extract all text and numbers from this chart."
"What is the RSI value shown?"
"List all indicator values visible in this chart."
```

### Multi-Chart Comparison:
```
"Which chart shows a stronger setup?"
"Compare the daily vs weekly timeframe."
"Which stock has better momentum?"
```

---

## 📊 Cost Comparison

| Provider | Cost per 100 charts | Free tier | Setup difficulty |
|---|---|---|---|
| **Google Gemini** | **$0** | 1500/day forever | Easy (1 API key) |
| OpenRouter GLM-4.5V | $0.01 | $1-5 credits | Done ✅ |
| GPT4Free | $0 | Unlimited | None (unstable) |
| GPT-4o (OpenRouter) | $0.50 | None | Easy |
| Claude 3.5 (OpenRouter) | $1.50 | None | Easy |

**Recommendation**: Get Gemini API key → 1500 FREE analyses/day forever!

---

## 🚀 Quick Test Right Now

Let's test with your existing chart:

```powershell
cd F:\projects\claude\.devin

python multi_provider_vision.py "F:\projects\claude\scanner-v3\charts\PIRAMALFIN_analysis_2026-07-18.png" "Analyze this chart pattern"
```

This will use your OpenRouter key (already configured).

---

## 🔧 Troubleshooting

### "All providers failed"
- Check API keys are correct
- Check internet connection
- Check OpenRouter credits: https://openrouter.ai/api/v1/key

### "File not found"
- Use full path: `F:\projects\claude\...`
- Check file exists: `dir "F:\path\to\chart.png"`
- Use forward slashes or escape backslashes

### "Rate limit exceeded"
- Wait a few minutes
- Switch to Gemini (1500/day limit)
- Add more OpenRouter credits

### "Image too large"
- Max 5MB per image
- Compress with: `python -m PIL chart.png --optimize`

---

## 📝 Next Steps

1. **Test now**: Run the command above with your existing chart
2. **Get Gemini key**: https://aistudio.google.com/apikey (5 minutes)
3. **Enable Gemini**: Edit `multi_provider_vision.py` line 23
4. **Integrate**: Add to your scanner scripts

---

## 💰 Cost Optimization Strategy

**Phase 1: Testing (Now)**
- Use OpenRouter free credits ($1-5)
- ~500-1000 chart analyses for free

**Phase 2: Scale (After free credits)**
- Get Gemini API key (FREE FOREVER)
- 1500 charts/day = 45,000/month = $0

**Phase 3: Heavy Usage (If needed)**
- Add $5-10 to OpenRouter
- Use for overflow beyond 1500/day
- Cost: ~$0.01 per 100 charts

**Result**: Effectively unlimited FREE chart analysis! 🎉

---

## 📧 Support

- OpenRouter issues: safety@openrouter.ai
- Gemini issues: https://ai.google.dev/support
- This setup: Check `.devin/openrouter_bug_bounty_research.md`
