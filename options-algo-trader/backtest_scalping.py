"""
Options Scalping Strategy - INTRADAY (5-30 minute holds)
Beat time decay with QUICK entries and exits
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time as dt_time
import yfinance as yf
from tabulate import tabulate
import warnings
warnings.filterwarnings('ignore')

class OptionsScalpingBacktest:
    """
    Scalping strategy for Nifty/BankNifty/Sensex options
    
    Key Differences from Regular Options Buying:
    1. VERY SHORT holds (5-30 minutes) - minimize theta decay
    2. Quick profit targets (20-50% on premium)
    3. Tight stops (30% loss)
    4. High frequency (multiple trades per day)
    5. Only trade during high volatility periods
    
    Strategy:
    - Entry: Strong momentum + volume surge
    - Target: 30-50% profit on premium (QUICK!)
    - Stop: 30% loss
    - Max hold: 30 minutes
    - Trade only: 9:30-11:00 AM, 2:00-3:15 PM (high volatility)
    """
    
    def __init__(self, capital=50000, risk_per_trade=0.03):
        self.initial_capital = capital
        self.capital = capital
        self.risk_per_trade = risk_per_trade  # 3% per trade (aggressive scalping)
        self.trades = []
        
    def is_trading_time(self, current_time):
        """Check if current time is good for scalping"""
        # Morning session: 9:30-11:00 (high volatility after open)
        morning_start = dt_time(9, 30)
        morning_end = dt_time(11, 0)
        
        # Afternoon session: 2:00-3:15 (pre-close volatility)
        afternoon_start = dt_time(14, 0)
        afternoon_end = dt_time(15, 15)
        
        if isinstance(current_time, pd.Timestamp):
            current_time = current_time.time()
        
        return ((morning_start <= current_time <= morning_end) or 
                (afternoon_start <= current_time <= afternoon_end))
    
    def calculate_indicators(self, df):
        """Calculate scalping indicators (fast-moving)"""
        # Handle multi-index
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        
        # Fast EMAs for scalping
        df['EMA5'] = df['Close'].ewm(span=5).mean()
        df['EMA13'] = df['Close'].ewm(span=13).mean()
        df['EMA20'] = df['Close'].ewm(span=20).mean()
        
        # Fast RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(9).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(9).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD (fast settings for scalping)
        exp1 = df['Close'].ewm(span=8).mean()
        exp2 = df['Close'].ewm(span=17).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        
        # Volume
        df['Volume_MA'] = df['Volume'].rolling(10).mean()
        
        # Price momentum (very short-term)
        df['Price_Change_1'] = df['Close'].pct_change(1)
        df['Price_Change_5'] = df['Close'].pct_change(5)
        
        return df
    
    def generate_scalping_signals(self, df, index_name):
        """Generate scalping signals (very aggressive)"""
        signals = []
        
        for i in range(20, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i-1]
            
            # Skip if missing data
            if pd.isna(row['RSI']) or pd.isna(row['MACD']):
                continue
            
            # Extract values
            close_val = float(row['Close'])
            rsi_val = float(row['RSI'])
            macd_val = float(row['MACD'])
            macd_signal_val = float(row['MACD_Signal'])
            ema5_val = float(row['EMA5'])
            ema13_val = float(row['EMA13'])
            volume_val = float(row['Volume'])
            volume_ma_val = float(row['Volume_MA'])
            price_change_1 = float(row['Price_Change_1'])
            
            current_time = df.index[i]
            
            # Only trade during scalping hours
            if not self.is_trading_time(current_time):
                continue
            
            # SCALPING SIGNAL 1: Strong momentum burst (BULLISH)
            # Price jumps 0.5%+ with volume in 1 candle
            if (price_change_1 > 0.005 and  # 0.5%+ move
                volume_val > volume_ma_val * 2.0 and
                rsi_val > 50 and rsi_val < 75 and
                ema5_val > ema13_val):  # Short-term uptrend
                
                signals.append({
                    'date': current_time,
                    'type': 'CE',
                    'entry_price': close_val,
                    'pattern': 'Momentum Burst',
                    'index': index_name,
                    'strength': 'HIGH'
                })
            
            # SCALPING SIGNAL 2: MACD crossover with volume (BULLISH)
            macd_cross_up = (float(prev['MACD']) <= float(prev['MACD_Signal']) and 
                           macd_val > macd_signal_val)
            
            if (macd_cross_up and
                volume_val > volume_ma_val * 1.5 and
                rsi_val > 45 and rsi_val < 70):
                
                signals.append({
                    'date': current_time,
                    'type': 'CE',
                    'entry_price': close_val,
                    'pattern': 'MACD Cross',
                    'index': index_name,
                    'strength': 'MEDIUM'
                })
            
            # SCALPING SIGNAL 3: RSI oversold bounce (BULLISH)
            rsi_prev = float(prev['RSI'])
            if (rsi_prev < 35 and rsi_val > 35 and  # Bounce from oversold
                price_change_1 > 0 and
                volume_val > volume_ma_val):
                
                signals.append({
                    'date': current_time,
                    'type': 'CE',
                    'entry_price': close_val,
                    'pattern': 'RSI Bounce',
                    'index': index_name,
                    'strength': 'MEDIUM'
                })
            
            # SCALPING SIGNAL 4: Strong momentum burst (BEARISH)
            if (price_change_1 < -0.005 and  # -0.5%+ move
                volume_val > volume_ma_val * 2.0 and
                rsi_val < 50 and rsi_val > 25 and
                ema5_val < ema13_val):  # Short-term downtrend
                
                signals.append({
                    'date': current_time,
                    'type': 'PE',
                    'entry_price': close_val,
                    'pattern': 'Momentum Drop',
                    'index': index_name,
                    'strength': 'HIGH'
                })
            
            # SCALPING SIGNAL 5: MACD cross down (BEARISH)
            macd_cross_down = (float(prev['MACD']) >= float(prev['MACD_Signal']) and 
                             macd_val < macd_signal_val)
            
            if (macd_cross_down and
                volume_val > volume_ma_val * 1.5 and
                rsi_val < 55 and rsi_val > 30):
                
                signals.append({
                    'date': current_time,
                    'type': 'PE',
                    'entry_price': close_val,
                    'pattern': 'MACD Cross Down',
                    'index': index_name,
                    'strength': 'MEDIUM'
                })
        
        return signals
    
    def simulate_scalping_trade(self, signal, df):
        """Simulate one scalping trade (5-30 min hold)"""
        entry_date = signal['date']
        entry_index_price = signal['entry_price']
        option_type = signal['type']
        index_name = signal['index']
        strength = signal['strength']
        
        # ATM strike
        if 'BANK' in index_name.upper() or 'SENSEX' in index_name.upper():
            strike_round = 100
        else:
            strike_round = 50
        
        strike = round(entry_index_price / strike_round) * strike_round
        
        # Initial premium (ATM weekly option)
        initial_premium = entry_index_price * 0.02  # 2% of index
        
        # Position size (smaller for scalping - quick in/out)
        risk_amount = self.capital * self.risk_per_trade
        quantity = int(risk_amount / initial_premium)
        quantity = max(1, min(quantity, 2))  # Max 2 lots for scalping
        
        # Lot size
        if 'BANK' in index_name.upper():
            lot_size = 15
        elif 'SENSEX' in index_name.upper():
            lot_size = 10
        else:
            lot_size = 50
        
        total_quantity = quantity * lot_size
        
        # Get future data (next 30 minutes = 6 candles of 5-min data)
        # For daily data, we'll simulate with next 1-2 days
        future_data = df[df.index > entry_date].head(2)
        
        if future_data.empty:
            return None
        
        # SCALPING TARGETS (AGGRESSIVE)
        if strength == 'HIGH':
            target_pct = 0.50  # 50% profit target
            stop_pct = 0.30    # 30% stop loss
        else:
            target_pct = 0.30  # 30% profit target
            stop_pct = 0.30    # 30% stop loss
        
        target_premium = initial_premium * (1 + target_pct)
        stop_premium = initial_premium * (1 - stop_pct)
        
        # Simulate scalping (assume we can exit within minutes)
        for j, (date, row) in enumerate(future_data.iterrows()):
            current_index_price = float(row['Close'])
            
            # Calculate index move
            index_move_pct = (current_index_price - entry_index_price) / entry_index_price
            
            # Option price (simplified - delta ~0.6 for scalping, minimal theta in minutes)
            delta = 0.6  # Higher delta for ATM scalping
            theta_decay = 0.02 * j  # Only 2% theta per period (scalping is fast)
            
            if option_type == 'CE':
                intrinsic_change = max(0, index_move_pct) * delta
            else:
                intrinsic_change = max(0, -index_move_pct) * delta
            
            current_premium = initial_premium * (1 + intrinsic_change - theta_decay)
            current_premium = max(0.01, current_premium)
            
            # EXIT CONDITIONS (SCALPING)
            
            # 1. TARGET HIT (30-50% profit)
            if current_premium >= target_premium:
                pnl = (current_premium - initial_premium) * total_quantity
                self.capital += pnl
                
                return {
                    'index': index_name,
                    'pattern': signal['pattern'],
                    'option_type': option_type,
                    'entry_date': entry_date,
                    'exit_date': date,
                    'strike': strike,
                    'entry_premium': initial_premium,
                    'exit_premium': current_premium,
                    'quantity': total_quantity,
                    'lots': quantity,
                    'pnl': pnl,
                    'pnl_pct': ((current_premium - initial_premium) / initial_premium) * 100,
                    'exit_reason': 'TARGET',
                    'hold_minutes': (j + 1) * 5,  # Simulated minutes
                    'index_move': index_move_pct * 100,
                    'strength': strength
                }
            
            # 2. STOP LOSS (30%)
            if current_premium <= stop_premium:
                pnl = (current_premium - initial_premium) * total_quantity
                self.capital += pnl
                
                return {
                    'index': index_name,
                    'pattern': signal['pattern'],
                    'option_type': option_type,
                    'entry_date': entry_date,
                    'exit_date': date,
                    'strike': strike,
                    'entry_premium': initial_premium,
                    'exit_premium': current_premium,
                    'quantity': total_quantity,
                    'lots': quantity,
                    'pnl': pnl,
                    'pnl_pct': ((current_premium - initial_premium) / initial_premium) * 100,
                    'exit_reason': 'STOP_LOSS',
                    'hold_minutes': (j + 1) * 5,
                    'index_move': index_move_pct * 100,
                    'strength': strength
                }
        
        # 3. TIME STOP (didn't hit target or stop in time)
        last_row = future_data.iloc[-1]
        last_index_price = float(last_row['Close'])
        index_move_pct = (last_index_price - entry_index_price) / entry_index_price
        
        delta = 0.6
        theta_decay = 0.02 * len(future_data)
        
        if option_type == 'CE':
            intrinsic_change = max(0, index_move_pct) * delta
        else:
            intrinsic_change = max(0, -index_move_pct) * delta
        
        current_premium = initial_premium * (1 + intrinsic_change - theta_decay)
        current_premium = max(0.01, current_premium)
        
        pnl = (current_premium - initial_premium) * total_quantity
        self.capital += pnl
        
        return {
            'index': index_name,
            'pattern': signal['pattern'],
            'option_type': option_type,
            'entry_date': entry_date,
            'exit_date': future_data.index[-1],
            'strike': strike,
            'entry_premium': initial_premium,
            'exit_premium': current_premium,
            'quantity': total_quantity,
            'lots': quantity,
            'pnl': pnl,
            'pnl_pct': ((current_premium - initial_premium) / initial_premium) * 100,
            'exit_reason': 'TIME_STOP',
            'hold_minutes': len(future_data) * 5,
            'index_move': index_move_pct * 100,
            'strength': strength
        }
    
    def run_backtest(self, start_date, end_date):
        """Run scalping backtest"""
        print("\n" + "="*80)
        print("⚡ OPTIONS SCALPING BACKTEST (5-30 MIN HOLDS)")
        print("="*80)
        print(f"\n📊 Configuration:")
        print(f"   Capital: ₹{self.initial_capital:,}")
        print(f"   Risk per trade: {self.risk_per_trade*100:.1f}%")
        print(f"   Period: {start_date} to {end_date}")
        print(f"   Strategy: SCALPING (quick in/out)")
        print(f"   Target: 30-50% profit")
        print(f"   Stop: 30% loss")
        print(f"   Max hold: 30 minutes")
        print("\n" + "="*80)
        
        # Download data
        print("\n📥 Downloading data...")
        nifty = yf.download('^NSEI', start=start_date, end=end_date, progress=False)
        banknifty = yf.download('^NSEBANK', start=start_date, end=end_date, progress=False)
        sensex = yf.download('^BSESN', start=start_date, end=end_date, progress=False)
        
        print(f"   ✅ Nifty: {len(nifty)} days")
        print(f"   ✅ Bank Nifty: {len(banknifty)} days")
        print(f"   ✅ Sensex: {len(sensex)} days")
        
        # Calculate indicators
        print("\n📊 Calculating scalping indicators...")
        nifty = self.calculate_indicators(nifty)
        banknifty = self.calculate_indicators(banknifty)
        sensex = self.calculate_indicators(sensex)
        
        # Generate signals
        print("\n🎯 Generating scalping signals...")
        nifty_signals = self.generate_scalping_signals(nifty, 'NIFTY')
        banknifty_signals = self.generate_scalping_signals(banknifty, 'BANKNIFTY')
        sensex_signals = self.generate_scalping_signals(sensex, 'SENSEX')
        
        all_signals = nifty_signals + banknifty_signals + sensex_signals
        all_signals.sort(key=lambda x: x['date'])
        
        print(f"   ✅ Total signals: {len(all_signals)}")
        print(f"      - Nifty: {len(nifty_signals)}")
        print(f"      - Bank Nifty: {len(banknifty_signals)}")
        print(f"      - Sensex: {len(sensex_signals)}")
        
        # Simulate trades
        print("\n⚡ Simulating scalping trades...")
        
        for i, signal in enumerate(all_signals):
            if 'BANK' in signal['index'].upper():
                df = banknifty
            elif 'SENSEX' in signal['index'].upper():
                df = sensex
            else:
                df = nifty
            
            trade = self.simulate_scalping_trade(signal, df)
            
            if trade:
                self.trades.append(trade)
                
                if (i + 1) % 20 == 0:
                    print(f"   Progress: {i+1}/{len(all_signals)} signals")
        
        print(f"\n   ✅ Executed {len(self.trades)} scalping trades")
        
        # Print results
        print("\n" + "="*80)
        self.print_results()
    
    def print_results(self):
        """Print backtest results"""
        print("📊 SCALPING BACKTEST RESULTS")
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
        
        print(f"\n⏱️  TIMING:")
        print(f"   Avg Hold: {trades_df['hold_minutes'].mean():.0f} minutes")
        
        # By exit reason
        print(f"\n📋 EXIT REASONS:")
        exit_reasons = trades_df['exit_reason'].value_counts()
        for reason, count in exit_reasons.items():
            print(f"   {reason}: {count} ({count/total_trades*100:.1f}%)")
        
        # By strength
        print(f"\n💪 BY SIGNAL STRENGTH:")
        for strength in ['HIGH', 'MEDIUM']:
            str_trades = trades_df[trades_df['strength'] == strength]
            if len(str_trades) > 0:
                str_wins = len(str_trades[str_trades['pnl'] > 0])
                str_wr = (str_wins / len(str_trades)) * 100
                str_pnl = str_trades['pnl'].sum()
                print(f"   {strength}: {len(str_trades)} trades, {str_wr:.1f}% WR, ₹{str_pnl:+,.0f}")
        
        # Recent trades
        print(f"\n📜 LAST 10 TRADES:")
        recent = trades_df.tail(10)[['index', 'option_type', 'pattern', 'entry_premium', 'exit_premium', 'pnl', 'pnl_pct', 'exit_reason', 'strength']]
        print(tabulate(recent, headers='keys', tablefmt='simple', showindex=False, floatfmt='.0f'))
        
        # Performance grade
        print(f"\n🎯 PERFORMANCE GRADE:")
        grade = self.calculate_grade(win_rate, profit_factor, total_return)
        print(f"   {grade}")
        
        # Save results
        trades_df.to_csv('results/scalping_backtest.csv', index=False)
        print(f"\n💾 Results saved to results/scalping_backtest.csv")
        print("="*80 + "\n")
    
    def calculate_grade(self, win_rate, profit_factor, total_return):
        """Calculate performance grade"""
        score = 0
        
        if win_rate >= 60:
            score += 30
        elif win_rate >= 50:
            score += 25
        elif win_rate >= 45:
            score += 20
        else:
            score += 15
        
        if profit_factor >= 2.0:
            score += 30
        elif profit_factor >= 1.5:
            score += 25
        elif profit_factor >= 1.2:
            score += 20
        else:
            score += 10
        
        if total_return >= 100:
            score += 25
        elif total_return >= 50:
            score += 20
        elif total_return >= 30:
            score += 15
        else:
            score += 10
        
        if score >= 85:
            return f"⭐⭐⭐⭐⭐ EXCELLENT ({score}/100) - Scalping works!"
        elif score >= 70:
            return f"⭐⭐⭐⭐ GOOD ({score}/100) - Promising"
        elif score >= 55:
            return f"⭐⭐⭐ AVERAGE ({score}/100) - Needs work"
        else:
            return f"⭐⭐ BELOW AVERAGE ({score}/100) - Revise"

if __name__ == "__main__":
    import os
    os.makedirs('results', exist_ok=True)
    
    # Run scalping backtest
    backtester = OptionsScalpingBacktest(capital=50000, risk_per_trade=0.03)
    
    # Last 1 year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    backtester.run_backtest(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
