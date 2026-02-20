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
    df = df[["dt", "Open", "High", "Low", "Close"]].dropna()
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
        if ev.get("impact") not in ("High", "high"):
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

    if   score >= 2:   result["trend"] = "UPTREND"
    elif score <= -2:  result["trend"] = "DOWNTREND"
    else:              result["trend"] = "NEUTRAL"

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

    fig = make_subplots(
        rows=5, cols=1,
        row_heights=[0.52, 0.22, 0.08, 0.08, 0.10],
        vertical_spacing=0.005,
        shared_xaxes=True,
    )

    # ── Row 1: EUR/USD Candlestick
    fig.add_trace(go.Candlestick(
        x=df["dt"],
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        increasing=dict(line=dict(color="#4a9eff", width=1), fillcolor="#4a9eff"),
        decreasing=dict(line=dict(color="#4a9eff", width=1), fillcolor="#1b1f2b"),
        name="EUR/USD", hoverinfo="x+y",
    ), row=1, col=1)

    # Session shading on main chart
    for blk in session_blocks:
        fig.add_shape(
            type="rect", xref="x", yref="paper",
            x0=blk["x0"], x1=blk["x1"], y0=0.48, y1=1.0,
            fillcolor=blk["color"], line=dict(width=0), layer="below",
        )

    # ── Row 2: DXY line chart (correlation panel)
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
                line=dict(color="#f0a500", width=1.5),
                name="DXY", showlegend=False,
            ), row=2, col=1)
            fig.add_trace(go.Scatter(
                x=dxy_merged["dt"], y=e20,
                mode="lines", line=dict(color="#58a6ff", width=1, dash="dot"),
                name="EMA20", showlegend=False,
            ), row=2, col=1)
            fig.add_trace(go.Scatter(
                x=dxy_merged["dt"], y=e50,
                mode="lines", line=dict(color="#e74c3c", width=1, dash="dot"),
                name="EMA50", showlegend=False,
            ), row=2, col=1)

            # Colour DXY trend arrow in annotation
            trend = dxy_analysis.get("trend", "NEUTRAL")
            arrow = {"UPTREND": "▲ UPTREND", "DOWNTREND": "▼ DOWNTREND", "NEUTRAL": "◆ NEUTRAL"}.get(trend, "")
            color = {"UPTREND": "#e74c3c", "DOWNTREND": "#3fb950", "NEUTRAL": "#8b949e"}.get(trend, "#8b949e")
            fig.add_annotation(
                x=dxy_merged["dt"].iloc[-1], y=float(closes.iloc[-1]),
                xref="x2", yref="y2",
                text=f"DXY {arrow}",
                showarrow=False, bgcolor=color,
                font=dict(size=9, color="#fff"),
                xanchor="right", yanchor="bottom",
            )

    # ── Row 3: Sessions strip
    for blk in session_blocks:
        mid = blk["x0"] + (blk["x1"] - blk["x0"]) / 2
        fig.add_trace(go.Scatter(
            x=[blk["x0"], blk["x0"], blk["x1"], blk["x1"], blk["x0"]],
            y=[0, 1, 1, 0, 0],
            fill="toself", fillcolor=blk["color"],
            line=dict(width=0), mode="lines",
            showlegend=False, hoverinfo="skip",
        ), row=3, col=1)

    seen_s = {}
    for blk in session_blocks:
        n = blk["name"]
        mid = blk["x0"] + (blk["x1"] - blk["x0"]) / 2
        if n not in seen_s or (mid - seen_s[n]).total_seconds() > 86400:
            seen_s[n] = mid
            fig.add_annotation(
                x=mid, y=0.5, xref="x3", yref="y3",
                text=f"<b>{n}</b>", showarrow=False,
                font=dict(size=8, color="rgba(200,210,220,0.7)"),
                xanchor="center", yanchor="middle",
            )

    # ── Row 4: Calendar markers
    cal_in = [e for e in cal_events if df["dt"].min() <= e["dt"] <= df["dt"].max()]
    if cal_in:
        fig.add_trace(go.Scatter(
            x=[e["dt"] for e in cal_in], y=[0.5] * len(cal_in),
            mode="markers",
            marker=dict(symbol="square", size=11, color="#e74c3c", line=dict(width=0)),
            name="Calendar",
            customdata=[
                f"<b>{e['currency']}</b>: {e['title']}<br>"
                f"Actual: <b>{e['actual'] or '—'}</b> | Forecast: {e['forecast'] or '—'} | Prev: {e['previous'] or '—'}"
                for e in cal_in
            ],
            hovertemplate="%{customdata}<extra>📅 Calendar</extra>",
            showlegend=False,
        ), row=4, col=1)
    else:
        fig.add_trace(go.Scatter(x=[df["dt"].iloc[0]], y=[0.5], mode="markers",
                                 marker=dict(opacity=0), showlegend=False, hoverinfo="skip"), row=4, col=1)

    # ── Row 5: News signal markers (bull=green, bear=red, neutral=orange)
    news_in = [n for n in news_items if df["dt"].min() <= n["dt"] <= df["dt"].max()]
    SIG_COLORS = {"BULL": "#3fb950", "BEAR": "#e74c3c", "": "#e67e22"}
    if news_in:
        fig.add_trace(go.Scatter(
            x=[n["dt"] for n in news_in], y=[0.5] * len(news_in),
            mode="markers",
            marker=dict(
                symbol="square", size=11,
                color=[SIG_COLORS.get(n.get("signal", ""), "#e67e22") for n in news_in],
                line=dict(width=0)
            ),
            name="News",
            customdata=[
                f"{n['title'][:90]}<br><b>Signal: {n.get('signal','NEUTRAL') or 'NEUTRAL'}</b>"
                for n in news_in
            ],
            hovertemplate="%{customdata}<extra>📰 News</extra>",
            showlegend=False,
        ), row=5, col=1)
    else:
        fig.add_trace(go.Scatter(x=[df["dt"].iloc[0]], y=[0.5], mode="markers",
                                 marker=dict(opacity=0), showlegend=False, hoverinfo="skip"), row=5, col=1)

    # ── Axes
    common_axis = dict(showgrid=False, zeroline=False, showticklabels=False,
                       showline=True, linecolor="#2e3347")
    fig.update_layout(
        height=780,
        paper_bgcolor="#1b1f2b",
        plot_bgcolor="#1b1f2b",
        margin=dict(l=52, r=65, t=4, b=4),
        xaxis_rangeslider_visible=False,
        hoverlabel=dict(bgcolor="#252a3a", font_size=12, bordercolor="#3e4460"),
        dragmode="pan",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#21262d", gridwidth=0.5,
                     zeroline=False, tickfont=dict(color="#6b7380", size=10),
                     showline=False, row=1, col=1)
    fig.update_yaxes(showgrid=True, gridcolor="#21262d", gridwidth=0.5,
                     zeroline=False, tickfont=dict(color="#8b949e", size=10),
                     side="right", tickformat=".4f", showline=False, row=1, col=1)
    fig.update_xaxes(showgrid=True, gridcolor="#21262d", gridwidth=0.5,
                     zeroline=False, tickfont=dict(color="#6b7380", size=10),
                     showline=False, row=2, col=1)
    fig.update_yaxes(showgrid=True, gridcolor="#21262d", gridwidth=0.5,
                     zeroline=False, tickfont=dict(color="#8b949e", size=9),
                     side="right", tickformat=".2f", showline=False, row=2, col=1)
    for r in [3, 4, 5]:
        fig.update_xaxes(**common_axis, row=r, col=1)
        fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False,
                         range=[0, 1], showline=True, linecolor="#2e3347", row=r, col=1)
    fig.update_xaxes(showticklabels=True, tickfont=dict(color="#6b7380", size=10), row=5, col=1)

    # Row labels
    for txt, y_paper in [("DXY", 0.34), ("Sessions", 0.17), ("Calendar", 0.09), ("News", 0.02)]:
        fig.add_annotation(
            x=-0.015, y=y_paper, xref="paper", yref="paper",
            text=f"<b>{txt}</b>", showarrow=False,
            font=dict(size=9, color="#8b949e"), xanchor="right", yanchor="middle",
        )
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
if "tf" not in st.session_state:
    st.session_state.tf = "1H"

