# 🚀 NSE Options Algo Trading System

**Strategy**: Intraday Momentum Scalping  
**Capital**: ₹50,000 - ₹1,00,000  
**Risk**: Aggressive (5-10% per trade)  
**Mode**: Paper Trading → Live Trading  
**Market**: NSE Options (Nifty, Bank Nifty, Fin Nifty)  

---

## 📊 **STRATEGY OVERVIEW**

### **Core Concept:**
- **Scalp intraday momentum** in liquid options
- **5-15 minute timeframe**
- **Quick entries/exits** (hold 5-30 minutes)
- **High win rate** (60-70% target)
- **Small profits, tight stops** (R:R 1:1 to 1:2)

### **Entry Signals:**
1. **Strong directional move** in underlying (Nifty/BankNifty)
2. **Volume surge** (2x+ average)
3. **ATM/OTM options** with high liquidity
4. **Momentum confirmation** (RSI, MACD, price action)

### **Exit Signals:**
1. **Target hit** (0.5-1% profit on capital)
2. **Stop loss** (0.5% loss on capital)
3. **Time stop** (30 min max hold)
4. **Momentum reversal** (opposite signal)
5. **3:15 PM** (square off all positions)

---

## 🎯 **POSITION SIZING**

### **Capital: ₹50,000**
- Max risk per trade: **₹2,500** (5%)
- Lot size: **1 lot** (Nifty 50 qty)
- Max open positions: **2**
- Daily loss limit: **₹5,000** (10%)

### **Capital: ₹1,00,000**
- Max risk per trade: **₹5,000** (5%)
- Lot size: **2 lots** (Nifty 100 qty)
- Max open positions: **3**
- Daily loss limit: **₹10,000** (10%)

---

## 📁 **PROJECT STRUCTURE**

```
options-algo-trader/
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── config.py                  # Configuration settings
├── strategy.py                # Core trading strategy
├── backtest.py                # Backtesting engine
├── paper_trader.py            # Paper trading simulator
├── live_trader.py             # Live trading (Zerodha/broker API)
├── data/
│   ├── fetch_options_data.py  # Download options chain data
│   └── market_data.py         # Real-time data handler
├── indicators/
│   ├── momentum.py            # RSI, MACD, momentum indicators
│   └── volume.py              # Volume analysis
├── risk/
│   ├── position_sizer.py      # Position sizing logic
│   └── risk_manager.py        # Risk management rules
├── utils/
│   ├── logger.py              # Trade logging
│   └── telegram_bot.py        # Telegram alerts
└── results/
    ├── backtest_results.csv   # Backtest performance
    └── paper_trades.csv       # Paper trading log
```

---

## 🚀 **QUICK START**

### **1. Install Dependencies**
```powershell
cd F:\projects\claude\options-algo-trader
pip install -r requirements.txt
```

### **2. Configure Settings**
Edit `config.py`:
- Set capital amount
- Set risk percentage
- Configure Telegram bot (optional)

### **3. Backtest Strategy**
```powershell
python backtest.py --days 30 --capital 50000
```

### **4. Paper Trade**
```powershell
python paper_trader.py
```

### **5. Go Live** (when ready)
```powershell
python live_trader.py
```

---

## 📊 **EXPECTED PERFORMANCE**

### **Backtest Targets (30 days):**
- **Win Rate**: 60-70%
- **Avg Win**: ₹500-1,000
- **Avg Loss**: ₹300-500
- **Trades/Day**: 3-5
- **Monthly Return**: 10-20%
- **Max Drawdown**: <15%

### **Risk Metrics:**
- **Sharpe Ratio**: >1.5
- **Profit Factor**: >1.5
- **Max Consecutive Losses**: <5

---

## ⚠️ **RISK WARNINGS**

1. **Options are risky** - Can lose 100% of premium
2. **Intraday is volatile** - Quick moves both ways
3. **Slippage matters** - Use limit orders
4. **Liquidity critical** - Only trade ATM/near ATM
5. **Time decay** - Theta works against you
6. **Paper trade first** - Prove strategy before live

---

## 🎓 **LEARNING PATH**

### **Week 1: Setup & Backtest**
- Install system
- Run backtests
- Understand strategy
- Optimize parameters

### **Week 2: Paper Trading**
- Run paper trader daily
- Track all trades
- Analyze performance
- Refine rules

### **Week 3-4: Live Trading (Small)**
- Start with 1 lot
- Follow rules strictly
- Log everything
- Scale up slowly

---

## 📞 **SUPPORT**

- **Documentation**: See individual .py files
- **Issues**: Check logs in results/
- **Questions**: Read strategy.py comments

---

**Created**: 2026-08-27  
**Status**: Ready to build  
**Next**: Install dependencies and backtest  
