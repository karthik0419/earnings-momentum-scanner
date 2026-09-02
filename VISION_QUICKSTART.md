# 🚀 GLM Vision API - Quick Start

**Status**: ✅ Configured & Tested (2026-08-23)

---

## 📸 How to Analyze TradingView Charts

### **After Restarting Devin:**

Just paste the image path in chat:
```
Analyze this chart: F:\projects\claude\scanner-v3\charts\PIRAMALFIN_analysis_2026-07-18.png
```

Or ask specific questions:
```
Is this a Cup & Handle? F:\projects\claude\scanner-v3\charts\STOCK_NAME.png
```

---

## 📂 Where Are My Charts?

- **Scanner-v3**: `F:\projects\claude\scanner-v3\charts\*.png`
- **Scanner-v2**: `F:\projects\claude\scanner-v2\charts\*.png`
- **Chart Visualizer**: `F:\projects\claude\chart-visualizer\output\*.png`

---

## 💰 Current Setup

- **Provider**: OpenRouter GLM-4.5V
- **Cost**: $0.0001 per image (~1 cent per 100 charts)
- **Free Credits**: $1-5 (hundreds of analyses)
- **Speed**: 5-10 seconds per analysis

---

## ⚡ Make It FREE Forever (Optional)

1. Get Gemini API key: https://aistudio.google.com/apikey
2. Edit `.devin/multi_provider_vision.py` line 23
3. Change `"enabled": False` to `"enabled": True`
4. Paste your key

**Result**: 1500 free analyses/day, PERMANENT

---

## 🛠️ Alternative: Command Line

```powershell
cd F:\projects\claude\.devin
python multi_provider_vision.py "F:\path\to\chart.png"
```

---

## 📚 Full Docs

- **AGENTS.md**: Full configuration details
- **.devin/VISION_USAGE_GUIDE.md**: Complete usage guide
- **.devin/multi_provider_vision.py**: Multi-provider router script

---

## ✅ Tested Example

**Input**: `F:\projects\claude\scanner-v3\charts\PIRAMALFIN_analysis_2026-07-18.png`

**Output**: 
- Pattern: Cup & Handle (73.6/100 score)
- Breakout: ₹2,220
- Stop Loss: ₹2,020
- Target: ₹2,680
- Risk/Reward: 1:3.7

**Cost**: $0.004

---

**Ready to use after restart!** 🎉
