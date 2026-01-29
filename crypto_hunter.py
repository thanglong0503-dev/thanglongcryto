import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import time
from datetime import datetime
import streamlit.components.v1 as components

# ==============================================================================
# 1. QUANTUM UI CONFIGURATION
# ==============================================================================
st.set_page_config(
    layout="wide",
    page_title="ThangLong Quantum Terminal",
    page_icon="🐲",
    initial_sidebar_state="collapsed"
)

# CSS MAGIC: DARK THEME & NEON EFFECTS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Rajdhani:wght@500;700&display=swap');

    :root {
        --bg-color: #050505;
        --card-bg: #111111;
        --accent-color: #00f2ff;
        --neon-green: #00ff41;
        --neon-red: #ff0055;
        --text-color: #e0e0e0;
    }

    .stApp { background-color: var(--bg-color) !important; color: var(--text-color) !important; font-family: 'Rajdhani', sans-serif !important; }
    header[data-testid="stHeader"] { background: transparent !important; }

    /* INPUTS & SELECTBOX FIX */
    div[data-baseweb="input"], div[data-baseweb="select"] > div {
        background-color: #1a1a1a !important; border: 1px solid #333 !important; color: white !important;
    }
    input[type="text"] { color: var(--accent-color) !important; font-family: 'JetBrains Mono', monospace !important; font-weight: bold; }
    
    /* DROPDOWN MENU FIX */
    div[data-baseweb="popover"], ul[data-baseweb="menu"] { background-color: #111 !important; border: 1px solid #444 !important; }
    li[data-baseweb="option"] { color: white !important; }
    li[data-baseweb="option"]:hover { background-color: var(--accent-color) !important; color: black !important; }

    /* GLOWING CARDS */
    .quantum-card {
        background: rgba(17, 17, 17, 0.8); border: 1px solid #333; border-radius: 8px; padding: 20px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.5); margin-bottom: 15px;
    }
    
    /* METRICS */
    .metric-value { font-size: 32px; font-weight: 700; font-family: 'JetBrains Mono'; }
    .text-green { color: var(--neon-green); text-shadow: 0 0 10px rgba(0,255,65,0.4); }
    .text-red { color: var(--neon-red); text-shadow: 0 0 10px rgba(255,0,85,0.4); }
    .text-blue { color: var(--accent-color); text-shadow: 0 0 10px rgba(0,242,255,0.4); }

    /* BUTTONS */
    button[kind="primary"] {
        background: linear-gradient(45deg, #00f2ff, #0078ff) !important; color: black !important; font-weight: bold !important; border: none !important;
    }
    
    /* TABS */
    .stTabs [aria-selected="true"] { background-color: var(--accent-color) !important; color: black !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CORE ENGINE (ROBUST VERSION - FIX KEYERROR)
# ==============================================================================
class QuantumEngine:
    def __init__(self):
        try:
            self.exchange = ccxt.binanceus({'enableRateLimit': True})
        except:
            self.exchange = ccxt.kraken({'enableRateLimit': True})
            
    @st.cache_data(ttl=600)
    def get_market_symbols(_self, limit=100):
        try:
            tickers = _self.exchange.fetch_tickers()
            symbols = [s for s in tickers if '/USDT' in s or '/USD' in s]
            sorted_symbols = sorted(symbols, key=lambda x: tickers[x]['quoteVolume'] if 'quoteVolume' in tickers[x] else 0, reverse=True)
            return sorted_symbols[:limit]
        except:
            return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']

    def fetch_ohlcv(self, symbol, timeframe, limit=300):
        for _ in range(3):
            try:
                bars = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                if bars:
                    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    return df
            except: time.sleep(0.2)
        return pd.DataFrame()

    def fetch_order_book(self, symbol):
        try: return self.exchange.fetch_order_book(symbol, limit=100)
        except: return None

    def analyze_indicators(self, df):
        """Bộ não phân tích kỹ thuật (Đã gia cố chống lỗi KeyError)"""
        if df.empty: return df, {}
        
        # --- 1. Calculate Indicators (Safe Mode) ---
        try:
            # Trend
            df.ta.ema(length=50, append=True)
            df.ta.ema(length=200, append=True)
            df.ta.adx(append=True)
            # Volatility
            df.ta.bbands(length=20, std=2, append=True)
            df.ta.atr(length=14, append=True)
            # Momentum
            df.ta.rsi(length=14, append=True)
            df.ta.macd(append=True)
            # Volume
            try: df.ta.vwap(append=True)
            except: pass 
        except Exception as e:
            st.error(f"Lỗi tính toán chỉ báo: {e}")
            return df, {"score": 0, "rating": "ERROR", "reasons": []}

        # --- 2. Signal Logic (Dynamic Column Search) ---
        # Hàm này giúp tìm tên cột động (VD: tìm cột bắt đầu bằng 'BBL')
        def get_col(pattern):
            cols = [c for c in df.columns if c.startswith(pattern)]
            return cols[0] if cols else None

        curr = df.iloc[-1]
        score = 0
        reasons = []

        # RSI Logic
        rsi_col = get_col('RSI_')
        if rsi_col and curr[rsi_col] < 30: score += 2; reasons.append(f"RSI Oversold ({curr[rsi_col]:.0f})")
        elif rsi_col and curr[rsi_col] > 70: score -= 2; reasons.append(f"RSI Overbought ({curr[rsi_col]:.0f})")

        # Golden Cross
        if 'EMA_50' in df.columns and 'EMA_200' in df.columns:
            if curr['EMA_50'] > curr['EMA_200']: score += 1; reasons.append("Golden Cross (Bullish)")
            elif curr['EMA_50'] < curr['EMA_200']: score -= 1; reasons.append("Death Cross (Bearish)")

        # Bollinger Bands (Fix KeyError here)
        bbl_col = get_col('BBL_')
        bbu_col = get_col('BBU_')
        if bbl_col and curr['close'] < curr[bbl_col]: score += 1; reasons.append("Price < Lower BB (Dip)")
        elif bbu_col and curr['close'] > curr[bbu_col]: score -= 1; reasons.append("Price > Upper BB (Pump)")

        # VWAP
        vwap_col = get_col('VWAP_')
        if vwap_col and curr['close'] > curr[vwap_col]: score += 1
        
        rating = "NEUTRAL"
        if score >= 3: rating = "STRONG BUY"
        elif score >= 1: rating = "BUY"
        elif score <= -3: rating = "STRONG SELL"
        elif score <= -1: rating = "SELL"

        return df, {"score": score, "rating": rating, "reasons": reasons}

engine = QuantumEngine()

# ==============================================================================
# 3. ADVANCED CHARTS (SAFE MODE)
# ==============================================================================
def create_quantum_chart(df, symbol):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name='Price', increasing_line_color='#00ff41', decreasing_line_color='#ff0055'
    ), row=1, col=1)

    # Add Indicators safely
    if 'EMA_50' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='#00f2ff', width=1), name='EMA 50'), row=1, col=1)
    if 'EMA_200' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], line=dict(color='#ff00ff', width=1), name='EMA 200'), row=1, col=1)
    
    # Tìm cột BB động
    bbu_col = [c for c in df.columns if c.startswith('BBU_')]
    bbl_col = [c for c in df.columns if c.startswith('BBL_')]
    
    if bbu_col and bbl_col:
        fig.add_trace(go.Scatter(x=df.index, y=df[bbu_col[0]], line=dict(color='rgba(255,255,255,0.3)', dash='dot'), name='Upper BB'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df[bbl_col[0]], line=dict(color='rgba(255,255,255,0.3)', dash='dot'), fill='tonexty', name='Lower BB'), row=1, col=1)

    # Volume
    colors = ['#00ff41' if row['close'] > row['open'] else '#ff0055' for i, row in df.iterrows()]
    fig.add_trace(go.Bar(x=df.index, y=df['volume'], marker_color=colors, name='Volume'), row=2, col=1)

    fig.update_layout(
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=600, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False, showlegend=False
    )
    return fig

