"""
Mock Backtesting System for Options Algo Trading
Simulates realistic options trading with synthetic data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import random
from tabulate import tabulate
import config
from strategy import MomentumScalpingStrategy

class MockOptionsData:
    """Generate realistic mock options data"""
    
    def __init__(self, underlying="NIFTY", days=30):
        self.underlying = underlying
        self.days = days
        self.base_price = 24000 if underlying == "NIFTY" else 52000  # BankNifty
        
    def generate_intraday_data(self, date, volatility=0.01):
        """Generate 5-minute intraday data for one day"""
        # Trading hours: 9:15 AM to 3:30 PM (375 minutes = 75 candles)
        start_time = datetime.combine(date, time(9, 15))
        
        data = []
        current_price = self.base_price
        
        # Generate 75 candles (5-min each)
        for i in range(75):
            timestamp = start_time + timedelta(minutes=i*5)
            
            # Random walk with drift
            drift = random.uniform(-0.002, 0.002)
            shock = random.gauss(0, volatility)
            price_change = drift + shock
            
            # Add momentum bursts (20% chance)
            if random.random() < 0.2:
                momentum = random.choice([0.005, -0.005])  # 0.5% move
                price_change += momentum
            
            current_price *= (1 + price_change)
            
            # OHLC
            high = current_price * (1 + abs(random.gauss(0, 0.001)))
            low = current_price * (1 - abs(random.gauss(0, 0.001)))
            open_price = current_price * (1 + random.gauss(0, 0.0005))
            close = current_price
            
            # Volume (higher during momentum)
            base_volume = random.randint(50000, 200000)
            if abs(price_change) > 0.003:  # Momentum move
                volume = base_volume * random.uniform(2, 5)  # Volume surge
            else:
                volume = base_volume
            
            data.append({
                'timestamp': timestamp,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': int(volume)
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
    
    def generate_option_price(self, underlying_price, strike, option_type, dte):
        """Generate realistic option price based on Black-Scholes approximation"""
        # Simplified option pricing
        moneyness = (underlying_price - strike) / strike
        
        if option_type == "CE":  # Call
            intrinsic = max(0, underlying_price - strike)
        else:  # Put
            intrinsic = max(0, strike - underlying_price)
        
        # Time value (decreases with time)
        time_value = abs(moneyness) * 100 * (dte / 7)  # Rough approximation
        
        # Add some randomness
        noise = random.gauss(0, 5)
        
        option_price = intrinsic + time_value + noise
        return max(10, option_price)  # Min Rs 10
    
    def get_atm_strike(self, underlying_price):
        """Get ATM strike (rounded to nearest 50)"""
        return round(underlying_price / 50) * 50

class MockBacktester:
    """Backtest strategy with mock data"""
    
    def __init__(self, capital=50000, days=30):
        self.capital = capital
        self.initial_capital = capital
        self.days = days
        self.strategy = MomentumScalpingStrategy()
        self.trades = []
        self.equity_curve = []
        
    def run(self):
        """Run backtest"""
        print("\n" + "="*80)
        print("🚀 MOCK BACKTEST - NSE OPTIONS MOMENTUM SCALPING")
        print("="*80)
        print(f"\n📊 Configuration:")
        print(f"   Capital: ₹{self.capital:,}")
        print(f"   Days: {self.days}")
        print(f"   Risk per trade: {config.RISK_PER_TRADE*100:.1f}%")
        print(f"   Target: {config.TARGET_PROFIT_PCT*100:.1f}%")
        print(f"   Stop Loss: {config.STOP_LOSS_PCT*100:.1f}%")
        print(f"   Max hold: {config.MAX_HOLD_TIME_MINUTES} min")
        print("\n" + "="*80)
        
        # Generate data for each day
        start_date = datetime.now() - timedelta(days=self.days)
        
        for day in range(self.days):
            current_date = start_date + timedelta(days=day)
            
            # Skip weekends
            if current_date.weekday() >= 5:
                continue
            
            print(f"\n📅 Day {day+1}/{self.days}: {current_date.strftime('%Y-%m-%d')}")
            
            # Reset daily stats
            self.strategy.reset_daily_stats()
            
            # Generate intraday data
            data_gen = MockOptionsData(underlying="NIFTY", days=1)
            underlying_df = data_gen.generate_intraday_data(current_date)
            
            # Calculate indicators
            underlying_df = self.strategy.calculate_indicators(underlying_df)
            
            # Simulate trading
            self.simulate_day(underlying_df, data_gen, current_date)
            
            # Track equity
            self.equity_curve.append({
                'date': current_date,
                'capital': self.capital,
                'daily_pnl': self.strategy.daily_pnl
            })
            
            print(f"   💰 End of day capital: ₹{self.capital:,.0f} (P&L: ₹{self.strategy.daily_pnl:+,.0f})")
        
        # Print results
        self.print_results()
    
    def simulate_day(self, underlying_df, data_gen, current_date):
        """Simulate one trading day"""
        open_positions = []
        
        for i in range(len(underlying_df)):
            current_time = underlying_df.index[i]
            current_underlying = underlying_df['close'].iloc[i]
            
            # Get data up to current point
            df_slice = underlying_df.iloc[:i+1]
            
            # Check exit conditions for open positions
            for position in open_positions[:]:
                # Update option price (simplified)
                option_price_change = (current_underlying - position['underlying_entry']) / position['underlying_entry']
                current_option_price = position['entry_price'] * (1 + option_price_change * 2)  # Options move 2x underlying
                
                # Update trailing stop
                position = self.strategy.update_trailing_stop(position, current_option_price)
                
                # Check exit
                should_exit, reason, exit_price = self.strategy.check_exit_conditions(
                    position, current_option_price, current_time
                )
                
                if should_exit:
                    # Close position
                    pnl = self.strategy.calculate_pnl(
                        position['entry_price'],
                        exit_price,
                        position['quantity']
                    )
                    
                    # Update capital
                    self.capital += pnl['net_pnl']
                    self.strategy.daily_pnl += pnl['net_pnl']
                    
                    # Track consecutive losses
                    if pnl['net_pnl'] < 0:
                        self.strategy.consecutive_losses += 1
                    else:
                        self.strategy.consecutive_losses = 0
                    
                    # Log trade
                    trade = {
                        'date': current_date,
                        'entry_time': position['entry_time'],
                        'exit_time': current_time,
                        'instrument': position['instrument'],
                        'option_type': position['option_type'],
                        'strike': position['strike'],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'quantity': position['quantity'],
                        'pnl': pnl['net_pnl'],
                        'pnl_pct': pnl['pnl_pct'],
                        'reason': reason,
                        'hold_time': (current_time - position['entry_time']).total_seconds() / 60
                    }
                    self.trades.append(trade)
                    
                    # Print trade
                    emoji = "✅" if pnl['net_pnl'] > 0 else "❌"
                    print(f"   {emoji} {reason}: {position['instrument']} {position['option_type']} "
                          f"₹{position['entry_price']:.0f}→₹{exit_price:.0f} "
                          f"P&L: ₹{pnl['net_pnl']:+,.0f} ({pnl['pnl_pct']:+.2f}%) "
                          f"Hold: {trade['hold_time']:.0f}min")
                    
                    # Remove from open positions
                    open_positions.remove(position)
                    self.strategy.trade_count += 1
            
            # Generate entry signals (only if we have room for new positions)
            if len(open_positions) < config.MAX_OPEN_POSITIONS and i >= config.LOOKBACK_CANDLES:
                # Try both CE and PE
                for option_type in ["CE", "PE"]:
                    signal, reason = self.strategy.generate_signal(df_slice, option_type)
                    
                    if signal == "BUY":
                        # Get ATM strike
                        strike = data_gen.get_atm_strike(current_underlying)
                        
                        # Get option price
                        dte = 3  # Days to expiry (simplified)
                        option_price = data_gen.generate_option_price(
                            current_underlying, strike, option_type, dte
                        )
                        
                        # Calculate position size
                        quantity = self.strategy.calculate_position_size(option_price)
                        
                        # Check if we have enough capital
                        required_capital = option_price * quantity
                        if required_capital > self.capital * 0.5:  # Max 50% per position
                            continue
                        
                        # Calculate targets
                        targets = self.strategy.calculate_targets(option_price)
                        
                        # Open position
                        position = {
                            'entry_time': current_time,
                            'instrument': 'NIFTY',
                            'option_type': option_type,
                            'strike': strike,
                            'entry_price': option_price,
                            'quantity': quantity,
                            'underlying_entry': current_underlying,
                            **targets
                        }
                        
                        open_positions.append(position)
                        
                        print(f"   🔔 ENTRY: NIFTY {strike} {option_type} @ ₹{option_price:.0f} "
                              f"Qty: {quantity} Target: ₹{targets['target']:.0f} "
                              f"SL: ₹{targets['stop_loss']:.0f}")
                        
                        break  # Only one entry per candle
    
    def print_results(self):
        """Print backtest results"""
        print("\n" + "="*80)
        print("📊 BACKTEST RESULTS")
        print("="*80)
        
        if not self.trades:
            print("\n❌ No trades executed")
            return
        
        # Convert trades to DataFrame
        trades_df = pd.DataFrame(self.trades)
        
        # Calculate metrics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        total_pnl = trades_df['pnl'].sum()
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        profit_factor = abs(trades_df[trades_df['pnl'] > 0]['pnl'].sum() / 
                           trades_df[trades_df['pnl'] < 0]['pnl'].sum()) if losing_trades > 0 else 0
        
        final_capital = self.capital
        total_return = ((final_capital - self.initial_capital) / self.initial_capital) * 100
        
        # Max drawdown
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df['peak'] = equity_df['capital'].cummax()
        equity_df['drawdown'] = (equity_df['capital'] - equity_df['peak']) / equity_df['peak'] * 100
        max_drawdown = equity_df['drawdown'].min()
        
        # Print summary
        print(f"\n💰 CAPITAL:")
        print(f"   Initial: ₹{self.initial_capital:,}")
        print(f"   Final: ₹{final_capital:,}")
        print(f"   Total P&L: ₹{total_pnl:+,}")
        print(f"   Return: {total_return:+.2f}%")
        
        print(f"\n📈 TRADES:")
        print(f"   Total: {total_trades}")
        print(f"   Winners: {winning_trades} ({win_rate:.1f}%)")
        print(f"   Losers: {losing_trades} ({100-win_rate:.1f}%)")
        print(f"   Avg trades/day: {total_trades/self.days:.1f}")
        
        print(f"\n💵 P&L:")
        print(f"   Avg Win: ₹{avg_win:+,.0f}")
        print(f"   Avg Loss: ₹{avg_loss:+,.0f}")
        print(f"   Profit Factor: {profit_factor:.2f}")
        print(f"   Max Drawdown: {max_drawdown:.2f}%")
        
        # Avg hold time
        avg_hold = trades_df['hold_time'].mean()
        print(f"\n⏱️  TIMING:")
        print(f"   Avg Hold Time: {avg_hold:.1f} minutes")
        
        # Exit reasons breakdown
        print(f"\n📋 EXIT REASONS:")
        exit_reasons = trades_df['reason'].value_counts()
        for reason, count in exit_reasons.items():
            print(f"   {reason}: {count} ({count/total_trades*100:.1f}%)")
        
        # Recent trades
        print(f"\n📜 LAST 10 TRADES:")
        recent = trades_df.tail(10)[['date', 'instrument', 'option_type', 'entry_price', 'exit_price', 'pnl', 'reason']]
        print(tabulate(recent, headers='keys', tablefmt='simple', showindex=False, floatfmt='.0f'))
        
        # Performance grade
        print(f"\n🎯 PERFORMANCE GRADE:")
        grade = self.calculate_grade(win_rate, profit_factor, total_return, max_drawdown)
        print(f"   {grade}")
        
        print("\n" + "="*80)
        
        # Save results
        trades_df.to_csv('results/mock_backtest_trades.csv', index=False)
        equity_df.to_csv('results/mock_backtest_equity.csv', index=False)
        print(f"\n💾 Results saved to results/mock_backtest_trades.csv")
    
    def calculate_grade(self, win_rate, profit_factor, total_return, max_drawdown):
        """Calculate performance grade"""
        score = 0
        
        # Win rate (max 30 points)
        if win_rate >= 70:
            score += 30
        elif win_rate >= 60:
            score += 25
        elif win_rate >= 50:
            score += 20
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
        if total_return >= 20:
            score += 25
        elif total_return >= 10:
            score += 20
        elif total_return >= 5:
            score += 15
        else:
            score += 5
        
        # Max drawdown (max 15 points)
        if max_drawdown > -10:
            score += 15
        elif max_drawdown > -15:
            score += 10
        else:
            score += 5
        
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
    
    # Create results directory
    os.makedirs('results', exist_ok=True)
    
    # Run backtest
    backtester = MockBacktester(capital=50000, days=30)
    backtester.run()
