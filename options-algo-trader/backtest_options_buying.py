"""
Backtest Options Buying Strategy
Using scanner-v3 signals + ATM options buying
"""

import sys
import os
sys.path.append('F:\\projects\\claude\\scanner-v3')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from tabulate import tabulate
import warnings
warnings.filterwarnings('ignore')

class OptionsBuyingBacktest:
    """
    Backtest options buying strategy based on scanner-v3 signals
    
    Strategy:
    1. Use scanner-v3 pattern signals (C&H, Double Bottom, Breakout, etc.)
    2. Buy ATM Call option on BREAKOUT signal
    3. Stop Loss: 50% of premium OR 2x ATR (whichever tighter)
    4. Target: T1 from scanner (50% of measured move)
    5. Max hold: 7 days (weekly expiry)
    """
    
    def __init__(self, capital=50000, risk_per_trade=0.05):
        self.initial_capital = capital
        self.capital = capital
        self.risk_per_trade = risk_per_trade
        self.trades = []
        self.equity_curve = []
        
    def simulate_option_price(self, stock_price, strike, days_to_expiry, stock_move_pct):
        """
        Simplified option pricing simulation
        
        Real options have complex pricing (Black-Scholes), but for backtesting
        we can approximate based on:
        - Intrinsic value (stock_price - strike)
        - Time value (decreases with time)
        - Delta effect (options move ~0.5-0.7x of stock for ATM)
        """
        # ATM option delta ~0.5 (moves 50% of stock)
        delta = 0.5
        
        # Time decay (theta) - loses ~10-15% per day for weekly options
        theta_decay_per_day = 0.12
        
        # Initial premium (simplified)
        # ATM option premium is typically 2-4% of stock price for weekly
        initial_premium = stock_price * 0.03  # 3% of stock price
        
        # Calculate new premium after stock move
        intrinsic_gain = stock_price * stock_move_pct * delta
        time_decay = initial_premium * theta_decay_per_day * (7 - days_to_expiry)
        
        new_premium = initial_premium + intrinsic_gain - time_decay
        
        # Premium can't go below zero
        new_premium = max(0, new_premium)
        
        return initial_premium, new_premium
    
    def calculate_atr(self, df, period=14):
        """Calculate ATR for stop loss"""
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(period).mean()
        
        return atr
    
    def detect_patterns(self, df):
        """
        Simplified pattern detection (based on scanner-v3 logic)
        Returns list of signals with entry, target, stop
        """
        signals = []
        
        # Calculate indicators
        df['SMA20'] = df['Close'].rolling(20).mean()
        df['SMA50'] = df['Close'].rolling(50).mean()
        df['Volume_MA'] = df['Volume'].rolling(20).mean()
        df['ATR'] = self.calculate_atr(df)
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        for i in range(50, len(df)):
            current = df.iloc[i]
            prev = df.iloc[i-1]
            
            # Skip if not enough data
            if pd.isna(current['ATR']).any() if isinstance(current['ATR'], pd.Series) else pd.isna(current['ATR']):
                continue
            if pd.isna(current['RSI']).any() if isinstance(current['RSI'], pd.Series) else pd.isna(current['RSI']):
                continue
            
            # BREAKOUT PATTERN
            # Price breaks above 20-day high with volume
            high_20 = df['High'].iloc[i-20:i].max()
            
            # Convert Series to scalar if needed
            close_val = float(current['Close'].iloc[0]) if isinstance(current['Close'], pd.Series) else float(current['Close'])
            volume_val = float(current['Volume'].iloc[0]) if isinstance(current['Volume'], pd.Series) else float(current['Volume'])
            volume_ma_val = float(current['Volume_MA'].iloc[0]) if isinstance(current['Volume_MA'], pd.Series) else float(current['Volume_MA'])
            rsi_val = float(current['RSI'].iloc[0]) if isinstance(current['RSI'], pd.Series) else float(current['RSI'])
            sma20_val = float(current['SMA20'].iloc[0]) if isinstance(current['SMA20'], pd.Series) else float(current['SMA20'])
            atr_val = float(current['ATR'].iloc[0]) if isinstance(current['ATR'], pd.Series) else float(current['ATR'])
            
            if (close_val > high_20 and 
                volume_val > volume_ma_val * 1.5 and
                rsi_val > 50 and rsi_val < 70 and
                close_val > sma20_val):
                
                # Calculate target (10% move from breakout)
                target_price = close_val * 1.10
                
                # Calculate stop loss (2x ATR or 5%, whichever tighter)
                atr_stop = close_val - (2 * atr_val)
                pct_stop = close_val * 0.95
                stop_price = max(atr_stop, pct_stop)
                
                signal = {
                    'date': df.index[i],
                    'pattern': 'Breakout',
                    'entry_price': close_val,
                    'target_price': target_price,
                    'stop_price': stop_price,
                    'atr': atr_val,
                    'score': 60  # Base score
                }
                
                signals.append(signal)
            
            # DOUBLE BOTTOM PATTERN
            # Two lows at similar level, breakout above neckline
            if i >= 60:
                lows = df['Low'].iloc[i-60:i]
                low_1_idx = lows.iloc[:30].idxmin()
                low_2_idx = lows.iloc[30:].idxmin()
                
                if low_1_idx != low_2_idx:
                    low_1 = df.loc[low_1_idx, 'Low']
                    low_2 = df.loc[low_2_idx, 'Low']
                    
                    # Lows should be within 3% of each other
                    if abs(low_1 - low_2) / low_1 < 0.03:
                        # Neckline is the high between the two lows
                        between_highs = df.loc[low_1_idx:low_2_idx, 'High']
                        neckline = between_highs.max()
                        
                        # Breakout above neckline
                        if (current['Close'] > neckline and
                            current['Volume'] > current['Volume_MA'] * 1.5):
                            
                            # Target: Measured move (neckline + (neckline - low))
                            measured_move = neckline - min(low_1, low_2)
                            target_price = neckline + (measured_move * 0.5)  # 50% of move
                            
                            # Stop: Below recent low
                            stop_price = min(low_1, low_2) * 0.98
                            
                            signal = {
                                'date': df.index[i],
                                'pattern': 'Double Bottom',
                                'entry_price': current['Close'],
                                'target_price': target_price,
                                'stop_price': stop_price,
                                'atr': current['ATR'],
                                'score': 70  # Higher score (proven pattern)
                            }
                            
                            signals.append(signal)
        
        return signals
    
    def backtest_stock(self, symbol, start_date, end_date):
        """Backtest one stock"""
        try:
            # Download data
            df = yf.download(symbol, start=start_date, end=end_date, progress=False)
            
            if df.empty or len(df) < 60:
                return []
            
            # Detect patterns
            signals = self.detect_patterns(df)
            
            stock_trades = []
            
            for signal in signals:
                entry_date = signal['date']
                entry_stock_price = signal['entry_price']
                target_stock_price = signal['target_price']
                stop_stock_price = signal['stop_price']
                
                # Simulate ATM option purchase
                strike = round(entry_stock_price / 50) * 50  # Round to nearest 50
                
                # Get future price data (max 7 days hold)
                future_data = df[df.index > entry_date].head(7)
                
                if future_data.empty:
                    continue
                
                # Initial option premium
                initial_premium, _ = self.simulate_option_price(
                    entry_stock_price, strike, 7, 0
                )
                
                # Position size (risk 5% of capital)
                risk_amount = self.capital * self.risk_per_trade
                
                # Stop loss on option: 50% of premium
                option_stop_loss = initial_premium * 0.50
                
                # Quantity (how many options can we buy with risk amount)
                # Risk = premium * quantity
                quantity = int(risk_amount / initial_premium)
                quantity = max(1, quantity)  # At least 1
                
                # Track the trade
                exit_date = None
                exit_price = None
                exit_reason = None
                pnl = 0
                
                for j, (date, row) in enumerate(future_data.iterrows()):
                    days_held = j + 1
                    stock_price = row['Close']
                    
                    # Calculate stock move %
                    stock_move_pct = (stock_price - entry_stock_price) / entry_stock_price
                    
                    # Simulate current option price
                    _, current_premium = self.simulate_option_price(
                        entry_stock_price, strike, 7 - days_held, stock_move_pct
                    )
                    
                    # Check exit conditions
                    
                    # 1. Target hit (stock reached target)
                    if stock_price >= target_stock_price:
                        exit_date = date
                        exit_price = current_premium
                        exit_reason = 'TARGET'
                        pnl = (exit_price - initial_premium) * quantity
                        break
                    
                    # 2. Stop loss hit (option lost 50%)
                    if current_premium <= option_stop_loss:
                        exit_date = date
                        exit_price = current_premium
                        exit_reason = 'STOP_LOSS'
                        pnl = (exit_price - initial_premium) * quantity
                        break
                    
                    # 3. Stock stop hit (underlying hit stop)
                    if stock_price <= stop_stock_price:
                        exit_date = date
                        exit_price = current_premium
                        exit_reason = 'STOCK_STOP'
                        pnl = (exit_price - initial_premium) * quantity
                        break
                    
                    # 4. Time stop (7 days / expiry)
                    if days_held >= 7:
                        exit_date = date
                        exit_price = current_premium
                        exit_reason = 'TIME_STOP'
                        pnl = (exit_price - initial_premium) * quantity
                        break
                
                # If no exit, close at last available price
                if exit_date is None:
                    last_row = future_data.iloc[-1]
                    exit_date = future_data.index[-1]
                    stock_move_pct = (last_row['Close'] - entry_stock_price) / entry_stock_price
                    _, exit_price = self.simulate_option_price(
                        entry_stock_price, strike, 0, stock_move_pct
                    )
                    exit_reason = 'TIME_STOP'
                    pnl = (exit_price - initial_premium) * quantity
                
                # Update capital
                self.capital += pnl
                
                # Record trade
                trade = {
                    'symbol': symbol,
                    'pattern': signal['pattern'],
                    'entry_date': entry_date,
                    'exit_date': exit_date,
                    'entry_stock': entry_stock_price,
                    'exit_stock': future_data.loc[exit_date, 'Close'] if exit_date in future_data.index else entry_stock_price,
                    'strike': strike,
                    'entry_premium': initial_premium,
                    'exit_premium': exit_price,
                    'quantity': quantity,
                    'pnl': pnl,
                    'pnl_pct': (pnl / (initial_premium * quantity)) * 100,
                    'exit_reason': exit_reason,
                    'days_held': (exit_date - entry_date).days if exit_date else 0,
                    'capital_after': self.capital
                }
                
                stock_trades.append(trade)
                self.trades.append(trade)
            
            return stock_trades
            
        except Exception as e:
            print(f"Error backtesting {symbol}: {e}")
            return []
    
    def run_backtest(self, stock_list, start_date, end_date):
        """Run backtest on multiple stocks"""
        print("\n" + "="*80)
        print("🚀 OPTIONS BUYING BACKTEST (Scanner-v3 Signals)")
        print("="*80)
        print(f"\n📊 Configuration:")
        print(f"   Capital: ₹{self.initial_capital:,}")
        print(f"   Risk per trade: {self.risk_per_trade*100:.1f}%")
        print(f"   Period: {start_date} to {end_date}")
        print(f"   Stocks: {len(stock_list)}")
        print("\n" + "="*80)
        
        for i, symbol in enumerate(stock_list, 1):
            print(f"\r   Progress: {i}/{len(stock_list)} ({i/len(stock_list)*100:.1f}%) - {symbol}     ", end='')
            self.backtest_stock(symbol, start_date, end_date)
        
        print("\n\n" + "="*80)
        self.print_results()
    
    def print_results(self):
        """Print backtest results"""
        print("📊 BACKTEST RESULTS")
        print("="*80)
        
        if not self.trades:
            print("\n❌ No trades executed")
            return
        
        trades_df = pd.DataFrame(self.trades)
        
        # Overall metrics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        win_rate = (winning_trades / total_trades) * 100
        
        total_pnl = trades_df['pnl'].sum()
        total_return = ((self.capital - self.initial_capital) / self.initial_capital) * 100
        
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        avg_win_pct = trades_df[trades_df['pnl'] > 0]['pnl_pct'].mean() if winning_trades > 0 else 0
        avg_loss_pct = trades_df[trades_df['pnl'] < 0]['pnl_pct'].mean() if losing_trades > 0 else 0
        
        profit_factor = abs(trades_df[trades_df['pnl'] > 0]['pnl'].sum() / 
                           trades_df[trades_df['pnl'] < 0]['pnl'].sum()) if losing_trades > 0 else 0
        
        avg_hold = trades_df['days_held'].mean()
        
        # Max drawdown
        trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()
        trades_df['peak'] = trades_df['cumulative_pnl'].cummax()
        trades_df['drawdown'] = trades_df['cumulative_pnl'] - trades_df['peak']
        max_drawdown = trades_df['drawdown'].min()
        max_drawdown_pct = (max_drawdown / self.initial_capital) * 100
        
        # Print summary
        print(f"\n💰 CAPITAL:")
        print(f"   Initial: ₹{self.initial_capital:,}")
        print(f"   Final: ₹{self.capital:,.0f}")
        print(f"   Total P&L: ₹{total_pnl:+,.0f}")
        print(f"   Return: {total_return:+.2f}%")
        
        print(f"\n📈 TRADES:")
        print(f"   Total: {total_trades}")
        print(f"   Winners: {winning_trades} ({win_rate:.1f}%)")
        print(f"   Losers: {losing_trades} ({100-win_rate:.1f}%)")
        
        print(f"\n💵 P&L:")
        print(f"   Avg Win: ₹{avg_win:+,.0f} ({avg_win_pct:+.1f}%)")
        print(f"   Avg Loss: ₹{avg_loss:+,.0f} ({avg_loss_pct:+.1f}%)")
        print(f"   Profit Factor: {profit_factor:.2f}")
        print(f"   Max Drawdown: ₹{max_drawdown:,.0f} ({max_drawdown_pct:.2f}%)")
        
        print(f"\n⏱️  TIMING:")
        print(f"   Avg Hold: {avg_hold:.1f} days")
        
        # Exit reasons
        print(f"\n📋 EXIT REASONS:")
        exit_reasons = trades_df['exit_reason'].value_counts()
        for reason, count in exit_reasons.items():
            print(f"   {reason}: {count} ({count/total_trades*100:.1f}%)")
        
        # Pattern breakdown
        print(f"\n🎯 PATTERN BREAKDOWN:")
        pattern_stats = trades_df.groupby('pattern').agg({
            'pnl': ['count', 'sum', 'mean'],
            'pnl_pct': 'mean'
        }).round(2)
        
        for pattern in pattern_stats.index:
            count = int(pattern_stats.loc[pattern, ('pnl', 'count')])
            total_pnl = pattern_stats.loc[pattern, ('pnl', 'sum')]
            avg_pnl = pattern_stats.loc[pattern, ('pnl', 'mean')]
            avg_pct = pattern_stats.loc[pattern, ('pnl_pct', 'mean')]
            wins = len(trades_df[(trades_df['pattern'] == pattern) & (trades_df['pnl'] > 0)])
            wr = (wins / count) * 100
            
            print(f"   {pattern}: {count} trades, {wr:.1f}% WR, ₹{avg_pnl:+,.0f} avg ({avg_pct:+.1f}%)")
        
        # Recent trades
        print(f"\n📜 LAST 10 TRADES:")
        recent = trades_df.tail(10)[['symbol', 'pattern', 'entry_date', 'entry_premium', 'exit_premium', 'pnl', 'pnl_pct', 'exit_reason']]
        recent['entry_date'] = recent['entry_date'].dt.strftime('%Y-%m-%d')
        print(tabulate(recent, headers='keys', tablefmt='simple', showindex=False, floatfmt='.0f'))
        
        # Performance grade
        print(f"\n🎯 PERFORMANCE GRADE:")
        grade = self.calculate_grade(win_rate, profit_factor, total_return, max_drawdown_pct)
        print(f"   {grade}")
        
        # Save results
        trades_df.to_csv('results/options_buying_backtest.csv', index=False)
        print(f"\n💾 Results saved to results/options_buying_backtest.csv")
        print("="*80 + "\n")
    
    def calculate_grade(self, win_rate, profit_factor, total_return, max_drawdown):
        """Calculate performance grade"""
        score = 0
        
        # Win rate (max 30 points)
        if win_rate >= 60:
            score += 30
        elif win_rate >= 50:
            score += 25
        elif win_rate >= 45:
            score += 20
        elif win_rate >= 40:
            score += 15
        else:
            score += 10
        
        # Profit factor (max 30 points)
        if profit_factor >= 2.0:
            score += 30
        elif profit_factor >= 1.5:
            score += 25
        elif profit_factor >= 1.2:
            score += 20
        else:
            score += 10
        
        # Total return (max 25 points)
        if total_return >= 100:
            score += 25
        elif total_return >= 50:
            score += 20
        elif total_return >= 30:
            score += 15
        elif total_return >= 10:
            score += 10
        else:
            score += 5
        
        # Max drawdown (max 15 points)
        if max_drawdown > -10:
            score += 15
        elif max_drawdown > -15:
            score += 10
        elif max_drawdown > -20:
            score += 7
        else:
            score += 3
        
        # Grade
        if score >= 85:
            return f"⭐⭐⭐⭐⭐ EXCELLENT ({score}/100) - Ready for live trading!"
        elif score >= 70:
            return f"⭐⭐⭐⭐ GOOD ({score}/100) - Needs minor tweaks"
        elif score >= 55:
            return f"⭐⭐⭐ AVERAGE ({score}/100) - Needs improvement"
        elif score >= 40:
            return f"⭐⭐ BELOW AVERAGE ({score}/100) - Major changes needed"
        else:
            return f"⭐ POOR ({score}/100) - Strategy not viable"

