"""
COMBINED SWING TRADING STRATEGY FOR EUR/USD
============================================
Strategy 1: DXY Trend Analysis (Market Bias)
Strategy 2: Price Action + Rejection Candles (Entry Signals)

Target: 30-60 pips per trade
Direction: LONG ONLY
Frequency: 1-2 trades per day or 1-2 per week

Author: Swing Trader Bot
Last Updated: February 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os


# ═══════════════════════════════════════════════════════════════════════════
# TECHNICAL INDICATORS
# ═══════════════════════════════════════════════════════════════════════════

def ema(series: pd.Series, span: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return series.ewm(span=span, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average"""
    return series.rolling(window=period).mean()


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range"""
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    close = df["Close"].astype(float)
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
    """Calculate MACD"""
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average Directional Index"""
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    close = df["Close"].astype(float)
    
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    plus_di = 100 * (plus_dm.rolling(period).mean() / tr.rolling(period).mean())
    minus_di = 100 * (minus_dm.rolling(period).mean() / tr.rolling(period).mean())
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx_val = dx.rolling(period).mean()
    
    return adx_val


# ═══════════════════════════════════════════════════════════════════════════
# STRATEGY 1: DXY TREND ANALYSIS (Market Bias)
# ═══════════════════════════════════════════════════════════════════════════

