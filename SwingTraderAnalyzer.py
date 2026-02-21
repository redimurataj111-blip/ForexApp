"""
SWING TRADER SIGNAL ANALYZER
=============================
Generates comprehensive signal reports and trade summaries
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from SwingTraderCombined import (
    generate_combined_signals,
    aggregate_signals_over_period,
    backtest_swing_strategy,
    generate_signal_report,
    save_report_json
)


class SwingTraderSignalAnalyzer:
    """
    Main analyzer class for generating swing trading signals and reports
    """
    
    def __init__(self, eurusd_df: pd.DataFrame, dxy_df: pd.DataFrame):
        """
        Initialize the analyzer with price data
        
        Parameters:
        - eurusd_df: DataFrame with EURUSD OHLC data
        - dxy_df: DataFrame with DXY OHLC data
        """
        self.eurusd_df = eurusd_df.copy()
        self.dxy_df = dxy_df.copy()
        self.report = None
        self.backtest_result = None
    
    def run_analysis(self, output_file: str = "swing_trader_report.json",
                     lookback_days: int = 30,
                     max_concurrent_trades: int = 1) -> dict:
        """
        Run complete analysis including signal generation and backtesting
        
        Parameters:
        - output_file: Output JSON filename
        - lookback_days: Backtest period (30 for 1 month, 730 for 2 years)
        - max_concurrent_trades: Max concurrent LONG positions (1 = 1 trade at a time, 5 = aggressive)
        """
        print("=" * 70)
        print("SWING TRADING STRATEGY ANALYSIS")
        print("=" * 70)
        
        # Step 1: Generate backtest results
        print(f"\n[1/3] Running 2-Year Backtest ({lookback_days} days, {max_concurrent_trades} concurrent LONG)...")
        self.backtest_result = backtest_swing_strategy(
            self.eurusd_df,
            self.dxy_df,
            min_pips=30,
            max_pips=60,
            lookback_days=lookback_days,
            max_concurrent_trades=max_concurrent_trades
        )
        print(f"      ✓ Backtest Complete: {self.backtest_result.get('total_trades', 0)} trades analyzed")
        print(f"        Period: {lookback_days} days | Max Concurrent Positions: {max_concurrent_trades}")
        
        # Step 2: Generate signal report
        print("\n[2/3] Generating Signal Report...")
        self.report = generate_signal_report(self.eurusd_df, self.dxy_df, self.backtest_result)
        print("      ✓ Signal Report Generated")
        
        # Step 3: Save report
        print("\n[3/3] Saving Report to File...")
        save_report_json(self.report, filename=output_file)
        print(f"      ✓ Report Saved: {output_file}")
        
        return self.report
    
    def print_signal_summary(self):
        """
        Print a human-readable signal summary to console
        """
        if not self.report:
            print("No report generated. Run run_analysis() first.")
            return
        
        print("\n" + "=" * 70)
        print("CURRENT SIGNAL STATUS")
        print("=" * 70)
        
        signals = self.report["current_signals"]
        print(f"\n📊 Combined Strategy Signal: {signals['combined_signal']}")
        print(f"   Confidence: {signals['confidence']:.1f}%")
        print(f"   Confluence: {'✓ YES' if signals['confluence'] else '✗ NO'}")
        
        print(f"\n🔵 Strategy 1 - DXY Trend Bias:")
        print(f"   Bias: {signals['dxy_bias']}")
        print(f"   Strength: {signals['dxy_strength']:.1f}%")
        adx_val = f"{signals['dxy_adx']:.2f}" if signals['dxy_adx'] else 'N/A'
        print(f"   ADX: {adx_val}")
        dxy_price = f"{signals['current_dxy_price']:.4f}" if signals['current_dxy_price'] else 'N/A'
        print(f"   DXY Price: {dxy_price}")
        
        print(f"\n🟢 Strategy 2 - Price Action:")
        print(f"   Signal: {signals['price_action']}")
        print(f"   Confidence: {signals['price_action_confidence']:.1f}%")
        print(f"   Type: {signals['entry_type'] if signals['entry_type'] else 'N/A'}")
        eurusd_price = f"{signals['current_eurusd_price']:.5f}" if signals['current_eurusd_price'] else 'N/A'
        print(f"   EUR/USD Price: {eurusd_price}")
        
        print("\n" + "=" * 70)
        print("30-DAY SIGNAL SUMMARY (Bullish/Bearish/Neutral Count)")
        print("=" * 70)
        
        summary = self.report["signal_summary"]
        print(f"\nTotal Signals Analyzed: {summary['total_signals']}")
        print(f"\n🟢 BULLISH SIGNALS:  {summary['bullish_signals']:3d}  ({summary['bullish_pct']:5.1f}%)")
        print(f"🔴 BEARISH SIGNALS:  {summary['bearish_signals']:3d}  ({summary['bearish_pct']:5.1f}%)")
        print(f"⚪ NEUTRAL SIGNALS:   {summary['neutral_signals']:3d}  ({summary['neutral_pct']:5.1f}%)")
        
        print(f"\n📈 LONG Ready Status: {'✓ YES - Setup Ready' if summary['long_ready'] else '✗ NO - Waiting'}")
        
        if summary['latest_signal']:
            latest = summary['latest_signal']
            print(f"\nLatest Signal:")
            print(f"   Time: {latest['timestamp']}")
            print(f"   Signal: {latest['signal']}")
            print(f"   Confidence: {latest['confidence']:.1f}%")
            print(f"   DXY Bias: {latest['dxy_bias']}")
            print(f"   Price Action: {latest['price_action']}")
        
        print("\n" + "=" * 70)
        print("BACKTEST RESULTS (30-60 Pips Target, LONG ONLY)")
        print("=" * 70)
        
        bt = self.report["backtest"]
        if bt.get("error"):
            print(f"\n⚠️  Error: {bt['error']}")
        else:
            print(f"\nTotal Trades: {bt['total_trades']}")
            print(f"Wins: {bt['wins']}")
            print(f"Losses: {bt['losses']}")
            print(f"Win Rate: {bt['win_rate']:.1f}%")
            print(f"\nAvg Winner: {bt['avg_win_pips']:.1f} pips")
            print(f"Avg Loser: {bt['avg_loss_pips']:.1f} pips")
            print(f"\nProfit Factor: {bt['profit_factor']:.2f}")
            print(f"Total P&L: {bt['total_pnl_pips']:.0f} pips")
            print(f"Max Drawdown: {bt['max_drawdown']:.1f}%")
            print(f"Final Equity: ${bt['final_equity']:.2f}")
        
        print("\n" + "=" * 70)
    
    def print_trade_history(self, limit: int = 10):
        """
        Print recent trades from backtest
        """
        if not self.backtest_result or "trades" not in self.backtest_result:
            print("No trade history available")
            return
        
        trades = self.backtest_result["trades"]
        print("\n" + "=" * 70)
        print(f"RECENT TRADES (Last {limit})")
        print("=" * 70)
        
        for i, trade in enumerate(trades[-limit:], 1):
            entry_dt = trade.get("entry_date", "N/A")
            exit_dt = trade.get("exit_date", "N/A")
            entry_p = trade.get("entry_price", 0)
            exit_p = trade.get("exit_price", 0)
            pnl = trade.get("pnl_pips", 0)
            status = trade.get("status", "N/A")
            days = trade.get("days_held", 0)
            
            pnl_color = "🟢" if pnl > 0 else "🔴"
            
            print(f"\nTrade #{i}")
            print(f"  Entry: {entry_p:.5f} @ {entry_dt}")
            print(f"  Exit:  {exit_p:.5f} @ {exit_dt}")
            print(f"  P&L: {pnl_color} {pnl:+.1f} pips")
            print(f"  Status: {status} | Days Held: {days}")
    
    def export_signals_csv(self, filename: str = "swing_signals.csv"):
        """
        Export signals to CSV for analysis
        """
        if not self.report or "signal_summary" not in self.report:
            print("No report available to export")
            return
        
        signals_list = self.report["signal_summary"].get("signals", [])
        if not signals_list:
            print("No signals to export")
            return
        
        # Create DataFrame
        df = pd.DataFrame(signals_list)
        df.to_csv(filename, index=False)
        print(f"✓ Signals exported to {filename}")
    
    def export_trades_csv(self, filename: str = "swing_trades.csv"):
        """
        Export trades to CSV for analysis
        """
        if not self.backtest_result or "trades" not in self.backtest_result:
            print("No trades available to export")
            return
        
        trades = self.backtest_result["trades"]
        df = pd.DataFrame(trades)
        df.to_csv(filename, index=False)
        print(f"✓ Trades exported to {filename}")


# ═══════════════════════════════════════════════════════════════════════════
# STANDALONE FUNCTIONS FOR QUICK ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def quick_signal_check(eurusd_df: pd.DataFrame, dxy_df: pd.DataFrame) -> dict:
    """
    Quick signal check - returns current combined signal
    """
    return generate_combined_signals(eurusd_df, dxy_df)


def quick_backtest(eurusd_df: pd.DataFrame, dxy_df: pd.DataFrame) -> dict:
    """
    Quick backtest with default 30-60 pip target
    """
    return backtest_swing_strategy(eurusd_df, dxy_df, min_pips=30, max_pips=60, lookback_days=30)


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("SwingTraderSignalAnalyzer module loaded successfully")
    print("\nUsage Example:")
    print("  from SwingTraderAnalyzer import SwingTraderSignalAnalyzer")
    print("  analyzer = SwingTraderSignalAnalyzer(eurusd_df, dxy_df)")
    print("  report = analyzer.run_analysis()")
    print("  analyzer.print_signal_summary()")
    print("  analyzer.print_trade_history()")
