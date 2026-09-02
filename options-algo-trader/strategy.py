"""
Intraday Options Momentum Scalping Strategy
Core trading logic and signal generation
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
import config

class MomentumScalpingStrategy:
    """
    Intraday momentum scalping strategy for NSE options
    
    Entry Signals:
    - Strong directional move in underlying
    - Volume surge (2x+ average)
    - RSI confirmation
    - MACD crossover
    
    Exit Signals:
    - Target hit (1% profit)
    - Stop loss (0.5% loss)
    - Time stop (30 min)
    - Momentum reversal
    - 3:15 PM square off
    """
    
    def __init__(self):
        self.name = "Momentum Scalping"
        self.timeframe = config.TIMEFRAME
        self.positions = []
        self.daily_pnl = 0
        self.trade_count = 0
        self.consecutive_losses = 0
        
    def calculate_indicators(self, df):
        """Calculate technical indicators"""
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=config.RSI_PERIOD).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=config.RSI_PERIOD).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=config.MACD_FAST, adjust=False).mean()
        exp2 = df['close'].ewm(span=config.MACD_SLOW, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=config.MACD_SIGNAL, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # Volume
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_surge'] = df['volume'] / df['volume_ma']
        
        # Price momentum
        df['price_change'] = df['close'].pct_change()
        df['price_change_5'] = df['close'].pct_change(5)
        
        # ATR for stop loss
        df['high_low'] = df['high'] - df['low']
        df['high_close'] = abs(df['high'] - df['close'].shift())
        df['low_close'] = abs(df['low'] - df['close'].shift())
        df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df['atr'] = df['tr'].rolling(window=14).mean()
        
        return df
    
    def check_time_filter(self, current_time):
        """Check if current time is within trading hours"""
        market_open = time(9, 15)
        market_close = time(15, 30)
        no_trade_after = time(15, 15)
        avoid_first = time(9, 30)
        
        if current_time < market_open or current_time > market_close:
            return False, "Market closed"
        
        if current_time < avoid_first:
            return False, "Avoiding first 15 minutes"
        
        if current_time > no_trade_after:
            return False, "No new trades after 3:15 PM"
        
        return True, "OK"
    
    def check_risk_limits(self):
        """Check if risk limits are breached"""
        # Daily loss limit
        if self.daily_pnl < -config.CAPITAL * config.MAX_DAILY_LOSS:
            return False, f"Daily loss limit hit (₹{self.daily_pnl:,.0f})"
        
        # Max trades per day
        if self.trade_count >= config.MAX_TRADES_PER_DAY:
            return False, f"Max trades per day reached ({self.trade_count})"
        
        # Consecutive losses
        if self.consecutive_losses >= config.MAX_CONSECUTIVE_LOSSES:
            return False, f"Max consecutive losses ({self.consecutive_losses})"
        
        # Max open positions
        if len(self.positions) >= config.MAX_OPEN_POSITIONS:
            return False, f"Max open positions ({len(self.positions)})"
        
        return True, "OK"
    
    def generate_signal(self, df, option_type="CE"):
        """
        Generate trading signal
        
        Returns:
        - "BUY": Enter long position
        - "SELL": Exit position
        - "HOLD": No action
        """
        if len(df) < config.LOOKBACK_CANDLES:
            return "HOLD", "Insufficient data"
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Check time filter
        current_time = latest.name.time() if isinstance(latest.name, pd.Timestamp) else datetime.now().time()
        time_ok, time_msg = self.check_time_filter(current_time)
        if not time_ok:
            return "HOLD", time_msg
        
        # Check risk limits
        risk_ok, risk_msg = self.check_risk_limits()
        if not risk_ok:
            return "HOLD", risk_msg
        
        # === ENTRY SIGNALS ===
        
        # 1. Price momentum
        strong_move = abs(latest['price_change']) > config.MIN_PRICE_MOVE
        
        # 2. Volume surge
        volume_surge = latest['volume_surge'] > config.VOLUME_SURGE_MULTIPLIER
        
        # 3. RSI confirmation
        if option_type == "CE":  # Call option - bullish
            rsi_ok = config.RSI_OVERSOLD < latest['rsi'] < 70
            price_up = latest['price_change'] > 0
            macd_bullish = latest['macd'] > latest['macd_signal']
            
            if strong_move and volume_surge and rsi_ok and price_up and macd_bullish:
                return "BUY", "Bullish momentum signal"
        
        elif option_type == "PE":  # Put option - bearish
            rsi_ok = 30 < latest['rsi'] < config.RSI_OVERBOUGHT
            price_down = latest['price_change'] < 0
            macd_bearish = latest['macd'] < latest['macd_signal']
            
            if strong_move and volume_surge and rsi_ok and price_down and macd_bearish:
                return "BUY", "Bearish momentum signal"
        
        # === EXIT SIGNALS ===
        
        # Momentum reversal
        if option_type == "CE" and latest['macd'] < latest['macd_signal']:
            return "SELL", "Momentum reversal (bearish)"
        
        if option_type == "PE" and latest['macd'] > latest['macd_signal']:
            return "SELL", "Momentum reversal (bullish)"
        
        # RSI extreme
        if latest['rsi'] > 80 or latest['rsi'] < 20:
            return "SELL", "RSI extreme"
        
        return "HOLD", "No clear signal"
    
    def calculate_position_size(self, option_price):
        """Calculate position size based on risk management"""
        # Risk amount per trade
        risk_amount = config.CAPITAL * config.RISK_PER_TRADE
        
        # Stop loss in Rs
        stop_loss_amount = option_price * config.STOP_LOSS_PCT
        
        # Quantity = Risk amount / Stop loss per unit
        quantity = int(risk_amount / stop_loss_amount)
        
        # Round to lot size (50 for Nifty)
        lot_size = 50
        lots = max(1, quantity // lot_size)
        quantity = lots * lot_size
        
        # Cap at configured lot size
        max_quantity = config.POSITION_SIZE_LOTS * lot_size
        quantity = min(quantity, max_quantity)
        
        return quantity
    
    def calculate_targets(self, entry_price):
        """Calculate target and stop loss prices"""
        target = entry_price * (1 + config.TARGET_PROFIT_PCT)
        stop_loss = entry_price * (1 - config.STOP_LOSS_PCT)
        
        return {
            'entry': entry_price,
            'target': target,
            'stop_loss': stop_loss,
            'trailing_stop': None  # Will be updated dynamically
        }
    
    def update_trailing_stop(self, position, current_price):
        """Update trailing stop loss"""
        if not config.USE_TRAILING_STOP:
            return position
        
        # Calculate new trailing stop
        new_trailing_stop = current_price * (1 - config.TRAILING_STOP_PCT)
        
        # Update if higher than current stop
        if position['trailing_stop'] is None or new_trailing_stop > position['trailing_stop']:
            position['trailing_stop'] = new_trailing_stop
        
        return position
    
    def check_exit_conditions(self, position, current_price, current_time):
        """Check if position should be exited"""
        # Target hit
        if current_price >= position['target']:
            return True, "Target hit", current_price
        
        # Stop loss hit
        stop_price = position['trailing_stop'] if position['trailing_stop'] else position['stop_loss']
        if current_price <= stop_price:
            return True, "Stop loss hit", current_price
        
        # Time stop
        entry_time = position['entry_time']
        hold_minutes = (current_time - entry_time).total_seconds() / 60
        if hold_minutes > config.MAX_HOLD_TIME_MINUTES:
            return True, "Time stop", current_price
        
        # Square off time (3:15 PM)
        if current_time.time() >= time(15, 15):
            return True, "Square off time", current_price
        
        return False, "Hold", current_price
    
    def calculate_pnl(self, entry_price, exit_price, quantity):
        """Calculate P&L for a trade"""
        pnl_per_unit = exit_price - entry_price
        gross_pnl = pnl_per_unit * quantity
        
        # Deduct brokerage
        brokerage = config.BACKTEST_COMMISSION
        net_pnl = gross_pnl - brokerage
        
        return {
            'gross_pnl': gross_pnl,
            'brokerage': brokerage,
            'net_pnl': net_pnl,
            'pnl_pct': (net_pnl / (entry_price * quantity)) * 100
        }
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.daily_pnl = 0
        self.trade_count = 0
        self.positions = []
        print(f"\n📅 New trading day - Stats reset")
    
    def print_signal(self, signal, reason, df):
        """Print signal details"""
        latest = df.iloc[-1]
        print(f"\n{'='*60}")
        print(f"🎯 SIGNAL: {signal}")
        print(f"📝 Reason: {reason}")
        print(f"📊 Price: {latest['close']:.2f}")
        print(f"📈 RSI: {latest['rsi']:.2f}")
        print(f"📊 MACD: {latest['macd']:.4f}")
        print(f"📊 Volume Surge: {latest['volume_surge']:.2f}x")
        print(f"{'='*60}\n")

if __name__ == "__main__":
    # Test strategy
    strategy = MomentumScalpingStrategy()
    print(f"✅ Strategy initialized: {strategy.name}")
    print(f"⏰ Timeframe: {strategy.timeframe}")
    print(f"📊 Lookback: {config.LOOKBACK_CANDLES} candles")
