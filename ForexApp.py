import streamlit as st
import yfinance as yf
import requests
import feedparser
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pytz

st.set_page_config(layout="wide", page_title="EUR/USD - ForexFactory Style", page_icon="📈")

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
  border-right: 1px solid #2e3347; min-width: 260px;
}
.pair-label { font-size: 1.3rem; font-weight: 700; color: #e0e6f0; letter-spacing: 0.5px; }
.price-val  { font-size: 1.55rem; font-weight: 700; color: #e0e6f0; letter-spacing: 1px; }
.perf-panel { display: flex; flex: 1; }
.perf-col   { flex: 1; border-right: 1px solid #2e3347; padding: 8px 14px; }
.perf-col:last-child { border-right: none; }
.perf-label { font-size: 0.68rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px; }
.perf-row   { display: flex; justify-content: space-between; font-size: 0.76rem; margin-bottom: 2px; }
.perf-key   { color: #8b949e; }
.pos { color: #3fb950; font-weight: 500; }
.neg { color: #e74c3c; font-weight: 500; }
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
.imp-high { color: #e74c3c; font-weight: 700; font-size:1.1rem; }
.curr-usd { color: #58a6ff; font-weight:700; }
.curr-eur { color: #3fb950; font-weight:700; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DATA
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

@st.cache_data(ttl=30)
def get_price_data(tf="1H"):
    period, interval = TF_MAP[tf]
    df = yf.download("EURUSD=X", period=period, interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.reset_index()
    dt_col = "Datetime" if "Datetime" in df.columns else "Date"
    df = df.rename(columns={dt_col: "dt"})
    df["dt"] = pd.to_datetime(df["dt"]).dt.tz_localize(None)
    df = df[["dt","Open","High","Low","Close"]].dropna()
    return df

@st.cache_data(ttl=60)
def get_live_price():
    try:
        t = yf.Ticker("EURUSD=X")
        h = t.history(period="1d", interval="1m")
        return float(h["Close"].iloc[-1])
    except:
        return None

@st.cache_data(ttl=300)
def get_calendar():
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        events = r.json()
        out = []
        for ev in events:
            if ev.get("impact") != "High":
                continue
            if ev.get("currency") not in ("EUR","USD"):
                continue
            try:
                dt = datetime.fromisoformat(ev["date"].replace("Z","+00:00")).replace(tzinfo=None)
            except:
                continue
            out.append({
                "dt":       dt,
                "currency": ev.get("currency",""),
                "title":    ev.get("title",""),
                "actual":   ev.get("actual") or "",
                "forecast": ev.get("forecast") or "",
                "previous": ev.get("previous") or "",
            })
        return sorted(out, key=lambda x: x["dt"])
    except:
        return []

@st.cache_data(ttl=120)
def get_news():
    feeds = [
        "https://www.forexlive.com/feed/news",
        "https://www.fxstreet.com/rss/news",
    ]
    keywords = ["eurusd","eur/usd","euro","ecb","federal reserve","fed","fomc",
                "powell","lagarde","usd","dollar","inflation","cpi","nfp",
                "interest rate","gdp","durable goods","pmi"]
    articles = []
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                title = e.get("title","")
                content = (title + " " + e.get("summary","")).lower()
                if not any(k in content for k in keywords):
                    continue
                pub = e.get("published_parsed") or e.get("updated_parsed")
                dt = datetime(*pub[:6]) if pub else datetime.utcnow()
                articles.append({"dt": dt, "title": title, "link": e.get("link","#"), "source": feed.feed.get("title","")})
        except:
            continue
    seen, unique = set(), []
    for a in sorted(articles, key=lambda x: x["dt"], reverse=True):
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    return unique[:40]


# ══════════════════════════════════════════════════════════════════════════════
# SESSIONS
# ══════════════════════════════════════════════════════════════════════════════
SESSIONS = [
    {"name":"Sydney",   "start":21, "end":6,  "color":"rgba(230,220,80,0.10)"},
    {"name":"London",   "start":8,  "end":17, "color":"rgba(80,180,80,0.10)"},
    {"name":"New York", "start":13, "end":22, "color":"rgba(230,220,80,0.10)"},
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
                    e_dt = datetime(d.year, d.month, d.day+1, e_h)
                except:
                    continue
            else:
                e_dt = datetime(d.year, d.month, d.day, e_h)
            if e_dt < df["dt"].min() or s_dt > df["dt"].max():
                continue
            blocks.append({"x0":s_dt,"x1":e_dt,"color":sess["color"],"name":sess["name"]})
    return blocks


# ══════════════════════════════════════════════════════════════════════════════
# CHART — 4 subplots: Candles | Sessions | Calendar | News
# ══════════════════════════════════════════════════════════════════════════════
def build_chart(df, cal_events, news_items):
    if df.empty:
        return go.Figure()

    session_blocks = get_session_blocks(df)

    # row_heights must sum to 1.0
    fig = make_subplots(
        rows=4, cols=1,
        row_heights=[0.73, 0.10, 0.085, 0.085],
        vertical_spacing=0.005,
        shared_xaxes=True,
    )

    # ── Row 1: Candlestick
    fig.add_trace(go.Candlestick(
        x=df["dt"],
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        increasing=dict(line=dict(color="#4a9eff",width=1), fillcolor="#4a9eff"),
        decreasing=dict(line=dict(color="#4a9eff",width=1), fillcolor="#1b1f2b"),
        name="EUR/USD", hoverinfo="x+y",
    ), row=1, col=1)

    # Shading on the main chart
    for blk in session_blocks:
        fig.add_shape(
            type="rect", xref="x", yref="paper",
            x0=blk["x0"], x1=blk["x1"],
            y0=0.27, y1=1.0,
            fillcolor=blk["color"],
            line=dict(width=0), layer="below",
        )

    # ── Row 2: Sessions strip — colored bands
    for blk in session_blocks:
        mid = blk["x0"] + (blk["x1"] - blk["x0"]) / 2
        fig.add_trace(go.Scatter(
            x=[blk["x0"], blk["x0"], blk["x1"], blk["x1"], blk["x0"]],
            y=[0, 1, 1, 0, 0],
            fill="toself",
            fillcolor=blk["color"],
            line=dict(width=0),
            mode="lines",
            showlegend=False,
            hoverinfo="skip",
            text=blk["name"],
        ), row=2, col=1)

    # Session name labels in strip
    seen_s = {}
    for blk in session_blocks:
        n = blk["name"]
        mid = blk["x0"] + (blk["x1"]-blk["x0"])/2
        if n not in seen_s or (mid-seen_s[n]).total_seconds() > 86400:
            seen_s[n] = mid
            fig.add_annotation(
                x=mid, y=0.5,
                xref="x2", yref="y2",
                text=f"<b>{n}</b>",
                showarrow=False,
                font=dict(size=8, color="rgba(200,210,220,0.7)"),
                xanchor="center", yanchor="middle",
            )

    # ── Row 3: Calendar markers — HIGH IMPACT only (red squares)
    cal_in = [e for e in cal_events if df["dt"].min() <= e["dt"] <= df["dt"].max()]
    if cal_in:
        fig.add_trace(go.Scatter(
            x=[e["dt"] for e in cal_in],
            y=[0.5]*len(cal_in),
            mode="markers",
            marker=dict(symbol="square", size=11, color="#e74c3c", line=dict(width=0)),
            name="Calendar",
            customdata=[
                f"<b>{e['currency']}</b>: {e['title']}<br>"
                f"Actual: <b>{e['actual'] or '—'}</b> | Forecast: {e['forecast'] or '—'} | Prev: {e['previous'] or '—'}"
                for e in cal_in
            ],
            hovertemplate="%{customdata}<extra>📅 Calendar Event</extra>",
            showlegend=False,
        ), row=3, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=[df["dt"].iloc[0]], y=[0.5], mode="markers",
            marker=dict(opacity=0), showlegend=False, hoverinfo="skip"
        ), row=3, col=1)

    # ── Row 4: News markers — high-impact EUR/USD (orange squares)
    news_in = [n for n in news_items if df["dt"].min() <= n["dt"] <= df["dt"].max()]
    if news_in:
        fig.add_trace(go.Scatter(
            x=[n["dt"] for n in news_in],
            y=[0.5]*len(news_in),
            mode="markers",
            marker=dict(symbol="square", size=11, color="#e67e22", line=dict(width=0)),
            name="News",
            customdata=[n["title"][:100] for n in news_in],
            hovertemplate="%{customdata}<extra>📰 News</extra>",
            showlegend=False,
        ), row=4, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=[df["dt"].iloc[0]], y=[0.5], mode="markers",
            marker=dict(opacity=0), showlegend=False, hoverinfo="skip"
        ), row=4, col=1)

    # ── Axes styling
    common_axis = dict(showgrid=False, zeroline=False, showticklabels=False, showline=True, linecolor="#2e3347")

    fig.update_layout(
        height=640,
        paper_bgcolor="#1b1f2b",
        plot_bgcolor="#1b1f2b",
        margin=dict(l=52, r=65, t=4, b=4),
        xaxis_rangeslider_visible=False,
        hoverlabel=dict(bgcolor="#252a3a", font_size=12, bordercolor="#3e4460"),
        dragmode="pan",
    )

    # Row 1 — main chart
    fig.update_xaxes(showgrid=True, gridcolor="#21262d", gridwidth=0.5,
                     zeroline=False, tickfont=dict(color="#6b7380",size=10),
                     showline=False, row=1, col=1)
    fig.update_yaxes(showgrid=True, gridcolor="#21262d", gridwidth=0.5,
                     zeroline=False, tickfont=dict(color="#8b949e",size=10),
                     side="right", tickformat=".4f", showline=False, row=1, col=1)

    # Rows 2/3/4 — strips
    for r in [2, 3, 4]:
        fig.update_xaxes(**common_axis, row=r, col=1)
        fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False,
                         range=[0,1], showline=True, linecolor="#2e3347", row=r, col=1)

    # Last row shows x tick labels
    fig.update_xaxes(showticklabels=True, tickfont=dict(color="#6b7380",size=10), row=4, col=1)

    # ── Left-side row labels
    for txt, y_paper in [("Sessions", 0.192), ("Calendar", 0.096), ("News", 0.018)]:
        fig.add_annotation(
            x=-0.015, y=y_paper,
            xref="paper", yref="paper",
            text=f"<b>{txt}</b>",
            showarrow=False,
            font=dict(size=9, color="#8b949e"),
            xanchor="right", yanchor="middle",
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
    for label, bars in [("1hr",1),("6hr",6),("12hr",12)]:
        idx = max(0, len(df)-bars-1)
        ref = float(df["Close"].iloc[idx])
        res[label] = {
            "pip": round((last-ref)*10000, 1),
            "pct": round((last-ref)/ref*100, 2),
        }
    return res

def perf_color(v, suffix=""):
    if v > 0:   return f'<span class="pos">+{v}{suffix}</span>'
    elif v < 0: return f'<span class="neg">{v}{suffix}</span>'
    return f'<span class="neu">{v}{suffix}</span>'


# ══════════════════════════════════════════════════════════════════════════════
# STATE + LOAD
# ══════════════════════════════════════════════════════════════════════════════
if "tf" not in st.session_state:
    st.session_state.tf = "1H"

df         = get_price_data(st.session_state.tf)
live_price = get_live_price()
cal_events = get_calendar()
news_items = get_news()
perf       = calc_perf(df)

if live_price is None and not df.empty:
    live_price = float(df["Close"].iloc[-1])

p1  = perf.get("1hr",  {"pip":0,"pct":0})
p6  = perf.get("6hr",  {"pip":0,"pct":0})
p12 = perf.get("12hr", {"pip":0,"pct":0})
price_str = f"{live_price:.5f}" if live_price else "—"


# ══════════════════════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════════════════════

# Header
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
  </div>
</div>
""", unsafe_allow_html=True)

# Timeframe bar
tf_options = list(TF_MAP.keys())
cols = st.columns([2.2] + [0.38]*len(tf_options) + [0.9])
with cols[0]:
    st.markdown('<span style="color:#8b949e;font-size:0.8rem;line-height:2.4;">Chart for EUR/USD</span>', unsafe_allow_html=True)
for i, tf in enumerate(tf_options):
    with cols[i+1]:
        if st.button(tf, key=f"tf_{tf}", use_container_width=True):
            st.session_state.tf = tf
            st.cache_data.clear()
            st.rerun()
with cols[-1]:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# OHLC bar
if not df.empty:
    last = df.iloc[-1]
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

# Chart
fig = build_chart(df, cal_events, news_items)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False,"scrollZoom":True})

# Bottom panels
col_left, col_right = st.columns(2)

with col_left:
    stories_html = "".join(
        f'<div class="story-item"><span class="story-time">{n["dt"].strftime("%b %d %H:%M")}</span>'
        f'<span class="story-title"><a href="{n["link"]}" target="_blank">{n["title"]}</a></span></div>'
        for n in news_items[:20]
    ) or '<div class="story-item" style="color:#8b949e;">No high-impact stories found.</div>'

    st.markdown(f"""
    <div class="section-panel">
      <div class="section-header">
        📰 Latest Stories for EUR/USD
        &nbsp;<span style="background:#e74c3c;color:#fff;font-size:0.65rem;padding:1px 5px;border-radius:3px;">HIGH IMPACT</span>
      </div>
      {stories_html}
    </div>""", unsafe_allow_html=True)

with col_right:
    now = datetime.utcnow()
    upcoming = [e for e in cal_events if e["dt"] >= now]
    rows_html = "".join(
        f'<tr>'
        f'<td style="white-space:nowrap;">{e["dt"].strftime("%a %d, %H:%M")}</td>'
        f'<td><span class="{"curr-usd" if e["currency"]=="USD" else "curr-eur"}">{e["currency"]}</span></td>'
        f'<td class="imp-high">●</td>'
        f'<td>{e["title"]}</td>'
        f'<td style="text-align:right;color:#8b949e;">{e["forecast"] or "—"}</td>'
        f'<td style="text-align:right;color:#4a5568;">{e["previous"] or "—"}</td>'
        f'</tr>'
        for e in upcoming
    ) or '<tr><td colspan="6" style="color:#8b949e;padding:10px;">No upcoming high-impact events.</td></tr>'

    st.markdown(f"""
    <div class="section-panel">
      <div class="section-header">
        📅 Upcoming Events for EUR/USD
        &nbsp;<span style="background:#e74c3c;color:#fff;font-size:0.65rem;padding:1px 5px;border-radius:3px;">HIGH IMPACT</span>
      </div>
      <table class="ev-table">
        <thead><tr>
          <th>Due</th><th>CCY</th><th>Impact</th><th>Event</th>
          <th style="text-align:right;">Forecast</th>
          <th style="text-align:right;">Previous</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>""", unsafe_allow_html=True)

st.markdown(
    f"<br><span style='color:#4a5568;font-size:0.73rem;'>"
    f"TF: {st.session_state.tf} · {len(cal_events)} high-impact calendar events · "
    f"{len(news_items)} news items · {datetime.utcnow().strftime('%H:%M UTC')}"
    f"</span>", unsafe_allow_html=True
)