"""
Configuration for NSE Options Algo Trading System
Edit these settings before running
"""

# ============================================================
# CAPITAL & RISK MANAGEMENT
# ============================================================

CAPITAL = 50000  # Total trading capital in Rs
RISK_PER_TRADE = 0.05  # 5% risk per trade (aggressive)
MAX_DAILY_LOSS = 0.10  # 10% max daily loss
MAX_OPEN_POSITIONS = 2  # Max simultaneous positions
POSITION_SIZE_LOTS = 1  # Lot size (1 lot = 50 qty for Nifty)

# ============================================================
# STRATEGY PARAMETERS
# ============================================================

# Timeframe
TIMEFRAME = "5min"  # 1min, 5min, 15min
LOOKBACK_CANDLES = 20  # Candles to analyze

# Entry Signals
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

VOLUME_SURGE_MULTIPLIER = 2.0  # 2x average volume
MIN_PRICE_MOVE = 0.003  # 0.3% minimum move

# Exit Signals
TARGET_PROFIT_PCT = 0.01  # 1% profit target
STOP_LOSS_PCT = 0.005  # 0.5% stop loss
MAX_HOLD_TIME_MINUTES = 30  # Max hold time
TRAILING_STOP_PCT = 0.003  # 0.3% trailing stop

# Time Filters
MARKET_OPEN = "09:15"
MARKET_CLOSE = "15:30"
NO_TRADE_AFTER = "15:15"  # Square off all by 3:15 PM
AVOID_FIRST_MINUTES = 15  # Avoid first 15 min (9:15-9:30)

# ============================================================
# INSTRUMENTS
# ============================================================

# Underlying indices
INSTRUMENTS = [
    "NIFTY",      # Nifty 50
    "BANKNIFTY",  # Bank Nifty
    # "FINNIFTY",   # Fin Nifty (optional)
]

# Option types
OPTION_TYPES = ["CE", "PE"]  # Call, Put

# Strike selection
STRIKE_SELECTION = "ATM"  # ATM, OTM1, OTM2, ITM1
OTM_OFFSET = 100  # Points away from ATM

# Expiry
EXPIRY_TYPE = "WEEKLY"  # WEEKLY, MONTHLY
DAYS_TO_EXPIRY_MIN = 0  # Min days to expiry
DAYS_TO_EXPIRY_MAX = 7  # Max days to expiry

# ============================================================
# FILTERS
# ============================================================

# Liquidity filters
MIN_OPTION_PRICE = 10  # Min premium (Rs)
MAX_OPTION_PRICE = 500  # Max premium (Rs)
MIN_OI = 100000  # Min open interest
MIN_VOLUME = 10000  # Min volume

# Volatility filters
MIN_IV = 15  # Min implied volatility (%)
MAX_IV = 50  # Max implied volatility (%)

# Greeks filters (optional)
MAX_DELTA = 0.7  # Max delta (for directional trades)
MIN_THETA = -50  # Min theta (time decay)

# ============================================================
# BROKER API (for live trading)
# ============================================================

# Zerodha Kite Connect
BROKER = "ZERODHA"  # ZERODHA, ANGELONE, UPSTOX, FYERS
API_KEY = ""  # Your API key
API_SECRET = ""  # Your API secret
ACCESS_TOKEN = ""  # Generated access token

# ============================================================
# TELEGRAM ALERTS
# ============================================================

TELEGRAM_ENABLED = False  # Enable Telegram notifications
TELEGRAM_BOT_TOKEN = ""  # Bot token from @BotFather
TELEGRAM_CHAT_ID = ""  # Your chat ID

# Alert types
ALERT_ON_ENTRY = True
ALERT_ON_EXIT = True
ALERT_ON_STOP_LOSS = True
ALERT_ON_TARGET = True
ALERT_ON_DAILY_LIMIT = True

# ============================================================
# LOGGING
# ============================================================

LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = True
LOG_FILE = "results/trading.log"

# Save trades to CSV
SAVE_TRADES = True
TRADES_FILE = "results/trades.csv"

# ============================================================
# BACKTESTING
# ============================================================

BACKTEST_START_DATE = "2026-07-01"
BACKTEST_END_DATE = "2026-08-27"
BACKTEST_INITIAL_CASH = 50000
BACKTEST_COMMISSION = 20  # Rs per trade (both sides)