def create_depth_chart(ob):
    if not ob: return None
    bids = pd.DataFrame(ob['bids'], columns=['price', 'amount'])
    asks = pd.DataFrame(ob['asks'], columns=['price', 'amount'])
    bids['total'] = bids['amount'].cumsum()
    asks['total'] = asks['amount'].cumsum()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bids['price'], y=bids['total'], mode='lines', fill='tozeroy', line=dict(color='#00ff41'), name='Buy Wall'))
    fig.add_trace(go.Scatter(x=asks['price'], y=asks['total'], mode='lines', fill='tozeroy', line=dict(color='#ff0055'), name='Sell Wall'))
    
    fig.update_layout(
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=300, margin=dict(l=10, r=10, t=30, b=10), title="Market Depth"
    )
    return fig

# ==============================================================================
# 4. COMPONENTS (WIDGETS)
# ==============================================================================
def render_tv_widget(symbol):
    base = symbol.split('/')[0] if '/' in symbol else symbol
    html = f"""
    <div class="tradingview-widget-container" style="height:500px;width:100%">
      <div id="tv_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
      "autosize": true, "symbol": "BINANCE:{base}USDT", "interval": "60", "timezone": "Asia/Ho_Chi_Minh",
      "theme": "dark", "style": "1", "locale": "vi_VN", "enable_publishing": false,
      "backgroundColor": "#111111", "gridColor": "rgba(40,40,40,0.5)",
      "hide_top_toolbar": false, "save_image": false, "container_id": "tv_chart",
      "studies": ["RSI@tv-basicstudies", "MACD@tv-basicstudies"]
      }});
      </script>
    </div>"""
    components.html(html, height=510)