def analyze_dxy_bias(dxy_df: pd.DataFrame) -> dict:
    """
    Analyze DXY to determine market bias.
    DXY Downtrend → EUR/USD Bullish
    DXY Uptrend → EUR/USD Bearish
    """
    if dxy_df.empty or len(dxy_df) < 50:
        return {"bias": "NEUTRAL", "strength": 0, "ema_21": None, "ema_50": None, "adx_val": None}
    
    try:
        # Calculate moving averages
        ema_21 = ema(dxy_df["Close"], 21).iloc[-1]
        ema_50 = ema(dxy_df["Close"], 50).iloc[-1]
        current_price = float(dxy_df["Close"].iloc[-1])
        
        # Calculate ADX for trend strength
        adx_val = adx(dxy_df, 14).iloc[-1]
        
        # Determine bias
        if ema_21 < ema_50:
            bias = "DOWNTREND"  # EUR/USD Bullish
            strength = min((ema_50 - ema_21) / current_price * 100, 100)
        else:
            bias = "UPTREND"    # EUR/USD Bearish
            strength = min((ema_21 - ema_50) / current_price * 100, 100)
        
        # Verify with ADX (trend strength must be > 20 for strong bias)
        if pd.isna(adx_val) or adx_val < 20:
            bias = "NEUTRAL"
        
        return {
            "bias": bias,
            "strength": strength,
            "ema_21": ema_21,
            "ema_50": ema_50,
            "adx_val": adx_val if not pd.isna(adx_val) else None,
            "current_price": current_price
        }
    except Exception as e:
        return {"bias": "NEUTRAL", "strength": 0, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# STRATEGY 2: PRICE ACTION + REJECTION CANDLES (Entry Signal)
# ═══════════════════════════════════════════════════════════════════════════

def detect_rejection_candles(df: pd.DataFrame, lookback: int = 5) -> dict:
    """
    Detect rejection (pin bar) candles that indicate potential reversals.
    - Long rejection: price touches low, closes near high
    - Empty body: small body relative to wicks
    """
    if df.empty or len(df) < lookback:
        return {"detected": False, "type": None, "strength": 0}
    
    try:
        recent = df.iloc[-lookback:].copy()
        last_candle = recent.iloc[-1]
        
        open_price = float(last_candle["Open"])
        high = float(last_candle["High"])
        low = float(last_candle["Low"])
        close = float(last_candle["Close"])
        
        # Calculate candle metrics
        body = abs(close - open_price)
        wick_down = open_price - low if open_price < close else close - low
        wick_up = high - open_price if open_price > close else high - close
        total_range = high - low
        
        # Rejection candle criteria
        if total_range > 0:
            body_ratio = body / total_range
            lower_wick_ratio = wick_down / total_range
            
            # Bullish rejection: long lower wick, small body, close near high
            if lower_wick_ratio > 0.5 and body_ratio < 0.3 and close > open_price:
                return {
                    "detected": True,
                    "type": "BULLISH_REJECTION",
                    "strength": min(lower_wick_ratio * 100, 100),
                    "entry_level": close
                }
            
            # Bearish rejection: long upper wick, small body, close near low
            if wick_up / total_range > 0.5 and body_ratio < 0.3 and close < open_price:
                return {
                    "detected": True,
                    "type": "BEARISH_REJECTION",
                    "strength": min(wick_up / total_range * 100, 100),
                    "entry_level": close
                }
        
        return {"detected": False, "type": None, "strength": 0}
    except Exception as e:
        return {"detected": False, "type": None, "strength": 0, "error": str(e)}


def detect_breakout(df: pd.DataFrame, period: int = 20) -> dict:
    """
    Detect Donchian breakouts (price breaks above/below recent highs/lows)
    """
    if df.empty or len(df) < period + 1:
        return {"breakout": False, "type": None, "level": None}
    
    try:
        recent_high = df["High"].iloc[-period:-1].max()
        recent_low = df["Low"].iloc[-period:-1].min()
        current_price = float(df["Close"].iloc[-1])
        
        if current_price > recent_high:
            return {"breakout": True, "type": "BULLISH_BREAKOUT", "level": recent_high}
        elif current_price < recent_low:
            return {"breakout": True, "type": "BEARISH_BREAKOUT", "level": recent_low}
        
        return {"breakout": False, "type": None, "level": None}
    except Exception as e:
        return {"breakout": False, "type": None, "level": None, "error": str(e)}


def analyze_price_action(eurusd_df: pd.DataFrame) -> dict:
    """
    Analyze price action for entry signals using rejection candles and breakouts
    """
    if eurusd_df.empty or len(eurusd_df) < 25:
        return {"signal": "NEUTRAL", "confidence": 0, "type": None}
    
    try:
        # Check for rejection candles (primary entry signal)
        rejection = detect_rejection_candles(eurusd_df, lookback=5)
        
        # Check for breakouts (confirmation signal)
        breakout = detect_breakout(eurusd_df, period=20)
        
        # Determine combined signal
        signal = "NEUTRAL"
        confidence = 0
        signal_type = None
        
        if rejection.get("detected") and rejection.get("type") == "BULLISH_REJECTION":
            signal = "BULLISH"
            confidence = rejection.get("strength", 50)
            signal_type = "REJECTION_CANDLE"
            
            # Boost if confirmed by breakout
            if breakout.get("breakout") and breakout.get("type") == "BULLISH_BREAKOUT":
                signal = "BULLISH"
                confidence = min(confidence + 20, 100)
                signal_type = "REJECTION_BREAKOUT"
        
        elif rejection.get("detected") and rejection.get("type") == "BEARISH_REJECTION":
            signal = "BEARISH"
            confidence = rejection.get("strength", 50)
            signal_type = "REJECTION_CANDLE"
        
        elif breakout.get("breakout") and breakout.get("type") == "BULLISH_BREAKOUT":
            signal = "BULLISH"
            confidence = 60
            signal_type = "BREAKOUT"
        
        elif breakout.get("breakout") and breakout.get("type") == "BEARISH_BREAKOUT":
            signal = "BEARISH"
            confidence = 60
            signal_type = "BREAKOUT"
        
        return {
            "signal": signal,
            "confidence": confidence,
            "type": signal_type,
            "rejection": rejection,
            "breakout": breakout
        }
    except Exception as e:
        return {"signal": "NEUTRAL", "confidence": 0, "type": None, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# COMBINED STRATEGY SIGNALS
# ═══════════════════════════════════════════════════════════════════════════

def generate_combined_signals(eurusd_df: pd.DataFrame, dxy_df: pd.DataFrame) -> dict:
    """
    Combine Strategy 1 (DXY Bias) + Strategy 2 (Price Action)
    Only generate LONG signals at confluence of both strategies
    """
    if eurusd_df.empty or dxy_df.empty:
        return {
            "signal": "NEUTRAL",
            "confidence": 0,
            "strategy1_bias": "NEUTRAL",
            "strategy2_signal": "NEUTRAL",
            "confluence": False
        }
    
    try:
        # Get Strategy 1: DXY Bias
        dxy_bias = analyze_dxy_bias(dxy_df)
        
        # Get Strategy 2: Price Action
        price_action = analyze_price_action(eurusd_df)
        
        # Get current price
        current_price = float(eurusd_df["Close"].iloc[-1])
        
        # CONFLUENCE: Both strategies must be BULLISH for LONG entry
        signal = "NEUTRAL"
        confidence = 0
        confluence = False
        
        if (dxy_bias.get("bias") == "DOWNTREND" and 
            price_action.get("signal") == "BULLISH"):
            signal = "LONG"
            confidence = min(
                (dxy_bias.get("strength", 0) + price_action.get("confidence", 0)) / 2,
                100
            )
            confluence = True
        
        return {
            "signal": signal,
            "confidence": confidence,
            "confluence": confluence,
            "strategy1_bias": dxy_bias.get("bias", "NEUTRAL"),
            "strategy1_strength": dxy_bias.get("strength", 0),
            "strategy2_signal": price_action.get("signal", "NEUTRAL"),
            "strategy2_confidence": price_action.get("confidence", 0),
            "strategy2_type": price_action.get("type", None),
            "current_price": current_price,
            "dxy_price": dxy_bias.get("current_price", None),
            "dxy_adx": dxy_bias.get("adx_val", None)
        }
    except Exception as e:
        return {
            "signal": "NEUTRAL",
            "confidence": 0,
            "confluence": False,
            "error": str(e)
        }


# ═══════════════════════════════════════════════════════════════════════════
# SIGNAL AGGREGATOR & SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

def aggregate_signals_over_period(eurusd_df: pd.DataFrame, dxy_df: pd.DataFrame, 
                                  lookback_days: int = 30) -> dict:
    """
    Analyze signals over a period and generate summary statistics
    """
    # Ensure datetime column
    eurusd_df = eurusd_df.copy()
    if "dt" not in eurusd_df.columns:
        eurusd_df["dt"] = pd.to_datetime(eurusd_df.index)
    
    dxy_df = dxy_df.copy()
    if "dt" not in dxy_df.columns:
        dxy_df["dt"] = pd.to_datetime(dxy_df.index)
    
    # Filter to lookback period
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)
    eurusd_df = eurusd_df[eurusd_df["dt"] >= cutoff].reset_index(drop=True)
    dxy_df = dxy_df[dxy_df["dt"] >= cutoff].reset_index(drop=True)
    
    if eurusd_df.empty or len(eurusd_df) < 5:
        return {
            "total_signals": 0,
            "bullish_signals": 0,
            "bearish_signals": 0,
            "neutral_signals": 0,
            "bullish_pct": 0,
            "bearish_pct": 0,
            "neutral_pct": 0,
            "long_ready": False,
            "signals": []
        }
    
    try:
        signals = []
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        long_ready_count = 0
        
        # Analyze every 4H candle (starting from index 4)
        analysis_interval = max(1, len(eurusd_df) // 10)  # Sample ~10 analysis points
        
        for i in range(max(4, analysis_interval), len(eurusd_df), analysis_interval):
            eurusd_slice = eurusd_df.iloc[:i+1].copy()
            dxy_slice = dxy_df.iloc[:i+1].copy()
            
            combined = generate_combined_signals(eurusd_slice, dxy_slice)
            
            signal_record = {
                "timestamp": eurusd_slice["dt"].iloc[-1],
                "price": combined.get("current_price"),
                "signal": combined.get("signal"),
                "confidence": combined.get("confidence"),
                "confluence": combined.get("confluence"),
                "dxy_bias": combined.get("strategy1_bias"),
                "price_action": combined.get("strategy2_signal")
            }
            signals.append(signal_record)
            
            # Count signals
            if combined.get("signal") == "LONG":
                bullish_count += 1
                long_ready_count += 1
            elif combined.get("signal") == "NEUTRAL":
                neutral_count += 1
        
        total = len(signals)
        bullish_pct = (bullish_count / total * 100) if total > 0 else 0
        bearish_pct = (bearish_count / total * 100) if total > 0 else 0
        neutral_pct = (neutral_count / total * 100) if total > 0 else 0
        
        return {
            "total_signals": total,
            "bullish_signals": bullish_count,
            "bearish_signals": bearish_count,
            "neutral_signals": neutral_count,
            "bullish_pct": bullish_pct,
            "bearish_pct": bearish_pct,
            "neutral_pct": neutral_pct,
            "long_ready": long_ready_count > 0,
            "long_ready_count": long_ready_count,
            "signals": signals,
            "latest_signal": signals[-1] if signals else None
        }
    except Exception as e:
        return {
            "total_signals": 0,
            "bullish_signals": 0,
            "bearish_signals": 0,
            "neutral_signals": 0,
            "bullish_pct": 0,
            "bearish_pct": 0,
            "neutral_pct": 0,
            "long_ready": False,
            "error": str(e)
        }


# ═══════════════════════════════════════════════════════════════════════════
# BACKTEST ENGINE (30-60 PIPS TARGET, LONG ONLY)
# ═══════════════════════════════════════════════════════════════════════════

def backtest_swing_strategy(eurusd_df: pd.DataFrame, dxy_df: pd.DataFrame,
                           min_pips: float = 30, max_pips: float = 60,
                           lookback_days: int = 30, max_concurrent_trades: int = 5) -> dict:
    """
    Backtest the combined swing trading strategy with support for multiple concurrent positions.
    
    Parameters:
    - min_pips: Minimum target (30 pips)
    - max_pips: Maximum target (60 pips)
    - lookback_days: Period to backtest (default 30, use 730 for 2 years)
    - max_concurrent_trades: Maximum concurrent LONG positions (default 5, increase for aggressive trading)
    
    Returns:
    - Trade history, statistics, and equity curve
    """
    
    eurusd_df = eurusd_df.copy()
    if "dt" not in eurusd_df.columns:
        eurusd_df["dt"] = pd.to_datetime(eurusd_df.index)
    
    dxy_df = dxy_df.copy()
    if "dt" not in dxy_df.columns:
        dxy_df["dt"] = pd.to_datetime(dxy_df.index)
    
    # Filter to lookback
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)
    eurusd_df = eurusd_df[eurusd_df["dt"] >= cutoff].reset_index(drop=True)
    dxy_df = dxy_df[dxy_df["dt"] >= cutoff].reset_index(drop=True)
    
    if eurusd_df.empty or len(eurusd_df) < 50:
        return {"error": "Insufficient data for backtest", "trades": []}
    
    try:
        trades = []
        active_positions = []  # List of active LONG positions
        equity = 1000  # Starting equity
        equity_curve = [equity]
        dates = [eurusd_df["dt"].iloc[0]]
        
        # Set ATR-based stop loss
        atr_val = atr(eurusd_df, 14)
        
        for i in range(25, len(eurusd_df)):
            current_date = eurusd_df["dt"].iloc[i]
            current_price = float(eurusd_df["Close"].iloc[i])
            high = float(eurusd_df["High"].iloc[i])
            low = float(eurusd_df["Low"].iloc[i])
            
            # ─ ENTRY LOGIC (Allow multiple concurrent positions) ─
            # Check if we can open new position(s)
            if len(active_positions) < max_concurrent_trades:
                # Get latest combined signal
                eurusd_slice = eurusd_df.iloc[:i+1]
                dxy_slice = dxy_df.iloc[:i+1]
                combined_sig = generate_combined_signals(eurusd_slice, dxy_slice)
                
                # Enter long if: LONG signal + confluence + no recent entry on this signal
                if combined_sig.get("signal") == "LONG" and combined_sig.get("confluence"):
                    # Check if we already have a position from very recent entry (within last 2 bars)
                    recent_entries = [p for p in active_positions if i - p["entry_index"] <= 2]
                    if not recent_entries:  # Avoid duplicate entries from same signal
                        atr_current = atr_val.iloc[i]
                        stop_loss = current_price - (atr_current if not pd.isna(atr_current) else 0.005)
                        
                        # Add new position
                        active_positions.append({
                            "entry_price": current_price,
                            "entry_date": current_date,
                            "entry_index": i,
                            "stop_loss": stop_loss,
                            "min_target": current_price + (min_pips * 0.0001),
                            "max_target": current_price + (max_pips * 0.0001)
                        })
            
            # ─ EXIT LOGIC (Check all active positions) ─
            positions_to_remove = []
            
            for pos_idx, position in enumerate(active_positions):
                entry_price = position["entry_price"]
                entry_date = position["entry_date"]
                stop_loss = position["stop_loss"]
                min_target = position["min_target"]
                max_target = position["max_target"]
                
                # Early target hit (min_pips)
                if high >= min_target:
                    exit_price = min_target
                    pnl_pips = (exit_price - entry_price) * 10000
                    
                    trades.append({
                        "entry_date": entry_date,
                        "exit_date": current_date,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl_pips": pnl_pips,
                        "status": "TARGET_MIN",
                        "days_held": (current_date - entry_date).days
                    })
                    
                    equity += pnl_pips / 100
                    positions_to_remove.append(pos_idx)
                
                # Full target hit (max_pips)
                elif high >= max_target:
                    exit_price = max_target
                    pnl_pips = (exit_price - entry_price) * 10000
                    
                    trades.append({
                        "entry_date": entry_date,
                        "exit_date": current_date,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl_pips": pnl_pips,
                        "status": "TARGET_MAX",
                        "days_held": (current_date - entry_date).days
                    })
                    
                    equity += pnl_pips / 100
                    positions_to_remove.append(pos_idx)
                
                # Stop loss hit
                elif low <= stop_loss:
                    exit_price = stop_loss
                    pnl_pips = (exit_price - entry_price) * 10000
                    
                    trades.append({
                        "entry_date": entry_date,
                        "exit_date": current_date,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl_pips": pnl_pips,
                        "status": "SL",
                        "days_held": (current_date - entry_date).days
                    })
                    
                    equity += pnl_pips / 100
                    positions_to_remove.append(pos_idx)
            
            # Remove closed positions (in reverse to preserve indices)
            for pos_idx in sorted(positions_to_remove, reverse=True):
                active_positions.pop(pos_idx)
            
            # Update equity curve
            equity_curve.append(equity)
            dates.append(current_date)
        
        # ─ CALCULATE STATISTICS ─
        wins = [t for t in trades if t["pnl_pips"] > 0]
        losses = [t for t in trades if t["pnl_pips"] < 0]
        
        total_trades = len(trades)
        win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0
        avg_win_pips = (sum(t["pnl_pips"] for t in wins) / len(wins)) if wins else 0
        avg_loss_pips = (sum(t["pnl_pips"] for t in losses) / len(losses)) if losses else 0
        
        total_pnl = sum(t["pnl_pips"] for t in trades)
        profit_factor = 0
        if losses:
            profit_factor = abs(sum(t["pnl_pips"] for t in wins)) / abs(sum(t["pnl_pips"] for t in losses)) if losses else 0
        
        # Max drawdown
        max_dd = 0
        if equity_curve:
            peak = equity_curve[0]
            for e in equity_curve:
                if e > peak:
                    peak = e
                dd = (peak - e) / peak * 100 if peak > 0 else 0
                if dd > max_dd:
                    max_dd = dd
        
        return {
            "trades": trades,
            "total_trades": total_trades,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": win_rate,
            "avg_win_pips": avg_win_pips,
            "avg_loss_pips": avg_loss_pips,
            "profit_factor": profit_factor,
            "total_pnl_pips": total_pnl,
            "final_equity": equity,
            "max_drawdown": max_dd,
            "equity_curve": equity_curve,
            "dates": dates,
            "backtest_period_days": lookback_days
        }
    except Exception as e:
        return {"error": str(e), "trades": []}


# ═══════════════════════════════════════════════════════════════════════════
# SIGNAL REPORTER
# ═══════════════════════════════════════════════════════════════════════════

def generate_signal_report(eurusd_df: pd.DataFrame, dxy_df: pd.DataFrame,
                          backtest_result: dict = None) -> dict:
    """
    Generate a comprehensive signal report with current signals and backtest results
    """
    
    # Get latest signals
    latest_combined = generate_combined_signals(eurusd_df, dxy_df)
    
    # Get signal aggregation over 30 days
    signal_summary = aggregate_signals_over_period(eurusd_df, dxy_df, lookback_days=30)
    
    # Format report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "current_signals": {
            "combined_signal": latest_combined.get("signal"),
            "confidence": latest_combined.get("confidence"),
            "confluence": latest_combined.get("confluence"),
            "dxy_bias": latest_combined.get("strategy1_bias"),
            "dxy_strength": latest_combined.get("strategy1_strength"),
            "price_action": latest_combined.get("strategy2_signal"),
            "price_action_confidence": latest_combined.get("strategy2_confidence"),
            "entry_type": latest_combined.get("strategy2_type"),
            "current_eurusd_price": latest_combined.get("current_price"),
            "current_dxy_price": latest_combined.get("dxy_price"),
            "dxy_adx": latest_combined.get("dxy_adx")
        },
        "signal_summary": signal_summary,
        "backtest": backtest_result if backtest_result else {}
    }
    
    return report


