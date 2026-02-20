import streamlit as st
import yfinance as yf
import requests
import feedparser
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pytz
import re
import os
import sys
import json

st.set_page_config(layout="wide", page_title="EUR/USD + DXY Signals", page_icon="📈")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
*, html, body, [class*="css"] { font-family: 'Roboto', sans-serif !important; box-sizing: border-box; }
.main, section[data-testid="stMain"] > div { background: #1b1f2b !important; padding-top: 0 !important; }
.block-container { padding: 0.5rem 1rem 1rem 1rem !important; max-width: 100% !important; }

.price-header {
  display: flex; align-items: stretch; gap: 0;
  border: 1px solid #2e3347; border-radius: 4px; overflow: hidden;
  margin-bottom: 6px; background: #1b1f2b;
}
.price-box {
  display: flex; align-items: center; gap: 14px;
  padding: 12px 22px; background: #252a3a;
  border-right: 1px solid #2e3347; min-width: 220px;
}
.pair-label { font-size: 1.2rem; font-weight: 700; color: #e0e6f0; letter-spacing: 0.5px; }
.price-val  { font-size: 1.45rem; font-weight: 700; color: #e0e6f0; letter-spacing: 1px; }
.perf-panel { display: flex; flex: 1; }
.perf-col   { flex: 1; border-right: 1px solid #2e3347; padding: 8px 14px; }
.perf-col:last-child { border-right: none; }
.perf-label { font-size: 0.68rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px; }
.perf-row   { display: flex; justify-content: space-between; font-size: 0.76rem; margin-bottom: 2px; }
.perf-key   { color: #8b949e; }
.pos { color: #3fb950; font-weight: 600; }
.neg { color: #e74c3c; font-weight: 600; }
.neu { color: #8b949e; }

.ohlc-bar {
  background: #1b1f2b; border-bottom: 1px solid #2e3347;
  padding: 4px 12px; font-size: 0.76rem; color: #8b949e;
  display: flex; gap: 18px; align-items: center; margin-bottom:2px;
}

div[data-testid="stButton"] button {
  background: #252a3a !important; color: #8b949e !important;
  border: 1px solid #2e3347 !important; font-size: 0.78rem !important;
  padding: 3px 10px !important; border-radius: 3px !important;
}
div[data-testid="stButton"] button:hover { background: #1a5276 !important; color: #58a6ff !important; }

.section-panel { background: #252a3a; border: 1px solid #2e3347; border-radius: 4px; overflow: hidden; margin-top: 10px; }
.section-header { background: #1e2233; padding: 7px 14px; font-size: 0.82rem; font-weight: 600; color: #c9d1d9; border-bottom: 1px solid #2e3347; }
.story-item { padding: 7px 14px; border-bottom: 1px solid #1e2233; font-size: 0.79rem; }
.story-item:last-child { border-bottom: none; }
.story-time { color: #8b949e; font-size: 0.72rem; margin-right: 8px; }
.story-title a { color: #58a6ff; text-decoration: none; }
.story-title a:hover { text-decoration: underline; }

.ev-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; }
.ev-table th { color: #8b949e; font-weight: 500; padding: 5px 10px; border-bottom: 1px solid #2e3347; text-align: left; font-size: 0.72rem; text-transform: uppercase; }
.ev-table td { padding: 6px 10px; border-bottom: 1px solid #1e2233; color: #c9d1d9; }
.ev-table tr:last-child td { border-bottom: none; }
.ev-past td { opacity: 0.55; }
.imp-high { color: #e74c3c; font-weight: 700; font-size:1.1rem; }
.curr-usd { color: #58a6ff; font-weight:700; }
.curr-eur { color: #3fb950; font-weight:700; }

/* ── Signal Card ── */
.signal-card {
  background: #1e2233; border: 1px solid #2e3347; border-radius: 6px;
  padding: 14px 18px; margin-bottom: 10px;
}
.signal-title { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 8px; }
.sig-bull { font-size: 1.25rem; font-weight: 700; color: #3fb950; }
.sig-bear { font-size: 1.25rem; font-weight: 700; color: #e74c3c; }
.sig-neu  { font-size: 1.25rem; font-weight: 700; color: #8b949e; }
.signal-detail { font-size: 0.76rem; color: #8b949e; margin-top: 5px; line-height: 1.55; }
.signal-detail span.bull { color: #3fb950; }
.signal-detail span.bear { color: #e74c3c; }

/* Supply/Demand Level tags */
.level-demand { display:inline-block; background:#3fb95020; border:1px solid #3fb950; color:#3fb950; font-size:0.68rem; padding:1px 6px; border-radius:3px; margin:1px; }
.level-supply { display:inline-block; background:#e74c3c20; border:1px solid #e74c3c; color:#e74c3c; font-size:0.68rem; padding:1px 6px; border-radius:3px; margin:1px; }

/* News signal badge */
.news-sig-bull { display:inline-block; background:#3fb950; color:#000; font-size:0.65rem; font-weight:700; padding:1px 6px; border-radius:3px; margin-left:6px; }
.news-sig-bear { display:inline-block; background:#e74c3c; color:#fff; font-size:0.65rem; font-weight:700; padding:1px 6px; border-radius:3px; margin-left:6px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TIMEFRAME MAP
# ══════════════════════════════════════════════════════════════════════════════
TF_MAP = {
    "1M":  ("2d",  "1m"),
    "5M":  ("5d",  "5m"),
    "15M": ("7d",  "15m"),
    "1H":  ("30d", "1h"),
    "4H":  ("60d", "4h"),
    "D":   ("1y",  "1d"),
    "M":   ("5y",  "1mo"),
}


# ══════════════════════════════════════════════════════════════════════════════
# DATA FETCHERS
# ══════════════════════════════════════════════════════════════════════════════
def _clean_df(df, ticker_name):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.reset_index()
    dt_col = "Datetime" if "Datetime" in df.columns else "Date"
    df = df.rename(columns={dt_col: "dt"})
    df["dt"] = pd.to_datetime(df["dt"]).dt.tz_localize(None)
    # Preserve Volume when available for volume bars (useful for plotting)
    cols = ["dt", "Open", "High", "Low", "Close"]
    if "Volume" in df.columns:
        cols.append("Volume")
    df = df[cols].dropna()
    return df

@st.cache_data(ttl=30)
def get_price_data(tf="1H"):
    period, interval = TF_MAP[tf]
    df = yf.download("EURUSD=X", period=period, interval=interval, progress=False)
    return _clean_df(df, "EURUSD")

@st.cache_data(ttl=30)
def get_dxy_data(tf="1H"):
    period, interval = TF_MAP[tf]
    df = yf.download("DX-Y.NYB", period=period, interval=interval, progress=False)
    return _clean_df(df, "DXY")

@st.cache_data(ttl=60)
def get_live_price(ticker="EURUSD=X"):
    try:
        t = yf.Ticker(ticker)
        h = t.history(period="1d", interval="1m")
        return float(h["Close"].iloc[-1])
    except:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# CALENDAR  (fixed: show today+upcoming, multiple fallback sources)
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def get_calendar():
    sources = [
        "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
        "https://cdn-nfs.faireconomy.media/ff_calendar_thisweek.json",
    ]
    events = []
    for url in sources:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            raw = r.json()
            if raw:
                events = raw
                break
        except Exception:
            continue

    out = []
    for ev in events:
        # Include High and Medium impact events (or any impact if no high/medium available)
        impact = ev.get("impact", "").lower()
        if impact not in ("high", "medium", "low"):
            continue
        ccy = ev.get("currency", "")
        if ccy not in ("EUR", "USD"):
            continue
        date_str = ev.get("date", "")
        if not date_str:
            continue
        try:
            # Handle both "2024-03-15T13:30:00-04:00" and "2024-03-15T13:30:00Z"
            date_str = date_str.replace("Z", "+00:00")
            dt_aware = datetime.fromisoformat(date_str)
            dt = dt_aware.astimezone(pytz.utc).replace(tzinfo=None)
        except Exception:
            try:
                dt = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
            except Exception:
                continue

        out.append({
            "dt":       dt,
            "currency": ccy,
            "title":    ev.get("title", ""),
            "actual":   ev.get("actual") or "",
            "forecast": ev.get("forecast") or "",
            "previous": ev.get("previous") or "",
            "impact":   impact.capitalize(),
        })

    return sorted(out, key=lambda x: x["dt"])


# ══════════════════════════════════════════════════════════════════════════════
# NEWS
# ══════════════════════════════════════════════════════════════════════════════
# Keywords that signal USD weakness → EURUSD bullish
USD_WEAK_KWORDS = [
    "dollar falls", "dollar weakens", "dollar drops", "usd sells off",
    "dollar declines", "dollar lower", "dollar under pressure",
    "fed cuts", "rate cut", "dovish fed", "fed dovish",
    "below forecast", "miss", "disappoints", "weaker than expected",
    "unemployment rises", "jobless claims rise", "nfp miss",
    "inflation cools", "cpi lower", "pce lower",
]
# Keywords that signal USD strength → EURUSD bearish
USD_STRONG_KWORDS = [
    "dollar rises", "dollar rallies", "dollar surges", "dollar gains",
    "dollar higher", "usd jumps", "dollar strengthens",
    "fed hikes", "rate hike", "hawkish fed", "fed hawkish",
    "beat", "better than expected", "strong jobs", "nfp beat",
    "inflation rises", "cpi hotter", "pce higher",
    "euro falls", "eur/usd drops", "eurusd falls",
]

def classify_news_signal(title: str, summary: str = "") -> str:
    """Return 'BULL', 'BEAR', or '' based on headline sentiment."""
    text = (title + " " + summary).lower()
    bull_hits = sum(1 for k in USD_WEAK_KWORDS   if k in text)
    bear_hits = sum(1 for k in USD_STRONG_KWORDS if k in text)
    if bull_hits > bear_hits:
        return "BULL"
    elif bear_hits > bull_hits:
        return "BEAR"
    return ""

@st.cache_data(ttl=120)
def get_news():
    feeds = [
        "https://www.forexlive.com/feed/news",
        "https://www.fxstreet.com/rss/news",
        "https://www.investing.com/rss/news_301.rss",
    ]
    keywords = ["eurusd", "eur/usd", "euro", "ecb", "federal reserve", "fed", "fomc",
                "powell", "lagarde", "usd", "dollar", "inflation", "cpi", "nfp",
                "interest rate", "gdp", "durable goods", "pmi", "dxy"]
    articles = []
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                title   = e.get("title", "")
                summary = e.get("summary", "")
                content = (title + " " + summary).lower()
                if not any(k in content for k in keywords):
                    continue
                pub = e.get("published_parsed") or e.get("updated_parsed")
                dt  = datetime(*pub[:6]) if pub else datetime.utcnow()
                sig = classify_news_signal(title, summary)
                articles.append({
                    "dt":     dt,
                    "title":  title,
                    "link":   e.get("link", "#"),
                    "source": feed.feed.get("title", ""),
                    "signal": sig,
                })
        except Exception:
            continue

    seen, unique = set(), []
    for a in sorted(articles, key=lambda x: x["dt"], reverse=True):
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    return unique[:40]


# ══════════════════════════════════════════════════════════════════════════════
# DXY ANALYSIS  — trend + supply/demand levels
# ══════════════════════════════════════════════════════════════════════════════
def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range (ATR)."""
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    close = df["Close"].astype(float)
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI)."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def adx(df: pd.DataFrame, period: int = 14) -> tuple:
    """Calculate ADX, +DI, -DI. Returns (ADX series, +DI series, -DI series)."""
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    close = df["Close"].astype(float)
    
    # Calculate directional movements
    up_move = high.diff()
    down_move = -low.diff()
    
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr_val = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr_val)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr_val)
    
    di_diff = abs(plus_di - minus_di)
    di_sum = plus_di + minus_di
    dx = 100 * (di_diff / di_sum)
    adx_val = dx.rolling(period).mean()
    
    return adx_val, plus_di, minus_di

def donchian_channel(df: pd.DataFrame, period: int = 20) -> tuple:
    """Calculate Donchian Channel. Returns (upper band, lower band, middle band)."""
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    
    upper = high.rolling(period).max()
    lower = low.rolling(period).min()
    middle = (upper + lower) / 2
    
    return upper, lower, middle

def analyze_dxy(dxy_df: pd.DataFrame) -> dict:
    """
    Returns:
        trend       : 'DOWNTREND' | 'UPTREND' | 'NEUTRAL'
        eur_signal  : 'BULLISH' | 'BEARISH' | 'NEUTRAL'
        supply_levels : list of price floats (DXY swing highs → EURUSD demand)
        demand_levels : list of price floats (DXY swing lows  → EURUSD supply)
        ema20, ema50  : latest EMA values
        score_dxy     : int  (positive = DXY bullish = EURUSD bearish)
    """
    result = {
        "trend": "NEUTRAL", "eur_signal": "NEUTRAL",
        "supply_levels": [], "demand_levels": [],
        "ema20": None, "ema50": None, "score_dxy": 0,
        "last_close": None, "change_pct": 0.0,
    }
    if dxy_df is None or len(dxy_df) < 55:
        return result

    closes = dxy_df["Close"].astype(float)
    highs  = dxy_df["High"].astype(float)
    lows   = dxy_df["Low"].astype(float)

    e20 = ema(closes, 20)
    e50 = ema(closes, 50)
    last_close = float(closes.iloc[-1])
    result["last_close"] = last_close
    result["ema20"] = round(float(e20.iloc[-1]), 3)
    result["ema50"] = round(float(e50.iloc[-1]), 3)

    # Compute ADX on DXY and use it to help determine trend
    try:
        dxy_adx_series, dxy_plus_di, dxy_minus_di = adx(dxy_df, 14)
        dxy_adx_val = float(dxy_adx_series.iloc[-1]) if not pd.isna(dxy_adx_series.iloc[-1]) else 0
        plus_di_val = float(dxy_plus_di.iloc[-1]) if not pd.isna(dxy_plus_di.iloc[-1]) else 0
        minus_di_val = float(dxy_minus_di.iloc[-1]) if not pd.isna(dxy_minus_di.iloc[-1]) else 0
    except Exception:
        dxy_adx_val = 0
        plus_di_val = 0
        minus_di_val = 0

    result["dxy_adx"] = dxy_adx_val

    # Change % over last 5 bars
    ref = float(closes.iloc[-6]) if len(closes) >= 6 else float(closes.iloc[0])
    result["change_pct"] = round((last_close - ref) / ref * 100, 3)

    # Trend scoring
    score = 0
    if last_close > float(e20.iloc[-1]):   score += 1
    if last_close > float(e50.iloc[-1]):   score += 1
    if float(e20.iloc[-1]) > float(e50.iloc[-1]): score += 1
    if result["change_pct"] > 0.15:        score += 1
    if result["change_pct"] > 0.40:        score += 1
    if last_close < float(e20.iloc[-1]):   score -= 1
    if last_close < float(e50.iloc[-1]):   score -= 1
    if float(e20.iloc[-1]) < float(e50.iloc[-1]): score -= 1
    if result["change_pct"] < -0.15:       score -= 1
    if result["change_pct"] < -0.40:       score -= 1
    result["score_dxy"] = score

    # If ADX is strong, prefer ADX+DI direction over EMA heuristic
    if dxy_adx_val > 25:
        if plus_di_val > minus_di_val:
            result["trend"] = "UPTREND"
        elif minus_di_val > plus_di_val:
            result["trend"] = "DOWNTREND"
        else:
            # fallback to score heuristic
            if score >= 2:
                result["trend"] = "UPTREND"
            elif score <= -2:
                result["trend"] = "DOWNTREND"
            else:
                result["trend"] = "NEUTRAL"
    else:
        if score >= 2:
            result["trend"] = "UPTREND"
        elif score <= -2:
            result["trend"] = "DOWNTREND"
        else:
            result["trend"] = "NEUTRAL"

    # EUR/USD signal is INVERSE of DXY trend
    inv = {"UPTREND": "BEARISH", "DOWNTREND": "BULLISH", "NEUTRAL": "NEUTRAL"}
    result["eur_signal"] = inv[result["trend"]]

    # Supply/Demand detection on DXY (swing highs / lows with lookback=5)
    lb = 5
    sup, dem = [], []
    n = len(dxy_df)
    for i in range(lb, n - lb):
        h = float(highs.iloc[i])
        l = float(lows.iloc[i])
        if h == float(highs.iloc[i-lb:i+lb+1].max()):
            sup.append(round(h, 3))   # DXY swing high = supply on DXY → demand zone on EURUSD
        if l == float(lows.iloc[i-lb:i+lb+1].min()):
            dem.append(round(l, 3))   # DXY swing low  = demand on DXY → supply zone on EURUSD

    # Keep closest 3 levels above and below current price
    sup_above = sorted([x for x in sup if x > last_close])[:3]
    dem_below = sorted([x for x in dem if x < last_close], reverse=True)[:3]
    result["supply_levels"] = sup_above   # DXY resistance → EURUSD demand trigger
    result["demand_levels"] = dem_below   # DXY support    → EURUSD supply trigger
    return result


# ══════════════════════════════════════════════════════════════════════════════
# TIMEFRAME STACK & CONFLUENCE CHECKLIST
# ══════════════════════════════════════════════════════════════════════════════
def evaluate_confluence_factors(eurusd_df: pd.DataFrame, dxy_df: pd.DataFrame, dxy_analysis: dict, cal_events: list) -> dict:
    """
    Evaluates the 8-factor confluence checklist for swing trading setup.
    Returns dict with factor status, current values, and setup quality score.
    """
    factors = {
        1: {"name": "DXY Trend (Mandatory)", "met": False, "value": None, "detail": ""},
        2: {"name": "DXY at Key Level", "met": False, "value": None, "detail": ""},
        3: {"name": "EUR/USD Market Structure", "met": False, "value": None, "detail": ""},
        4: {"name": "ADX on EUR/USD > 20", "met": False, "value": None, "detail": ""},
        5: {"name": "EUR/USD at Demand/Supply Zone", "met": False, "value": None, "detail": ""},
        6: {"name": "Donchian Channel Breakout", "met": False, "value": None, "detail": ""},
        7: {"name": "RSI Divergence", "met": False, "value": None, "detail": ""},
        8: {"name": "Session Timing (Bonus)", "met": False, "value": None, "detail": ""},
    }
    
    try:
        if eurusd_df.empty or dxy_df.empty:
            return {"factors": factors, "confluence_score": 0, "setup_quality": "NO DATA", "recommendation": ""}
        
        # ── Factor 1: DXY Trend (Mandatory)
        dxy_trend = dxy_analysis.get("trend", "NEUTRAL")
        dxy_adx, _, _ = adx(dxy_df, 14)
        dxy_adx_val = float(dxy_adx.iloc[-1]) if not pd.isna(dxy_adx.iloc[-1]) else 0
        # Accept Factor 1 when EITHER DXY trend label exists OR ADX indicates a strong trend
        factor1_met = (dxy_trend in ("UPTREND", "DOWNTREND")) or (dxy_adx_val > 20)
        factors[1]["met"] = factor1_met
        factors[1]["value"] = dxy_trend
        factors[1]["detail"] = f"{dxy_trend} (ADX: {dxy_adx_val:.1f})"
        
        # ── Factor 2: DXY at Key Level
        dxy_last = float(dxy_df["Close"].iloc[-1])
        supply_lvls = dxy_analysis.get("supply_levels", [])
        demand_lvls = dxy_analysis.get("demand_levels", [])
        dxy_key_level = None
        dxy_level_dist = None
        
        for lvl in supply_lvls:
            dist = abs(lvl - dxy_last) / dxy_last * 100
            if dist < 0.3:
                factor2_met = True
                dxy_key_level = lvl
                dxy_level_dist = dist
                break
        else:
            for lvl in demand_lvls:
                dist = abs(lvl - dxy_last) / dxy_last * 100
                if dist < 0.3:
                    factor2_met = True
                    dxy_key_level = lvl
                    dxy_level_dist = dist
                    break
            else:
                factor2_met = False
        
        factors[2]["met"] = factor2_met
        factors[2]["value"] = f"{dxy_last:.2f}"
        if dxy_key_level:
            factors[2]["detail"] = f"{dxy_level_dist:.2f}% from level {dxy_key_level}"
        else:
            factors[2]["detail"] = f"Nearest level: {min((abs(l-dxy_last) for l in supply_lvls + demand_lvls), default=float('inf')):.3f} pips away"
        
        # ── Factor 3: EUR/USD Market Structure
        eurusd_last = float(eurusd_df["Close"].iloc[-1])
        eurusd_last_high = float(eurusd_df["High"].iloc[-1])
        eurusd_last_low = float(eurusd_df["Low"].iloc[-1])
        
        # Check for higher highs/lows (bullish) or lower highs/lows (bearish)
        lookback = min(20, len(eurusd_df) - 1)
        check_high = float(eurusd_df["High"].iloc[-lookback:-1].max())
        check_low = float(eurusd_df["Low"].iloc[-lookback:-1].min())
        
        higher_highs = eurusd_last_high > check_high
        higher_lows = eurusd_last_low > check_low
        lower_highs = eurusd_last_high < check_high
        lower_lows = eurusd_last_low < check_low
        
        structure_bullish = higher_highs and higher_lows
        structure_bearish = lower_highs and lower_lows
        factor3_met = structure_bullish or structure_bearish
        
        factors[3]["met"] = factor3_met
        factors[3]["value"] = "Bullish" if structure_bullish else ("Bearish" if structure_bearish else "Ranging")
        factors[3]["detail"] = f"HH/HL" if structure_bullish else ("LH/LL" if structure_bearish else "Range")
        
        # ── Factor 4: ADX on EUR/USD > 20
        eurusd_adx, _, _ = adx(eurusd_df, 14)
        eurusd_adx_val = float(eurusd_adx.iloc[-1]) if not pd.isna(eurusd_adx.iloc[-1]) else 0
        factor4_met = eurusd_adx_val > 20
        factors[4]["met"] = factor4_met
        factors[4]["value"] = f"{eurusd_adx_val:.1f}"
        factors[4]["detail"] = "Trending" if eurusd_adx_val > 25 else ("Moderate" if eurusd_adx_val > 20 else "Ranging")
        
        # ── Factor 5: Price at Demand/Supply Zone
        # Look for pullbacks to previous support/resistance
        lookback_zone = min(50, len(eurusd_df) - 1)
        prev_highs = eurusd_df["High"].iloc[-lookback_zone:-1].nlargest(3)
        prev_lows = eurusd_df["Low"].iloc[-lookback_zone:-1].nsmallest(3)
        
        zone_threshold = 0.0010  # 10 pips
        at_supply = any(abs(float(eurusd_df["Close"].iloc[-1]) - float(h)) < zone_threshold for h in prev_highs)
        at_demand = any(abs(float(eurusd_df["Close"].iloc[-1]) - float(l)) < zone_threshold for l in prev_lows)
        factor5_met = at_supply or at_demand
        
        factors[5]["met"] = factor5_met
        factors[5]["value"] = "Supply" if at_supply else ("Demand" if at_demand else "Mid-range")
        factors[5]["detail"] = "" if at_supply or at_demand else "Not at established zone"
        
        # ── Factor 6: Donchian Channel Breakout
        upper_band, lower_band, _ = donchian_channel(eurusd_df, 20)
        current_price = eurusd_last
        above_upper = current_price > float(upper_band.iloc[-2]) and current_price > float(upper_band.iloc[-3])
        below_lower = current_price < float(lower_band.iloc[-2]) and current_price < float(lower_band.iloc[-3])
        factor6_met = above_upper or below_lower
        
        factors[6]["met"] = factor6_met
        factors[6]["value"] = "Above Upper" if above_upper else ("Below Lower" if below_lower else "Inside")
        factors[6]["detail"] = f"Upper: {float(upper_band.iloc[-1]):.5f} | Lower: {float(lower_band.iloc[-1]):.5f}"
        
        # ── Factor 7: RSI Divergence
        rsi_val = rsi(eurusd_df["Close"], 14)
        current_rsi = float(rsi_val.iloc[-1]) if not pd.isna(rsi_val.iloc[-1]) else 50
        
        # Look for divergence in last 10 candles
        lookback_div = min(10, len(eurusd_df) - 1)
        recent_lows = eurusd_df["Low"].iloc[-lookback_div:-1]
        recent_rsi = rsi_val.iloc[-lookback_div:-1]
        
        price_lower_low = float(recent_lows.iloc[-1]) < float(recent_lows.iloc[-max(1, lookback_div-5):].min())
        rsi_higher_low = float(recent_rsi.iloc[-1]) > float(recent_rsi.iloc[-max(1, lookback_div-5):].min())
        factor7_met = price_lower_low and rsi_higher_low
        
        factors[7]["met"] = factor7_met
        factors[7]["value"] = f"RSI {current_rsi:.1f}"
        factors[7]["detail"] = "Bullish divergence detected" if factor7_met else "No divergence"
        
        # ── Factor 8: Session Timing
        now_utc = datetime.utcnow()
        hour_utc = now_utc.hour
        in_london = 8 <= hour_utc < 17
        in_london_ny = 13 <= hour_utc < 17
        factor8_met = in_london or in_london_ny
        
        factors[8]["met"] = factor8_met
        factors[8]["value"] = f"{hour_utc:02d}:00 UTC"
        if in_london_ny:
            factors[8]["detail"] = "London/NY Overlap (HIGH LIQUIDITY)"
        elif in_london:
            factors[8]["detail"] = "London Session (GOOD)"
        else:
            factors[8]["detail"] = f"Off-hours (LOW LIQUIDITY)"
        
        # Calculate confluence score
        confluence_score = sum(1 for f in factors.values() if f["met"])
        
        # Setup quality assessment
        if not factors[1]["met"]:
            setup_quality = "⛔ NO TREND"
            recommendation = "DXY must be in clear trend with ADX > 20. Waiting for trend development."
        elif confluence_score >= 5:
            setup_quality = f"✅ SETUP READY ({confluence_score}/8)"
            recommendation = "5+ confluence factors aligned. Monitor 1H chart for entry trigger (Donchian breakout or rejection)."
        elif confluence_score >= 4:
            setup_quality = f"🟡 PARTIAL ({confluence_score}/8)"
            recommendation = "Getting closer to setup. Additional factors developing."
        else:
            setup_quality = f"🔴 NO SETUP ({confluence_score}/8)"
            recommendation = "Not enough confluence factors. Continue monitoring."
        
        return {
            "factors": factors,
            "confluence_score": confluence_score,
            "setup_quality": setup_quality,
            "recommendation": recommendation,
            "dxy_trend": dxy_trend,
            "eurusd_structure": factors[3]["value"],
            "eurusd_adx": eurusd_adx_val,
            "dxy_adx": dxy_adx_val,
        }
    
    except Exception as e:
        return {
            "factors": factors,
            "confluence_score": 0,
            "setup_quality": "ERROR",
            "recommendation": f"Analysis error: {str(e)}",
            "error": str(e),
        }


# ══════════════════════════════════════════════════════════════════════════════
# REJECTION CANDLE DETECTION (PIN BAR, HAMMER, ENGULFING)
# ══════════════════════════════════════════════════════════════════════════════
def detect_rejection_candles(df: pd.DataFrame, lookback: int = 5) -> dict:
    """
    Detect rejection candles (pin bars, hammers, engulfing patterns) at price zones.
    Returns list of identified rejection patterns with signal type (BULLISH/BEARISH).
    """
    rejections = []
    
    if df.empty or len(df) < lookback + 1:
        return {"patterns": rejections, "count": 0}
    
    try:
        for i in range(len(df) - lookback, len(df)):
            if i < 1:
                continue
                
            curr = df.iloc[i]
            prev = df.iloc[i - 1]
            
            o, h, l, c = float(curr["Open"]), float(curr["High"]), float(curr["Low"]), float(curr["Close"])
            p_c = float(prev["Close"])
            
            body = abs(c - o)
            upper_wick = h - max(o, c)
            lower_wick = min(o, c) - l
            range_bar = h - l
            
            # PIN BAR: Long wick on one end, small body
            if range_bar > 0:
                wick_ratio = max(upper_wick, lower_wick) / range_bar
                body_ratio = body / range_bar
                
                if wick_ratio > 0.6 and body_ratio < 0.3:
                    if upper_wick > lower_wick:
                        rejections.append({
                            "type": "Pin Bar (Bearish)",
                            "signal": "BEARISH",
                            "price": h,
                            "bar_idx": i,
                            "strength": "High wick rejection at resistance",
                        })
                    else:
                        rejections.append({
                            "type": "Pin Bar (Bullish)",
                            "signal": "BULLISH",
                            "price": l,
                            "bar_idx": i,
                            "strength": "High wick rejection at support",
                        })
            
            # HAMMER/INVERTED HAMMER: At swing low/high
            if body_ratio < 0.4:
                if upper_wick < lower_wick and c > o:
                    rejections.append({
                        "type": "Hammer (Bullish)",
                        "signal": "BULLISH",
                        "price": l,
                        "bar_idx": i,
                        "strength": "Rejection at lows with close on top half",
                    })
                elif lower_wick < upper_wick and c < o:
                    rejections.append({
                        "type": "Inverted Hammer (Bearish)",
                        "signal": "BEARISH",
                        "price": h,
                        "bar_idx": i,
                        "strength": "Rejection at highs with close on bottom half",
                    })
            
            # ENGULFING: Current bar engulfs previous bar
            if i > 0:
                p_o, p_h, p_l, p_c_val = float(prev["Open"]), float(prev["High"]), float(prev["Low"]), float(prev["Close"])
                
                if o < p_l and c > p_h and c > o:
                    rejections.append({
                        "type": "Bullish Engulfing",
                        "signal": "BULLISH",
                        "price": c,
                        "bar_idx": i,
                        "strength": "Current candle completely engulfs prior bearish candle",
                    })
                elif o > p_h and c < p_l and c < o:
                    rejections.append({
                        "type": "Bearish Engulfing",
                        "signal": "BEARISH",
                        "price": c,
                        "bar_idx": i,
                        "strength": "Current candle completely engulfs prior bullish candle",
                    })
    
    except Exception as e:
        pass
    
    return {"patterns": rejections, "count": len(rejections)}


# ══════════════════════════════════════════════════════════════════════════════
# POSITION MANAGEMENT & PARTIAL CLOSE TRACKING
# ══════════════════════════════════════════════════════════════════════════════
def calculate_position_management(current_price: float, entry_price: float, 
                                  stop_loss: float, direction: str = "long") -> dict:
    """
    Track position P&L and identify partial close thresholds.
    Returns alerts for 40pips (break-even move), 80pips (close 35%), 100pips (close more).
    """
    if direction.lower() == "long":
        pips_gain = (current_price - entry_price) * 10000
    else:  # short
        pips_gain = (entry_price - current_price) * 10000
    
    alerts = []
    partial_closes = []
    
    # Break-even alert at 40-50 pips
    if 40 <= pips_gain < 50:
        alerts.append({
            "level": "40-50 pips",
            "action": "MOVE STOP TO BREAK-EVEN",
            "description": "Position at break-even threshold. Move stop immediately to lock in zero loss.",
        })
    
    # First partial close at 80 pips
    if pips_gain >= 80:
        partial_closes.append({
            "threshold": "80 pips",
            "pct_close": 35,
            "action": "Close 35% of position at 80 pips target",
            "pips": pips_gain,
        })
    
    # Second partial close at 100+ pips
    if pips_gain >= 100:
        partial_closes.append({
            "threshold": "100 pips",
            "pct_close": 35,
            "action": "Close another 35% at 100 pips",
            "pips": pips_gain,
        })
    
    return {
        "current_pips": pips_gain,
        "break_even_distance": 40 - pips_gain if pips_gain < 40 else 0,
        "alerts": alerts,
        "partial_closes": partial_closes,
        "position_status": "AT TARGET" if pips_gain >= 80 else ("NEAR BREAKEVEN" if pips_gain >= 30 else "IN RISK"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# POST-NEWS PULLBACK ENTRY DETECTION
# ══════════════════════════════════════════════════════════════════════════════
def detect_news_pullback_entry(df: pd.DataFrame, news_items: list, 
                               cal_events: list, demand_zones: list) -> dict:
    """
    Detect the sequence: high-impact news → spike → pullback into demand zone → entry signal.
    Returns entry opportunities with confluence confirmation.
    """
    entries = []
    
    if df.empty or len(df) < 20:
        return {"pullback_entries": entries, "count": 0}
    
    try:
        # Find recent high-impact news (last 24 hours)
        now = datetime.utcnow()
        recent_news = [n for n in news_items if (now - n["dt"]).total_seconds() < 86400 and n.get("signal") in ("BULL", "BEAR")]
        recent_cal = [e for e in cal_events if (now - e["dt"]).total_seconds() < 86400 and e.get("impact") == "High"]
        
        if not recent_news and not recent_cal:
            return {"pullback_entries": entries, "count": 0}
        
        # Look for spike (large body) followed by pullback (rejection)
        for i in range(len(df) - 3, len(df)):
            if i < 3:
                continue
            
            spike_bar = df.iloc[i - 2]
            pullback_bar = df.iloc[i - 1]
            current_bar = df.iloc[i]
            
            spike_range = float(spike_bar["High"]) - float(spike_bar["Low"])
            pullback_range = float(pullback_bar["High"]) - float(pullback_bar["Low"])
            
            # Spike is unusually large (2x normal volatility)
            if pullback_range > 0 and spike_range > 2 * pullback_range:
                spike_body = abs(float(spike_bar["Close"]) - float(spike_bar["Open"]))
                spike_ratio = spike_body / spike_range
                
                # If spike body is >60%, it's a real move with pullback possible
                if spike_ratio > 0.6:
                    pullback_low = float(pullback_bar["Low"])
                    
                    # Check if pullback low is near demand zone
                    for zone in demand_zones:
                        zone_price = zone if isinstance(zone, float) else zone.get("price", 0)
                        if abs(pullback_low - zone_price) < 0.0010:  # Within 10 pips
                            entries.append({
                                "type": "Post-News Pullback",
                                "signal": "BULLISH" if float(spike_bar["Close"]) > float(spike_bar["Open"]) else "BEARISH",
                                "entry_zone": pullback_low,
                                "spike_time": spike_bar.get("dt", ""),
                                "pullback_time": pullback_bar.get("dt", ""),
                                "confluence": "News event + spike + pullback + demand zone align",
                                "strength": "HIGH CONFIDENCE",
                            })
    
    except Exception as e:
        pass
    
    return {"pullback_entries": entries, "count": len(entries)}


# ══════════════════════════════════════════════════════════════════════════════
# EARLY EXIT RULE DETECTION (4H CANDLE CLOSES AGAINST POSITION)
# ══════════════════════════════════════════════════════════════════════════════
def detect_early_exit_signals(df_1h: pd.DataFrame, df_4h: pd.DataFrame, 
                             entry_price: float, direction: str = "long") -> dict:
    """
    Monitor if a 4H candle closes strongly against the position before 40 pips profit.
    Returns exit signals when position should be closed for discretionary reasons.
    """
    exit_signals = []
    
    try:
        if df_4h.empty or len(df_4h) < 2:
            return {"exit_signals": exit_signals, "count": 0}
        
        current_4h = df_4h.iloc[-1]
        prev_4h = df_4h.iloc[-2]
        
        current_price = float(df_1h["Close"].iloc[-1]) if not df_1h.empty else 0
        p_gain = (current_price - entry_price) * 10000 if direction.lower() == "long" else (entry_price - current_price) * 10000
        
        # Check if we're below 40 pips profit
        if p_gain < 40:
            current_4h_close = float(current_4h["Close"])
            current_4h_open = float(current_4h["Open"])
            prev_4h_close = float(prev_4h["Close"])
            
            # For LONG position: check if 4H closes below entry or shows strong rejection
            if direction.lower() == "long":
                if current_4h_close < entry_price and current_4h_close < current_4h_open:
                    exit_signals.append({
                        "type": "Early Exit - 4H Close Against",
                        "severity": "HIGH",
                        "reason": f"4H candle closed BELOW entry price ({current_4h_close:.5f} < {entry_price:.5f}) with bearish bar",
                        "action": "EXIT POSITION immediately - discretionary rule triggered",
                        "pips_at_exit": p_gain,
                    })
                elif (current_4h_open - current_4h_close) > (entry_price - current_price) * 2:
                    exit_signals.append({
                        "type": "Early Exit - Strong 4H Rejection",
                        "severity": "MEDIUM",
                        "reason": "4H candle shows strong bearish close against entry before 40 pips",
                        "action": "Consider exiting - setup invalidated",
                        "pips_at_exit": p_gain,
                    })
            
            # For SHORT position: similar logic inverted
            else:
                if current_4h_close > entry_price and current_4h_close > current_4h_open:
                    exit_signals.append({
                        "type": "Early Exit - 4H Close Against",
                        "severity": "HIGH",
                        "reason": f"4H candle closed ABOVE entry price ({current_4h_close:.5f} > {entry_price:.5f}) with bullish bar",
                        "action": "EXIT POSITION immediately - discretionary rule triggered",
                        "pips_at_exit": p_gain,
                    })
                elif (current_4h_close - current_4h_open) > (current_price - entry_price) * 2:
                    exit_signals.append({
                        "type": "Early Exit - Strong 4H Rejection",
                        "severity": "MEDIUM",
                        "reason": "4H candle shows strong bullish close against entry before 40 pips",
                        "action": "Consider exiting - setup invalidated",
                        "pips_at_exit": p_gain,
                    })
    
    except Exception as e:
        pass
    
    return {"exit_signals": exit_signals, "count": len(exit_signals)}


# ══════════════════════════════════════════════════════════════════════════════
# "DO NOT ENTER BEFORE NEWS" WARNING SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
def check_news_proximity_warning(cal_events: list, current_price: float, 
                                 threshold_hours: int = 2) -> dict:
    """
    Alert if a high-impact event is within threshold_hours AND position is not at break-even.
    Returns active warnings with countdown timer.
    """
    warnings = []
    
    try:
        now = datetime.utcnow()
        
        for event in cal_events:
            event_time = event.get("dt")
            if not event_time:
                continue
            
            time_until = (event_time - now).total_seconds() / 3600
            impact = event.get("impact", "").lower()
            
            # Only warn for High impact events within threshold
            if impact == "high" and 0 < time_until < threshold_hours:
                warnings.append({
                    "event": event.get("title", ""),
                    "currency": event.get("currency", ""),
                    "impact": "HIGH",
                    "time_until_hours": round(time_until, 1),
                    "status": "🚫 DO NOT ENTER" if time_until < threshold_hours else "⚠️ APPROACHING",
                    "detail": f"High-impact {event.get('currency')} event in {round(time_until, 1)} hours - NO NEW ENTRIES",
                })
            
            # Also flag if event just passed (within last 2 hours) and high impact
            elif impact == "high" and -threshold_hours < time_until <= 0:
                warnings.append({
                    "event": event.get("title", ""),
                    "currency": event.get("currency", ""),
                    "impact": "HIGH",
                    "time_until_hours": round(time_until, 1),
                    "status": "⚠️ JUST RELEASED",
                    "detail": f"High-impact event released {round(-time_until, 1)} hours ago - CAUTION on new positions",
                })
    
    except Exception as e:
        pass
    
    return {
        "active_warnings": warnings,
        "warning_count": len(warnings),
        "can_trade": len(warnings) == 0,
    }


# ══════════════════════════════════════════════════════════════════════════════
# DYNAMIC TRAILING STOP CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
def calculate_dynamic_trailing_stop(df_4h: pd.DataFrame, current_price: float, 
                                    direction: str = "long", lookback: int = 20) -> dict:
    """
    Calculate a dynamic trailing stop at ATR × 2.0 below the most recent swing low (long).
    For shorts, it's above the most recent swing high.
    """
    trailing_data = {}
    
    try:
        if df_4h.empty or len(df_4h) < lookback:
            return {"error": "Insufficient 4H data for trailing stop calculation"}
        
        recent_df = df_4h.iloc[-lookback:]
        
        if direction.lower() == "long":
            # Find swing low (lowest point before current high)
            recent_lows = recent_df["Low"].astype(float)
            swing_low = float(recent_lows.min())
            
            # ATR on 4H
            atr_4h = atr(df_4h, 14)
            atr_val = float(atr_4h.iloc[-1]) if not pd.isna(atr_4h.iloc[-1]) else 0
            
            # Trailing stop = swing low - (ATR × 2.0)
            trailing_stop = swing_low - (atr_val * 2.0)
            
            stop_distance_pips = (current_price - trailing_stop) * 10000
            
            trailing_data = {
                "type": "Trailing Stop (LONG)",
                "swing_low": swing_low,
                "atr_multiplier": 2.0,
                "atr_value": atr_val,
                "trailing_stop": trailing_stop,
                "stop_distance_pips": stop_distance_pips,
                "moving_target": f"Trail below 4H swing low ({swing_low:.5f}) by ATR × 2.0",
                "status": "ACTIVE" if current_price > trailing_stop else "STOP HIT",
            }
        
        else:  # SHORT
            recent_highs = recent_df["High"].astype(float)
            swing_high = float(recent_highs.max())
            
            atr_4h = atr(df_4h, 14)
            atr_val = float(atr_4h.iloc[-1]) if not pd.isna(atr_4h.iloc[-1]) else 0
            
            trailing_stop = swing_high + (atr_val * 2.0)
            
            stop_distance_pips = (trailing_stop - current_price) * 10000
            
            trailing_data = {
                "type": "Trailing Stop (SHORT)",
                "swing_high": swing_high,
                "atr_multiplier": 2.0,
                "atr_value": atr_val,
                "trailing_stop": trailing_stop,
                "stop_distance_pips": stop_distance_pips,
                "moving_target": f"Trail above 4H swing high ({swing_high:.5f}) by ATR × 2.0",
                "status": "ACTIVE" if current_price < trailing_stop else "STOP HIT",
            }
    
    except Exception as e:
        return {"error": f"Trailing stop calculation failed: {str(e)}"}
    
    return trailing_data


# ══════════════════════════════════════════════════════════════════════════════
# 3-TIMEFRAME STACK ANALYSIS (AUTO-PULL DAILY / 4H / 1H)
# ══════════════════════════════════════════════════════════════════════════════
def analyze_timeframe_stack(eurusd_1h: pd.DataFrame, eurusd_4h: pd.DataFrame, 
                            eurusd_daily: pd.DataFrame, dxy_df_dict: dict) -> dict:
    """
    Analyze the 3-timeframe stack (Daily=map, 4H=signal, 1H=entry) simultaneously.
    Returns consolidated analysis showing where we are in the setup across all timeframes.
    """
    stack_analysis = {
        "daily_map": {},
        "h4_signal": {},
        "h1_entry": {},
        "overall_confluence": 0,
        "setup_status": "NO SETUP",
    }
    
    try:
        # ── DAILY (MAP) - Identify overall trend direction
        if not eurusd_daily.empty and len(eurusd_daily) > 20:
            daily_adx, daily_plus_di, daily_minus_di = adx(eurusd_daily, 14)
            daily_adx_val = float(daily_adx.iloc[-1]) if not pd.isna(daily_adx.iloc[-1]) else 0
            daily_plus = float(daily_plus_di.iloc[-1]) if not pd.isna(daily_plus_di.iloc[-1]) else 0
            daily_minus = float(daily_minus_di.iloc[-1]) if not pd.isna(daily_minus_di.iloc[-1]) else 0
            daily_close = float(eurusd_daily["Close"].iloc[-1])
            daily_open = float(eurusd_daily["Open"].iloc[-1])
            daily_high = float(eurusd_daily["High"].iloc[-1])
            daily_low = float(eurusd_daily["Low"].iloc[-1])
            
            if daily_plus > daily_minus and daily_adx_val > 20:
                daily_trend = "UPTREND (Bullish Map)"
            elif daily_minus > daily_plus and daily_adx_val > 20:
                daily_trend = "DOWNTREND (Bearish Map)"
            else:
                daily_trend = "RANGING (No clear direction)"
            
            stack_analysis["daily_map"] = {
                "trend": daily_trend,
                "adx": daily_adx_val,
                "plus_di": daily_plus,
                "minus_di": daily_minus,
                "candle_type": "Bullish" if daily_close > daily_open else "Bearish",
                "range_pips": (daily_high - daily_low) * 10000,
                "role": "Sets overall market direction - highest priority",
            }
        
        # ── 4H (SIGNAL) - Identify setup formation and potential entry zone
        if not eurusd_4h.empty and len(eurusd_4h) > 20:
            h4_adx, h4_plus_di, h4_minus_di = adx(eurusd_4h, 14)
            h4_adx_val = float(h4_adx.iloc[-1]) if not pd.isna(h4_adx.iloc[-1]) else 0
            h4_plus = float(h4_plus_di.iloc[-1]) if not pd.isna(h4_plus_di.iloc[-1]) else 0
            h4_minus = float(h4_minus_di.iloc[-1]) if not pd.isna(h4_minus_di.iloc[-1]) else 0
            h4_upper, h4_lower, _ = donchian_channel(eurusd_4h, 20)
            h4_upper_val = float(h4_upper.iloc[-1]) if not pd.isna(h4_upper.iloc[-1]) else 0
            h4_lower_val = float(h4_lower.iloc[-1]) if not pd.isna(h4_lower.iloc[-1]) else 0
            h4_current = float(eurusd_4h["Close"].iloc[-1])
            recent_h4_low = float(eurusd_4h["Low"].iloc[-20:].min())
            recent_h4_high = float(eurusd_4h["High"].iloc[-20:].max())
            
            if h4_plus > h4_minus and h4_adx_val > 20:
                h4_signal = "BULLISH SETUP - ADX > 20, uptrend structure"
            elif h4_minus > h4_plus and h4_adx_val > 20:
                h4_signal = "BEARISH SETUP - ADX > 20, downtrend structure"
            else:
                h4_signal = "CONSOLIDATING - Waiting for ADX > 20"
            
            stack_analysis["h4_signal"] = {
                "signal": h4_signal,
                "adx": h4_adx_val,
                "plus_di": h4_plus,
                "minus_di": h4_minus,
                "donchian_upper": h4_upper_val,
                "donchian_lower": h4_lower_val,
                "setup_zone": f"Between {recent_h4_low:.5f} - {recent_h4_high:.5f}",
                "role": "Defines setup formation and entry zone",
            }
        
        # ── 1H (ENTRY) - Identify exact entry trigger
        if not eurusd_1h.empty and len(eurusd_1h) > 20:
            h1_upper, h1_lower, _ = donchian_channel(eurusd_1h, 20)
            h1_upper_val = float(h1_upper.iloc[-1]) if not pd.isna(h1_upper.iloc[-1]) else 0
            h1_lower_val = float(h1_lower.iloc[-1]) if not pd.isna(h1_lower.iloc[-1]) else 0
            h1_current = float(eurusd_1h["Close"].iloc[-1])
            h1_high_5 = float(eurusd_1h["High"].iloc[-5:].max())
            h1_low_5 = float(eurusd_1h["Low"].iloc[-5:].min())
            
            # Check for rejection pattern
            rejections = detect_rejection_candles(eurusd_1h, 5)
            
            if h1_current > h1_upper_val:
                entry_trigger = "🟢 DONCHIAN BREAKOUT - Ready to Buy"
            elif h1_current < h1_lower_val:
                entry_trigger = "🔴 DONCHIAN BREAKOUT - Ready to Sell"
            elif rejections["count"] > 0 and rejections["patterns"]:
                entry_trigger = f"⚡ REJECTION PATTERN ({rejections['patterns'][-1]['type']}) - Entry Signal"
            else:
                entry_trigger = "⚪ Waiting for breakout or rejection signal"
            
            stack_analysis["h1_entry"] = {
                "trigger": entry_trigger,
                "donchian_upper": h1_upper_val,
                "donchian_lower": h1_lower_val,
                "recent_high_5bar": h1_high_5,
                "recent_low_5bar": h1_low_5,
                "rejection_patterns": rejections["patterns"],
                "role": "Provides exact timing and entry point",
            }
        
        # ── Calculate overall confluence score
        confluence = 0
        if stack_analysis["daily_map"] and "TREND" in stack_analysis["daily_map"].get("trend", ""):
            confluence += 1
        if stack_analysis["h4_signal"] and stack_analysis["h4_signal"].get("adx", 0) > 20:
            confluence += 1
        if stack_analysis["h1_entry"] and "BREAKOUT" in stack_analysis["h1_entry"].get("trigger", ""):
            confluence += 2
        
        stack_analysis["overall_confluence"] = confluence
        if confluence >= 3:
            stack_analysis["setup_status"] = "✅ SETUP READY - All timeframes aligned"
        elif confluence >= 2:
            stack_analysis["setup_status"] = "🟡 PARTIAL - Multiple timeframes aligned"
        else:
            stack_analysis["setup_status"] = "🔴 NO SETUP - Insufficient confluence"
    
    except Exception as e:
        stack_analysis["error"] = str(e)
    
    return stack_analysis


# ══════════════════════════════════════════════════════════════════════════════
# RISK MANAGEMENT & STOP LOSS CALCULATIONS
# ══════════════════════════════════════════════════════════════════════════════
def calculate_risk_metrics(df: pd.DataFrame, setup_type: str = "bullish") -> dict:
    """
    Calculate ATR-based stop loss, profit targets, and risk/reward ratio.
    setup_type: 'bullish', 'bearish'
    """
    try:
        if df.empty or len(df) < 15:
            return {"error": "Insufficient data"}
        
        atr_val = atr(df, 14)
        current_atr = float(atr_val.iloc[-1]) if not pd.isna(atr_val.iloc[-1]) else 0
        current_price = float(df["Close"].iloc[-1])
        
        # Convert ATR to pips (EURUSD is 4 decimals, 1 pip = 0.0001)
        atr_pips = current_atr * 10000
        
        # Find demand (support) and supply (resistance) zones
        lookback = min(50, len(df) - 1)
        recent_lows = df["Low"].iloc[-lookback:-1]
        recent_highs = df["High"].iloc[-lookback:-1]
        
        support = float(recent_lows.min())
        resistance = float(recent_highs.max())
        
        if setup_type.lower() == "bullish":
            # BUY setup: Stop below support + ATR buffer
            stop_loss = support - (current_atr * 1.0)
            min_target_1 = current_price + (current_atr * 4)  # 40-50 pips target area
            min_target_2 = current_price + (current_atr * 8)  # 80-120 pips
            extended_target = current_price + (current_atr * 12)  # Extended target
            
            stop_distance_pips = (current_price - stop_loss) * 10000
            target1_pips = (min_target_1 - current_price) * 10000
            target2_pips = (min_target_2 - current_price) * 10000
            
        else:  # bearish
            # SELL setup: Stop above resistance + ATR buffer
            stop_loss = resistance + (current_atr * 1.0)
            min_target_1 = current_price - (current_atr * 4)
            min_target_2 = current_price - (current_atr * 8)
            extended_target = current_price - (current_atr * 12)
            
            stop_distance_pips = (stop_loss - current_price) * 10000
            target1_pips = (current_price - min_target_1) * 10000
            target2_pips = (current_price - min_target_2) * 10000
        
        # Risk/Reward calculations
        rr_ratio_1 = target1_pips / stop_distance_pips if stop_distance_pips > 0 else 0
        rr_ratio_2 = target2_pips / stop_distance_pips if stop_distance_pips > 0 else 0
        
        return {
            "atr_pips": atr_pips,
            "current_price": current_price,
            "current_atr": current_atr,
            "stop_loss": stop_loss,
            "stop_distance_pips": stop_distance_pips,
            "target_40_50pip": min_target_1,
            "target_80_120pip": min_target_2,
            "extended_target": extended_target,
            "target1_pips": target1_pips,
            "target2_pips": target2_pips,
            "rr_ratio_min": rr_ratio_1,
            "rr_ratio_extended": rr_ratio_2,
            "support": support,
            "resistance": resistance,
            "setup_type": setup_type,
        }
    except Exception as e:
        return {"error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# COMPREHENSIVE SIGNAL AGGREGATOR
# ══════════════════════════════════════════════════════════════════════════════
def aggregate_all_signals(eurusd_df: pd.DataFrame, dxy_df: pd.DataFrame, dxy_analysis: dict, 
                          news_items: list, cal_events: list, confluence_data: dict) -> dict:
    """
    Aggregates ALL signals with DXY as a leading indicator for EUR/USD.
    Returns consolidated signals and FINAL bullish/bearish verdict.
    """
    signals = {
        "eurusd_indicators": [],
        "eurusd_confluence": [],
        "news_signals": [],
        "calendar_signals": [],
        "bullish_count": 0,
        "bearish_count": 0,
        "neutral_count": 0,
        "overall_verdict": "NEUTRAL",
        "confidence": 0,
        "signal_count": 0,
    }
    
    try:
        # ──────────────────────────────────────────────────────────────
        # EURUSD INDICATOR SIGNALS
        # ──────────────────────────────────────────────────────────────
        if not eurusd_df.empty and len(eurusd_df) > 20:
            eurusd_adx, eurusd_plus_di, eurusd_minus_di = adx(eurusd_df, 14)
            eurusd_adx_val = float(eurusd_adx.iloc[-1]) if not pd.isna(eurusd_adx.iloc[-1]) else 0
            eurusd_plus_di_val = float(eurusd_plus_di.iloc[-1]) if not pd.isna(eurusd_plus_di.iloc[-1]) else 0
            eurusd_minus_di_val = float(eurusd_minus_di.iloc[-1]) if not pd.isna(eurusd_minus_di.iloc[-1]) else 0
            
            # ADX Signal
            if eurusd_adx_val > 25:
                if eurusd_plus_di_val > eurusd_minus_di_val:
                    signals["eurusd_indicators"].append({
                        "indicator": "ADX",
                        "signal": "BULLISH",
                        "value": f"{eurusd_adx_val:.1f}",
                        "detail": "Strong uptrend (ADX > 25, +DI > -DI)"
                    })
                else:
                    signals["eurusd_indicators"].append({
                        "indicator": "ADX",
                        "signal": "BEARISH",
                        "value": f"{eurusd_adx_val:.1f}",
                        "detail": "Strong downtrend (ADX > 25, -DI > +DI)"
                    })
            elif 20 < eurusd_adx_val <= 25:
                if eurusd_plus_di_val > eurusd_minus_di_val:
                    signals["eurusd_indicators"].append({
                        "indicator": "ADX",
                        "signal": "BULLISH",
                        "value": f"{eurusd_adx_val:.1f}",
                        "detail": "Moderate uptrend (ADX 20-25)"
                    })
                else:
                    signals["eurusd_indicators"].append({
                        "indicator": "ADX",
                        "signal": "BEARISH",
                        "value": f"{eurusd_adx_val:.1f}",
                        "detail": "Moderate downtrend (ADX 20-25)"
                    })
            else:
                signals["eurusd_indicators"].append({
                    "indicator": "ADX",
                    "signal": "NEUTRAL",
                    "value": f"{eurusd_adx_val:.1f}",
                    "detail": "No clear trend (ADX < 20)"
                })
            
            # RSI Signal
            rsi_val = rsi(eurusd_df["Close"], 14)
            rsi_current = float(rsi_val.iloc[-1]) if not pd.isna(rsi_val.iloc[-1]) else 50
            if rsi_current > 70:
                signals["eurusd_indicators"].append({
                    "indicator": "RSI(14)",
                    "signal": "BEARISH",
                    "value": f"{rsi_current:.1f}",
                    "detail": "Overbought (RSI > 70)"
                })
            elif rsi_current < 30:
                signals["eurusd_indicators"].append({
                    "indicator": "RSI(14)",
                    "signal": "BULLISH",
                    "value": f"{rsi_current:.1f}",
                    "detail": "Oversold (RSI < 30)"
                })
            else:
                signals["eurusd_indicators"].append({
                    "indicator": "RSI(14)",
                    "signal": "NEUTRAL",
                    "value": f"{rsi_current:.1f}",
                    "detail": "Neutral zone (30-70)"
                })
            
            # Donchian Channel Signal
            upper_band, lower_band, _ = donchian_channel(eurusd_df, 20)
            current_price = float(eurusd_df["Close"].iloc[-1])
            above_upper = current_price > float(upper_band.iloc[-2])
            below_lower = current_price < float(lower_band.iloc[-2])
            
            if above_upper:
                signals["eurusd_indicators"].append({
                    "indicator": "Donchian(20)",
                    "signal": "BULLISH",
                    "value": f"{current_price:.5f}",
                    "detail": "Price above 20-period upper band"
                })
            elif below_lower:
                signals["eurusd_indicators"].append({
                    "indicator": "Donchian(20)",
                    "signal": "BEARISH",
                    "value": f"{current_price:.5f}",
                    "detail": "Price below 20-period lower band"
                })
            else:
                signals["eurusd_indicators"].append({
                    "indicator": "Donchian(20)",
                    "signal": "NEUTRAL",
                    "value": f"{current_price:.5f}",
                    "detail": "Price inside Donchian band"
                })
            
            # EMA Crossover Signal (20/50)
            ema20 = ema(eurusd_df["Close"].astype(float), 20)
            ema50 = ema(eurusd_df["Close"].astype(float), 50)
            ema20_val = float(ema20.iloc[-1]) if not pd.isna(ema20.iloc[-1]) else 0
            ema50_val = float(ema50.iloc[-1]) if not pd.isna(ema50.iloc[-1]) else 0
            
            if ema20_val > ema50_val and current_price > ema20_val:
                signals["eurusd_indicators"].append({
                    "indicator": "EMA(20/50)",
                    "signal": "BULLISH",
                    "value": f"P:{current_price:.5f}",
                    "detail": "Price > EMA20 > EMA50"
                })
            elif ema20_val < ema50_val and current_price < ema20_val:
                signals["eurusd_indicators"].append({
                    "indicator": "EMA(20/50)",
                    "signal": "BEARISH",
                    "value": f"P:{current_price:.5f}",
                    "detail": "Price < EMA20 < EMA50"
                })
            else:
                signals["eurusd_indicators"].append({
                    "indicator": "EMA(20/50)",
                    "signal": "NEUTRAL",
                    "value": f"P:{current_price:.5f}",
                    "detail": "Mixed signal"
                })
        
        # ──────────────────────────────────────────────────────────────
        # DXY AS LEADING INDICATOR FOR EUR/USD
        # ──────────────────────────────────────────────────────────────
        if not dxy_df.empty and len(dxy_df) > 20:
            dxy_adx, dxy_plus_di, dxy_minus_di = adx(dxy_df, 14)
            dxy_adx_val = float(dxy_adx.iloc[-1]) if not pd.isna(dxy_adx.iloc[-1]) else 0
            dxy_plus_di_val = float(dxy_plus_di.iloc[-1]) if not pd.isna(dxy_plus_di.iloc[-1]) else 0
            dxy_minus_di_val = float(dxy_minus_di.iloc[-1]) if not pd.isna(dxy_minus_di.iloc[-1]) else 0
            
            # DXY ADX Signal (inverted for EURUSD)
            if dxy_adx_val > 25:
                if dxy_plus_di_val > dxy_minus_di_val:
                    signals["eurusd_indicators"].append({
                        "indicator": "DXY ADX (Leading)",
                        "signal": "BEARISH",
                        "value": f"{dxy_adx_val:.1f}",
                        "detail": "DXY strong uptrend → USD strength → EUR/USD downside"
                    })
                else:
                    signals["eurusd_indicators"].append({
                        "indicator": "DXY ADX (Leading)",
                        "signal": "BULLISH",
                        "value": f"{dxy_adx_val:.1f}",
                        "detail": "DXY strong downtrend → USD weakness → EUR/USD upside"
                    })
            elif 20 < dxy_adx_val <= 25:
                if dxy_plus_di_val > dxy_minus_di_val:
                    signals["eurusd_indicators"].append({
                        "indicator": "DXY ADX (Leading)",
                        "signal": "BEARISH",
                        "value": f"{dxy_adx_val:.1f}",
                        "detail": "DXY moderate uptrend → moderate bearish bias"
                    })
                else:
                    signals["eurusd_indicators"].append({
                        "indicator": "DXY ADX (Leading)",
                        "signal": "BULLISH",
                        "value": f"{dxy_adx_val:.1f}",
                        "detail": "DXY moderate downtrend → moderate bullish bias"
                    })
            else:
                signals["eurusd_indicators"].append({
                    "indicator": "DXY ADX (Leading)",
                    "signal": "NEUTRAL",
                    "value": f"{dxy_adx_val:.1f}",
                    "detail": "DXY no clear trend (ADX < 20)"
                })
            
            # DXY Trend Signal (main driver)
            dxy_trend = dxy_analysis.get("trend", "NEUTRAL")
            if dxy_trend == "UPTREND":
                signals["eurusd_indicators"].append({
                    "indicator": "DXY Trend (Primary)",
                    "signal": "BEARISH",
                    "value": dxy_trend,
                    "detail": "Dollar Index uptrend → sell EUR/USD"
                })
            elif dxy_trend == "DOWNTREND":
                signals["eurusd_indicators"].append({
                    "indicator": "DXY Trend (Primary)",
                    "signal": "BULLISH",
                    "value": dxy_trend,
                    "detail": "Dollar Index downtrend → buy EUR/USD"
                })
            else:
                signals["eurusd_indicators"].append({
                    "indicator": "DXY Trend (Primary)",
                    "signal": "NEUTRAL",
                    "value": dxy_trend,
                    "detail": "Dollar Index neutral trend"
                })
        
        # ──────────────────────────────────────────────────────────────
        # CONFLUENCE FACTOR SIGNALS
        # ──────────────────────────────────────────────────────────────
        if confluence_data and "factors" in confluence_data:
            factors = confluence_data.get("factors", {})
            confluence_score = confluence_data.get("confluence_score", 0)
            
            for factor_num in [1, 3, 4, 6, 7]:  # Key factors for signaling
                if factor_num in factors and factors[factor_num]["met"]:
                    factor_name = factors[factor_num]["name"]
                    if factor_num == 1:  # DXY Trend
                        if dxy_analysis.get("trend") == "DOWNTREND":
                            signals["eurusd_confluence"].append({
                                "factor": f"F{factor_num}: {factor_name}",
                                "signal": "BULLISH",
                                "value": "✅",
                                "detail": factors[factor_num].get("detail", "")
                            })
                        else:
                            signals["eurusd_confluence"].append({
                                "factor": f"F{factor_num}: {factor_name}",
                                "signal": "BEARISH",
                                "value": "✅",
                                "detail": factors[factor_num].get("detail", "")
                            })
                    elif factor_num == 3:  # Market Structure
                        struct = factors[factor_num]["value"]
                        sig = "BULLISH" if struct == "Bullish" else ("BEARISH" if struct == "Bearish" else "NEUTRAL")
                        signals["eurusd_confluence"].append({
                            "factor": f"F{factor_num}: {factor_name}",
                            "signal": sig,
                            "value": struct,
                            "detail": factors[factor_num].get("detail", "")
                        })
                    else:
                        signals["eurusd_confluence"].append({
                            "factor": f"F{factor_num}: {factor_name}",
                            "signal": "✅ MET",
                            "value": factors[factor_num].get("value", ""),
                            "detail": factors[factor_num].get("detail", "")
                        })
            
            if confluence_score >= 5:
                signals["overall_bias"] = "SETUP READY"
            elif confluence_score >= 4:
                signals["overall_bias"] = "FORMING"
            else:
                signals["overall_bias"] = "WAITING"
        
        # ──────────────────────────────────────────────────────────────
        # NEWS SIGNALS
        # ──────────────────────────────────────────────────────────────
        cutoff = datetime.utcnow() - timedelta(hours=6)
        recent_news = [n for n in news_items if n["dt"] >= cutoff][:5]
        for news in recent_news:
            sig = news.get("signal", "")
            if sig:
                signals["news_signals"].append({
                    "time": news["dt"].strftime("%H:%M"),
                    "signal": "BULLISH" if sig == "BULL" else ("BEARISH" if sig == "BEAR" else "NEUTRAL"),
                    "title": news["title"][:50],
                    "source": news.get("source", "")[:20]
                })
        
        # ──────────────────────────────────────────────────────────────
        # CALENDAR EVENT SIGNALS
        # ──────────────────────────────────────────────────────────────
        now = datetime.utcnow()
        recent_events = [e for e in cal_events if now - timedelta(hours=2) <= e["dt"] <= now + timedelta(hours=2)]
        for event in recent_events:
            # Check if event beat or missed forecast
            if event.get("actual") and event.get("forecast"):
                try:
                    def parse_val(s):
                        s = re.sub(r"[^0-9.\-]", "", str(s))
                        return float(s) if s else None
                    
                    actual = parse_val(event["actual"])
                    forecast = parse_val(event["forecast"])
                    
                    if actual and forecast:
                        diff = (actual - forecast) / abs(forecast) * 100
                        ccy = event.get("currency", "")
                        
                        if ccy == "USD":
                            sig = "BEARISH" if diff > 5 else ("BULLISH" if diff < -5 else "NEUTRAL")
                        elif ccy == "EUR":
                            sig = "BULLISH" if diff > 5 else ("BEARISH" if diff < -5 else "NEUTRAL")
                        else:
                            sig = "NEUTRAL"
                        
                        signals["calendar_signals"].append({
                            "time": event["dt"].strftime("%H:%M"),
                            "currency": ccy,
                            "signal": sig,
                            "title": event["title"][:40],
                            "impact": event.get("impact", "Unknown")
                        })
                except:
                    pass
        
        # ──────────────────────────────────────────────────────────────
        # CALCULATE FINAL VERDICT - Count all signals
        # ──────────────────────────────────────────────────────────────
        all_signals_list = (signals["eurusd_indicators"] + signals["eurusd_confluence"] + 
                           signals["news_signals"] + signals["calendar_signals"])
        
        bullish_signals = [s for s in all_signals_list if s.get("signal") == "BULLISH"]
        bearish_signals = [s for s in all_signals_list if s.get("signal") == "BEARISH"]
        neutral_signals = [s for s in all_signals_list if s.get("signal") == "NEUTRAL"]
        
        signals["bullish_count"] = len(bullish_signals)
        signals["bearish_count"] = len(bearish_signals)
        signals["neutral_count"] = len(neutral_signals)
        signals["signal_count"] = len(all_signals_list)
        
        # Calculate confidence and final verdict
        if signals["signal_count"] > 0:
            bullish_pct = (signals["bullish_count"] / signals["signal_count"]) * 100
            bearish_pct = (signals["bearish_count"] / signals["signal_count"]) * 100
            
            # Determine verdict based on signal ratio
            if bullish_pct > 60:
                signals["overall_verdict"] = "BULLISH"
                signals["confidence"] = min(bullish_pct, 95)  # Cap at 95%
            elif bearish_pct > 60:
                signals["overall_verdict"] = "BEARISH"
                signals["confidence"] = min(bearish_pct, 95)
            elif bullish_pct > bearish_pct:
                signals["overall_verdict"] = "SLIGHTLY BULLISH"
                signals["confidence"] = bullish_pct
            elif bearish_pct > bullish_pct:
                signals["overall_verdict"] = "SLIGHTLY BEARISH"
                signals["confidence"] = bearish_pct
            else:
                signals["overall_verdict"] = "NEUTRAL"
                signals["confidence"] = 50
        else:
            signals["overall_verdict"] = "NO DATA"
            signals["confidence"] = 0
        
        return signals
    except Exception as e:
        signals["error"] = str(e)
        return signals


# Cached helper: compute a compact summary for a given timeframe
@st.cache_data(ttl=120)
def compute_tf_summary(tf_key: str, news_items: list, cal_events: list) -> dict:
    """Return a short summary (verdict + confidence) for the given TF key using cached fetchers."""
    try:
        # Fetch price and DXY for this timeframe (cached by get_price_data/get_dxy_data)
        eur = get_price_data(tf_key)
        dxy = get_dxy_data(tf_key)
        dxy_an = analyze_dxy(dxy) if dxy is not None and not dxy.empty else {}
        conf = evaluate_confluence_factors(eur, dxy, dxy_an, cal_events) if not eur.empty and not dxy.empty else {}
        agg = aggregate_all_signals(eur, dxy, dxy_an, news_items, cal_events, conf) if not eur.empty else {"overall_verdict":"NO DATA","confidence":0}
        return {
            "tf": tf_key,
            "verdict": agg.get("overall_verdict", "NO DATA"),
            "confidence": agg.get("confidence", 0),
            "bullish": agg.get("bullish_count", 0),
            "bearish": agg.get("bearish_count", 0),
            "neutral": agg.get("neutral_count", 0),
        }
    except Exception as e:
        return {"tf": tf_key, "verdict": "ERROR", "confidence": 0, "error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# BACKTESTING ENGINE
# ══════════════════════════════════════════════════════════════════════════════
def backtest_strategy(eurusd_df: pd.DataFrame, dxy_df: pd.DataFrame, dxy_analysis_func, 
                      confluence_func, lookback_days: int = 30) -> dict:
    """
    Backtests the confluence-based swing trading strategy.
    Returns trade history, stats, and equity curve.
    """
    if eurusd_df.empty or dxy_df.empty:
        return {"error": "Insufficient data for backtest"}
    
    try:
        trades = []
        equity = 1000  # Starting equity in units
        equity_curve = [equity]
        dates = [eurusd_df["dt"].iloc[0]]
        # Diagnostic traces collected per loop iteration
        diagnostics = []
        
        # Filter to lookback period
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        df_test = eurusd_df[eurusd_df["dt"] >= cutoff_date].reset_index(drop=True)
        dxy_test = dxy_df[dxy_df["dt"] >= cutoff_date].reset_index(drop=True)
        
        # Allow lower-frequency timeframes (daily/monthly) by using an adaptive minimum
        min_len_required = 12  # require at least ~12 candles for any sensible backtest
        if len(df_test) < min_len_required or len(dxy_test) < min_len_required:
            return {"error": f"Not enough data in {lookback_days} days (need >= {min_len_required} candles)"}
        
        in_trade = False
        entry_price = 0.0
        entry_type = None
        entry_idx = 0
        stop_loss = 0.0
        target1 = 0.0
        target2 = 0.0
        entry_date = None
        position_size = 1.0  # fraction of full position remaining
        partial1_done = False
        partial2_done = False
        break_even_set = False
        
        # Sliding window analysis - adaptive start index based on available data
        start_idx = min(50, max(10, int(len(df_test) * 0.2)))
        for i in range(start_idx, len(df_test)):
            current_date = df_test.iloc[i]["dt"]
            current_price = float(df_test.iloc[i]["Close"])
            high = float(df_test.iloc[i]["High"])
            low = float(df_test.iloc[i]["Low"])
            
            # Use timestamp-aligned DXY window (slice DXY up to current_date)
            try:
                dxy_window = dxy_test[dxy_test["dt"] <= current_date].tail(120).reset_index(drop=True)
            except Exception:
                dxy_window = dxy_test.tail(120).reset_index(drop=True)

            if len(dxy_window) < 20:
                continue
            
            # Evaluate confluence at this point in time
            window_eurusd = df_test.iloc[max(0,i-50):i+1]
            
            try:
                dxy_analysis_result = dxy_analysis_func(dxy_window)
                confluence_result = confluence_func(window_eurusd, dxy_window, dxy_analysis_result, [])
            except Exception:
                continue

            confluence_score = confluence_result.get("confluence_score", 0)

            # --- Diagnostic capture: record DXY ADX, trend, met factors, confluence
            try:
                dxy_adx_series, dxy_plus, dxy_minus = adx(dxy_window, 14)
                dxy_adx_val = float(dxy_adx_series.iloc[-1]) if not pd.isna(dxy_adx_series.iloc[-1]) else None
            except Exception:
                dxy_adx_val = None

            try:
                facs = confluence_result.get("factors", {})
                met_factors = [int(k) for k, v in facs.items() if isinstance(v, dict) and v.get("met")]
            except Exception:
                met_factors = []

            diagnostics.append({
                "dt": current_date,
                "confluence_score": confluence_score,
                "dxy_trend": dxy_analysis_result.get("trend"),
                "dxy_adx": dxy_adx_val,
                "met_factors": met_factors,
                "in_trade": in_trade,
            })
            
            # EXIT LOGIC
            if in_trade:
                # current pip P&L for full position
                if entry_type == "long":
                    current_pips = (current_price - entry_price) * 10000
                else:
                    current_pips = (entry_price - current_price) * 10000

                # Break-even rule: at 40 pips move SL to entry
                if not break_even_set and current_pips >= 40:
                    stop_loss = entry_price
                    break_even_set = True

                # Partial closes at 80 and 100 pips
                if not partial1_done and current_pips >= 80:
                    # close 35% of position at current_price
                    pnl_pips = current_pips * 0.35
                    trades.append({
                        "entry_date": entry_date,
                        "exit_date": current_date,
                        "entry_price": entry_price,
                        "exit_price": current_price,
                        "type": entry_type.upper(),
                        "pnl_pips": pnl_pips,
                        "status": "PARTIAL1",
                        "days": (current_date - entry_date).days
                    })
                    partial1_done = True
                    position_size -= 0.35
                    equity += pnl_pips / 1000  # scale to equity units
                    equity_curve.append(equity)
                    dates.append(current_date)

                if not partial2_done and current_pips >= 100:
                    pnl_pips = current_pips * 0.35
                    trades.append({
                        "entry_date": entry_date,
                        "exit_date": current_date,
                        "entry_price": entry_price,
                        "exit_price": current_price,
                        "type": entry_type.upper(),
                        "pnl_pips": pnl_pips,
                        "status": "PARTIAL2",
                        "days": (current_date - entry_date).days
                    })
                    partial2_done = True
                    position_size -= 0.35
                    equity += pnl_pips / 1000
                    equity_curve.append(equity)
                    dates.append(current_date)

                # Dynamic trailing stop based on 4H swing
                # build 4H window corresponding to current_date
                try:
                    # find matching index in eurusd_df to get time for 4h slicing
                    time_for_4h = df_test.iloc[i]["dt"]
                    # select 4H candles up to this point
                    df_4h_all = eurusd_df.resample("4H", on="dt").agg({"Open":"first","High":"max","Low":"min","Close":"last"}).dropna().reset_index()
                except Exception:
                    df_4h_all = pd.DataFrame()

                if not df_4h_all.empty:
                    trailing = calculate_dynamic_trailing_stop(df_4h_all, current_price, direction=("long" if entry_type=="long" else "short"))
                    if "trailing_stop" in trailing:
                        trailing_stop = trailing["trailing_stop"]
                        # For LONG, move stop up but never below previous stop
                        if entry_type == "long" and trailing_stop > stop_loss:
                            stop_loss = max(stop_loss, trailing_stop)
                        if entry_type == "short" and trailing_stop < stop_loss:
                            stop_loss = min(stop_loss, trailing_stop)

                # Early exit discretionary rule: 4H candle close against position before 40 pips
                try:
                    # build a 4H dataframe slice
                    df_4h_slice = eurusd_df.resample("4H", on="dt").agg({"Open":"first","High":"max","Low":"min","Close":"last"}).dropna().reset_index()
                    early = detect_early_exit_signals(df_test.iloc[max(0,i-24):i+1], df_4h_slice, entry_price, direction=("long" if entry_type=="long" else "short"))
                    if early.get("count",0) > 0:
                        # force exit at market
                        pnl_pips = current_pips * position_size
                        trades.append({
                            "entry_date": entry_date,
                            "exit_date": current_date,
                            "entry_price": entry_price,
                            "exit_price": current_price,
                            "type": entry_type.upper(),
                            "pnl_pips": pnl_pips,
                            "status": "EARLY_EXIT",
                            "days": (current_date - entry_date).days
                        })
                        in_trade = False
                        position_size = 1.0
                        partial1_done = partial2_done = break_even_set = False
                        equity += pnl_pips / 1000
                        equity_curve.append(equity)
                        dates.append(current_date)
                        continue
                except Exception:
                    pass

                # Check stop hit after adjustments
                if entry_type == "long" and low <= stop_loss:
                    pnl_pips = (stop_loss - entry_price) * position_size * 10000
                    trades.append({
                        "entry_date": entry_date,
                        "exit_date": current_date,
                        "entry_price": entry_price,
                        "exit_price": stop_loss,
                        "type": "LONG",
                        "pnl_pips": pnl_pips,
                        "status": "SL",
                        "days": (current_date - entry_date).days
                    })
                    in_trade = False
                    position_size = 1.0
                    partial1_done = partial2_done = break_even_set = False
                    equity += pnl_pips / 1000
                    equity_curve.append(equity)
                    dates.append(current_date)
                    continue

                if entry_type == "short" and high >= stop_loss:
                    pnl_pips = (entry_price - stop_loss) * position_size * 10000
                    trades.append({
                        "entry_date": entry_date,
                        "exit_date": current_date,
                        "entry_price": entry_price,
                        "exit_price": stop_loss,
                        "type": "SHORT",
                        "pnl_pips": pnl_pips,
                        "status": "SL",
                        "days": (current_date - entry_date).days
                    })
                    in_trade = False
                    position_size = 1.0
                    partial1_done = partial2_done = break_even_set = False
                    equity += pnl_pips / 1000
                    equity_curve.append(equity)
                    dates.append(current_date)
                    continue

                # Check if target1 reached to close remaining (full) position
                if entry_type == "long" and high >= target1:
                    pnl_pips = (target1 - entry_price) * position_size * 10000
                    trades.append({
                        "entry_date": entry_date,
                        "exit_date": current_date,
                        "entry_price": entry_price,
                        "exit_price": target1,
                        "type": "LONG",
                        "pnl_pips": pnl_pips,
                        "status": "TP",
                        "days": (current_date - entry_date).days
                    })
                    in_trade = False
                    position_size = 1.0
                    partial1_done = partial2_done = break_even_set = False
                    equity += pnl_pips / 1000
                    equity_curve.append(equity)
                    dates.append(current_date)
                    continue

                if entry_type == "short" and low <= target1:
                    pnl_pips = (entry_price - target1) * position_size * 10000
                    trades.append({
                        "entry_date": entry_date,
                        "exit_date": current_date,
                        "entry_price": entry_price,
                        "exit_price": target1,
                        "type": "SHORT",
                        "pnl_pips": pnl_pips,
                        "status": "TP",
                        "days": (current_date - entry_date).days
                    })
                    in_trade = False
                    position_size = 1.0
                    partial1_done = partial2_done = break_even_set = False
                    equity += pnl_pips / 1000
                    equity_curve.append(equity)
                    dates.append(current_date)
                    continue
            
            # ENTRY LOGIC
            if not in_trade and (confluence_score >= 4):
                dxy_trend = dxy_analysis_result.get("trend", "NEUTRAL")
                
                # Generate entry based on DXY bias
                if dxy_trend == "DOWNTREND":  # EUR/USD Bullish
                    entry_price = current_price
                    entry_type = "long"
                    entry_date = current_date
                    
                    # Calculate stops and targets
                    atr_val = atr(window_eurusd, 14)
                    atr_pips = float(atr_val.iloc[-1]) * 10000 if not pd.isna(atr_val.iloc[-1]) else 50
                    low_50 = float(window_eurusd["Low"].iloc[-50:].min())
                    
                    stop_loss = low_50 - (atr_val.iloc[-1] * 1.0) if not pd.isna(atr_val.iloc[-1]) else entry_price - 0.0030
                    target1 = entry_price + (atr_val.iloc[-1] * 4) if not pd.isna(atr_val.iloc[-1]) else entry_price + 0.0040
                    target2 = entry_price + (atr_val.iloc[-1] * 8) if not pd.isna(atr_val.iloc[-1]) else entry_price + 0.0080
                    
                    in_trade = True
                    # reset management trackers
                    position_size = 1.0
                    partial1_done = False
                    partial2_done = False
                    break_even_set = False
                
                elif dxy_trend == "UPTREND":  # EUR/USD Bearish
                    entry_price = current_price
                    entry_type = "short"
                    entry_date = current_date
                    
                    atr_val = atr(window_eurusd, 14)
                    atr_pips = float(atr_val.iloc[-1]) * 10000 if not pd.isna(atr_val.iloc[-1]) else 50
                    high_50 = float(window_eurusd["High"].iloc[-50:].max())
                    
                    stop_loss = high_50 + (atr_val.iloc[-1] * 1.0) if not pd.isna(atr_val.iloc[-1]) else entry_price + 0.0030
                    target1 = entry_price - (atr_val.iloc[-1] * 4) if not pd.isna(atr_val.iloc[-1]) else entry_price - 0.0040
                    target2 = entry_price - (atr_val.iloc[-1] * 8) if not pd.isna(atr_val.iloc[-1]) else entry_price - 0.0080
                    
                    in_trade = True
                    position_size = 1.0
                    partial1_done = False
                    partial2_done = False
                    break_even_set = False

            # Allow post-news pullback entries even if confluence slightly below threshold
            if not in_trade and confluence_score >= 4:
                # detect post-news pullbacks in the recent window
                pull = detect_news_pullback_entry(window_eurusd, [], [], [risk_zone if (risk_zone := window_eurusd["Low"].min()) else None])
                if pull.get("count", 0) > 0:
                    # open trade in pull direction using DXY bias
                    p = pull["pullback_entries"][0]
                    if p.get("signal") == "BULLISH":
                        entry_price = current_price
                        entry_type = "long"
                    else:
                        entry_price = current_price
                        entry_type = "short"
                    entry_date = current_date
                    atr_val = atr(window_eurusd, 14)
                    stop_loss = (float(window_eurusd["Low"].min()) - atr_val.iloc[-1]) if entry_type == "long" else (float(window_eurusd["High"].max()) + atr_val.iloc[-1])
                    target1 = entry_price + (atr_val.iloc[-1] * 4) if entry_type == "long" else entry_price - (atr_val.iloc[-1] * 4)
                    target2 = entry_price + (atr_val.iloc[-1] * 8) if entry_type == "long" else entry_price - (atr_val.iloc[-1] * 8)
                    in_trade = True
                    position_size = 1.0
                    partial1_done = partial2_done = break_even_set = False
        
        # Calculate statistics
        if trades:
            wins = [t for t in trades if t["pnl_pips"] > 0]
            losses = [t for t in trades if t["pnl_pips"] < 0]
            
            win_rate = (len(wins) / len(trades) * 100) if trades else 0
            avg_win = (sum(t["pnl_pips"] for t in wins) / len(wins)) if wins else 0
            avg_loss = (sum(abs(t["pnl_pips"]) for t in losses) / len(losses)) if losses else 0
            profit_factor = (sum(t["pnl_pips"] for t in wins) / sum(abs(t["pnl_pips"]) for t in losses)) if losses and sum(abs(t["pnl_pips"]) for t in losses) > 0 else 0
            
            total_pnl = sum(t["pnl_pips"] for t in trades)
            total_return = equity - 1000
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
            total_pnl = 0
            total_return = 0
        
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
            "total_trades": len(trades),
            "wins": len(wins) if trades else 0,
            "losses": len(losses) if trades else 0,
            "win_rate": win_rate,
            "avg_win_pips": avg_win,
            "avg_loss_pips": avg_loss,
            "profit_factor": profit_factor,
            "total_pnl_pips": total_pnl,
            "total_return": total_return,
            "final_equity": equity,
            "max_drawdown": max_dd,
            "equity_curve": equity_curve,
            "dates": dates,
            "lookback_days": lookback_days,
            "diagnostics": diagnostics,
        }
    
    except Exception as e:
        return {"error": str(e), "error_detail": repr(e)}


# ══════════════════════════════════════════════════════════════════════════════
# MASTER SIGNAL ENGINE
# ══════════════════════════════════════════════════════════════════════════════
def generate_master_signal(dxy_analysis: dict, news_items: list, cal_events: list) -> dict:
    """
    Combines:
      1. DXY trend (weight 3)
      2. Recent high-impact news sentiment (weight 2 per strong signal)
      3. Calendar event outcomes vs forecast (weight 2 per beat/miss)
    Returns: final_signal, score, reasons[]
    """
    score = 0
    reasons = []

    # ── 1. DXY trend signal
    dxy_sig = dxy_analysis.get("eur_signal", "NEUTRAL")
    dxy_trend = dxy_analysis.get("trend", "NEUTRAL")
    dxy_score = dxy_analysis.get("score_dxy", 0)

    if dxy_sig == "BULLISH":
        score += 3
        reasons.append(f"🟢 DXY in {dxy_trend} → EUR/USD Bullish (score {dxy_score:+d})")
    elif dxy_sig == "BEARISH":
        score -= 3
        reasons.append(f"🔴 DXY in {dxy_trend} → EUR/USD Bearish (score {dxy_score:+d})")
    else:
        reasons.append(f"⚪ DXY NEUTRAL (score {dxy_score:+d})")

    # DXY key level proximity signal
    last_dxy = dxy_analysis.get("last_close")
    supply_lvls = dxy_analysis.get("supply_levels", [])
    demand_lvls = dxy_analysis.get("demand_levels", [])
    if last_dxy and supply_lvls:
        nearest_sup = supply_lvls[0]
        dist_pct = abs(nearest_sup - last_dxy) / last_dxy * 100
        if dist_pct < 0.25:
            score += 2
            reasons.append(f"🟢 DXY approaching supply at {nearest_sup} → EURUSD demand zone forming")
    if last_dxy and demand_lvls:
        nearest_dem = demand_lvls[0]
        dist_pct = abs(nearest_dem - last_dxy) / last_dxy * 100
        if dist_pct < 0.25:
            score -= 2
            reasons.append(f"🔴 DXY approaching demand at {nearest_dem} → EURUSD supply zone forming")

    # ── 2. News sentiment (last 6 hours)
    cutoff = datetime.utcnow() - timedelta(hours=6)
    recent_news = [n for n in news_items if n["dt"] >= cutoff]
    bull_news = [n for n in recent_news if n.get("signal") == "BULL"]
    bear_news = [n for n in recent_news if n.get("signal") == "BEAR"]
    if bull_news:
        score += min(len(bull_news) * 2, 4)
        reasons.append(f"🟢 {len(bull_news)} recent news signal USD weakness → EUR/USD Bullish")
    if bear_news:
        score -= min(len(bear_news) * 2, 4)
        reasons.append(f"🔴 {len(bear_news)} recent news signal USD strength → EUR/USD Bearish")

    # ── 3. Calendar event outcomes
    for ev in cal_events:
        actual_str   = ev.get("actual", "")
        forecast_str = ev.get("forecast", "")
        if not actual_str or not forecast_str:
            continue
        try:
            # Strip non-numeric except . - %K M B
            def parse_val(s):
                s = re.sub(r"[^0-9.\-]", "", str(s))
                return float(s) if s else None
            actual   = parse_val(actual_str)
            forecast = parse_val(forecast_str)
            if actual is None or forecast is None:
                continue
            diff_pct = (actual - forecast) / abs(forecast) * 100 if forecast != 0 else 0
            ccy = ev["currency"]
            title = ev["title"]
            if ccy == "USD":
                # Strong USD data → EURUSD bearish
                if diff_pct > 5:
                    score -= 2
                    reasons.append(f"🔴 USD {title}: {actual_str} vs {forecast_str} (beat) → Bearish EUR/USD")
                elif diff_pct < -5:
                    score += 2
                    reasons.append(f"🟢 USD {title}: {actual_str} vs {forecast_str} (miss) → Bullish EUR/USD")
            elif ccy == "EUR":
                # Strong EUR data → EURUSD bullish
                if diff_pct > 5:
                    score += 2
                    reasons.append(f"🟢 EUR {title}: {actual_str} vs {forecast_str} (beat) → Bullish EUR/USD")
                elif diff_pct < -5:
                    score -= 2
                    reasons.append(f"🔴 EUR {title}: {actual_str} vs {forecast_str} (miss) → Bearish EUR/USD")
        except Exception:
            continue

    # ── Final verdict
    if score >= 3:
        final = "BULLISH"
    elif score <= -3:
        final = "BEARISH"
    else:
        final = "NEUTRAL"

    return {"signal": final, "score": score, "reasons": reasons}


# ══════════════════════════════════════════════════════════════════════════════
# SESSIONS
# ══════════════════════════════════════════════════════════════════════════════
SESSIONS = [
    {"name": "Sydney",   "start": 21, "end": 6,  "color": "rgba(230,220,80,0.10)"},
    {"name": "London",   "start": 8,  "end": 17, "color": "rgba(80,180,80,0.10)"},
    {"name": "New York", "start": 13, "end": 22, "color": "rgba(230,220,80,0.10)"},
]

def get_session_blocks(df):
    if df.empty:
        return []
    blocks = []
    dates = pd.date_range(
        df["dt"].min().date(),
        df["dt"].max().date() + timedelta(days=1),
        freq="D"
    )
    for d in dates:
        for sess in SESSIONS:
            s_h, e_h = sess["start"], sess["end"]
            s_dt = datetime(d.year, d.month, d.day, s_h)
            if e_h <= s_h:
                try:
                    e_dt = datetime(d.year, d.month, d.day + 1, e_h)
                except Exception:
                    continue
            else:
                e_dt = datetime(d.year, d.month, d.day, e_h)
            if e_dt < df["dt"].min() or s_dt > df["dt"].max():
                continue
            blocks.append({"x0": s_dt, "x1": e_dt, "color": sess["color"], "name": sess["name"]})
    return blocks


# ══════════════════════════════════════════════════════════════════════════════
# EURUSD CHART  (5 rows: Candles | Sessions | Calendar | News | DXY)
# ══════════════════════════════════════════════════════════════════════════════
def build_eurusd_chart(df, dxy_df, cal_events, news_items, dxy_analysis):
    if df.empty:
        return go.Figure()

    session_blocks = get_session_blocks(df)
    has_dxy = dxy_df is not None and not dxy_df.empty

    # Add an explicit volume row under candles -> shift other panels down
    fig = make_subplots(
        rows=6, cols=1,
        row_heights=[0.44, 0.12, 0.20, 0.08, 0.08, 0.08],
        vertical_spacing=0.002,
        shared_xaxes=True,
    )

    # ── Row 1: EUR/USD Candlestick
    fig.add_trace(go.Candlestick(
        x=df["dt"],
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        increasing=dict(line=dict(color="#26a69a", width=1), fillcolor="#26a69a"),
        decreasing=dict(line=dict(color="#ef5350", width=1), fillcolor="#ef5350"),
        name="EUR/USD", 
        hovertemplate="<b>EUR/USD</b><br>Open: %{open:.5f}<br>High: %{high:.5f}<br>Low: %{low:.5f}<br>Close: %{close:.5f}<br>%{x|%Y-%m-%d %H:%M}<extra></extra>",
    ), row=1, col=1)

    # Current price horizontal line and right-side label (TradingView-style)
    try:
        last_close = float(df["Close"].iloc[-1])
        prev_close = float(df["Close"].iloc[-2]) if len(df) > 1 else last_close
        price_color = "#26a69a" if last_close >= prev_close else "#ef5350"
        fig.add_shape(type="line", xref="paper", x0=0, x1=1, yref="y1", y0=last_close, y1=last_close,
                      line=dict(color=price_color, width=1, dash="dot"), opacity=0.32, layer="above")
        fig.add_annotation(xref="paper", x=1.012, y=last_close, yref="y1",
                           text=f"{last_close:.5f}", showarrow=False,
                           bgcolor=price_color, font=dict(color="#ffffff", size=10), xanchor="left", yanchor="middle")
    except Exception:
        pass

    # Session shading on main chart
    for blk in session_blocks:
        fig.add_shape(
            type="rect", xref="x", yref="paper",
            x0=blk["x0"], x1=blk["x1"], y0=0.40, y1=1.0,
            fillcolor=blk["color"], line=dict(width=0), layer="below",
        )

    # ── Row 2: Volume bars (directly under candles)
    if "Volume" in df.columns:
        try:
            vols = df["Volume"].astype(float)
            # color bars by candle direction
            vol_colors = ["#26a69a" if c >= o else "#ef5350" for c, o in zip(df["Close"], df["Open"]) ]
            fig.add_trace(go.Bar(
                x=df["dt"], y=vols,
                marker=dict(color=vol_colors, opacity=0.35),
                showlegend=False, name="Volume",
                hovertemplate="Volume: %{y}<br>%{x|%Y-%m-%d %H:%M}<extra></extra>",
            ), row=2, col=1)
        except Exception:
            pass
    # ── Supply / Demand zones (visualized as translucent bands across chart width)
    try:
        lookback_z = min(60, len(df) - 1)
        prev_highs = df["High"].iloc[-lookback_z:-1].nlargest(2).tolist()
        prev_lows = df["Low"].iloc[-lookback_z:-1].nsmallest(2).tolist()
        x0 = df["dt"].iloc[0]
        x1 = df["dt"].iloc[-1]
        # Supply zones (recent highs)
        for h in prev_highs:
            top = float(h) + 0.0002
            bot = float(h) - 0.0002
            fig.add_shape(type="rect", xref="x", yref="y1", x0=x0, x1=x1,
                          y0=bot, y1=top, fillcolor="#ef5350", opacity=0.12,
                          line=dict(color="#ef5350", width=1), layer="below")
            try:
                fig.add_annotation(x=x1, y=float(h), xref="x", yref="y1",
                                   text="Supply Zone", showarrow=False,
                                   bgcolor="#ef5350", font=dict(color="#fff", size=8),
                                   xanchor="left", yanchor="middle")
            except Exception:
                pass
        # Demand zones (recent lows)
        for l in prev_lows:
            top = float(l) + 0.0002
            bot = float(l) - 0.0002
            fig.add_shape(type="rect", xref="x", yref="y1", x0=x0, x1=x1,
                          y0=bot, y1=top, fillcolor="#26a69a", opacity=0.12,
                          line=dict(color="#26a69a", width=1), layer="below")
            try:
                fig.add_annotation(x=x1, y=float(l), xref="x", yref="y1",
                                   text="Demand Zone", showarrow=False,
                                   bgcolor="#26a69a", font=dict(color="#000", size=8),
                                   xanchor="left", yanchor="middle")
            except Exception:
                pass
    except Exception:
        pass

    # ── Row 3: DXY line chart (correlation panel)
    if has_dxy:
        dxy_merged = dxy_df[
            (dxy_df["dt"] >= df["dt"].min()) & (dxy_df["dt"] <= df["dt"].max())
        ].copy()
        if not dxy_merged.empty:
            closes = dxy_merged["Close"].astype(float)
            e20 = ema(closes, 20)
            e50 = ema(closes, 50)

            fig.add_trace(go.Scatter(
                x=dxy_merged["dt"], y=closes,
                mode="lines",
                line=dict(color="#f0a500", width=2),
                name="DXY", 
                hovertemplate="<b>DXY</b><br>Close: %{y:.3f}<br>%{x|%Y-%m-%d %H:%M}<extra></extra>",
            ), row=3, col=1)
            fig.add_trace(go.Scatter(
                x=dxy_merged["dt"], y=e20,
                mode="lines", line=dict(color="#58a6ff", width=1.5, dash="dot"),
                name="DXY EMA20", 
                hovertemplate="<b>DXY EMA20</b><br>Value: %{y:.3f}<br>%{x|%Y-%m-%d %H:%M}<extra></extra>",
            ), row=3, col=1)
            fig.add_trace(go.Scatter(
                x=dxy_merged["dt"], y=e50,
                mode="lines", line=dict(color="#e74c3c", width=1.5, dash="dot"),
                name="DXY EMA50",
                hovertemplate="<b>DXY EMA50</b><br>Value: %{y:.3f}<br>%{x|%Y-%m-%d %H:%M}<extra></extra>",
            ), row=3, col=1)

            # Colour DXY trend arrow in annotation
            trend = dxy_analysis.get("trend", "NEUTRAL")
            arrow = {"UPTREND": "▲ UPTREND", "DOWNTREND": "▼ DOWNTREND", "NEUTRAL": "◆ NEUTRAL"}.get(trend, "")
            color = {"UPTREND": "#e74c3c", "DOWNTREND": "#3fb950", "NEUTRAL": "#8b949e"}.get(trend, "#8b949e")
            fig.add_annotation(
                x=dxy_merged["dt"].iloc[-1], y=float(closes.iloc[-1]),
                xref="x3", yref="y3",
                text=f"DXY {arrow}",
                showarrow=False, bgcolor=color,
                font=dict(size=9, color="#fff"),
                xanchor="right", yanchor="bottom",
            )

    # ── Row 4: Sessions strip (moved down since volume occupies row 2)
    for blk in session_blocks:
        mid = blk["x0"] + (blk["x1"] - blk["x0"]) / 2
        fig.add_trace(go.Scatter(
            x=[blk["x0"], blk["x0"], blk["x1"], blk["x1"], blk["x0"]],
            y=[0, 1, 1, 0, 0],
            fill="toself", fillcolor=blk["color"],
            line=dict(width=0), mode="lines",
            showlegend=False, hoverinfo="skip",
        ), row=4, col=1)

    seen_s = {}
    for blk in session_blocks:
        n = blk["name"]
        mid = blk["x0"] + (blk["x1"] - blk["x0"]) / 2
        if n not in seen_s or (mid - seen_s[n]).total_seconds() > 86400:
            seen_s[n] = mid
            fig.add_annotation(
                x=mid, y=0.5, xref="x4", yref="y4",
                text=f"<b>{n}</b>", showarrow=False,
                font=dict(size=8, color="rgba(200,210,220,0.7)"),
                xanchor="center", yanchor="middle",
            )

    # ── Row 4: Calendar markers (color-coded by impact)
    cal_in = [e for e in cal_events if df["dt"].min() <= e["dt"] <= df["dt"].max()]
    if cal_in:
        # Color code by impact: High=Red, Medium=Yellow, Low=Orange
        impact_colors = {"High": "#e74c3c", "Medium": "#f0a500", "Low": "#e67e22"}
        marker_sizes = {"High": 14, "Medium": 12, "Low": 10}
        
        fig.add_trace(go.Scatter(
            x=[e["dt"] for e in cal_in], y=[0.5] * len(cal_in),
            mode="markers+text",
            marker=dict(
                symbol="diamond", 
                size=[marker_sizes.get(e.get("impact", "Low"), 12) for e in cal_in],
                color=[impact_colors.get(e.get("impact", "Low"), "#e67e22") for e in cal_in],
                line=dict(width=1.5, color="rgba(255,255,255,0.4)")
            ),
            text=["📅"] * len(cal_in),
            textposition="middle center",
            name="Calendar Events",
            customdata=[
                f"<b>{e['currency']}: {e['title']}</b><br>"
                f"Impact: <b>{e.get('impact', 'Unknown')}</b><br>"
                f"Actual: <b>{e['actual'] or '—'}</b><br>" 
                f"Forecast: {e['forecast'] or '—'}<br>"
                f"Previous: {e['previous'] or '—'}"
                for e in cal_in
            ],
            hovertemplate="%{customdata}<extra>📅</extra>",
            showlegend=True,
        ), row=5, col=1)
    else:
        fig.add_trace(go.Scatter(x=[df["dt"].iloc[0]], y=[0.5], mode="markers",
                                 marker=dict(opacity=0), showlegend=False, hoverinfo="skip"), row=5, col=1)

    # ── Row 6: News signal markers (bull=green, bear=red, neutral=orange)
    news_in = [n for n in news_items if df["dt"].min() <= n["dt"] <= df["dt"].max()]
    SIG_COLORS = {"BULL": "#3fb950", "BEAR": "#e74c3c", "": "#e67e22"}
    if news_in:
        fig.add_trace(go.Scatter(
            x=[n["dt"] for n in news_in], y=[0.5] * len(news_in),
            mode="markers+text",
            marker=dict(
                symbol="circle", size=12,
                color=[SIG_COLORS.get(n.get("signal", ""), "#e67e22") for n in news_in],
                line=dict(width=1, color="rgba(255,255,255,0.3)")
            ),
            text=["📰"] * len(news_in),
            textposition="middle center",
            name="News",
            customdata=[
                f"<b>{n.get('signal','NEUTRAL') or 'NEUTRAL'}</b><br>"
                f"{n['title'][:80]}...<br>"
                f"<i>Source: {n.get('source','Unknown')}</i>"
                for n in news_in
            ],
            hovertemplate="%{customdata}<extra>📰</extra>",
            showlegend=True,
        ), row=6, col=1)
    else:
        fig.add_trace(go.Scatter(x=[df["dt"].iloc[0]], y=[0.5], mode="markers",
                                 marker=dict(opacity=0), showlegend=False, hoverinfo="skip"), row=6, col=1)

    # ── Axes
    common_axis = dict(showgrid=False, zeroline=False, showticklabels=False,
                       showline=True, linecolor="#2e3347")
    fig.update_layout(
        height=820,
        paper_bgcolor="#131722",
        plot_bgcolor="#131722",
        margin=dict(l=52, r=80, t=30, b=40),
        xaxis_rangeslider_visible=False,
        hoverlabel=dict(bgcolor="#252a3a", font_size=11, bordercolor="#3e4460", namelength=-1),
        dragmode="zoom",
        hovermode="x unified",
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="right",
            x=0.98,
            bgcolor="rgba(37, 42, 58, 0.8)",
            bordercolor="#2e3347",
            borderwidth=1,
            font=dict(size=9, color="#c9d1d9"),
        ),
    )
    # X axes: no vertical grid lines; Y axes: subtle horizontal grid lines
    fig.update_xaxes(showgrid=False, zeroline=False, tickfont=dict(color="#787b86", size=11),
                     showline=False, row=1, col=1)
    fig.update_yaxes(showgrid=True, gridcolor="#1e222d", gridwidth=0.5,
                     zeroline=False, tickfont=dict(color="#787b86", size=10),
                     side="right", tickformat=".5f", row=1, col=1)

    # Volume (row 2)
    fig.update_xaxes(showgrid=False, zeroline=False, tickfont=dict(color="#6b7380", size=10), row=2, col=1)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, row=2, col=1)

    # DXY (row 3)
    fig.update_xaxes(showgrid=False, zeroline=False, tickfont=dict(color="#6b7380", size=10), row=3, col=1)
    fig.update_yaxes(showgrid=True, gridcolor="#1e222d", gridwidth=0.5, zeroline=False,
                     tickfont=dict(color="#8b949e", size=9), side="right", tickformat=".2f", row=3, col=1)

    for r in [4, 5, 6]:
        fig.update_xaxes(showgrid=False, zeroline=False, tickfont=dict(color="#6b7380", size=9),
                         showline=True, linecolor="#2e3347", row=r, col=1)
        fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False,
                         range=[0, 1], showline=True, linecolor="#2e3347", row=r, col=1)
    fig.update_xaxes(showticklabels=True, tickfont=dict(color="#6b7380", size=10), row=6, col=1)

    # Row labels (left-side short labels for each panel)
    for txt, y_paper in [("Volume", 0.425), ("DXY", 0.30), ("Sessions", 0.17), ("Calendar", 0.09), ("News", 0.02)]:
        fig.add_annotation(
            x=-0.015, y=y_paper, xref="paper", yref="paper",
            text=f"<b>{txt}</b>", showarrow=False,
            font=dict(size=9, color="#8b949e"), xanchor="right", yanchor="middle",
        )
    # Watermark (pair + timeframe) — subtle TradingView-like label
    try:
        tf_label = st.session_state.get('tf', '1H')
        fig.add_annotation(x=0.02, y=0.98, xref='paper', yref='paper',
                           text=f"EURUSD · {tf_label}", showarrow=False,
                           font=dict(size=36, color='rgba(255,255,255,0.06)'), xanchor='left', yanchor='top')
    except Exception:
        pass
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
def calc_perf(df):
    if df.empty or len(df) < 2:
        return {}
    last = float(df["Close"].iloc[-1])
    res = {}
    for label, bars in [("1hr", 1), ("6hr", 6), ("12hr", 12)]:
        idx = max(0, len(df) - bars - 1)
        ref = float(df["Close"].iloc[idx])
        res[label] = {
            "pip": round((last - ref) * 10000, 1),
            "pct": round((last - ref) / ref * 100, 2),
        }
    return res

def perf_color(v, suffix=""):
    if v > 0:   return f'<span class="pos">+{v}{suffix}</span>'
    elif v < 0: return f'<span class="neg">{v}{suffix}</span>'
    return f'<span class="neu">{v}{suffix}</span>'


# ══════════════════════════════════════════════════════════════════════════════
# STATE + DATA LOAD
# ══════════════════════════════════════════════════════════════════════════════
# Headless backtest runner (invoke with env RUN_BACKTEST=1)
if os.environ.get("RUN_BACKTEST") == "1":
    tf_env = os.environ.get("BACKTEST_TF", "1H")
    lookback = int(os.environ.get("LOOKBACK_DAYS", "30"))
    print(f"Running headless backtest for {tf_env} (lookback {lookback}d)", file=sys.stderr)
    df_bt = get_price_data(tf_env)
    dxy_bt = get_dxy_data(tf_env)
    res = backtest_strategy(df_bt, dxy_bt, analyze_dxy, evaluate_confluence_factors, lookback_days=lookback)
    print(json.dumps(res, default=str))
    sys.exit(0)

if "tf" not in st.session_state:
    st.session_state.tf = "1H"

tf          = st.session_state.tf

# Load all 3 timeframes in background for stack analysis (no user selection needed)
df_daily    = get_price_data("D")
df_4h       = get_price_data("4H")
df_1h       = get_price_data("1H")

dxy_df      = get_dxy_data(tf)
dxy_df_daily = get_dxy_data("D")
dxy_df_4h   = get_dxy_data("4H")

# For charting (user selected timeframe)
df          = get_price_data(tf)

live_eur    = get_live_price("EURUSD=X")
live_dxy    = get_live_price("DX-Y.NYB")
cal_events  = get_calendar()
news_items  = get_news()
perf        = calc_perf(df)
dxy_an      = analyze_dxy(dxy_df)
master_sig  = generate_master_signal(dxy_an, news_items, cal_events)

# ── 3-TIMEFRAME STACK ANALYSIS (shows all timeframes simultaneously)
dxy_dict = {"daily": dxy_df_daily, "4h": dxy_df_4h, "1h": dxy_df}
timeframe_stack = analyze_timeframe_stack(df_1h, df_4h, df_daily, dxy_dict)

# Calculate confluence factors (timeframe stack analysis)
confluence_analysis = evaluate_confluence_factors(df, dxy_df, dxy_an, cal_events)

# Aggregate all signals from all sources
all_signals = aggregate_all_signals(df, dxy_df, dxy_an, news_items, cal_events, confluence_analysis)

# Run backtest
backtest_result = backtest_strategy(df, dxy_df, analyze_dxy, evaluate_confluence_factors, lookback_days=30)

# Determine setup bias based on DXY trend
setup_bias = "bullish" if dxy_an.get("trend") == "DOWNTREND" else "bearish"
risk_metrics = calculate_risk_metrics(df, setup_bias)

# ── NEW TRADE MANAGEMENT FEATURES ──
# Assuming an entry at average price, calculate position management
entry_price = float(df["Close"].iloc[-20]) if len(df) > 20 else float(df["Close"].iloc[-1])  # Entry 20 bars ago
current_price = float(df["Close"].iloc[-1])
position_mgmt = calculate_position_management(current_price, entry_price, 
                                              risk_metrics.get("stop_loss", 0), direction="long")

# Rejection candle detection (entry signals)
rejections = detect_rejection_candles(df, lookback=5)

# Post-news pullback detection
demand_zones = risk_metrics.get("resistance") if risk_metrics else []
news_pullbacks = detect_news_pullback_entry(df, news_items, cal_events, [demand_zones])

# Early exit rule (monitor 4H candles)
early_exits = detect_early_exit_signals(df_1h, df_4h, entry_price, direction="long")

# News proximity warning (do not enter before news)
news_warnings = check_news_proximity_warning(cal_events, current_price, threshold_hours=2)

# Dynamic trailing stop calculation
trailing_stop_data = calculate_dynamic_trailing_stop(df_4h, current_price, direction="long")

if live_eur is None and not df.empty:
    live_eur = float(df["Close"].iloc[-1])

p1  = perf.get("1hr",  {"pip": 0, "pct": 0})
p6  = perf.get("6hr",  {"pip": 0, "pct": 0})
p12 = perf.get("12hr", {"pip": 0, "pct": 0})
price_str = f"{live_eur:.5f}" if live_eur else "—"
dxy_str   = f"{live_dxy:.3f}" if live_dxy else (
    f"{dxy_an['last_close']:.3f}" if dxy_an.get("last_close") else "—")
dxy_chg   = dxy_an.get("change_pct", 0)


# ══════════════════════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════════════════════

# ── Price Header (EUR/USD + DXY side by side)
dxy_trend  = dxy_an.get("trend", "NEUTRAL")
dxy_color  = {"UPTREND": "#e74c3c", "DOWNTREND": "#3fb950", "NEUTRAL": "#8b949e"}.get(dxy_trend, "#8b949e")
eur_sig    = dxy_an.get("eur_signal", "NEUTRAL")
eur_sig_cl = {"BULLISH": "#3fb950", "BEARISH": "#e74c3c", "NEUTRAL": "#8b949e"}.get(eur_sig, "#8b949e")
dxy_arrow  = "▲" if dxy_chg > 0 else ("▼" if dxy_chg < 0 else "◆")

st.markdown(f"""
<div class="price-header">
  <div class="price-box">
    <span class="pair-label">EUR/USD</span>
    <span class="price-val">{price_str[:6]}<span style="font-size:1.1rem;color:#8b949e;">{price_str[6:]}</span></span>
    <span style="color:#3fb950;font-size:1rem;">▲</span>
  </div>
  <div class="perf-panel">
    <div class="perf-col">
      <div class="perf-label">Last 1 hr</div>
      <div class="perf-row"><span class="perf-key">Pip Chg:</span>{perf_color(p1['pip'])}</div>
      <div class="perf-row"><span class="perf-key">% Chg:</span>{perf_color(p1['pct'],'%')}</div>
    </div>
    <div class="perf-col">
      <div class="perf-label">Last 6 hr</div>
      <div class="perf-row"><span class="perf-key">Pip Chg:</span>{perf_color(p6['pip'])}</div>
      <div class="perf-row"><span class="perf-key">% Chg:</span>{perf_color(p6['pct'],'%')}</div>
    </div>
    <div class="perf-col">
      <div class="perf-label">Last 12 hr</div>
      <div class="perf-row"><span class="perf-key">Pip Chg:</span>{perf_color(p12['pip'])}</div>
      <div class="perf-row"><span class="perf-key">% Chg:</span>{perf_color(p12['pct'],'%')}</div>
    </div>
    <!-- DXY live panel -->
    <div class="perf-col" style="border-left:2px solid #f0a50060;">
      <div class="perf-label" style="color:#f0a500;">DXY Index</div>
      <div class="perf-row"><span class="perf-key">Price:</span>
        <span style="color:#f0a500;font-weight:600;">{dxy_str}</span>
      </div>
      <div class="perf-row"><span class="perf-key">Trend:</span>
        <span style="color:{dxy_color};font-weight:600;">{dxy_arrow} {dxy_trend}</span>
      </div>
    </div>
    <div class="perf-col">
      <div class="perf-label" style="color:{eur_sig_cl};">EUR/USD DXY Signal</div>
      <div class="perf-row" style="font-size:0.9rem;font-weight:700;color:{eur_sig_cl};">{eur_sig}</div>
      <div class="perf-row"><span class="perf-key">EMA20:</span>
        <span style="color:#58a6ff;">{dxy_an.get('ema20','—')}</span>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Timeframe bar
tf_options = list(TF_MAP.keys())
cols = st.columns([2.2] + [0.38] * len(tf_options) + [0.9])
with cols[0]:
    st.markdown('<span style="color:#8b949e;font-size:0.8rem;line-height:2.4;">Chart for EUR/USD + DXY</span>',
                unsafe_allow_html=True)
for i, tf_opt in enumerate(tf_options):
    with cols[i + 1]:
        if st.button(tf_opt, key=f"tf_{tf_opt}", use_container_width=True):
            # Change timeframe without clearing the entire cache to avoid
            # re-downloading all timeframes and long load times.
            st.session_state.tf = tf_opt
            st.rerun()
with cols[-1]:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Fast-load toggle: when enabled, the app limits heavy downloads and only loads core TFs on demand
fast_mode = st.checkbox("Fast loading mode (recommended)", value=True)

# Per-timeframe summaries (lightweight - core TFs)
st.markdown("### ⏱️ Timeframe Summaries (quick)")
tf_summary_cols = st.columns(4)
core_tfs = ["1H", "4H", "D"]
for i, tfk in enumerate(core_tfs):
    with tf_summary_cols[i % 4]:
        s = compute_tf_summary(tfk, news_items if 'news_items' in globals() else [], cal_events if 'cal_events' in globals() else [])
        color = "#3fb950" if "BULL" in s.get("verdict", "") else ("#e74c3c" if "BEAR" in s.get("verdict", "") else "#8b949e")
        st.markdown(f"""
        <div style="background:#1e2233;border:1px solid #2e3347;border-radius:6px;padding:8px;text-align:center;">
          <div style="font-size:0.95rem;font-weight:700;color:{color};">{s.get('verdict','NO DATA')}</div>
          <div style="font-size:0.75rem;color:#8b949e;margin-top:6px;">TF: {tfk} • Confidence: {s.get('confidence',0):.0f}%</div>
        </div>
        """, unsafe_allow_html=True)

if not fast_mode:
    # If user disables fast mode, compute summaries for all available TFs on demand
    if st.button("Compute summaries for all timeframes (may be slow)"):
        all_cols = st.columns(4)
        results = []
        for i, key in enumerate(TF_MAP.keys()):
            res = compute_tf_summary(key, news_items if 'news_items' in globals() else [], cal_events if 'cal_events' in globals() else [])
            results.append(res)
            with all_cols[i % 4]:
                color = "#3fb950" if "BULL" in res.get("verdict", "") else ("#e74c3c" if "BEAR" in res.get("verdict", "") else "#8b949e")
                st.markdown(f"<div style='background:#1e2233;border:1px solid #2e3347;border-radius:6px;padding:8px;text-align:center;'><div style='font-weight:700;color:{color};'>{res.get('tf')} — {res.get('verdict')}</div><div style='font-size:0.75rem;color:#8b949e;'>Confidence: {res.get('confidence',0):.0f}%</div></div>", unsafe_allow_html=True)

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  3-TIMEFRAME STACK ANALYSIS (Daily/4H/1H) - MULTI-TIMEFRAME CONFLUENCE  ║
# ╚════════════════════════════════════════════════════════════════════════════╝
if timeframe_stack and "error" not in timeframe_stack:
    st.markdown("## 📊 3-TIMEFRAME STACK Analysis (Daily Map → 4H Signal → 1H Entry)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="section-panel" style="background:#252a3a;">
            <div class="section-header">📍 DAILY (Map)</div>
            <div style="padding:12px 14px;">
              <div style="color:#e0e6f0;font-size:0.9rem;font-weight:600;margin-bottom:6px;">
                {timeframe_stack['daily_map'].get('trend', 'N/A')}
              </div>
              <div style="font-size:0.78rem;color:#8b949e;line-height:1.6;">
                <div>ADX: <span style="color:#58a6ff;font-weight:600;">{timeframe_stack['daily_map'].get('adx', 0):.1f}</span></div>
                <div>+DI: <span style="color:#3fb950;font-weight:600;">{timeframe_stack['daily_map'].get('plus_di', 0):.1f}</span></div>
                <div>-DI: <span style="color:#e74c3c;font-weight:600;">{timeframe_stack['daily_map'].get('minus_di', 0):.1f}</span></div>
                <div style="margin-top:6px;color:#c9d1d9;"><b>Overall direction:</b> {timeframe_stack['daily_map'].get('role', 'N/A')}</div>
              </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="section-panel" style="background:#252a3a;">
            <div class="section-header">📊 4H (Signal)</div>
            <div style="padding:12px 14px;">
              <div style="color:#e0e6f0;font-size:0.9rem;font-weight:600;margin-bottom:6px;">
                {timeframe_stack['h4_signal'].get('signal', 'N/A')}
              </div>
              <div style="font-size:0.78rem;color:#8b949e;line-height:1.6;">
                <div>ADX: <span style="color:#58a6ff;font-weight:600;">{timeframe_stack['h4_signal'].get('adx', 0):.1f}</span></div>
                <div>Zone: <span style="color:#e0e6f0;">{timeframe_stack['h4_signal'].get('setup_zone', 'N/A')[:30]}</span></div>
                <div style="margin-top:6px;color:#c9d1d9;"><b>Setup formation:</b> {timeframe_stack['h4_signal'].get('role', 'N/A')}</div>
              </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="section-panel" style="background:#252a3a;">
            <div class="section-header">⚡ 1H (Entry)</div>
            <div style="padding:12px 14px;">
              <div style="color:#e0e6f0;font-size:0.85rem;font-weight:600;margin-bottom:6px;">
                {timeframe_stack['h1_entry'].get('trigger', 'Waiting...')}
              </div>
              <div style="font-size:0.78rem;color:#8b949e;line-height:1.6;">
                <div>Upper: <span style="color:#58a6ff;">{timeframe_stack['h1_entry'].get('donchian_upper', 0):.5f}</span></div>
                <div>Lower: <span style="color:#e74c3c;">{timeframe_stack['h1_entry'].get('donchian_lower', 0):.5f}</span></div>
                <div style="margin-top:6px;color:#c9d1d9;"><b>Entry timing:</b> {timeframe_stack['h1_entry'].get('role', 'N/A')}</div>
              </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Overall confluence status
    status_color = "#3fb950" if "READY" in timeframe_stack.get("setup_status", "") else ("#f0a500" if "PARTIAL" in timeframe_stack.get("setup_status", "") else "#8b949e")
    st.markdown(f"""
    <div style="background:#1e2233;border:2px solid {status_color};border-radius:6px;padding:12px 14px;margin-top:10px;">
      <div style="color:{status_color};font-size:0.9rem;font-weight:700;">
        {timeframe_stack.get('setup_status', 'No Setup')}
      </div>
      <div style="color:#8b949e;font-size:0.78rem;margin-top:4px;">
        Confluence Score: <span style="color:{status_color};font-weight:600;">{timeframe_stack.get('overall_confluence', 0)}/4</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  TRADE MANAGEMENT PANEL - Position Tracking & Alerts                      ║
# ╚════════════════════════════════════════════════════════════════════════════╝
st.markdown("## 🎯 Trade Management & Position Alerts")

tm_col1, tm_col2 = st.columns(2)

with tm_col1:
    st.markdown(f"""
    <div class="section-panel" style="background:#252a3a;">
        <div class="section-header">💰 Position P&L Tracking</div>
        <div style="padding:12px 14px;">
          <div style="font-size:1rem;font-weight:700;color:#e0e6f0;margin-bottom:8px;">
            {position_mgmt.get('current_pips', 0):.1f} pips gain
          </div>
          <div style="font-size:0.85rem;color:#8b949e;line-height:1.8;">
            <div>Break-even distance: <span style="color:#e0e6f0;">{position_mgmt.get('break_even_distance', 0):.1f} pips</span></div>
            <div>Position status: <span style="color:{'#3fb950' if 'TARGET' in position_mgmt.get('position_status', '') else '#e74c3c'};">
              {position_mgmt.get('position_status', 'CLOSED')}
            </span></div>
          </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with tm_col2:
    if position_mgmt.get("alerts"):
        st.markdown(f"""
        <div class="section-panel" style="background:#1a3a2e;border-left:4px solid #3fb950;">
            <div class="section-header" style="background:#0f2f28;">🚨 BREAK-EVEN ALERT</div>
            <div style="padding:12px 14px;">
              <div style="color:#3fb950;font-weight:700;margin-bottom:6px;">
                ACTION REQUIRED
              </div>
              <div style="font-size:0.85rem;color:#8b949e;line-height:1.6;">
                {position_mgmt['alerts'][0].get('action', 'Move stop to break-even')}
                <br><span style="color:#c9d1d9;font-size:0.75rem;margin-top:4px;display:block;">
                  Level reached: {position_mgmt['alerts'][0].get('description', '')}
                </span>
              </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Partial close thresholds
    if position_mgmt.get("partial_closes"):
        st.markdown("**Partial Close Thresholds:**")
        for pc in position_mgmt["partial_closes"]:
            st.markdown(f"""
            • **{pc['threshold']}**: Close {pc['pct_close']}% of position
            """)

st.divider()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  ENTRY SIGNALS - Rejection Candles & News Pullbacks                        ║
# ╚════════════════════════════════════════════════════════════════════════════╝
st.markdown("## ⚡ Entry Signal Detection")

es_col1, es_col2 = st.columns(2)

with es_col1:
    st.markdown("### 📍 Rejection Candles (Pin Bars, Hammers, Engulfing)")
    if rejections["count"] > 0:
        for pattern in rejections["patterns"][-3:]:  # Show last 3
            color = "#3fb950" if pattern["signal"] == "BULLISH" else "#e74c3c"
            st.markdown(f"""
            <div style="background:#1e2233;border-left:4px solid {color};border-radius:4px;padding:10px 12px;margin-bottom:8px;">
              <div style="color:{color};font-weight:700;font-size:0.9rem;">{pattern['type']}</div>
              <div style="color:#8b949e;font-size:0.8rem;margin-top:4px;">{pattern['strength']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("⏳ No rejection candles detected in last 5 bars")

with es_col2:
    st.markdown("### 📰 Post-News Pullback Entries")
    if news_pullbacks["count"] > 0:
        for entry in news_pullbacks["pullback_entries"][:3]:
            color = "#3fb950" if entry["signal"] == "BULLISH" else "#e74c3c"
            st.markdown(f"""
            <div style="background:#1e2233;border-left:4px solid {color};border-radius:4px;padding:10px 12px;margin-bottom:8px;">
              <div style="color:{color};font-weight:700;font-size:0.9rem;">{entry['type']}</div>
              <div style="color:#8b949e;font-size:0.75rem;margin-top:3px;line-height:1.5;">
                Entry zone: <span style="color:#e0e6f0;">{entry['entry_zone']:.5f}</span><br>
                {entry['confluence']}
              </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("⏳ No post-news pullback entries detected")

st.divider()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  RISK & EXIT MANAGEMENT - Early Exits & News Warnings                     ║
# ╚════════════════════════════════════════════════════════════════════════════╝
st.markdown("## ⚠️ Risk Management & Exit Rules")

rm_col1, rm_col2 = st.columns(2)

with rm_col1:
    st.markdown("### 🚫 Early Exit Signals (4H Candle Closes Against)")
    if early_exits["count"] > 0:
        for exit_sig in early_exits["exit_signals"]:
            severity_color = "#e74c3c" if exit_sig["severity"] == "HIGH" else "#f0a500"
            st.markdown(f"""
            <div style="background:#1a0a0a;border-left:4px solid {severity_color};border-radius:4px;padding:10px 12px;margin-bottom:8px;">
              <div style="color:{severity_color};font-weight:700;font-size:0.85rem;">{exit_sig['type']}</div>
              <div style="color:#e0e6f0;font-size:0.78rem;margin-top:3px;line-height:1.6;">
                <b>Action:</b> {exit_sig['action']}<br>
                Pips at exit: {exit_sig['pips_at_exit']:.1f}
              </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ No early exit signals - position structure intact")

with rm_col2:
    st.markdown("### 🚨 Do NOT Enter Before News Warning")
    if news_warnings["active_warnings"]:
        for warning in news_warnings["active_warnings"]:
            st.markdown(f"""
            <div style="background:#1a1010;border-left:4px solid #e74c3c;border-radius:4px;padding:10px 12px;margin-bottom:8px;">
              <div style="color:#e74c3c;font-weight:700;font-size:0.85rem;">{warning['status']}</div>
              <div style="color:#e0e6f0;font-size:0.78rem;margin-top:3px;line-height:1.6;">
                <b>{warning['event']}</b> ({warning['currency']})<br>
                <span style="color:#f0a500;">Time until: {warning['time_until_hours']:.1f}h</span>
              </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ No high-impact news events within 2 hours - Safe to trade")

st.divider()


# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  DYNAMIC TRAILING STOP & ADVANCED EXIT MANAGEMENT                         ║
# ╚════════════════════════════════════════════════════════════════════════════╝
st.markdown("## 📈 Dynamic Trailing Stop (4H Swing High/Low ± ATR×2.0)")

if "error" not in trailing_stop_data:
    ts_col1, ts_col2 = st.columns(2)
    
    with ts_col1:
        st.markdown(f"""
        <div class="section-panel" style="background:#252a3a;">
            <div style="padding:12px 14px;">
              <div style="font-size:0.8rem;color:#8b949e;text-transform:uppercase;font-weight:600;margin-bottom:8px;">
                {trailing_stop_data.get('type', 'N/A')}
              </div>
              <div style="font-size:1rem;font-weight:700;color:#e0e6f0;margin-bottom:6px;">
                Trailing Stop: <span style="color:#58a6ff;">{trailing_stop_data.get('trailing_stop', 0):.5f}</span>
              </div>
              <div style="font-size:0.78rem;color:#8b949e;line-height:1.6;">
                <div>Stop distance: <span style="color:#e0e6f0;">{trailing_stop_data.get('stop_distance_pips', 0):.1f} pips</span></div>
                <div>ATR (4H): <span style="color:#58a6ff;">{trailing_stop_data.get('atr_value', 0):.5f}</span></div>
                <div style="margin-top:6px;color:#c9d1d9;">{trailing_stop_data.get('moving_target', 'N/A')}</div>
              </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with ts_col2:
        status_color = "#3fb950" if trailing_stop_data.get("status") == "ACTIVE" else "#e74c3c"
        st.markdown(f"""
        <div style="background:#1e2233;border:2px solid {status_color};border-radius:6px;padding:12px 14px;">
          <div style="color:{status_color};font-weight:700;font-size:0.85rem;margin-bottom:6px;">
            {trailing_stop_data.get('status', 'UNKNOWN')}
          </div>
          <div style="font-size:0.78rem;color:#8b949e;line-height:1.6;">
            Current price: <span style="color:#e0e6f0;">{current_price:.5f}</span><br>
            {trailing_stop_data.get('moving_target', 'Trail your stop as price moves')}
          </div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ── Chart Controls Help
st.markdown("""
<div style="background:#1e2233;border:1px solid #2e3347;border-radius:4px;padding:8px 12px;margin-bottom:8px;font-size:0.75rem;color:#8b949e;">
  <b style="color:#c9d1d9;">Chart Controls:</b> Scroll to zoom • Drag to pan • Double-click to reset • Hover for details • Use toolbar icons (top right) to select, zoom, or download
</div>
""", unsafe_allow_html=True)

# ── OHLC bar
if not df.empty:
    last     = df.iloc[-1]
    pip_range = round(abs(float(last["High"]) - float(last["Low"])) * 10000, 1)
    st.markdown(f"""
    <div class="ohlc-bar">
      <span style="color:#8b949e;">{last['dt'].strftime('%I:%M%p %b %d')}</span>
      <span>●&nbsp; Open:<span style="margin-left:4px;">{float(last['Open']):.4f}</span></span>
      <span>High:<span style="color:#3fb950;margin-left:4px;">{float(last['High']):.4f}</span></span>
      <span>Low:<span style="color:#e74c3c;margin-left:4px;">{float(last['Low']):.4f}</span></span>
      <span>Close:<span style="margin-left:4px;">{float(last['Close']):.4f}</span></span>
      <span style="color:#8b949e;">({pip_range} pip range)</span>
    </div>""", unsafe_allow_html=True)

# ── Chart
fig = build_eurusd_chart(df, dxy_df, cal_events, news_items, dxy_an)
chart_config = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "toImageButtonOptions": {"format": "png", "filename": "eurusd_chart"},
    "scrollZoom": True,
}
st.plotly_chart(fig, use_container_width=True, config=chart_config)


# ══════════════════════════════════════════════════════════════════════════════
# MASTER SIGNAL PANEL  (full width above news/calendar)
# ══════════════════════════════════════════════════════════════════════════════
sig_val   = master_sig["signal"]
sig_score = master_sig["score"]
sig_cls   = {"BULLISH": "sig-bull", "BEARISH": "sig-bear", "NEUTRAL": "sig-neu"}[sig_val]
sig_icon  = {"BULLISH": "🟢 BULLISH", "BEARISH": "🔴 BEARISH", "NEUTRAL": "⚪ NEUTRAL"}[sig_val]

reasons_html = "".join(
    f'<div style="margin:2px 0;">{r}</div>' for r in master_sig["reasons"]
) or "<div>No significant signals detected.</div>"

# Supply/demand level tags
sup_lvls = dxy_an.get("supply_levels", [])
dem_lvls = dxy_an.get("demand_levels", [])
sup_html = " ".join(f'<span class="level-supply">DXY Sup {x}</span>' for x in sup_lvls) or "—"
dem_html = " ".join(f'<span class="level-demand">DXY Dem {x}</span>' for x in dem_lvls) or "—"

st.markdown(f"""
<div class="signal-card">
  <div class="signal-title">🎯 Master EUR/USD Signal — All factors combined</div>
  <span class="{sig_cls}">{sig_icon}</span>
  <span style="color:#8b949e;font-size:0.85rem;margin-left:12px;">Composite Score: <b style="color:#e0e6f0;">{sig_score:+d}</b></span>
  <div class="signal-detail" style="margin-top:8px;">{reasons_html}</div>
  <div style="margin-top:8px;font-size:0.74rem;color:#8b949e;">
    DXY Key Levels →
    <span style="margin-left:6px;">Supply (resistance): {sup_html}</span>
    <span style="margin-left:10px;">Demand (support): {dem_html}</span>
  </div>
  <div style="margin-top:4px;font-size:0.70rem;color:#4a5568;">
    💡 When DXY forms a supply level, a demand zone is forming on EUR/USD (bullish).
    When DXY forms a demand level, a supply zone is forming on EUR/USD (bearish).
    Green news markers = USD weakness signal. Red markers = USD strength signal.
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CONFLUENCE CHECKLIST & SETUP ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 🎯 Timeframe Stack Analysis — 8-Factor Confluence Checklist")

# Confluence factors display
factors = confluence_analysis.get("factors", {})
confluence_score = confluence_analysis.get("confluence_score", 0)
setup_quality = confluence_analysis.get("setup_quality", "NO DATA")
recommendation = confluence_analysis.get("recommendation", "")

# Create tab-based layout
col1, col2, col3 = st.columns([1, 2, 1.5])

with col1:
    st.markdown(f"""
    <div style="background:#1e2233;border:1px solid #2e3347;border-radius:4px;padding:12px;text-align:center;">
      <div style="font-size:2.5rem;font-weight:700;color:#58a6ff;margin-bottom:4px;">{confluence_score}</div>
      <div style="font-size:0.9rem;color:#8b949e;margin-bottom:8px;">Factors Aligned</div>
      <div style="font-size:0.85rem;font-weight:600;color:#e0e6f0;background:#252a3a;padding:8px;border-radius:3px;">
        Minimum: 5/8
      </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # Setup quality badge
    if "✅" in setup_quality:
        quality_color = "#3fb950"
        quality_bg = "#3fb95020"
    elif "🟡" in setup_quality:
        quality_color = "#f0a500"
        quality_bg = "#f0a50020"
    else:
        quality_color = "#e74c3c"
        quality_bg = "#e74c3c20"
    
    st.markdown(f"""
    <div style="background:{quality_bg};border:1px solid {quality_color};border-radius:4px;padding:12px;">
      <div style="font-size:1rem;font-weight:700;color:{quality_color};margin-bottom:6px;">{setup_quality}</div>
      <div style="font-size:0.75rem;color:#8b949e;line-height:1.6;">{recommendation}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="background:#1e2233;border:1px solid #2e3347;border-radius:4px;padding:12px;">
      <div style="font-size:0.8rem;color:#8b949e;margin-bottom:4px;"><b>Setup Bias</b></div>
      <div style="font-size:1.1rem;font-weight:700;color:#e0e6f0;">{setup_bias.upper()}</div>
      <div style="font-size:0.75rem;color:#8b949e;margin-top:4px;">DXY: {dxy_an.get('trend', 'NEUTRAL')}</div>
    </div>
    """, unsafe_allow_html=True)

# Detailed factor breakdown
st.markdown("### Detailed Breakdown — All 8 Factors")
factor_cols = st.columns(2)

for idx, (factor_num, factor_info) in enumerate(factors.items()):
    col = factor_cols[idx % 2]
    with col:
        met = factor_info.get("met", False)
        status_color = "#3fb950" if met else "#8b949e"
        status_icon = "✅" if met else "❌"
        
        if factor_num == 1:
            mandatory = " ⚠️ MANDATORY" if not met else ""
            detail_text = f"{mandatory}<br>{factor_info.get('detail', '')}"
        else:
            detail_text = factor_info.get('detail', '')
        
        st.markdown(f"""
        <div style="background:#1e2233;border:1px solid {status_color};border-radius:4px;padding:10px;margin-bottom:8px;">
          <div style="display:flex;justify-content:space-between;align-items:start;gap:8px;">
            <div style="flex:1;">
              <div style="font-size:0.8rem;color:#8b949e;margin-bottom:2px;"><b>Factor {factor_num}</b></div>
              <div style="font-size:0.9rem;color:#e0e6f0;font-weight:600;">{factor_info.get('name', '')}</div>
              <div style="font-size:0.75rem;color:#8b949e;margin-top:3px;">{detail_text}</div>
            </div>
            <div style="font-size:1.2rem;color:{status_color};">{status_icon}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

# Risk Management Section
st.markdown("### Risk Management — ATR-Based Stops & Targets")

if "error" not in risk_metrics:
    rm = risk_metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("ATR (pips)", f"{rm.get('atr_pips', 0):.1f}")
    
    with col2:
        st.metric("Stop Distance", f"{rm.get('stop_distance_pips', 0):.1f} pips")
    
    with col3:
        st.metric("Min Target (40-50p)", f"{rm.get('target1_pips', 0):.1f} pips")
    
    with col4:
        st.metric("Extended Target", f"{rm.get('target2_pips', 0):.1f} pips")
    
    # Risk/Reward table
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style="background:#1e2233;border:1px solid #2e3347;border-radius:4px;padding:10px;margin-bottom:8px;">
          <div style="font-size:0.75rem;color:#8b949e;text-transform:uppercase;margin-bottom:8px;"><b>Entry & Stops</b></div>
          <div style="font-size:0.85rem;color:#e0e6f0;">
            <b>Entry:</b> {rm.get('current_price', 0):.5f}<br>
            <b>Stop:</b> {rm.get('stop_loss', 0):.5f}<br>
            <b>Risk:</b> {rm.get('stop_distance_pips', 0):.1f} pips
          </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background:#1e2233;border:1px solid #2e3347;border-radius:4px;padding:10px;margin-bottom:8px;">
          <div style="font-size:0.75rem;color:#8b949e;text-transform:uppercase;margin-bottom:8px;"><b>Risk/Reward Ratio</b></div>
          <div style="font-size:0.85rem;color:#e0e6f0;">
            <b>Min Target (40-50p):</b> {rm.get('rr_ratio_min', 0):.1f}:1<br>
            <b>Extended Target (80-120p):</b> {rm.get('rr_ratio_extended', 0):.1f}:1
          </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.warning("❌ Insufficient data for risk calculations")


# ══════════════════════════════════════════════════════════════════════════════
# MASTER SIGNAL SUMMARY - FINAL VERDICT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 🎯 MASTER SIGNAL SUMMARY — EUR/USD Market Prediction")

# Get verdict and confidence
verdict = all_signals.get("overall_verdict", "NO DATA")
confidence = all_signals.get("confidence", 0)
bullish_count = all_signals.get("bullish_count", 0)
bearish_count = all_signals.get("bearish_count", 0)
neutral_count = all_signals.get("neutral_count", 0)
total_signals = all_signals.get("signal_count", 0)

# Color based on verdict
if "BULLISH" in verdict and "SLIGHT" not in verdict:
    verdict_color = "#3fb950"
    verdict_bg = "#3fb95020"
    verdict_icon = "🟢 BULLISH"
elif "BEARISH" in verdict and "SLIGHT" not in verdict:
    verdict_color = "#e74c3c"
    verdict_bg = "#e74c3c20"
    verdict_icon = "🔴 BEARISH"
elif "SLIGHTLY BULLISH" in verdict:
    verdict_color = "#3fb950"
    verdict_bg = "#3fb95010"
    verdict_icon = "🟢 SLIGHTLY BULLISH"
elif "SLIGHTLY BEARISH" in verdict:
    verdict_color = "#e74c3c"
    verdict_bg = "#e74c3c10"
    verdict_icon = "🔴 SLIGHTLY BEARISH"
else:
    verdict_color = "#8b949e"
    verdict_bg = "#8b949e20"
    verdict_icon = "⚪ NEUTRAL"

# Master verdict box
col1, col2, col3 = st.columns([2, 3, 1])

with col1:
    st.markdown(f"""
    <div style="background:{verdict_bg};border:2px solid {verdict_color};border-radius:8px;padding:20px;text-align:center;">
      <div style="font-size:2rem;font-weight:700;color:{verdict_color};margin-bottom:8px;">{verdict_icon}</div>
      <div style="font-size:1.3rem;font-weight:700;color:#e0e6f0;">{verdict}</div>
      <div style="font-size:0.9rem;color:#8b949e;margin-top:8px;">Confidence: <b style="color:{verdict_color};">{confidence:.0f}%</b></div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background:#1e2233;border:1px solid #2e3347;border-radius:8px;padding:20px;">
      <div style="font-size:0.75rem;color:#8b949e;text-transform:uppercase;margin-bottom:12px;"><b>Signal Breakdown</b></div>
      <div style="display:flex;gap:15px;">
        <div style="flex:1;text-align:center;">
          <div style="font-size:1.8rem;font-weight:700;color:#3fb950;">{bullish_count}</div>
          <div style="font-size:0.75rem;color:#8b949e;">Bullish</div>
        </div>
        <div style="flex:1;text-align:center;">
          <div style="font-size:1.8rem;font-weight:700;color:#e74c3c;">{bearish_count}</div>
          <div style="font-size:0.75rem;color:#8b949e;">Bearish</div>
        </div>
        <div style="flex:1;text-align:center;">
          <div style="font-size:1.8rem;font-weight:700;color:#8b949e;">{neutral_count}</div>
          <div style="font-size:0.75rem;color:#8b949e;">Neutral</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="background:#1e2233;border:1px solid #2e3347;border-radius:8px;padding:20px;text-align:center;">
      <div style="font-size:0.75rem;color:#8b949e;text-transform:uppercase;margin-bottom:8px;"><b>Total Signals</b></div>
      <div style="font-size:2.5rem;font-weight:700;color:#58a6ff;">{total_signals}</div>
      <div style="font-size:0.75rem;color:#8b949e;margin-top:8px;">Active Signals</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# DETAILED SIGNALS DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📊 Detailed Signal Analysis")

# Create tabs for different signal categories
sig_tab1, sig_tab2, sig_tab3, sig_tab4 = st.tabs(
    ["🔵 EUR/USD + DXY Indicators", "🎯 Confluence Factors", "📰 News Signals", "📅 Calendar Signals"]
)

with sig_tab1:
    eurusd_sigs = all_signals.get("eurusd_indicators", [])
    if eurusd_sigs:
        for sig in eurusd_sigs:
            sig_type = sig.get("signal", "NEUTRAL")
            color = "#3fb950" if sig_type == "BULLISH" else ("#e74c3c" if sig_type == "BEARISH" else "#8b949e")
            icon = "🟢" if sig_type == "BULLISH" else ("🔴" if sig_type == "BEARISH" else "⚪")
            
            # Highlight DXY signals (leading indicators)
            is_dxy = "DXY" in sig.get('indicator', '')
            border_style = "border-left:6px solid" if is_dxy else "border-left:3px solid"
            
            st.markdown(f"""
            <div style="background:#1e2233;{border_style} {color};border-radius:4px;padding:12px;margin-bottom:8px;opacity:{'1' if is_dxy else '0.9'};">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <div style="font-size:0.85rem;font-weight:600;color:#e0e6f0;">{icon} {sig.get('indicator', '')}</div>
                  <div style="font-size:0.75rem;color:#8b949e;margin-top:2px;">{sig.get('detail', '')}</div>
                </div>
                <div style="text-align:right;font-weight:700;color:{color};font-size:0.95rem;">{sig_type}</div>
              </div>
              <div style="font-size:0.72rem;color:#8b949e;margin-top:4px;">Value: {sig.get('value', '—')}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No EUR/USD indicator signals")

with sig_tab2:
    conf_sigs = all_signals.get("eurusd_confluence", [])
    if conf_sigs:
        for sig in conf_sigs:
            sig_type = sig.get("signal", "✅ MET")
            is_directional = "BULLISH" in str(sig_type) or "BEARISH" in str(sig_type)
            
            if is_directional:
                color = "#3fb950" if sig_type == "BULLISH" else ("#e74c3c" if sig_type == "BEARISH" else "#8b949e")
                icon = "🟢" if sig_type == "BULLISH" else ("🔴" if sig_type == "BEARISH" else "✅")
            else:
                color = "#3fb950"
                icon = "✅"
            
            st.markdown(f"""
            <div style="background:#1e2233;border-left:4px solid {color};border-radius:4px;padding:12px;margin-bottom:8px;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <div style="font-size:0.85rem;font-weight:600;color:#e0e6f0;">{icon} {sig.get('factor', '')}</div>
                  <div style="font-size:0.75rem;color:#8b949e;margin-top:2px;">{sig.get('detail', '')}</div>
                </div>
                <div style="text-align:right;font-weight:700;color:{color};font-size:0.95rem;">{sig_type}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No confluence factors met")

with sig_tab3:
    news_sigs = all_signals.get("news_signals", [])
    if news_sigs:
        for sig in news_sigs:
            sig_type = sig.get("signal", "NEUTRAL")
            color = "#3fb950" if sig_type == "BULLISH" else ("#e74c3c" if sig_type == "BEARISH" else "#8b949e")
            icon = "🟢" if sig_type == "BULLISH" else ("🔴" if sig_type == "BEARISH" else "⚪")
            
            st.markdown(f"""
            <div style="background:#1e2233;border-left:4px solid {color};border-radius:4px;padding:12px;margin-bottom:8px;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <div style="font-size:0.85rem;font-weight:600;color:#e0e6f0;">{icon} {sig.get('title', '')}</div>
                  <div style="font-size:0.75rem;color:#8b949e;margin-top:2px;">Source: {sig.get('source', 'Unknown')}</div>
                </div>
                <div style="text-align:right;font-weight:700;color:{color};font-size:0.95rem;">{sig_type}</div>
              </div>
              <div style="font-size:0.72rem;color:#8b949e;margin-top:3px;">{sig.get('time', '')}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent news signals")

with sig_tab4:
    cal_sigs = all_signals.get("calendar_signals", [])
    if cal_sigs:
        for sig in cal_sigs:
            sig_type = sig.get("signal", "NEUTRAL")
            color = "#3fb950" if sig_type == "BULLISH" else ("#e74c3c" if sig_type == "BEARISH" else "#8b949e")
            icon = "🟢" if sig_type == "BULLISH" else ("🔴" if sig_type == "BEARISH" else "⚪")
            impact = sig.get("impact", "Unknown")
            impact_color = "#e74c3c" if impact == "High" else ("#f0a500" if impact == "Medium" else "#e67e22")
            
            st.markdown(f"""
            <div style="background:#1e2233;border-left:4px solid {color};border-radius:4px;padding:12px;margin-bottom:8px;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <div style="font-size:0.85rem;font-weight:600;color:#e0e6f0;">{icon} {sig.get('title', '')} ({sig.get('currency', '')})</div>
                  <div style="font-size:0.75rem;color:#8b949e;margin-top:2px;">
                    Impact: <span style="background:{impact_color}20;color:{impact_color};padding:1px 5px;border-radius:2px;font-weight:600;">{impact}</span>
                  </div>
                </div>
                <div style="text-align:right;font-weight:700;color:{color};font-size:0.95rem;">{sig_type}</div>
              </div>
              <div style="font-size:0.72rem;color:#8b949e;margin-top:3px;">{sig.get('time', '')}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No nearby calendar signals")


# ══════════════════════════════════════════════════════════════════════════════
# BACKTESTING RESULTS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📈 Strategy Backtest Results (Last 30 days)")

if "error" not in backtest_result:
    bt = backtest_result
    
    # Summary metrics in columns
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Trades", bt.get("total_trades", 0))
    with col2:
        win_pct = bt.get("win_rate", 0)
        st.metric("Win Rate", f"{win_pct:.1f}%", delta=f"{win_pct-50:.1f}%" if win_pct != 50 else None)
    with col3:
        st.metric("Wins | Losses", f"{bt.get('wins', 0)} | {bt.get('losses', 0)}")
    with col4:
        st.metric("Total P&L", f"{bt.get('total_pnl_pips', 0):.0f} pips")
    with col5:
        st.metric("Profit Factor", f"{bt.get('profit_factor', 0):.2f}")
    with col6:
        max_dd = bt.get("max_drawdown", 0)
        st.metric("Max Drawdown", f"-{max_dd:.1f}%", delta=-max_dd)
    
    # Trades table
    if bt.get("trades"):
        st.subheader("Trade History")
        trades_data = []
        for t in bt.get("trades", []):
            trades_data.append({
                "Entry Date": t["entry_date"],
                "Exit Date": t["exit_date"],
                "Type": t["type"],
                "Entry Price": f"{t['entry_price']:.5f}",
                "Exit Price": f"{t['exit_price']:.5f}",
                "P&L (pips)": f"{t['pnl_pips']:.0f}",
                "Status": t["status"],
                "Days": t["days"]
            })
        
        trades_df = pd.DataFrame(trades_data)
        st.dataframe(trades_df, use_container_width=True, hide_index=True)
    
    # Equity curve chart
    if len(bt.get("equity_curve", [])) > 1:
        st.subheader("Equity Curve")
        
        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(
            x=bt.get("dates", []),
            y=bt.get("equity_curve", []),
            mode="lines",
            name="Equity",
            line=dict(color="#3fb950", width=2),
            fill="tozeroy",
            fillcolor="rgba(63, 185, 80, 0.1)"
        ))
        
        fig_equity.update_layout(
            title="Portfolio Equity Over Time",
            xaxis_title="Date",
            yaxis_title="Equity (Units)",
            template="plotly_dark",
            hovermode="x unified",
            paper_bgcolor="#1b1f2b",
            plot_bgcolor="#1b1f2b",
            font=dict(color="#e0e6f0"),
            height=400
        )
        
        st.plotly_chart(fig_equity, use_container_width=True)
    
    # Statistics summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style="background:#1e2233;border:1px solid #2e3347;border-radius:4px;padding:12px;">
          <div style="font-size:0.75rem;color:#8b949e;text-transform:uppercase;margin-bottom:8px;"><b>Performance</b></div>
          <div style="font-size:0.85rem;color:#e0e6f0;line-height:2;">
            <b>Average Win:</b> {bt.get('avg_win_pips', 0):.1f} pips<br>
            <b>Average Loss:</b> {bt.get('avg_loss_pips', 0):.1f} pips<br>
            <b>Win/Loss Ratio:</b> {bt.get('avg_win_pips', 0) / max(bt.get('avg_loss_pips', 1), 0.1):.2f}:1<br>
            <b>Total Return:</b> {bt.get('total_return', 0):.0f} units
          </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background:#1e2233;border:1px solid #2e3347;border-radius:4px;padding:12px;">
          <div style="font-size:0.75rem;color:#8b949e;text-transform:uppercase;margin-bottom:8px;"><b>Summary</b></div>
          <div style="font-size:0.85rem;color:#e0e6f0;line-height:2;">
            <b>Period:</b> {bt.get('lookback_days', 0)} days<br>
            <b>Starting Equity:</b> 1000 units<br>
            <b>Final Equity:</b> {bt.get('final_equity', 0):.0f} units<br>
            <b>Max Drawdown:</b> -{bt.get('max_drawdown', 0):.1f}%
          </div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.warning(f"❌ Backtest Error: {backtest_result.get('error', 'Unknown error')}")


# ══════════════════════════════════════════════════════════════════════════════
# BOTTOM PANELS: News  |  Calendar
# ══════════════════════════════════════════════════════════════════════════════
col_left, col_right = st.columns(2)

# ── News panel
with col_left:
    SIG_BADGE = {
        "BULL": '<span class="news-sig-bull">USD WEAK ▲ EUR/USD</span>',
        "BEAR": '<span class="news-sig-bear">USD STRONG ▼ EUR/USD</span>',
        "":     "",
    }
    stories_html = "".join(
        f'<div class="story-item">'
        f'<span class="story-time">{n["dt"].strftime("%b %d %H:%M")}</span>'
        f'{SIG_BADGE.get(n.get("signal",""), "")}'
        f'<span class="story-title" style="margin-left:4px;"><a href="{n["link"]}" target="_blank">{n["title"]}</a></span>'
        f'</div>'
        for n in news_items[:20]
    ) or '<div class="story-item" style="color:#8b949e;">No high-impact stories found.</div>'

    st.markdown(f"""
    <div class="section-panel">
      <div class="section-header">
        📰 Latest Stories — EUR/USD / DXY Signals
        &nbsp;<span style="background:#e74c3c;color:#fff;font-size:0.65rem;padding:1px 5px;border-radius:3px;">HIGH IMPACT</span>
        &nbsp;<span style="background:#3fb950;color:#000;font-size:0.65rem;padding:1px 5px;border-radius:3px;">🟢 = USD Weak</span>
        &nbsp;<span style="background:#e74c3c;color:#fff;font-size:0.65rem;padding:1px 5px;border-radius:3px;">🔴 = USD Strong</span>
      </div>
      {stories_html}
    </div>""", unsafe_allow_html=True)

# ── Calendar panel  (shows today + upcoming, past events dimmed)
with col_right:
    now          = datetime.utcnow()
    today_start  = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # Show all events from today onwards (including past ones from today)
    visible_events = [e for e in cal_events if e["dt"] >= today_start]

    if not visible_events:
        # Fallback: show last 10 events of any day this week
        visible_events = cal_events[-10:] if cal_events else []

    def cal_signal_badge(ev):
        """Generate a mini signal badge for events that have actual vs forecast."""
        act_s  = ev.get("actual", "")
        fore_s = ev.get("forecast", "")
        if not act_s or not fore_s:
            return ""
        try:
            def pv(s):
                s = re.sub(r"[^0-9.\-]", "", str(s))
                return float(s) if s else None
            a, f = pv(act_s), pv(fore_s)
            if a is None or f is None:
                return ""
            diff = (a - f) / abs(f) * 100 if f != 0 else 0
            ccy  = ev["currency"]
            if abs(diff) < 3:
                return ""
            beat = diff > 0
            # USD beat → EURUSD bearish; USD miss → EURUSD bullish
            # EUR beat → EURUSD bullish; EUR miss → EURUSD bearish
            if (ccy == "USD" and not beat) or (ccy == "EUR" and beat):
                return '<span style="color:#3fb950;font-size:0.65rem;margin-left:4px;">▲EUR/USD</span>'
            else:
                return '<span style="color:#e74c3c;font-size:0.65rem;margin-left:4px;">▼EUR/USD</span>'
        except:
            return ""

    def impact_badge(impact):
        """Color badge for event impact level."""
        colors = {"High": "#e74c3c", "Medium": "#f0a500", "Low": "#e67e22"}
        color = colors.get(impact, "#8b949e")
        return f'<span style="background:{color}20;border:1px solid {color};color:{color};font-size:0.65rem;padding:1px 5px;border-radius:3px;margin-right:6px;font-weight:600;">{impact}</span>'

    events_html = "".join(
        f'<div class="story-item">'
        f'<span class="story-time">{e["dt"].strftime("%b %d %H:%M")}</span> '
        f'{impact_badge(e.get("impact", "Low"))}'
        f'<b style="color:#e0e6f0;">{e["currency"]}</b> {e["title"]}'
        f'{cal_signal_badge(e)}'
        f'<div style="font-size:0.70rem;color:#8b949e;margin-top:2px;">'
        f'Actual: <span style="color:#e0e6f0;">{e.get("actual","—")}</span> | '
        f'Forecast: {e.get("forecast","—")} | Prev: {e.get("previous","—")}'
        f'</div>'
        f'</div>'
        for e in visible_events
    ) or '<div class="story-item" style="color:#8b949e;">No upcoming events today.</div>'

    st.markdown(f"""
    <div class="section-panel">
      <div class="section-header">
        📅 Economic Calendar — Today & Upcoming
        &nbsp;<span style="background:#e74c3c20;border:1px solid #e74c3c;color:#e74c3c;font-size:0.65rem;padding:1px 5px;border-radius:3px;">HIGH</span>
        &nbsp;<span style="background:#f0a50020;border:1px solid #f0a500;color:#f0a500;font-size:0.65rem;padding:1px 5px;border-radius:3px;">MEDIUM</span>
        &nbsp;<span style="background:#e67e2220;border:1px solid #e67e22;color:#e67e22;font-size:0.65rem;padding:1px 5px;border-radius:3px;">LOW</span>
      </div>
      {events_html}
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TRADING STRATEGY GUIDE
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("📚 Trading Strategy Guide — Complete Ruleset"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### ⏰ Timeframe Stack (Your Map → Signal → Entry)
        1. **Daily Chart (Map)** - Overall trend direction & major zones. Check once per morning.
        2. **4H Chart (Signal Generator)** - DXY correlation, market structure, confluence factors. Main analysis.
        3. **1H Chart (Entry)** - Donchian breakout or rejection candle. Precise entry timing.
        
        ### 🎯 DXY as Lead Indicator (Foundation First)
        - **DXY Downtrend** (ADX > 20) → EUR/USD Bias = BULLISH
        - **DXY Uptrend** (ADX > 20) → EUR/USD Bias = BEARISH
        - **Key Setup**: DXY approaching swing high/low = highest probability entry point
        - Without clear DXY trend, the setup does not exist yet. Wait.
        
        ### 📋 8-Factor Confluence Checklist
        **Minimum: 5/8 factors must align before entering**
        
        1. **DXY Trend** (MANDATORY) - Must be clear trend with ADX > 20
        2. **DXY at Key Level** - Within 0.3% of swing high/low
        3. **Market Structure** - HH/HL (bullish) or LH/LL (bearish) on EUR/USD 4H
        4. **ADX on EUR/USD** - Must be > 20 (confirms trend energy)
        5. **Price at Zone** - At demand (support) or supply (resistance) zone
        6. **Donchian Breakout** - 1H close above upper band (buy) or below lower band (sell)
        7. **RSI Divergence** - Lower low in price, higher low in RSI = bullish signal (bonus)
        8. **Session Timing** - London (08:00-17:00) or London/NY overlap (13:00-17:00) UTC
        """)
    
    with col2:
        st.markdown("""
        ### 💼 Entry Rules (1H Chart)
        - **Donchian Breakout**: Price closes ABOVE 20-period upper band (buy) or BELOW lower band (sell)
        - **Rejection Candle**: Pin bar, hammer, or engulfing at the zone that closes back inside
        - **Entry Timing**: At candle close, never mid-candle. Never on limit orders.
        
        ### 🛑 Stop Loss (Risk Management)
        ```
        Stop = Zone Edge + (ATR × 1.0)
        ```
        - **Bullish Trade**: Stop = lowest point of demand zone - ATR buffer
        - **Bearish Trade**: Stop = highest point of supply zone + ATR buffer
        - Typical stop: 15-25 pips (not fixed, depends on ATR)
        - Reason: If price breaks the zone, your thesis is invalidated. Exit before this happens.
        
        ### 🎁 Take Profit & Exit Management
        1. **At 40-50 pips profit** → Move stop to breakeven (lock in the idea)
        2. **At 80-100 pips profit** → Close 30-40% of position (lock in real profit)
        3. **Remaining position** → Trail stop at ATR × 2.0 below recent 4H swing low
        4. **Don't pick exit level** → Let trailing stop do the work. Check once per 4H candle.
        5. **Early Exit Rule** → If 4H candle closes strongly against you AND breaks the entry zone, exit immediately
        
        ### 📰 News Integration
        - **Before High-Impact Release** (NFP, CPI, FOMC, ECB):
          - If NOT at breakeven yet → Close position or accept conscious risk
          - If at breakeven → Can hold (stop protects you)
        - **Post-News Pullback** (Best Entry):
          - News creates direction, pullback creates entry, zone creates stop
          - Setup after USD CPI miss: DXY rejects resistance → EUR/USD pulls back to demand zone → BUY
        
        ### 📊 Realistic Expectations (40-50 pip minimum targets)
        - **~8-12 setups per month** that meet 5+ factor criteria
        - **~5-7 actual entries** from those setups
        - **58-65% win rate** with proper execution
        - **Avg loser**: -15 to -25 pips
        - **Avg winner**: 80-150 pips (properly managed with breakeven + partials + trailing)
        - **Math**: Even at 60% win rate, 3-4x winner/loser ratio = +2-15% monthly returns
        
        ⚠️ **Key Psychology**: At +50 pips you're NOT exiting. You're BARELY breakeven. That's when 150-200 pip winners are born.
        """)


# ── Footer
st.markdown(
    f"<br><span style='color:#4a5568;font-size:0.73rem;'>"
    f"TF: {st.session_state.tf} · {len(cal_events)} calendar events (showing today+) · "
    f"{len(news_items)} news items · DXY: {dxy_str} · Master Signal: {sig_val} ({sig_score:+d}) · "
    f"{datetime.utcnow().strftime('%H:%M UTC')}"
    f"</span>", unsafe_allow_html=True
)