tf          = st.session_state.tf
df          = get_price_data(tf)
dxy_df      = get_dxy_data(tf)
live_eur    = get_live_price("EURUSD=X")
live_dxy    = get_live_price("DX-Y.NYB")
cal_events  = get_calendar()
news_items  = get_news()
perf        = calc_perf(df)
dxy_an      = analyze_dxy(dxy_df)
master_sig  = generate_master_signal(dxy_an, news_items, cal_events)

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
            st.session_state.tf = tf_opt
            st.cache_data.clear()
            st.rerun()
with cols[-1]:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

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
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "scrollZoom": True})


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
        except Exception:
            return ""

    rows_html = ""
    for e in visible_events:
        is_past  = e["dt"] < now
        row_cls  = "ev-past" if is_past else ""
        now_mark = ' <span style="background:#f0a500;color:#000;font-size:0.62rem;padding:0 3px;border-radius:2px;">NOW</span>' \
                   if abs((e["dt"] - now).total_seconds()) < 3600 else ""
        badge    = cal_signal_badge(e)
        rows_html += (
            f'<tr class="{row_cls}">'
            f'<td style="white-space:nowrap;">{e["dt"].strftime("%a %d, %H:%M")} UTC{now_mark}</td>'
            f'<td><span class="{"curr-usd" if e["currency"]=="USD" else "curr-eur"}">{e["currency"]}</span></td>'
            f'<td class="imp-high">●</td>'
            f'<td>{e["title"]}{badge}</td>'
            f'<td style="text-align:right;color:{"#3fb950" if e.get("actual") else "#8b949e"};">'
            f'{e["actual"] or "—"}</td>'
            f'<td style="text-align:right;color:#8b949e;">{e["forecast"] or "—"}</td>'
            f'<td style="text-align:right;color:#4a5568;">{e["previous"] or "—"}</td>'
            f'</tr>'
        )

    if not rows_html:
        rows_html = '<tr><td colspan="7" style="color:#8b949e;padding:10px;">No high-impact events found for this week.</td></tr>'

    st.markdown(f"""
    <div class="section-panel">
      <div class="section-header">
        📅 High-Impact Economic Calendar — EUR &amp; USD
        &nbsp;<span style="background:#e74c3c;color:#fff;font-size:0.65rem;padding:1px 5px;border-radius:3px;">HIGH IMPACT</span>
      </div>
      <table class="ev-table">
        <thead><tr>
          <th>Time (UTC)</th><th>CCY</th><th>!</th><th>Event</th>
          <th style="text-align:right;">Actual</th>
          <th style="text-align:right;">Forecast</th>
          <th style="text-align:right;">Previous</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>""", unsafe_allow_html=True)

# ── Footer
st.markdown(
    f"<br><span style='color:#4a5568;font-size:0.73rem;'>"
    f"TF: {st.session_state.tf} · {len(cal_events)} calendar events (showing today+) · "
    f"{len(news_items)} news items · DXY: {dxy_str} · Master Signal: {sig_val} ({sig_score:+d}) · "
    f"{datetime.utcnow().strftime('%H:%M UTC')}"
    f"</span>", unsafe_allow_html=True
)