if __name__ == "__main__":
    import os
    os.makedirs('results', exist_ok=True)
    
    # Backbone 50 stocks (from scanner-v3)
    backbone50 = [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
        'HINDUNILVR.NS', 'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS',
        'LT.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'MARUTI.NS', 'TITAN.NS',
        'SUNPHARMA.NS', 'ULTRACEMCO.NS', 'BAJFINANCE.NS', 'NESTLEIND.NS', 'WIPRO.NS',
        'HCLTECH.NS', 'TECHM.NS', 'POWERGRID.NS', 'NTPC.NS', 'TATAMOTORS.NS',
        'TATASTEEL.NS', 'ADANIENT.NS', 'ONGC.NS', 'JSWSTEEL.NS', 'HINDALCO.NS',
        'INDUSINDBK.NS', 'BAJAJFINSV.NS', 'DIVISLAB.NS', 'DRREDDY.NS', 'CIPLA.NS',
        'EICHERMOT.NS', 'BRITANNIA.NS', 'APOLLOHOSP.NS', 'ADANIPORTS.NS', 'COALINDIA.NS',
        'TATACONSUM.NS', 'GRASIM.NS', 'HEROMOTOCO.NS', 'SBILIFE.NS', 'BAJAJ-AUTO.NS',
        'BPCL.NS', 'HDFCLIFE.NS', 'SHREECEM.NS', 'PIDILITIND.NS', 'HAVELLS.NS'
    ]
    
    # Run backtest
    backtester = OptionsBuyingBacktest(capital=50000, risk_per_trade=0.05)
    
    # Backtest period: Last 1 year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    backtester.run_backtest(
        stock_list=backbone50,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