# ============================================================
# PAPER TRADING
# ============================================================

PAPER_TRADING_MODE = True  # Start in paper trading mode
PAPER_SLIPPAGE = 0.001  # 0.1% slippage simulation
PAPER_DELAY_SECONDS = 1  # Simulated execution delay

# ============================================================
# SAFETY LIMITS
# ============================================================

# Circuit breakers
MAX_TRADES_PER_DAY = 10
MAX_CONSECUTIVE_LOSSES = 5
COOL_DOWN_AFTER_LOSS_STREAK = 30  # Minutes

# Position limits
MAX_POSITION_VALUE = CAPITAL * 0.5  # Max 50% of capital in one position
MAX_TOTAL_EXPOSURE = CAPITAL * 1.0  # Max 100% total exposure

# Drawdown limits
MAX_DRAWDOWN_PCT = 0.15  # Stop trading if 15% drawdown
DAILY_PROFIT_TARGET = 0.05  # 5% daily profit target (optional stop)

# ============================================================
# ADVANCED SETTINGS
# ============================================================

# Order types
ORDER_TYPE = "LIMIT"  # LIMIT, MARKET
LIMIT_ORDER_OFFSET = 0.5  # Rs offset for limit orders

# Execution
USE_BRACKET_ORDERS = False  # Use bracket orders (SL + target)
USE_TRAILING_STOP = True  # Enable trailing stop loss

# Data source
DATA_SOURCE = "YFINANCE"  # YFINANCE, NSEPY, BROKER_API
DATA_REFRESH_SECONDS = 5  # Refresh interval for live data

# ============================================================
# VALIDATION
# ============================================================

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    if CAPITAL < 25000:
        errors.append("Capital should be at least Rs 25,000 for options trading")
    
    if RISK_PER_TRADE > 0.10:
        errors.append("Risk per trade should not exceed 10%")
    
    if MAX_DAILY_LOSS > 0.20:
        errors.append("Max daily loss should not exceed 20%")
    
    if not INSTRUMENTS:
        errors.append("At least one instrument must be selected")
    
    if PAPER_TRADING_MODE and (API_KEY or API_SECRET):
        print("⚠️  Warning: Paper trading mode enabled but API credentials found")
    
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"   • {error}")
        return False
    
    print("✅ Configuration validated successfully")
    return True

# ============================================================
# DISPLAY CONFIGURATION
# ============================================================

def print_config():
    """Print current configuration"""
    print("\n" + "="*60)
    print("📊 NSE OPTIONS ALGO TRADING - CONFIGURATION")
    print("="*60)
    print(f"\n💰 CAPITAL & RISK:")
    print(f"   Capital: ₹{CAPITAL:,}")
    print(f"   Risk per trade: {RISK_PER_TRADE*100:.1f}% (₹{CAPITAL*RISK_PER_TRADE:,.0f})")
    print(f"   Max daily loss: {MAX_DAILY_LOSS*100:.1f}% (₹{CAPITAL*MAX_DAILY_LOSS:,.0f})")
    print(f"   Position size: {POSITION_SIZE_LOTS} lot(s)")
    print(f"   Max open positions: {MAX_OPEN_POSITIONS}")
    
    print(f"\n📈 STRATEGY:")
    print(f"   Timeframe: {TIMEFRAME}")
    print(f"   Target profit: {TARGET_PROFIT_PCT*100:.1f}%")
    print(f"   Stop loss: {STOP_LOSS_PCT*100:.1f}%")
    print(f"   Max hold time: {MAX_HOLD_TIME_MINUTES} minutes")
    
    print(f"\n🎯 INSTRUMENTS:")
    print(f"   Underlyings: {', '.join(INSTRUMENTS)}")
    print(f"   Strike selection: {STRIKE_SELECTION}")
    print(f"   Expiry: {EXPIRY_TYPE}")
    
    print(f"\n🔧 MODE:")
    print(f"   Paper trading: {'✅ ENABLED' if PAPER_TRADING_MODE else '❌ DISABLED'}")
    print(f"   Telegram alerts: {'✅ ENABLED' if TELEGRAM_ENABLED else '❌ DISABLED'}")
    print(f"   Broker: {BROKER if not PAPER_TRADING_MODE else 'N/A (Paper mode)'}")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    print_config()
    validate_config()
