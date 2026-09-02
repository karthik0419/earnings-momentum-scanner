"""
Backtest Options Buying Strategy - NIFTY & BANK NIFTY ONLY
Simplified, realistic approach for index options
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from tabulate import tabulate
import warnings
warnings.filterwarnings('ignore')

class NiftyBankNiftyOptionsBacktest:
    """
    Backtest options buying on Nifty 50 and Bank Nifty indices
    
    Strategy:
    1. Detect momentum signals (breakout, MACD crossover, RSI)
    2. Buy ATM Call/Put options
    3. Stop Loss: 50% of premium
    4. Target: 100% profit (2x premium)
    5. Max hold: 3 days (intraday to short-term)
    """
    
    def __init__(self, capital=50000, risk_per_trade=0.05):
        self.initial_capital = capital
        self.capital = capital
        self.risk_per_trade = risk_per_trade
        self.trades = []
        
    def calculate_indicators(self, df):
        """Calculate technical indicators"""
        # Handle multi-index columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        
        # SMA
        df['SMA20'] = df['Close'].rolling(20).mean()
        df['SMA50'] = df['Close'].rolling(50).mean()
        
        # EMA
        df['EMA9'] = df['Close'].ewm(span=9).mean()
        df['EMA21'] = df['Close'].ewm(span=21).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12).mean()
        exp2 = df['Close'].ewm(span=26).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # Volume
        df['Volume_MA'] = df['Volume'].rolling(20).mean()
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['ATR'] = true_range.rolling(14).mean()
        
        return df
    
    def generate_signals(self, df, index_name):
        """Generate buy/sell signals"""
        signals = []
        
        for i in range(50, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i-1]
            
            # Skip if missing data
            rsi_val = float(row['RSI'])
            macd_val = float(row['MACD'])
            
            if pd.isna(rsi_val) or pd.isna(macd_val):
                continue
            
            # BULLISH SIGNALS (Buy Call)
            
            # Extract values
            close_val = float(row['Close'])
            sma20_val = float(row['SMA20'])
            volume_val = float(row['Volume'])
            volume_ma_val = float(row['Volume_MA'])
            
            # Signal 1: MACD Crossover + RSI > 50
            macd_cross_up = (float(prev['MACD']) <= float(prev['MACD_Signal']) and 
                           macd_val > float(row['MACD_Signal']))
            
            if (macd_cross_up and 
                rsi_val > 50 and rsi_val < 70 and
                close_val > sma20_val):
                
                signals.append({
                    'date': df.index[i],
                    'type': 'CE',  # Call option
                    'entry_price': close_val,
                    'pattern': 'MACD Crossover',
                    'index': index_name
                })
            
            # Signal 2: Breakout above 20-day high
            high_20 = df['High'].iloc[i-20:i].max()
            
            if (close_val > high_20 and
                volume_val > volume_ma_val * 1.5 and
                rsi_val > 50):
                
                signals.append({
                    'date': df.index[i],
                    'type': 'CE',
                    'entry_price': close_val,
                    'pattern': 'Breakout',
                    'index': index_name
                })
            
            # Signal 3: Strong momentum (1%+ move with volume)
            price_change = (close_val - float(prev['Close'])) / float(prev['Close'])
            
            if (price_change > 0.01 and  # 1%+ move
                volume_val > volume_ma_val * 2.0 and
                rsi_val > 55 and rsi_val < 75):
                
                signals.append({
                    'date': df.index[i],
                    'type': 'CE',
                    'entry_price': close_val,
                    'pattern': 'Momentum',
                    'index': index_name
                })
            
            # BEARISH SIGNALS (Buy Put)
            
            # Signal 4: MACD Cross Down + RSI < 50
            macd_cross_down = (float(prev['MACD']) >= float(prev['MACD_Signal']) and 
                             macd_val < float(row['MACD_Signal']))
            
            if (macd_cross_down and 
                rsi_val < 50 and rsi_val > 30 and
                close_val < sma20_val):
                
                signals.append({
                    'date': df.index[i],
                    'type': 'PE',  # Put option
                    'entry_price': close_val,
                    'pattern': 'MACD Cross Down',
                    'index': index_name
                })
        
        return signals
    
    def simulate_option_trade(self, signal, df):
        """Simulate one options trade"""
        entry_date = signal['date']
        entry_index_price = signal['entry_price']
        option_type = signal['type']
        index_name = signal['index']
        
        # ATM strike (round to nearest 50 for Nifty, 100 for BankNifty/Sensex)
        if 'BANK' in index_name.upper() or 'SENSEX' in index_name.upper():
            strike_round = 100
        else:
            strike_round = 50
        
        strike = round(entry_index_price / strike_round) * strike_round
        
        # Initial option premium (simplified)
        # Weekly ATM options typically 1-3% of index value
        initial_premium = entry_index_price * 0.02  # 2% of index
        
        # Position size
        risk_amount = self.capital * self.risk_per_trade
        quantity = int(risk_amount / initial_premium)
        quantity = max(1, min(quantity, 3))  # 1-3 lots max
        
        # Lot size
        if 'BANK' in index_name.upper():
            lot_size = 15  # Bank Nifty lot size
        elif 'SENSEX' in index_name.upper():
            lot_size = 10  # Sensex lot size
        else:
            lot_size = 50  # Nifty lot size
        
        total_quantity = quantity * lot_size
        
        # Get future data (max 3 days)
        future_data = df[df.index > entry_date].head(3)
        
        if future_data.empty:
            return None
        
        # Track the trade
        for j, (date, row) in enumerate(future_data.iterrows()):
            days_held = j + 1
            current_index_price = row['Close']
            
            # Calculate index move %
            index_move_pct = (current_index_price - entry_index_price) / entry_index_price
            
            # Option price simulation (simplified)
            # Delta ~0.5 for ATM, decreases 10% per day (theta)
            delta = 0.5
            theta_decay = 0.15 * days_held  # 15% per day
            
            if option_type == 'CE':  # Call
                intrinsic_change = max(0, index_move_pct) * delta
            else:  # Put
                intrinsic_change = max(0, -index_move_pct) * delta
            
            current_premium = initial_premium * (1 + intrinsic_change - theta_decay)
            current_premium = max(0.01, current_premium)  # Can't go below 0
            
            # Exit conditions
            
            # 1. Target: 100% profit (2x premium)
            if current_premium >= initial_premium * 2.0:
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
                    'days_held': days_held,
                    'index_move': index_move_pct * 100
                }
            
            # 2. Stop Loss: 50% loss
            if current_premium <= initial_premium * 0.5:
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
                    'days_held': days_held,
                    'index_move': index_move_pct * 100
                }
        
        # 3. Time stop (3 days)
        last_row = future_data.iloc[-1]
        last_date = future_data.index[-1]
        current_index_price = last_row['Close']
        index_move_pct = (current_index_price - entry_index_price) / entry_index_price
        
        delta = 0.5
        theta_decay = 0.15 * 3
        
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
            'exit_date': last_date,
            'strike': strike,
            'entry_premium': initial_premium,
            'exit_premium': current_premium,
            'quantity': total_quantity,
            'lots': quantity,
            'pnl': pnl,
            'pnl_pct': ((current_premium - initial_premium) / initial_premium) * 100,
            'exit_reason': 'TIME_STOP',
            'days_held': 3,
            'index_move': index_move_pct * 100
        }
    
    def run_backtest(self, start_date, end_date):
        """Run backtest on Nifty, Bank Nifty, and Sensex"""
        print("\n" + "="*80)
        print("🚀 NIFTY, BANK NIFTY & SENSEX OPTIONS BACKTEST")
        print("="*80)
        print(f"\n📊 Configuration:")
        print(f"   Capital: ₹{self.initial_capital:,}")
        print(f"   Risk per trade: {self.risk_per_trade*100:.1f}%")
        print(f"   Period: {start_date} to {end_date}")
        print(f"   Indices: NIFTY 50, BANK NIFTY, SENSEX")
        print("\n" + "="*80)
        
        # Download data
        print("\n📥 Downloading data...")
        
        nifty = yf.download('^NSEI', start=start_date, end=end_date, progress=False)
        banknifty = yf.download('^NSEBANK', start=start_date, end=end_date, progress=False)
        sensex = yf.download('^BSESN', start=start_date, end=end_date, progress=False)
        
        if nifty.empty or banknifty.empty or sensex.empty:
            print("❌ Failed to download data")
            return
        
        print(f"   ✅ Nifty: {len(nifty)} days")
        print(f"   ✅ Bank Nifty: {len(banknifty)} days")
        print(f"   ✅ Sensex: {len(sensex)} days")
        
        # Calculate indicators
        print("\n📊 Calculating indicators...")
        nifty = self.calculate_indicators(nifty)
        banknifty = self.calculate_indicators(banknifty)
        sensex = self.calculate_indicators(sensex)
        
        # Generate signals
        print("\n🎯 Generating signals...")
        nifty_signals = self.generate_signals(nifty, 'NIFTY')
        banknifty_signals = self.generate_signals(banknifty, 'BANKNIFTY')
        sensex_signals = self.generate_signals(sensex, 'SENSEX')
        
        all_signals = nifty_signals + banknifty_signals + sensex_signals
        all_signals.sort(key=lambda x: x['date'])
        
        print(f"   ✅ Total signals: {len(all_signals)}")
        print(f"      - Nifty: {len(nifty_signals)}")
        print(f"      - Bank Nifty: {len(banknifty_signals)}")
        print(f"      - Sensex: {len(sensex_signals)}")
        
        # Simulate trades
        print("\n💹 Simulating trades...")
        
        for i, signal in enumerate(all_signals):
            if 'BANK' in signal['index'].upper():
                df = banknifty
            elif 'SENSEX' in signal['index'].upper():
                df = sensex
            else:
                df = nifty
            
            trade = self.simulate_option_trade(signal, df)
            
            if trade:
                self.trades.append(trade)
                
                if (i + 1) % 10 == 0:
                    print(f"   Progress: {i+1}/{len(all_signals)} signals processed")
        
        print(f"\n   ✅ Executed {len(self.trades)} trades")
        
        # Print results
        print("\n" + "="*80)
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
        print(f"   Avg Hold: {trades_df['days_held'].mean():.1f} days")
        
        # By index
        print(f"\n📊 BY INDEX:")
        for index in ['NIFTY', 'BANKNIFTY', 'SENSEX']:
            idx_trades = trades_df[trades_df['index'] == index]
            if len(idx_trades) > 0:
                idx_wins = len(idx_trades[idx_trades['pnl'] > 0])
                idx_wr = (idx_wins / len(idx_trades)) * 100
                idx_pnl = idx_trades['pnl'].sum()
                print(f"   {index}: {len(idx_trades)} trades, {idx_wr:.1f}% WR, ₹{idx_pnl:+,.0f}")
        
        # By option type
        print(f"\n📊 BY OPTION TYPE:")
        for opt_type in ['CE', 'PE']:
            opt_trades = trades_df[trades_df['option_type'] == opt_type]
            if len(opt_trades) > 0:
                opt_wins = len(opt_trades[opt_trades['pnl'] > 0])
                opt_wr = (opt_wins / len(opt_trades)) * 100
                opt_pnl = opt_trades['pnl'].sum()
                print(f"   {opt_type}: {len(opt_trades)} trades, {opt_wr:.1f}% WR, ₹{opt_pnl:+,.0f}")
        
        # By pattern
        print(f"\n📊 BY PATTERN:")
        pattern_stats = trades_df.groupby('pattern').agg({
            'pnl': ['count', 'sum', 'mean']
        }).round(0)
        
        for pattern in pattern_stats.index:
            count = int(pattern_stats.loc[pattern, ('pnl', 'count')])
            total = pattern_stats.loc[pattern, ('pnl', 'sum')]
            avg = pattern_stats.loc[pattern, ('pnl', 'mean')]
            wins = len(trades_df[(trades_df['pattern'] == pattern) & (trades_df['pnl'] > 0)])
            wr = (wins / count) * 100
            print(f"   {pattern}: {count} trades, {wr:.1f}% WR, ₹{avg:+,.0f} avg")
        
        # Exit reasons
        print(f"\n📋 EXIT REASONS:")
        exit_reasons = trades_df['exit_reason'].value_counts()
        for reason, count in exit_reasons.items():
            print(f"   {reason}: {count} ({count/total_trades*100:.1f}%)")
        
        # Recent trades
        print(f"\n📜 LAST 10 TRADES:")
        recent = trades_df.tail(10)[['index', 'option_type', 'pattern', 'entry_premium', 'exit_premium', 'pnl', 'pnl_pct', 'exit_reason']]
        print(tabulate(recent, headers='keys', tablefmt='simple', showindex=False, floatfmt='.0f'))
        
        # Performance grade
        print(f"\n🎯 PERFORMANCE GRADE:")
        grade = self.calculate_grade(win_rate, profit_factor, total_return)
        print(f"   {grade}")
        
        # Save results
        trades_df.to_csv('results/nifty_banknifty_backtest.csv', index=False)
        print(f"\n💾 Results saved to results/nifty_banknifty_backtest.csv")
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
            return f"⭐⭐⭐⭐⭐ EXCELLENT ({score}/100) - Ready for live!"
        elif score >= 70:
            return f"⭐⭐⭐⭐ GOOD ({score}/100) - Promising"
        elif score >= 55:
            return f"⭐⭐⭐ AVERAGE ({score}/100) - Needs work"
        else:
            return f"⭐⭐ BELOW AVERAGE ({score}/100) - Revise strategy"

if __name__ == "__main__":
    import os
    os.makedirs('results', exist_ok=True)
    
    # Run backtest
    backtester = NiftyBankNiftyOptionsBacktest(capital=50000, risk_per_trade=0.05)
    
    # Last 1 year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    backtester.run_backtest(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