# ═══════════════════════════════════════════════════════════════════════════
# SAVE REPORTS
# ═══════════════════════════════════════════════════════════════════════════

def save_report_json(report: dict, filename: str = "swing_trader_report.json"):
    """Save report to JSON file"""
    try:
        # Convert non-serializable objects
        report_clean = {
            "timestamp": report.get("timestamp"),
            "current_signals": report.get("current_signals"),
            "signal_summary": {
                "total_signals": report["signal_summary"].get("total_signals"),
                "bullish_signals": report["signal_summary"].get("bullish_signals"),
                "bearish_signals": report["signal_summary"].get("bearish_signals"),
                "neutral_signals": report["signal_summary"].get("neutral_signals"),
                "bullish_pct": report["signal_summary"].get("bullish_pct"),
                "bearish_pct": report["signal_summary"].get("bearish_pct"),
                "neutral_pct": report["signal_summary"].get("neutral_pct"),
                "long_ready": report["signal_summary"].get("long_ready"),
            },
            "backtest": {
                "total_trades": report["backtest"].get("total_trades"),
                "wins": report["backtest"].get("wins"),
                "losses": report["backtest"].get("losses"),
                "win_rate": report["backtest"].get("win_rate"),
                "avg_win_pips": report["backtest"].get("avg_win_pips"),
                "avg_loss_pips": report["backtest"].get("avg_loss_pips"),
                "profit_factor": report["backtest"].get("profit_factor"),
                "total_pnl_pips": report["backtest"].get("total_pnl_pips"),
                "max_drawdown": report["backtest"].get("max_drawdown"),
                "final_equity": report["backtest"].get("final_equity")
            }
        }
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, 'w') as f:
            json.dump(report_clean, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving report: {e}")
        return False


if __name__ == "__main__":
    print("Swing Trading Strategy Module loaded successfully")
    print("Use: from SwingTraderCombined import *")
