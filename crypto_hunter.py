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
# 1. QUANTUM UI CONFIGURATION (CẤU HÌNH GIAO DIỆN SIÊU CẤP)
# ==============================================================================
st.set_page_config(
    layout="wide",
    page_title="ThangLong Quantum Terminal",
    page_icon="🐲",
    initial_sidebar_state="collapsed" # Mặc định đóng sidebar cho rộng
)

# CSS MAGIC: Biến Streamlit thành Bloomberg Terminal
st.markdown("""
<style>
    /* IMPORT FONT HACKER */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Rajdhani:wght@500;700&display=swap');

    /* --- ROOT VARIABLES --- */
    :root {
        --bg-color: #050505;
        --card-bg: #111111;
        --accent-color: #00f2ff; /* Cyber Blue */
        --neon-green: #00ff41;
        --neon-red: #ff0055;
        --text-color: #e0e0e0;
        --border-color: #333;
    }

    /* --- GLOBAL STYLES --- */
    .stApp {
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
        font-family: 'Rajdhani', sans-serif !important;
    }
    
    /* HEADER FIX */
    header[data-testid="stHeader"] { background: transparent !important; backdrop-filter: blur(10px); }

    /* --- CUSTOM INPUTS (FIXED VISIBILITY) --- */
    div[data-baseweb="input"], div[data-baseweb="select"] > div {
        background-color: #1a1a1a !important;
        border: 1px solid #333 !important;
        border-radius: 4px !important;
        color: white !important;
    }
    input[type="text"] {
        color: var(--accent-color) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: bold;
    }
    
    /* --- GLOWING CARDS --- */
    .quantum-card {
        background: rgba(17, 17, 17, 0.8);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(5px);
        margin-bottom: 15px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .quantum-card:hover {
        border-color: var(--accent-color);
        box-shadow: 0 0 20px rgba(0, 242, 255, 0.2);
    }

    /* --- METRICS --- */
    .metric-label { font-size: 14px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 32px; font-weight: 700; font-family: 'JetBrains Mono'; }
    .text-green { color: var(--neon-green); text-shadow: 0 0 10px rgba(0,255,65,0.4); }
    .text-red { color: var(--neon-red); text-shadow: 0 0 10px rgba(255,0,85,0.4); }
    .text-blue { color: var(--accent-color); text-shadow: 0 0 10px rgba(0,242,255,0.4); }

    /* --- BUTTONS --- */
    button[kind="primary"] {
        background: linear-gradient(45deg, #00f2ff, #0078ff) !important;
        color: black !important;
        font-weight: bold !important;
        border: none !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid var(--accent-color) !important;
        color: var(--accent-color) !important;
    }

    /* --- TABS --- */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1a1a1a;
        border-radius: 4px;
        color: white;
        border: 1px solid #333;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--accent-color) !important;
        color: black !important;
        font-weight: bold;
    }

    /* --- MENU FIX --- */
    div[data-baseweb="popover"], ul[data-baseweb="menu"] { background-color: #111 !important; border: 1px solid #444 !important; }
    li[data-baseweb="option"] { color: white !important; }
    li[data-baseweb="option"]:hover { background-color: var(--accent-color) !important; color: black !important; }

    /* --- SCROLLBAR --- */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #050505; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--accent-color); }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CORE ENGINE (DATA & LOGIC)
# ==============================================================================
class QuantumEngine:
    def __init__(self):
        # Fallback mechanism: Try US, then Global (proxied via CCXT logic if needed)
        try:
            self.exchange = ccxt.binanceus({'enableRateLimit': True})
            self.market_type = "SPOT (US)"
        except:
            self.exchange = ccxt.kraken({'enableRateLimit': True})
            self.market_type = "SPOT (Kraken)"
            
    @st.cache_data(ttl=600)
    def get_market_symbols(_self, limit=100):
        try:
            tickers = _self.exchange.fetch_tickers()
            symbols = [s for s in tickers if '/USDT' in s or '/USD' in s]
            # Sort by volume
            sorted_symbols = sorted(symbols, key=lambda x: tickers[x]['quoteVolume'] if 'quoteVolume' in tickers[x] else 0, reverse=True)
            return sorted_symbols[:limit]
        except:
            return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']

    def fetch_ohlcv(self, symbol, timeframe, limit=300):
        """Robust data fetching with retry"""
        for _ in range(3):
            try:
                bars = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                if bars:
                    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    return df
            except:
                time.sleep(0.2)
        return pd.DataFrame()

    def fetch_order_book(self, symbol):
        """Lấy dữ liệu Depth"""
        try:
            return self.exchange.fetch_order_book(symbol, limit=100)
        except:
            return None

    def analyze_indicators(self, df):
        """Bộ não phân tích kỹ thuật"""
        if df.empty: return df, {}
        
        # 1. Trend
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)
        df.ta.adx(append=True)
        
        # 2. Volatility
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.atr(length=14, append=True)
        
        # 3. Momentum
        df.ta.rsi(length=14, append=True)
        df.ta.macd(append=True)
        df.ta.stoch(append=True)
        
        # 4. Volume
        df.ta.vwap(append=True)
        df.ta.mfi(append=True)

        # --- SIGNAL LOGIC ---
        curr = df.iloc[-1]
        score = 0
        reasons = []

        # RSI Logic
        if curr['RSI_14'] < 30: score += 2; reasons.append("RSI Oversold")
        elif curr['RSI_14'] > 70: score -= 2; reasons.append("RSI Overbought")

        # Golden Cross
        if curr['EMA_50'] > curr['EMA_200']: score += 1; reasons.append("Golden Cross (Bullish)")
        elif curr['EMA_50'] < curr['EMA_200']: score -= 1; reasons.append("Death Cross (Bearish)")

        # Bollinger Bands
        if curr['close'] < curr['BBL_20_2.0']: score += 1; reasons.append("Price < Lower BB (Dip)")
        elif curr['close'] > curr['BBU_20_2.0']: score -= 1; reasons.append("Price > Upper BB (Pump)")

        # VWAP
        if 'VWAP_D' in curr and curr['close'] > curr['VWAP_D']: score += 1
        
        rating = "NEUTRAL"
        if score >= 3: rating = "STRONG BUY"
        elif score >= 1: rating = "BUY"
        elif score <= -3: rating = "STRONG SELL"
        elif score <= -1: rating = "SELL"

        return df, {"score": score, "rating": rating, "reasons": reasons}

engine = QuantumEngine()

# ==============================================================================
# 3. ADVANCED VISUALIZATION FUNCTIONS (PLOTLY)
# ==============================================================================
def create_quantum_chart(df, symbol):
    """Vẽ biểu đồ tương tác cao cấp"""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, row_heights=[0.7, 0.3])

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name='Price', increasing_line_color='#00ff41', decreasing_line_color='#ff0055'
    ), row=1, col=1)

    # EMA & BB
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='#00f2ff', width=1), name='EMA 50'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], line=dict(color='#ff00ff', width=1), name='EMA 200'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BBU_20_2.0'], line=dict(color='rgba(255,255,255,0.3)', dash='dot'), name='Upper BB'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BBL_20_2.0'], line=dict(color='rgba(255,255,255,0.3)', dash='dot'), fill='tonexty', name='Lower BB'), row=1, col=1)

    # Volume
    colors = ['#00ff41' if row['close'] > row['open'] else '#ff0055' for i, row in df.iterrows()]
    fig.add_trace(go.Bar(x=df.index, y=df['volume'], marker_color=colors, name='Volume'), row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=600,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_rangeslider_visible=False,
        showlegend=False
    )
    return fig

def create_depth_chart(ob):
    """Vẽ biểu đồ độ sâu thị trường (Market Depth)"""
    if not ob: return None
    bids = pd.DataFrame(ob['bids'], columns=['price', 'amount'])
    asks = pd.DataFrame(ob['asks'], columns=['price', 'amount'])
    
    bids['total'] = bids['amount'].cumsum()
    asks['total'] = asks['amount'].cumsum()

    fig = go.Figure()
    # Phe Mua (Green)
    fig.add_trace(go.Scatter(
        x=bids['price'], y=bids['total'], mode='lines', 
        fill='tozeroy', line=dict(color='#00ff41'), name='Buy Wall'
    ))
    # Phe Bán (Red)
    fig.add_trace(go.Scatter(
        x=asks['price'], y=asks['total'], mode='lines', 
        fill='tozeroy', line=dict(color='#ff0055'), name='Sell Wall'
    ))
    
    fig.update_layout(
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=300, margin=dict(l=10, r=10, t=30, b=10), title="Market Depth (Liquidty)"
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

# --- SIDEBAR (SETTINGS) ---
with st.sidebar:
    st.image("https://cryptologos.cc/logos/bitcoin-btc-logo.png", width=50)
    st.markdown("### QUANTUM SETTINGS")
    st.markdown("---")
    data_source = st.selectbox("Data Source", ["Binance US (Live)", "Kraken (Backup)", "Mock Data (Demo)"])
    theme_mode = st.radio("Theme", ["Cyberpunk", "Minimalist"])
    st.info("System Status: ONLINE 🟢")
    st.caption("v1.0.0 - Genesis")

# --- HEADER AREA ---
c1, c2 = st.columns([1, 5])
with c1:
    st.markdown("# 🐲")
with c2:
    st.markdown("# THANG LONG <span style='color:#00f2ff'>QUANTUM</span> TERMINAL", unsafe_allow_html=True)
    st.caption("AI-Powered Institutional Grade Crypto Analytics")

# --- SEARCH BAR (HYBRID) ---
search_col, list_col, tf_col = st.columns([2, 2, 1])
with search_col:
    manual_input = st.text_input("COMMAND LINE", placeholder="Enter Ticker (e.g. BTC)...", label_visibility="collapsed")
with list_col:
    coins = engine.get_market_symbols()
    dropdown_select = st.selectbox("WATCHLIST", coins, label_visibility="collapsed")
with tf_col:
    timeframe = st.selectbox("TIMEFRAME", ['15m', '1h', '4h', '1d'], index=2, label_visibility="collapsed")

# Logic Selection
symbol = f"{manual_input.upper()}/USDT" if manual_input else dropdown_select
if "/USDT" not in symbol and "/USD" not in symbol: symbol += "/USDT"

# --- MAIN DASHBOARD TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🚀 COCKPIT", "🧠 AI BRAIN", "🐋 WHALE RADAR", "📰 NEWS & SENTIMENT"])

# ================= TAB 1: COCKPIT (OVERVIEW) =================
with tab1:
    # 1. Fetch Data
    with st.spinner(f"Quantum Engine processing {symbol}..."):
        df = engine.fetch_ohlcv(symbol, timeframe)
        # Fallback if empty
        if df.empty:
            fallback = symbol.replace("/USDT", "/USD")
            df = engine.fetch_ohlcv(fallback, timeframe)
            if not df.empty: symbol = fallback

    if not df.empty:
        df, analysis = engine.analyze_indicators(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        change = (curr['close'] - prev['close']) / prev['close'] * 100
        
        # 2. KPI Cards
        k1, k2, k3, k4 = st.columns(4)
        
        with k1:
            st.markdown(f"""
            <div class="quantum-card">
                <div class="metric-label">CURRENT PRICE</div>
                <div class="metric-value text-blue">${curr['close']:,.4f}</div>
            </div>""", unsafe_allow_html=True)
        
        with k2:
            color = "text-green" if change >= 0 else "text-red"
            sign = "+" if change >= 0 else ""
            st.markdown(f"""
            <div class="quantum-card">
                <div class="metric-label">24H CHANGE</div>
                <div class="metric-value {color}">{sign}{change:.2f}%</div>
            </div>""", unsafe_allow_html=True)
            
        with k3:
            vol_fmt = f"${curr['volume']*curr['close']/1000000:.2f}M"
            st.markdown(f"""
            <div class="quantum-card">
                <div class="metric-label">VOLUME (EST)</div>
                <div class="metric-value">{vol_fmt}</div>
            </div>""", unsafe_allow_html=True)
            
        with k4:
            rsi = curr['RSI_14']
            rsi_col = "text-green" if rsi < 30 else ("text-red" if rsi > 70 else "text-blue")
            st.markdown(f"""
            <div class="quantum-card">
                <div class="metric-label">RSI STRENGTH</div>
                <div class="metric-value {rsi_col}">{rsi:.1f}</div>
            </div>""", unsafe_allow_html=True)

        # 3. Charts Area (Split view)
        c_chart1, c_chart2 = st.columns([2, 1])
        
        with c_chart1:
            st.markdown("### 📈 QUANTUM CHART (PYTHON CORE)")
            fig = create_quantum_chart(df, symbol)
            st.plotly_chart(fig, use_container_width=True)
            
        with c_chart2:
            st.markdown("### 🌏 GLOBAL FEED (TRADINGVIEW)")
            render_tv_widget(symbol)

    else:
        st.error(f"DATA STREAM INTERRUPTED FOR {symbol}. PLEASE CHECK CONNECTION.")

# ================= TAB 2: AI BRAIN (ADVANCED ANALYSIS) =================
with tab2:
    if not df.empty:
        col_ai_1, col_ai_2 = st.columns([1, 2])
        
        with col_ai_1:
            st.markdown("### 🤖 SIGNAL SYNTHESIS")
            rating = analysis['rating']
            r_color = "#444"
            if "BUY" in rating: r_color = "#00ff41"
            elif "SELL" in rating: r_color = "#ff0055"
            
            st.markdown(f"""
            <div class="quantum-card" style="text-align:center; border: 2px solid {r_color};">
                <div style="font-size:16px; color:#888;">AI VERDICT</div>
                <div style="font-size:48px; font-weight:bold; color:{r_color};">{rating}</div>
                <div style="font-size:20px; color:white;">CONFIDENCE: {abs(analysis['score'])}/5</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("#### 🔎 LOGIC BREAKDOWN")
            for r in analysis['reasons']:
                icon = "✅" if "Bullish" in r or "Dip" in r or "Oversold" in r else "🔻"
                st.markdown(f"""<div style="padding:10px; background:#1a1a1a; margin-bottom:5px; border-radius:4px;">{icon} {r}</div>""", unsafe_allow_html=True)

        with col_ai_2:
            st.markdown("### 📊 TECHNICAL MATRIX")
            tech_df = pd.DataFrame({
                "Indicator": ["EMA 50", "EMA 200", "RSI (14)", "MACD", "ATR", "ADX"],
                "Value": [
                    f"{curr['EMA_50']:.4f}", 
                    f"{curr['EMA_200']:.4f}", 
                    f"{curr['RSI_14']:.1f}", 
                    f"{curr['MACD_12_26_9']:.4f}",
                    f"{curr['ATRr_14']:.4f}",
                    f"{curr['ADX_14']:.1f}"
                ],
                "Signal": [
                    "BULL" if curr['close'] > curr['EMA_50'] else "BEAR",
                    "BULL" if curr['close'] > curr['EMA_200'] else "BEAR",
                    "NEUTRAL",
                    "BULL" if curr['MACDh_12_26_9'] > 0 else "BEAR",
                    "HIGH VOLATILITY" if curr['ATRr_14'] > prev['ATRr_14'] else "LOW",
                    "STRONG TREND" if curr['ADX_14'] > 25 else "WEAK"
                ]
            })
            
            def style_matrix(val):
                if val == "BULL": return "color: #00ff41; font-weight:bold"
                if val == "BEAR": return "color: #ff0055; font-weight:bold"
                return "color: #aaa"

            st.dataframe(tech_df.style.map(style_matrix, subset=['Signal']), use_container_width=True, height=300)

# ================= TAB 3: WHALE RADAR (ORDER BOOK) =================
with tab3:
    st.markdown("### 🐋 DEEP SEA SONAR (DEPTH & WALLS)")
    
    with st.spinner("Scanning Order Book..."):
        ob = engine.fetch_order_book(symbol)
    
    if ob:
        w1, w2 = st.columns([3, 1])
        with w1:
            depth_fig = create_depth_chart(ob)
            st.plotly_chart(depth_fig, use_container_width=True)
        
        with w2:
            # Calculate Wall Pressure
            bids_vol = sum([x[1] for x in ob['bids']])
            asks_vol = sum([x[1] for x in ob['asks']])
            total = bids_vol + asks_vol
            buy_pct = (bids_vol / total) * 100
            
            st.markdown("#### ⚖️ PRESSURE GAUGE")
            st.markdown(f"""
            <div style="background:#333; height:30px; border-radius:15px; overflow:hidden; display:flex;">
                <div style="width:{buy_pct}%; background:#00ff41; display:flex; align-items:center; justify-content:center; color:black; font-weight:bold;">{buy_pct:.0f}% BUY</div>
                <div style="width:{100-buy_pct}%; background:#ff0055; display:flex; align-items:center; justify-content:center; color:white; font-weight:bold;">{100-buy_pct:.0f}% SELL</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            st.markdown("#### 🧱 WALL DETECTED")
            top_bid = ob['bids'][0]
            top_ask = ob['asks'][0]
            st.info(f"🟢 Support: {top_bid[1]:.2f} @ {top_bid[0]}")
            st.error(f"🔴 Resistance: {top_ask[1]:.2f} @ {top_ask[0]}")
    else:
        st.warning("Depth Data Unavailable for this pair.")

# ================= TAB 4: NEWS & SIMULATION =================
with tab4:
    col_news, col_sim = st.columns(2)
    
    with col_news:
        st.markdown("### 📰 QUANTUM NEWS FEED (SIMULATED)")
        # Mock data (Vì News API xịn phải trả tiền)
        news_data = [
            {"time": "2 mins ago", "title": f"Huge {symbol.split('/')[0]} transaction detected: 5,000 BTC moved to unknown wallet.", "sentiment": "Neutral"},
            {"time": "15 mins ago", "title": "SEC Chairman comments on crypto regulations.", "sentiment": "Bearish"},
            {"time": "1 hour ago", "title": "Tech stocks rally, pulling crypto market up.", "sentiment": "Bullish"},
            {"time": "2 hours ago", "title": f"{symbol.split('/')[0]} breaks key resistance level at ${curr['close']*0.98:.2f}", "sentiment": "Bullish"},
        ]
        
        for n in news_data:
            color = "#00ff41" if n['sentiment'] == "Bullish" else ("#ff0055" if n['sentiment'] == "Bearish" else "#00f2ff")
            st.markdown(f"""
            <div style="border-left: 3px solid {color}; padding-left: 10px; margin-bottom: 15px; background: #111; padding: 10px; border-radius: 0 4px 4px 0;">
                <div style="font-size:12px; color:#666;">{n['time']} • <span style="color:{color}">{n['sentiment']}</span></div>
                <div style="font-size:15px; color:#e0e0e0;">{n['title']}</div>
            </div>
            """, unsafe_allow_html=True)

    with col_sim:
        st.markdown("### 🎲 TRADE SIMULATOR (PAPER)")
        st.caption("Test your strategy risk-free")
        
        amount = st.number_input("Amount (USD)", value=1000)
        leverage = st.slider("Leverage", 1, 20, 5)
        
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("OPEN LONG 🚀", type="primary", use_container_width=True):
            st.success(f"Position OPENED: LONG {symbol} x{leverage}. Entry: {curr['close']}")
            st.balloons()
            
        if col_btn2.button("OPEN SHORT 📉", type="primary", use_container_width=True):
            st.error(f"Position OPENED: SHORT {symbol} x{leverage}. Entry: {curr['close']}")

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #444; font-size: 12px;">
    THANGLONG QUANTUM TERMINAL | SYSTEM ID: TQT-9000-ALPHA <br>
    POWERED BY PYTHON • STREAMLIT • PLOTLY • PANDAS_TA
</div>
""", unsafe_allow_html=True)