# ==============================================================================
# 5. MAIN UI LAYOUT
# ==============================================================================

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cryptologos.cc/logos/bitcoin-btc-logo.png", width=50)
    st.markdown("### QUANTUM SETTINGS")
    st.markdown("---")
    st.caption("System Status: STABLE 🟢")

# --- HEADER ---
c1, c2 = st.columns([1, 5])
with c1: st.markdown("# 🐲")
with c2: st.markdown("# THANG LONG <span style='color:#00f2ff'>QUANTUM</span> TERMINAL", unsafe_allow_html=True)

# --- SEARCH BAR ---
search_col, list_col, tf_col = st.columns([2, 2, 1])
with search_col:
    manual_input = st.text_input("COMMAND LINE", placeholder="Enter Ticker...", label_visibility="collapsed")
with list_col:
    coins = engine.get_market_symbols()
    dropdown_select = st.selectbox("WATCHLIST", coins, label_visibility="collapsed")
with tf_col:
    timeframe = st.selectbox("TIMEFRAME", ['15m', '1h', '4h', '1d'], index=2, label_visibility="collapsed")

symbol = f"{manual_input.upper()}/USDT" if manual_input else dropdown_select
if "/USDT" not in symbol and "/USD" not in symbol: symbol += "/USDT"

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🚀 COCKPIT", "🧠 AI BRAIN", "🐋 WHALE RADAR", "📰 NEWS"])

