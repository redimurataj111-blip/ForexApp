"""
SWING TRADER RUNNER - Complete Demonstration
==============================================
This script demonstrates how to use the combined swing trading strategy.

Usage:
  python run_swing_trader.py
"""

import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timedelta

# Import strategy modules
from SwingTraderCombined import (
    backtest_swing_strategy,
    generate_combined_signals,
    aggregate_signals_over_period
)
from SwingTraderAnalyzer import SwingTraderSignalAnalyzer


def load_sample_data():
    """
    Load sample EURUSD and DXY data from backtest JSON files if available
    Otherwise, create synthetic data
    """
    print("Loading price data...")
    
    eurusd_data = None
    dxy_data = None
    
    # Try to load from CSV files if they exist
    try:
        if os.path.exists("eurusd_data.csv"):
            eurusd_data = pd.read_csv("eurusd_data.csv", parse_dates=['dt'])
            print("  ✓ Loaded EURUSD data from CSV")
    except:
        pass
    
    try:
        if os.path.exists("dxy_data.csv"):
            dxy_data = pd.read_csv("dxy_data.csv", parse_dates=['dt'])
            print("  ✓ Loaded DXY data from CSV")
    except:
        pass
    
    # Try to load from backtest JSON files
    if eurusd_data is None:
        try:
            import json
            with open("last_backtest_clean.json", "r") as f:
                bt_data = json.load(f)
                if "eurusd_quotes" in bt_data:
                    quotes = bt_data["eurusd_quotes"]
                    eurusd_data = pd.DataFrame(quotes)
                    eurusd_data['dt'] = pd.to_datetime(eurusd_data['dt'])
                    print("  ✓ Loaded EURUSD data from backtest file")
        except:
            pass
    
    # If still no data, create synthetic data
    if eurusd_data is None:
        print("  ⚠️  Creating synthetic EURUSD data (2 YEARS, 4H candles)...")
        # 2 years = ~730 days * 6 candles per day (4H) = ~4380 candles
        dates = pd.date_range(end=datetime.utcnow(), periods=4380, freq='4h')
        
        # Generate realistic EURUSD price movement
        np.random.seed(42)
        base_price = 1.0850
        returns = np.random.normal(0.0002, 0.005, len(dates))
        prices = base_price * np.exp(np.cumsum(returns))
        
        eurusd_data = pd.DataFrame({
            'dt': dates,
            'Open': prices * (1 + np.random.normal(0, 0.0001, len(prices))),
            'High': prices * (1 + np.abs(np.random.normal(0, 0.0005, len(prices)))),
            'Low': prices * (1 - np.abs(np.random.normal(0, 0.0005, len(prices)))),
            'Close': prices,
            'Volume': np.random.randint(1000, 5000, len(prices))
        })
    
    if dxy_data is None:
        print("  ⚠️  Creating synthetic DXY data (2 YEARS, 4H candles)...")
        dates = pd.date_range(end=datetime.utcnow(), periods=4380, freq='4h')
        
        # Generate DXY movement inversely correlated with EURUSD
        np.random.seed(42)
        base_dxy = 103.50
        returns = np.random.normal(-0.0001, 0.003, len(dates))
        dxy_prices = base_dxy * np.exp(np.cumsum(returns))
        
        dxy_data = pd.DataFrame({
            'dt': dates,
            'Open': dxy_prices * (1 + np.random.normal(0, 0.00005, len(dxy_prices))),
            'High': dxy_prices * (1 + np.abs(np.random.normal(0, 0.0003, len(dxy_prices)))),
            'Low': dxy_prices * (1 - np.abs(np.random.normal(0, 0.0003, len(dxy_prices)))),
            'Close': dxy_prices,
            'Volume': np.random.randint(1000, 3000, len(dxy_prices))
        })
    
    print(f"\nData Summary:")
    print(f"  EURUSD: {len(eurusd_data)} bars, {eurusd_data['dt'].min()} to {eurusd_data['dt'].max()}")
    print(f"  DXY: {len(dxy_data)} bars, {dxy_data['dt'].min()} to {dxy_data['dt'].max()}")
    
    return eurusd_data, dxy_data


def main():
    """
    Main execution function
    """
    print("\n" + "=" * 70)
    print("SWING TRADING STRATEGY - COMPLETE ANALYSIS (2-YEAR BACKTEST)")
    print("=" * 70)
    print(f"Started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # ─ LOAD DATA ─
    eurusd_df, dxy_df = load_sample_data()
    
    # ─ RUN ANALYSIS ─
    print("\n" + "=" * 70)
    print("INITIALIZING ANALYSIS ENGINE (2-YEAR AGGRESSIVE LONG TRADING)")
    print("=" * 70)
    
    analyzer = SwingTraderSignalAnalyzer(eurusd_df, dxy_df)
    
    # Run with 2-year lookback (730 days) and allow up to 5 concurrent LONG positions
    print("\n[Backtest Configuration]")
    print("  • Period: 2 YEARS (730 days)")
    print("  • Direction: LONG ONLY")
    print("  • Max Concurrent Positions: 5 (aggressive)")
    print("  • Targets: 30-60 pips per trade")
    print("  • Entry Rule: Confluence of DXY + Price Action")
    
    report = analyzer.run_analysis(
        output_file="swing_trader_report_2year.json",
        lookback_days=730,  # 2 years
        max_concurrent_trades=5  # Allow up to 5 concurrent LONG positions
    )
    
    # ─ PRINT RESULTS ─
    analyzer.print_signal_summary()
    
    # ─ SHOW TRADES ─
    analyzer.print_trade_history(limit=20)
    
    # ─ EXPORT FILES ─
    print("\n" + "=" * 70)
    print("EXPORTING DATA")
    print("=" * 70)
    print()
    analyzer.export_signals_csv("swing_signals_2year.csv")
    analyzer.export_trades_csv("swing_trades_2year.csv")
    
    # ─ FINAL SUMMARY ─
    print("\n" + "=" * 70)
    print("STRATEGY SETUP COMPLETE (2-YEAR AGGRESSIVE LONG TRADING)")
    print("=" * 70)
    print("""
Strategy Details:
  ✓ Strategy 1: DXY Trend Analysis (Market Bias)
  ✓ Strategy 2: Price Action + Rejection Candles (Entry Signals)
  ✓ Combined: Confluent signals for LONG entries only
  ✓ Target: 30-60 pips per trade
  ✓ Frequency: As many LONG trades as signals appear (up to 5 concurrent)
  ✓ Backtest Period: 2 YEARS (730 days)
  ✓ Trading Mode: AGGRESSIVE (maximize LONG positions)

Output Files Generated:
  • swing_trader_report_2year.json - Complete signal and backtest report
  • swing_signals_2year.csv - All signals generated (2-year analysis)
  • swing_trades_2year.csv - All trades from 2-year backtest

2-Year Backtest Results:
  • Period: 730 days (2 full years)
  • Max Concurrent LONG Positions: 5
  • Entry Rule: DXY downtrend + Bullish price action
  • Exit Rule: 30 pips (partial) or 60 pips (full) targets
  • Stop Loss: 1x ATR below entry

Next Steps:
  1. Review swing_trader_report_2year.json for detailed metrics
  2. Analyze swing_trades_2year.csv to see all trades
  3. Check cumulative P&L and win rate
  4. Monitor new signals daily for trade opportunities
  5. Execute trades when LONG signals appear + confluence met
    """)
    
    print("=" * 70)
    print(f"Completed at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
