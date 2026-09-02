"""
Automated Strategy Optimization Loop
Continuously improves strategy until excellent performance is achieved
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import itertools
from tabulate import tabulate
import json
import time

# Import our strategy
from strategy import MomentumScalpingStrategy
from mock_backtest import MockBacktester, MockOptionsData

class StrategyOptimizer:
    """
    Automated optimization loop for NSE options strategies
    Keeps iterating until we achieve excellent performance
    """
    
    def __init__(self, target_metrics=None):
        self.target_metrics = target_metrics or {
            'win_rate': 65.0,           # Target 65%+ win rate
            'profit_factor': 2.0,       # Target 2.0+ profit factor
            'total_return': 50.0,       # Target 50%+ return
            'max_drawdown': -15.0,      # Max 15% drawdown
            'avg_trades_per_day': 2.0,  # At least 2 trades/day
        }
        
        self.best_params = None
        self.best_score = 0
        self.iteration = 0
        self.optimization_history = []
    
    def generate_parameter_combinations(self):
        """Generate all parameter combinations to test"""
        param_grid = {
            # Entry thresholds
            'rsi_oversold': [25, 30, 35],
            'rsi_overbought': [65, 70, 75],
            'volume_surge': [1.5, 2.0, 2.5],
            'min_price_move': [0.002, 0.003, 0.005],  # 0.2%, 0.3%, 0.5%
            
            # Exit thresholds
            'target_profit': [0.008, 0.010, 0.015],  # 0.8%, 1%, 1.5%
            'stop_loss': [0.004, 0.005, 0.007],      # 0.4%, 0.5%, 0.7%
            'max_hold_time': [20, 30, 45],           # minutes
            
            # Risk management
            'risk_per_trade': [0.03, 0.05, 0.07],    # 3%, 5%, 7%
            'max_positions': [1, 2, 3],
            
            # Filters
            'use_trailing_stop': [True, False],
            'trailing_stop_pct': [0.002, 0.003, 0.005],
        }
        
        # Generate all combinations
        keys = param_grid.keys()
        values = param_grid.values()
        combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
        
        print(f"\n🔍 Total parameter combinations: {len(combinations):,}")
        return combinations
    
    def test_parameters(self, params, days=30, capital=50000):
        """Test a specific parameter combination"""
        # Update config with these parameters
        import config
        config.RSI_OVERSOLD = params['rsi_oversold']
        config.RSI_OVERBOUGHT = params['rsi_overbought']
        config.VOLUME_SURGE_MULTIPLIER = params['volume_surge']
        config.MIN_PRICE_MOVE = params['min_price_move']
        config.TARGET_PROFIT_PCT = params['target_profit']
        config.STOP_LOSS_PCT = params['stop_loss']
        config.MAX_HOLD_TIME_MINUTES = params['max_hold_time']
        config.RISK_PER_TRADE = params['risk_per_trade']
        config.MAX_OPEN_POSITIONS = params['max_positions']
        config.USE_TRAILING_STOP = params['use_trailing_stop']
        config.TRAILING_STOP_PCT = params['trailing_stop_pct']
        
        # Run backtest
        backtester = MockBacktester(capital=capital, days=days)
        
        # Suppress output
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            backtester.run()
        except Exception as e:
            sys.stdout = old_stdout
            return None
        
        sys.stdout = old_stdout
        
        # Calculate metrics
        if not backtester.trades:
            return None
        
        trades_df = pd.DataFrame(backtester.trades)
        
        total_trades = len(trades_df)
        if total_trades == 0:
            return None
        
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        total_pnl = trades_df['pnl'].sum()
        total_return = (total_pnl / capital) * 100
        
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        profit_factor = abs(trades_df[trades_df['pnl'] > 0]['pnl'].sum() / 
                           trades_df[trades_df['pnl'] < 0]['pnl'].sum()) if losing_trades > 0 else 0
        
        # Max drawdown
        equity_df = pd.DataFrame(backtester.equity_curve)
        if len(equity_df) > 0:
            equity_df['peak'] = equity_df['capital'].cummax()
            equity_df['drawdown'] = (equity_df['capital'] - equity_df['peak']) / equity_df['peak'] * 100
            max_drawdown = equity_df['drawdown'].min()
        else:
            max_drawdown = 0
        
        avg_trades_per_day = total_trades / days
        
        metrics = {
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'avg_trades_per_day': avg_trades_per_day,
            'total_trades': total_trades,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_pnl': total_pnl,
        }
        
        return metrics
    
    def calculate_score(self, metrics):
        """Calculate overall score for a parameter set"""
        if metrics is None:
            return 0
        
        score = 0
        
        # Win rate (max 30 points)
        if metrics['win_rate'] >= 70:
            score += 30
        elif metrics['win_rate'] >= 65:
            score += 25
        elif metrics['win_rate'] >= 60:
            score += 20
        elif metrics['win_rate'] >= 55:
            score += 15
        elif metrics['win_rate'] >= 50:
            score += 10
        else:
            score += 5
        
        # Profit factor (max 30 points)
        if metrics['profit_factor'] >= 2.5:
            score += 30
        elif metrics['profit_factor'] >= 2.0:
            score += 25
        elif metrics['profit_factor'] >= 1.5:
            score += 20
        elif metrics['profit_factor'] >= 1.2:
            score += 15
        else:
            score += 5
        
        # Total return (max 25 points)
        if metrics['total_return'] >= 50:
            score += 25
        elif metrics['total_return'] >= 30:
            score += 20
        elif metrics['total_return'] >= 20:
            score += 15
        elif metrics['total_return'] >= 10:
            score += 10
        else:
            score += 5
        
        # Max drawdown (max 10 points)
        if metrics['max_drawdown'] > -10:
            score += 10
        elif metrics['max_drawdown'] > -15:
            score += 7
        elif metrics['max_drawdown'] > -20:
            score += 5
        else:
            score += 2
        
        # Trade frequency (max 5 points)
        if metrics['avg_trades_per_day'] >= 3:
            score += 5
        elif metrics['avg_trades_per_day'] >= 2:
            score += 4
        elif metrics['avg_trades_per_day'] >= 1:
            score += 3
        else:
            score += 1
        
        return score
    
    def meets_targets(self, metrics):
        """Check if metrics meet target criteria"""
        if metrics is None:
            return False
        
        return (
            metrics['win_rate'] >= self.target_metrics['win_rate'] and
            metrics['profit_factor'] >= self.target_metrics['profit_factor'] and
            metrics['total_return'] >= self.target_metrics['total_return'] and
            metrics['max_drawdown'] >= self.target_metrics['max_drawdown'] and
            metrics['avg_trades_per_day'] >= self.target_metrics['avg_trades_per_day']
        )
    
    def optimize(self, max_iterations=100, sample_size=50):
        """
        Run optimization loop until targets are met
        
        Args:
            max_iterations: Maximum optimization iterations
            sample_size: Number of parameter combinations to test per iteration
        """
        print("\n" + "="*80)
        print("🚀 AUTOMATED STRATEGY OPTIMIZATION LOOP")
        print("="*80)
        print(f"\n🎯 Target Metrics:")
        for key, value in self.target_metrics.items():
            print(f"   {key}: {value}")
        print("\n" + "="*80)
        
        # Generate all parameter combinations
        all_combinations = self.generate_parameter_combinations()
        
        start_time = time.time()
        
        for iteration in range(max_iterations):
            self.iteration = iteration + 1
            
            print(f"\n{'='*80}")
            print(f"📊 ITERATION {self.iteration}/{max_iterations}")
            print(f"{'='*80}")
            
            # Sample random combinations
            if len(all_combinations) > sample_size:
                test_combinations = np.random.choice(
                    range(len(all_combinations)), 
                    size=sample_size, 
                    replace=False
                )
                params_to_test = [all_combinations[i] for i in test_combinations]
            else:
                params_to_test = all_combinations
            
            print(f"\n🔬 Testing {len(params_to_test)} parameter combinations...")
            
            iteration_results = []
            
            for i, params in enumerate(params_to_test):
                if (i + 1) % 10 == 0:
                    print(f"   Progress: {i+1}/{len(params_to_test)} ({(i+1)/len(params_to_test)*100:.1f}%)")
                
                metrics = self.test_parameters(params)
                
                if metrics:
                    score = self.calculate_score(metrics)
                    
                    result = {
                        'iteration': self.iteration,
                        'params': params,
                        'metrics': metrics,
                        'score': score
                    }
                    
                    iteration_results.append(result)
                    
                    # Update best if better
                    if score > self.best_score:
                        self.best_score = score
                        self.best_params = params
                        self.best_metrics = metrics
            
            # Sort by score
            iteration_results.sort(key=lambda x: x['score'], reverse=True)
            
            # Print top 5 from this iteration
            print(f"\n🏆 TOP 5 RESULTS (Iteration {self.iteration}):")
            print("-"*80)
            
            for i, result in enumerate(iteration_results[:5], 1):
                m = result['metrics']
                print(f"\n{i}. Score: {result['score']}/100")
                print(f"   Win Rate: {m['win_rate']:.1f}% | PF: {m['profit_factor']:.2f} | "
                      f"Return: {m['total_return']:+.1f}% | DD: {m['max_drawdown']:.1f}%")
            
            # Save history
            self.optimization_history.extend(iteration_results)
            
            # Check if we met targets
            if iteration_results and self.meets_targets(iteration_results[0]['metrics']):
                print(f"\n{'='*80}")
                print("🎉 TARGET METRICS ACHIEVED!")
                print(f"{'='*80}")
                self.print_final_results()
                return True
            
            # Print current best
            print(f"\n📈 CURRENT BEST (Overall):")
            print(f"   Score: {self.best_score}/100")
            if hasattr(self, 'best_metrics'):
                m = self.best_metrics
                print(f"   Win Rate: {m['win_rate']:.1f}% | PF: {m['profit_factor']:.2f} | "
                      f"Return: {m['total_return']:+.1f}% | DD: {m['max_drawdown']:.1f}%")
            
            elapsed = time.time() - start_time
            print(f"\n⏱️  Elapsed: {elapsed/60:.1f} minutes")
        
        print(f"\n{'='*80}")
        print(f"⚠️  Max iterations reached without meeting all targets")
        print(f"{'='*80}")
        self.print_final_results()
        return False
    
    def print_final_results(self):
        """Print final optimization results"""
        print(f"\n{'='*80}")
        print("📊 FINAL OPTIMIZATION RESULTS")
        print(f"{'='*80}")
        
        if not hasattr(self, 'best_metrics'):
            print("\n❌ No valid results found")
            return
        
        m = self.best_metrics
        
        print(f"\n🏆 BEST PARAMETERS FOUND:")
        print("-"*80)
        for key, value in self.best_params.items():
            print(f"   {key}: {value}")
        
        print(f"\n📈 PERFORMANCE METRICS:")
        print("-"*80)
        print(f"   Win Rate:          {m['win_rate']:.2f}% {'✅' if m['win_rate'] >= self.target_metrics['win_rate'] else '❌'}")
        print(f"   Profit Factor:     {m['profit_factor']:.2f} {'✅' if m['profit_factor'] >= self.target_metrics['profit_factor'] else '❌'}")
        print(f"   Total Return:      {m['total_return']:+.2f}% {'✅' if m['total_return'] >= self.target_metrics['total_return'] else '❌'}")
        print(f"   Max Drawdown:      {m['max_drawdown']:.2f}% {'✅' if m['max_drawdown'] >= self.target_metrics['max_drawdown'] else '❌'}")
        print(f"   Trades/Day:        {m['avg_trades_per_day']:.2f} {'✅' if m['avg_trades_per_day'] >= self.target_metrics['avg_trades_per_day'] else '❌'}")
        print(f"   Total Trades:      {m['total_trades']}")
        print(f"   Avg Win:           ₹{m['avg_win']:+,.0f}")
        print(f"   Avg Loss:          ₹{m['avg_loss']:+,.0f}")
        print(f"   Total P&L:         ₹{m['total_pnl']:+,.0f}")
        
        print(f"\n🎯 OVERALL SCORE: {self.best_score}/100")
        
        if self.best_score >= 85:
            grade = "⭐⭐⭐⭐⭐ EXCELLENT - Ready for live trading!"
        elif self.best_score >= 70:
            grade = "⭐⭐⭐⭐ GOOD - Minor tweaks needed"
        elif self.best_score >= 55:
            grade = "⭐⭐⭐ AVERAGE - Needs improvement"
        else:
            grade = "⭐⭐ BELOW AVERAGE - Major changes needed"
        
        print(f"   {grade}")
        
        # Save results
        self.save_results()
    
    def save_results(self):
        """Save optimization results to file"""
        results = {
            'best_params': self.best_params,
            'best_metrics': self.best_metrics,
            'best_score': self.best_score,
            'target_metrics': self.target_metrics,
            'total_iterations': self.iteration,
            'timestamp': datetime.now().isoformat()
        }
        
        with open('results/optimization_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save history
        history_df = pd.DataFrame([
            {
                'iteration': r['iteration'],
                'score': r['score'],
                **r['metrics']
            }
            for r in self.optimization_history
        ])
        history_df.to_csv('results/optimization_history.csv', index=False)
        
        print(f"\n💾 Results saved:")
        print(f"   results/optimization_results.json")
        print(f"   results/optimization_history.csv")

if __name__ == "__main__":
    import os
    os.makedirs('results', exist_ok=True)
    
    # Set target metrics (AGGRESSIVE TARGETS)
    target_metrics = {
        'win_rate': 65.0,           # 65%+ win rate
        'profit_factor': 2.0,       # 2.0+ profit factor
        'total_return': 50.0,       # 50%+ return in 30 days
        'max_drawdown': -15.0,      # Max 15% drawdown
        'avg_trades_per_day': 2.0,  # At least 2 trades/day
    }
    
    # Create optimizer
    optimizer = StrategyOptimizer(target_metrics=target_metrics)
    
    # Run optimization loop
    # Will keep iterating until targets are met or max iterations reached
    success = optimizer.optimize(
        max_iterations=20,    # Max 20 iterations
        sample_size=30        # Test 30 combinations per iteration
    )
    
    if success:
        print(f"\n🎉 Optimization successful! Targets achieved!")
    else:
        print(f"\n⚠️  Optimization incomplete. Best result shown above.")
    
    print(f"\n{'='*80}")
    print("✅ Optimization complete!")
    print(f"{'='*80}\n")