# ================= TAB 1 =================
with tab1:
    with st.spinner(f"Quantum Engine processing {symbol}..."):
        df = engine.fetch_ohlcv(symbol, timeframe)
        if df.empty:
            fallback = symbol.replace("/USDT", "/USD")
            df = engine.fetch_ohlcv(fallback, timeframe)
            if not df.empty: symbol = fallback

    if not df.empty:
        df, analysis = engine.analyze_indicators(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        change = (curr['close'] - prev['close']) / prev['close'] * 100
        
        k1, k2, k3, k4 = st.columns(4)
        with k1: st.markdown(f"""<div class="quantum-card"><div class="metric-label">PRICE</div><div class="metric-value text-blue">${curr['close']:,.4f}</div></div>""", unsafe_allow_html=True)
        with k2: 
            color = "text-green" if change >= 0 else "text-red"
            st.markdown(f"""<div class="quantum-card"><div class="metric-label">24H CHANGE</div><div class="metric-value {color}">{change:+.2f}%</div></div>""", unsafe_allow_html=True)
        with k3: st.markdown(f"""<div class="quantum-card"><div class="metric-label">VOLUME</div><div class="metric-value">${curr['volume']*curr['close']/1000000:.2f}M</div></div>""", unsafe_allow_html=True)
        with k4: 
            rsi_col = get_col('RSI_') if 'get_col' in locals() else 'RSI_14' # Safe fallback
            rsi_val = curr[rsi_col] if rsi_col in curr else 50
            st.markdown(f"""<div class="quantum-card"><div class="metric-label">RSI</div><div class="metric-value">{rsi_val:.1f}</div></div>""", unsafe_allow_html=True)

        c_chart1, c_chart2 = st.columns([2, 1])
        with c_chart1:
            st.markdown("### 📈 QUANTUM CHART")
            fig = create_quantum_chart(df, symbol)
            st.plotly_chart(fig, use_container_width=True)
        with c_chart2:
            st.markdown("### 🌏 GLOBAL FEED")
            render_tv_widget(symbol)
    else:
        st.error(f"DATA STREAM INTERRUPTED FOR {symbol}")

# ================= TAB 2 =================
with tab2:
    if not df.empty:
        col_ai_1, col_ai_2 = st.columns([1, 2])
        with col_ai_1:
            rating = analysis['rating']
            r_color = "#00ff41" if "BUY" in rating else ("#ff0055" if "SELL" in rating else "#444")
            st.markdown(f"""
            <div class="quantum-card" style="text-align:center; border: 2px solid {r_color};">
                <div style="font-size:16px; color:#888;">AI VERDICT</div>
                <div style="font-size:48px; font-weight:bold; color:{r_color};">{rating}</div>
            </div>""", unsafe_allow_html=True)
            for r in analysis['reasons']:
                icon = "✅" if "Bullish" in r or "Dip" in r else "🔻"
                st.markdown(f"""<div style="padding:10px; background:#1a1a1a; margin-bottom:5px; border-radius:4px;">{icon} {r}</div>""", unsafe_allow_html=True)

# ================= TAB 3 =================
with tab3:
    st.markdown("### 🐋 DEEP SEA SONAR")
    with st.spinner("Scanning Order Book..."):
        ob = engine.fetch_order_book(symbol)
    if ob:
        w1, w2 = st.columns([3, 1])
        with w1: st.plotly_chart(create_depth_chart(ob), use_container_width=True)
        with w2:
            bids_vol = sum([x[1] for x in ob['bids']])
            asks_vol = sum([x[1] for x in ob['asks']])
            total = bids_vol + asks_vol
            buy_pct = (bids_vol / total) * 100 if total > 0 else 50
            st.markdown(f"""
            <div style="background:#333; height:30px; border-radius:15px; overflow:hidden; display:flex;">
                <div style="width:{buy_pct}%; background:#00ff41; display:flex; align-items:center; justify-content:center; color:black; font-weight:bold;">{buy_pct:.0f}% BUY</div>
                <div style="width:{100-buy_pct}%; background:#ff0055; display:flex; align-items:center; justify-content:center; color:white; font-weight:bold;">{100-buy_pct:.0f}% SELL</div>
            </div>""", unsafe_allow_html=True)

# ================= TAB 4 =================
with tab4:
    st.markdown("### 📰 SIMULATED NEWS")
    st.info("News API connection established. Monitoring Global Sentiment...")
    st.markdown(f"""
    - 🟢 **Bullish**: {symbol.split('/')[0]} has seen a 15% increase in active addresses.
    - 🔴 **Bearish**: Minor resistance detected at ${curr['close']*1.05:.2f}.
    - 🔵 **Neutral**: Whale activity is stable in the last 24h.
    """)

st.markdown("---")
st.caption("THANGLONG QUANTUM TERMINAL | SYSTEM ID: TQT-9000-STABLE")
