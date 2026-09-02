"""
OPTIMIZED Calendar Spread Backtest - 5 Years
Better exit rules: Exit when profitable OR at breakeven
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from tabulate import tabulate
import warnings
warnings.filterwarnings('ignore')

class OptimizedCalendarBacktest:
    """
    OPTIMIZED Calendar Spread Strategy
    
    Key Improvements:
    1. Exit when profitable (any profit > 0)
    2. Exit at breakeven if moving against us
    3. Tighter stop loss (30% instead of 50%)
    4. Don't hold to expiry (exit early)
    5. Take profits quickly (don't be greedy)
    
    New Exit Rules:
    - Exit if profit > 10% (quick profit)
    - Exit if profit > 5% after 3 days (don't wait)
    - Exit at breakeven if losing (preserve capital)
    - Exit if loss > 30% (tight stop)
    - Exit if VIX spikes
    - Max hold: 5 days (not 7)
    """
    
    def __init__(self, capital=50000, risk_per_trade=0.15):
        self.initial_capital = capital
        self.capital = capital
        self.risk_per_trade = risk_per_trade
        self.trades = []
        self.equity_curve = []
        
    def calculate_vix_proxy(self, df):
        """Calculate VIX proxy from price volatility"""
        returns = df['Close'].pct_change()
        volatility = returns.rolling(20).std() * np.sqrt(252) * 100
        return volatility
    
    def is_range_bound(self, df, idx):
        """Check if market is range-bound"""
        if idx < 20:
            return False
        
        recent = df.iloc[idx-20:idx]
        sma20 = recent['Close'].mean()
        current_price = df.iloc[idx]['Close']
        deviation = abs(current_price - sma20) / sma20
        
        return deviation < 0.03
    
    def calculate_option_premium(self, spot, strike, days_to_expiry, volatility):
        """Simplified option premium calculation"""
        moneyness = abs(spot - strike) / spot
        time_factor = np.sqrt(days_to_expiry / 365.0)
        vol_factor = volatility / 100.0
        
        if moneyness < 0.01:  # ATM
            premium = spot * vol_factor * time_factor * 0.4
        elif spot > strike:  # ITM
            intrinsic = spot - strike
            time_value = spot * vol_factor * time_factor * 0.3
            premium = intrinsic + time_value
        else:  # OTM
            premium = spot * vol_factor * time_factor * 0.2
        
        return max(premium, 1.0)
    
    def simulate_optimized_calendar(self, index_name, df, entry_idx):
        """Simulate one OPTIMIZED calendar spread trade"""
        
        entry_date = df.index[entry_idx]
        entry_spot = float(df.iloc[entry_idx]['Close'])
        entry_vix = float(df.iloc[entry_idx]['VIX_Proxy'])
        
        # ATM strike
        if 'NIFTY' in index_name and 'BANK' not in index_name:
            strike_round = 50
        else:
            strike_round = 100
        
        strike = round(entry_spot / strike_round) * strike_round
        
        # Calculate premiums
        weekly_premium = self.calculate_option_premium(entry_spot, strike, 7, entry_vix)
        monthly_premium = self.calculate_option_premium(entry_spot, strike, 30, entry_vix)
        
        net_debit = monthly_premium - weekly_premium
        
        # Position size
        risk_amount = self.capital * self.risk_per_trade
        
        if 'BANK' in index_name:
            lot_size = 15
        elif 'SENSEX' in index_name:
            lot_size = 10
        else:
            lot_size = 50
        
        lots = max(1, int(risk_amount / (net_debit * lot_size)))
        lots = min(lots, 3)
        
        total_cost = net_debit * lot_size * lots
        
        # Get future data (max 5 days, not 7)
        future_data = df.iloc[entry_idx+1:entry_idx+6]
        
        if len(future_data) < 3:
            return None
        
        # Track the trade with OPTIMIZED exits
        for i, (date, row) in enumerate(future_data.iterrows()):
            days_held = i + 1
            current_spot = float(row['Close'])
            current_vix = float(row['VIX_Proxy'])
            
            # Days remaining
            weekly_dte = max(0, 7 - days_held)
            monthly_dte = max(0, 30 - days_held)
            
            # Current premiums
            current_weekly = self.calculate_option_premium(current_spot, strike, weekly_dte, current_vix)
            current_monthly = self.calculate_option_premium(current_spot, strike, monthly_dte, current_vix)
            
            # Current spread value
            current_spread_value = current_monthly - current_weekly
            
            # P&L
            pnl = (current_spread_value - net_debit) * lot_size * lots
            pnl_pct = ((current_spread_value - net_debit) / net_debit) * 100
            
            # OPTIMIZED EXIT CONDITIONS
            
            # 1. Quick profit: Exit if profit > 10% (take it and run!)
            if pnl_pct >= 10:
                self.capital += pnl
                
                return {
                    'index': index_name,
                    'entry_date': entry_date,
                    'exit_date': date,
                    'strike': strike,
                    'entry_spot': entry_spot,
                    'exit_spot': current_spot,
                    'entry_vix': entry_vix,
                    'exit_vix': current_vix,
                    'net_debit': net_debit,
                    'lots': lots,
                    'total_cost': total_cost,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'exit_reason': 'QUICK_PROFIT',
                    'days_held': days_held,
                    'capital_after': self.capital
                }
            
            # 2. Delayed profit: Exit if profit > 5% after 3 days (don't wait too long)
            if days_held >= 3 and pnl_pct >= 5:
                self.capital += pnl
                
                return {
                    'index': index_name,
                    'entry_date': entry_date,
                    'exit_date': date,
                    'strike': strike,
                    'entry_spot': entry_spot,
                    'exit_spot': current_spot,
                    'entry_vix': entry_vix,
                    'exit_vix': current_vix,
                    'net_debit': net_debit,
                    'lots': lots,
                    'total_cost': total_cost,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'exit_reason': 'DELAYED_PROFIT',
                    'days_held': days_held,
                    'capital_after': self.capital
                }
            
            # 3. Breakeven exit: Exit at breakeven if losing (preserve capital)
            if days_held >= 2 and pnl_pct < 0 and pnl_pct > -5:
                # If we're slightly negative, exit at breakeven
                # Better to preserve capital than hope for recovery
                self.capital += pnl
                
                return {
                    'index': index_name,
                    'entry_date': entry_date,
                    'exit_date': date,
                    'strike': strike,
                    'entry_spot': entry_spot,
                    'exit_spot': current_spot,
                    'entry_vix': entry_vix,
                    'exit_vix': current_vix,
                    'net_debit': net_debit,
                    'lots': lots,
                    'total_cost': total_cost,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'exit_reason': 'BREAKEVEN',
                    'days_held': days_held,
                    'capital_after': self.capital
                }
            
            # 4. Tight stop loss: 30% (not 50%)
            if pnl_pct <= -30:
                self.capital += pnl
                
                return {
                    'index': index_name,
                    'entry_date': entry_date,
                    'exit_date': date,
                    'strike': strike,
                    'entry_spot': entry_spot,
                    'exit_spot': current_spot,
                    'entry_vix': entry_vix,
                    'exit_vix': current_vix,
                    'net_debit': net_debit,
                    'lots': lots,
                    'total_cost': total_cost,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'exit_reason': 'STOP_LOSS',
                    'days_held': days_held,
                    'capital_after': self.capital
                }
            
            # 5. VIX spike: Exit if VIX jumps 40%+
            if current_vix > entry_vix * 1.4:
                self.capital += pnl
                
                return {
                    'index': index_name,
                    'entry_date': entry_date,
                    'exit_date': date,
                    'strike': strike,
                    'entry_spot': entry_spot,
                    'exit_spot': current_spot,
                    'entry_vix': entry_vix,
                    'exit_vix': current_vix,
                    'net_debit': net_debit,
                    'lots': lots,
                    'total_cost': total_cost,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'exit_reason': 'VIX_SPIKE',
                    'days_held': days_held,
                    'capital_after': self.capital
                }
            
            # 6. Time stop: Max 5 days (exit early, don't hold to expiry)
            if days_held >= 5:
                self.capital += pnl
                
                return {
                    'index': index_name,
                    'entry_date': entry_date,
                    'exit_date': date,
                    'strike': strike,
                    'entry_spot': entry_spot,
                    'exit_spot': current_spot,
                    'entry_vix': entry_vix,
                    'exit_vix': current_vix,
                    'net_debit': net_debit,
                    'lots': lots,
                    'total_cost': total_cost,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'exit_reason': 'TIME_STOP',
                    'days_held': days_held,
                    'capital_after': self.capital
                }
        
        return None
    
    def run_backtest(self, start_date, end_date):
        """Run optimized 5-year backtest"""
        print("\n" + "="*80)
        print("⚡ OPTIMIZED CALENDAR SPREAD BACKTEST (5 YEARS)")
        print("="*80)
        print(f"\n📊 Configuration:")
        print(f"   Capital: ₹{self.initial_capital:,}")
        print(f"   Risk per trade: {self.risk_per_trade*100:.1f}%")
        print(f"   Period: {start_date} to {end_date}")
        print(f"\n🎯 OPTIMIZED EXIT RULES:")
        print(f"   ✅ Exit if profit > 10% (quick profit)")
        print(f"   ✅ Exit if profit > 5% after 3 days")
        print(f"   ✅ Exit at breakeven if slightly negative")
        print(f"   ✅ Stop loss: 30% (tighter)")
        print(f"   ✅ Max hold: 5 days (not 7)")
        print("\n" + "="*80)
        
        # Download data
        print("\n📥 Downloading 5 years of data...")
        
        nifty = yf.download('^NSEI', start=start_date, end=end_date, progress=False)
        banknifty = yf.download('^NSEBANK', start=start_date, end=end_date, progress=False)
        sensex = yf.download('^BSESN', start=start_date, end=end_date, progress=False)
        
        # Handle multi-index
        for df in [nifty, banknifty, sensex]:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
        
        print(f"   ✅ Nifty: {len(nifty)} days")
        print(f"   ✅ Bank Nifty: {len(banknifty)} days")
        print(f"   ✅ Sensex: {len(sensex)} days")
        
        # Calculate VIX proxy
        print("\n📊 Calculating volatility...")
        nifty['VIX_Proxy'] = self.calculate_vix_proxy(nifty)
        banknifty['VIX_Proxy'] = self.calculate_vix_proxy(banknifty)
        sensex['VIX_Proxy'] = self.calculate_vix_proxy(sensex)
        
        nifty = nifty.dropna()
        banknifty = banknifty.dropna()
        sensex = sensex.dropna()
        
        # Scan for opportunities
        print("\n🔍 Scanning for opportunities...")
        
        opportunities = []
        
        for idx_name, df in [('NIFTY', nifty), ('BANKNIFTY', banknifty), ('SENSEX', sensex)]:
            for i in range(20, len(df), 7):
                row = df.iloc[i]
                vix_proxy = row['VIX_Proxy']
                
                if vix_proxy > 15:
                    continue
                
                if not self.is_range_bound(df, i):
                    continue
                
                if df.index[i].dayofweek > 2:
                    continue
                
                opportunities.append({
                    'index': idx_name,
                    'df': df,
                    'idx': i,
                    'date': df.index[i],
                    'vix': vix_proxy
                })
        
        print(f"   ✅ Found {len(opportunities)} opportunities")
        
        # Execute trades
        print("\n💹 Executing optimized calendar spreads...")
        
        for i, opp in enumerate(opportunities):
            if (i + 1) % 50 == 0:
                print(f"   Progress: {i+1}/{len(opportunities)} ({(i+1)/len(opportunities)*100:.1f}%)")
            
            trade = self.simulate_optimized_calendar(opp['index'], opp['df'], opp['idx'])
            
            if trade:
                self.trades.append(trade)
                self.equity_curve.append({
                    'date': trade['exit_date'],
                    'capital': self.capital,
                    'trade_pnl': trade['pnl']
                })
        
        print(f"\n   ✅ Executed {len(self.trades)} trades")
        
        # Print results
        print("\n" + "="*80)
        self.print_results()
    
    def print_results(self):
        """Print comprehensive results"""
        print("📊 OPTIMIZED BACKTEST RESULTS")
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
        
        years = (trades_df['exit_date'].max() - trades_df['entry_date'].min()).days / 365.25
        cagr = ((self.capital / self.initial_capital) ** (1 / years) - 1) * 100
        
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        avg_win_pct = trades_df[trades_df['pnl'] > 0]['pnl_pct'].mean() if winning_trades > 0 else 0
        avg_loss_pct = trades_df[trades_df['pnl'] < 0]['pnl_pct'].mean() if losing_trades > 0 else 0
        
        profit_factor = abs(trades_df[trades_df['pnl'] > 0]['pnl'].sum() / 
                           trades_df[trades_df['pnl'] < 0]['pnl'].sum()) if losing_trades > 0 else 0
        
        expectancy = (win_rate/100 * avg_win) + ((100-win_rate)/100 * avg_loss)
        
        # Max drawdown
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df['peak'] = equity_df['capital'].cummax()
        equity_df['drawdown'] = equity_df['capital'] - equity_df['peak']
        equity_df['drawdown_pct'] = (equity_df['drawdown'] / equity_df['peak']) * 100
        max_drawdown = equity_df['drawdown'].min()
        max_drawdown_pct = equity_df['drawdown_pct'].min()
        
        trades_per_year = total_trades / years
        
        # Print summary
        print(f"\n💰 CAPITAL:")
        print(f"   Initial: ₹{self.initial_capital:,}")
        print(f"   Final: ₹{self.capital:,.0f}")
        print(f"   Total P&L: ₹{total_pnl:+,.0f}")
        print(f"   Total Return: {total_return:+.2f}%")
        print(f"   CAGR: {cagr:.2f}%")
        
        print(f"\n📈 TRADES:")
        print(f"   Total: {total_trades} ({trades_per_year:.1f} per year)")
        print(f"   Winners: {winning_trades} ({win_rate:.1f}%)")
        print(f"   Losers: {losing_trades} ({100-win_rate:.1f}%)")
        
        print(f"\n💵 P&L:")
        print(f"   Avg Win: ₹{avg_win:+,.0f} ({avg_win_pct:+.1f}%)")
        print(f"   Avg Loss: ₹{avg_loss:+,.0f} ({avg_loss_pct:+.1f}%)")
        print(f"   Expectancy: ₹{expectancy:+,.0f}")
        print(f"   Profit Factor: {profit_factor:.2f}")
        print(f"   Max Drawdown: ₹{max_drawdown:,.0f} ({max_drawdown_pct:.2f}%)")
        
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
                idx_avg = idx_trades['pnl'].mean()
                print(f"   {index}: {len(idx_trades)} trades, {idx_wr:.1f}% WR, ₹{idx_pnl:+,.0f} total, ₹{idx_avg:+,.0f} avg")
        
        # By exit reason
        print(f"\n📋 EXIT REASONS:")
        exit_reasons = trades_df['exit_reason'].value_counts()
        for reason, count in exit_reasons.items():
            reason_trades = trades_df[trades_df['exit_reason'] == reason]
            reason_pnl = reason_trades['pnl'].sum()
            reason_avg = reason_trades['pnl'].mean()
            reason_wins = len(reason_trades[reason_trades['pnl'] > 0])
            reason_wr = (reason_wins / len(reason_trades)) * 100
            print(f"   {reason}: {count} ({count/total_trades*100:.1f}%), {reason_wr:.1f}% WR, ₹{reason_pnl:+,.0f} total, ₹{reason_avg:+,.0f} avg")
        
        # Yearly breakdown
        print(f"\n📅 YEARLY BREAKDOWN:")
        trades_df['year'] = pd.to_datetime(trades_df['exit_date']).dt.year
        
        for year in sorted(trades_df['year'].unique()):
            year_trades = trades_df[trades_df['year'] == year]
            year_count = len(year_trades)
            year_wins = len(year_trades[year_trades['pnl'] > 0])
            year_wr = (year_wins / year_count) * 100
            year_pnl = year_trades['pnl'].sum()
            year_return = (year_pnl / self.initial_capital) * 100
            print(f"   {year}: {year_count} trades, {year_wr:.1f}% WR, ₹{year_pnl:+,.0f} ({year_return:+.1f}%)")
        
        # Comparison
        print(f"\n📊 COMPARISON TO ORIGINAL:")
        print(f"   Original CAGR: 1.93%")
        print(f"   Optimized CAGR: {cagr:.2f}%")
        print(f"   Improvement: {cagr - 1.93:.2f}% ({((cagr/1.93)-1)*100:+.1f}%)")
        
        print(f"\n📊 BENCHMARK COMPARISON:")
        print(f"   Optimized Calendar: {cagr:.2f}%")
        print(f"   Bank FD (7%): 7.00%")
        print(f"   Nifty 50 (12%): 12.00%")
        print(f"   scanner-v3 (60-120%): 60-120%")
        print(f"   Options Selling (50-60%): 50-60%")
        
        if cagr > 60:
            print(f"   ✅ BEATS scanner-v3!")
        elif cagr > 12:
            print(f"   ✅ BEATS Nifty Index")
        elif cagr > 7:
            print(f"   ✅ BEATS Bank FD")
        else:
            print(f"   ❌ Still underperforms FD")
        
        # Performance grade
        print(f"\n🎯 PERFORMANCE GRADE:")
        grade = self.calculate_grade(win_rate, profit_factor, cagr, max_drawdown_pct)
        print(f"   {grade}")
        
        # Save results
        trades_df.to_csv('results/calendar_optimized_backtest.csv', index=False)
        equity_df.to_csv('results/calendar_optimized_equity.csv', index=False)
        
        print(f"\n💾 Results saved:")
        print(f"   - results/calendar_optimized_backtest.csv")
        print(f"   - results/calendar_optimized_equity.csv")
        print("="*80 + "\n")
    
    def calculate_grade(self, win_rate, profit_factor, cagr, max_dd):
        """Calculate performance grade"""
        score = 0
        
        if win_rate >= 70:
            score += 25
        elif win_rate >= 65:
            score += 22
        elif win_rate >= 60:
            score += 18
        elif win_rate >= 55:
            score += 15
        else:
            score += 10
        
        if profit_factor >= 2.5:
            score += 25
        elif profit_factor >= 2.0:
            score += 22
        elif profit_factor >= 1.5:
            score += 18
        elif profit_factor >= 1.2:
            score += 15
        else:
            score += 10
        
        if cagr >= 80:
            score += 30
        elif cagr >= 60:
            score += 25
        elif cagr >= 40:
            score += 20
        elif cagr >= 20:
            score += 15
        else:
            score += 10
        
        if max_dd > -10:
            score += 20
        elif max_dd > -20:
            score += 15
        elif max_dd > -30:
            score += 10
        else:
            score += 5
        
        if score >= 90:
            return f"⭐⭐⭐⭐⭐ EXCEPTIONAL ({score}/100)"
        elif score >= 80:
            return f"⭐⭐⭐⭐⭐ EXCELLENT ({score}/100)"
        elif score >= 70:
            return f"⭐⭐⭐⭐ GOOD ({score}/100)"
        elif score >= 60:
            return f"⭐⭐⭐ AVERAGE ({score}/100)"
        else:
            return f"⭐⭐ BELOW AVERAGE ({score}/100)"

if __name__ == "__main__":
    import os
    os.makedirs('results', exist_ok=True)
    
    backtester = OptimizedCalendarBacktest(capital=50000, risk_per_trade=0.15)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5*365)
    
    print(f"\n🚀 Starting OPTIMIZED 5-year backtest...")
    print(f"   Testing improved exit rules...")
    print(f"   This may take 5-10 minutes...\n")
    
    backtester.run_backtest(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
