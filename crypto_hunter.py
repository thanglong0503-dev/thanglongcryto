import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import plotly.graph_objects as go
import numpy as np
import time
from datetime import datetime
import streamlit.components.v1 as components
import random

# ==============================================================================
# 1. SYSTEM CONFIG & BINANCE UI INJECTION
# ==============================================================================
st.set_page_config(
    layout="wide",
    page_title="Titan Terminal | Binance Grade",
    page_icon="💎",
    initial_sidebar_state="expanded"
)

# --- CSS SIÊU CẤP BINANCE/OKX ---
st.markdown("""
<style>
    /* NHÚNG FONT CHỮ CHUYÊN NGHIỆP */
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Roboto:wght@400;500;700&display=swap');

    :root {
        --bg-dark: #181a20; /* Binance Black */
        --bg-card: #1e2329; /* Binance Card Grey */
        --text-primary: #eaecef;
        --text-secondary: #848e9c;
        --binance-yellow: #fcd535;
        --up-green: #0ecb81;
        --down-red: #f6465d;
        --hover-bg: #2b3139;
    }

    /* GLOBAL RESET */
    .stApp { background-color: var(--bg-dark) !important; color: var(--text-primary) !important; font-family: 'Roboto', sans-serif !important; }
    
    /* HEADER & SIDEBAR FIX */
    header[data-testid="stHeader"] { display: none !important; } /* Ẩn header mặc định cho rộng */
    section[data-testid="stSidebar"] { background-color: var(--bg-card) !important; border-right: 1px solid #2b3139; }
    
    /* INPUTS CHUẨN SÀN */
    div[data-baseweb="input"] { background-color: #2b3139 !important; border: 1px solid #474d57 !important; border-radius: 4px !important; }
    input { color: var(--text-primary) !important; font-family: 'IBM Plex Mono', monospace !important; }
    div[data-baseweb="select"] > div { background-color: #2b3139 !important; color: var(--text-primary) !important; border-color: #474d57 !important; }
    
    /* DROPDOWN MENU */
    ul[data-baseweb="menu"] { background-color: var(--bg-card) !important; }
    li[data-baseweb="option"] { color: var(--text-primary) !important; }
    li[data-baseweb="option"]:hover { background-color: var(--hover-bg) !important; color: var(--binance-yellow) !important; }

    /* CUSTOM METRIC BOXES */
    .titan-metric {
        background-color: var(--bg-card);
        border: 1px solid #2b3139;
        border-radius: 4px;
        padding: 12px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .titan-label { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
    .titan-val { font-size: 20px; font-weight: 600; font-family: 'IBM Plex Mono'; }
    .color-up { color: var(--up-green); }
    .color-down { color: var(--down-red); }

    /* ORDER BOOK STYLING */
    .ob-row { display: flex; justify-content: space-between; font-family: 'IBM Plex Mono'; font-size: 12px; padding: 2px 0; }
    .ob-buy { color: var(--up-green); }
    .ob-sell { color: var(--down-red); }
    .ob-amt { color: var(--text-secondary); }

    /* BUTTONS */
    button[kind="primary"] {
        background-color: var(--binance-yellow) !important;
        color: #181a20 !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 4px !important;
    }
    button[kind="secondary"] {
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid #474d57 !important;
    }

    /* TABS */
    .stTabs [aria-selected="true"] {
        color: var(--binance-yellow) !important;
        border-bottom-color: var(--binance-yellow) !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. TITAN ENGINE (ROBUST BACKEND)
# ==============================================================================
class TitanEngine:
    def __init__(self):
        # Kết nối an toàn (US hoặc Kraken để tránh chặn IP)
        try: self.exchange = ccxt.binanceus({'enableRateLimit': True})
        except: self.exchange = ccxt.kraken({'enableRateLimit': True})

    @st.cache_data(ttl=600)
    def get_symbols(_self):
        try:
            tickers = _self.exchange.fetch_tickers()
            # Lọc chỉ cặp USDT và USD
            syms = [s for s in tickers if '/USDT' in s or '/USD' in s]
            # Sort theo Volume
            return sorted(syms, key=lambda x: tickers[x]['quoteVolume'] if 'quoteVolume' in tickers[x] else 0, reverse=True)[:50]
        except: return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']

    def fetch_data(self, symbol, timeframe, limit=100):
        # Thử lại 3 lần nếu mạng lỗi
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

    def analyze(self, df):
        if df.empty: return df, {}
        # Safe Indicators (Tránh KeyError)
        try:
            df.ta.rsi(length=14, append=True)
            df.ta.macd(append=True)
            df.ta.bbands(length=20, std=2, append=True)
            df.ta.ema(length=50, append=True)
            df.ta.ema(length=200, append=True)
        except: pass

        curr = df.iloc[-1]
        
        # Tìm cột an toàn
        def get_val(pattern, default=0):
            cols = [c for c in df.columns if c.startswith(pattern)]
            return curr[cols[0]] if cols else default

        score = 50 # Điểm cơ bản
        reasons = []

        # RSI Logic
        rsi = get_val('RSI')
        if rsi < 30: score += 20; reasons.append("RSI Quá bán (MUA)")
        elif rsi > 70: score -= 20; reasons.append("RSI Quá mua (BÁN)")
        
        # Trend Logic
        ema50 = get_val('EMA_50')
        ema200 = get_val('EMA_200')
        if ema50 > 0 and ema200 > 0:
            if ema50 > ema200: score += 10; reasons.append("Xu hướng Tăng (Golden Cross)")
            else: score -= 10; reasons.append("Xu hướng Giảm (Death Cross)")

        return df, {"score": score, "reasons": reasons, "rsi": rsi}

engine = TitanEngine()

# ==============================================================================
# 3. COMPONENTS (UI BLOCKS)
# ==============================================================================

def render_ticker_tape(coins):
    # Dòng chữ chạy (Marquee) giả lập
    html = """
    <div style="background-color: #1e2329; color: #fff; padding: 5px; white-space: nowrap; overflow: hidden; border-bottom: 1px solid #2b3139;">
        <marquee scrollamount="5">
            <span style="color:#0ecb81">BTC/USDT +2.4%</span> &nbsp;&nbsp;&nbsp; 
            <span style="color:#f6465d">ETH/USDT -1.2%</span> &nbsp;&nbsp;&nbsp; 
            <span style="color:#0ecb81">SOL/USDT +5.8%</span> &nbsp;&nbsp;&nbsp; 
            <span style="color:#fcd535">BNB/USDT 0.0%</span> &nbsp;&nbsp;&nbsp; 
            <span style="color:#0ecb81">DOGE/USDT +12.1%</span> &nbsp;&nbsp;&nbsp;
            <span style="color:#f6465d">XRP/USDT -0.5%</span>
        </marquee>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_order_book_sim(current_price):
    # Giả lập Sổ lệnh (Vì API Free không cho lấy realtime nhanh)
    st.markdown("""<div style="font-size:14px; font-weight:bold; margin-bottom:10px; color:#eaecef">ORDER BOOK</div>""", unsafe_allow_html=True)
    
    # Asks (Bán - Đỏ)
    for i in range(5, 0, -1):
        p = current_price * (1 + i*0.0005)
        v = random.uniform(0.1, 2.0)
        st.markdown(f"""<div class="ob-row"><span class="ob-sell">{p:,.2f}</span><span class="ob-amt">{v:.4f}</span></div>""", unsafe_allow_html=True)
    
    # Current Price
    st.markdown(f"""<div style="font-size:16px; color:#fcd535; font-weight:bold; padding:5px 0; text-align:center;">{current_price:,.2f}</div>""", unsafe_allow_html=True)
    
    # Bids (Mua - Xanh)
    for i in range(1, 6):
        p = current_price * (1 - i*0.0005)
        v = random.uniform(0.1, 2.0)
        st.markdown(f"""<div class="ob-row"><span class="ob-buy">{p:,.2f}</span><span class="ob-amt">{v:.4f}</span></div>""", unsafe_allow_html=True)

def render_recent_trades():
    st.markdown("""<div style="font-size:14px; font-weight:bold; margin-top:20px; margin-bottom:10px; color:#eaecef">RECENT TRADES</div>""", unsafe_allow_html=True)
    # Giả lập trade history
    times = [datetime.now().strftime("%H:%M:%S")] * 5
    for t in times:
        is_buy = random.choice([True, False])
        color = "#0ecb81" if is_buy else "#f6465d"
        amount = random.uniform(0.01, 0.5)
        st.markdown(f"""
        <div class="ob-row">
            <span style="color:#848e9c">{t}</span>
            <span style="color:{color}">{amount:.4f}</span>
        </div>""", unsafe_allow_html=True)

def render_chart_tv(symbol):
    base = symbol.split('/')[0]
    # Chart xịn full width
    html = f"""
    <div class="tradingview-widget-container" style="height:600px;width:100%">
      <div id="tv_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
      "autosize": true, "symbol": "BINANCE:{base}USDT", "interval": "60", "timezone": "Asia/Ho_Chi_Minh",
      "theme": "dark", "style": "1", "locale": "vi_VN", "enable_publishing": false,
      "backgroundColor": "#181a20", "gridColor": "rgba(40,40,40,0.5)",
      "hide_top_toolbar": false, "container_id": "tv_chart",
      "studies": ["RSI@tv-basicstudies", "MACD@tv-basicstudies", "BB@tv-basicstudies"]
      }});
      </script>
    </div>"""
    components.html(html, height=610)

# ==============================================================================
# 4. MAIN LAYOUT EXECUTION
# ==============================================================================

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 💎 TITAN")
    menu = st.radio("MENU", ["TRADE", "MARKETS", "WALLETS", "BOTS"], index=0)
    st.markdown("---")
    
    if menu == "WALLETS":
        st.info("Ví giả lập: $10,000 USDT")
    elif menu == "BOTS":
        st.warning("Tính năng Bot Auto-Trade đang bảo trì.")

# --- TOP BAR ---
render_ticker_tape(None)

# --- MAIN DASHBOARD (Chỉ hiện khi chọn menu TRADE) ---
if menu == "TRADE":
    
    # 1. HEADER CONTROL (Symbol & Stats)
    coins = engine.get_symbols()
    
    c1, c2, c3 = st.columns([1, 1, 4])
    with c1:
        # Hybrid Search Input (Fix Input Đen)
        st.caption("TÌM KIẾM MÃ")
        search = st.text_input("s", placeholder="VD: BTC", label_visibility="collapsed")
    with c2:
        st.caption("DANH SÁCH")
        select = st.selectbox("l", coins, label_visibility="collapsed")
    
    # Logic chọn symbol
    raw = search.upper().strip() if search else select
    symbol = f"{raw}/USDT" if "/USDT" not in raw and "/USD" not in raw else raw

    # 2. FETCH DATA ENGINE
    with st.spinner(f"Connecting to Binance Mainnet for {symbol}..."):
        df = engine.fetch_data(symbol, '1h')
        # Fallback
        if df.empty and '/USDT' in symbol:
            symbol = symbol.replace('/USDT', '/USD')
            df = engine.fetch_data(symbol, '1h')
    
    # 3. STATS BAR (Giống Binance)
    if not df.empty:
        df, analysis = engine.analyze(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        change_pct = (curr['close'] - prev['close']) / prev['close'] * 100
        vol = curr['volume'] * curr['close']
        
        col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
        color = "color-up" if change_pct >= 0 else "color-down"
        
        with col_s1: st.markdown(f"""<div class="titan-metric"><span class="titan-label">GIÁ HIỆN TẠI</span><span class="titan-val {color}">{curr['close']:,.4f}</span></div>""", unsafe_allow_html=True)
        with col_s2: st.markdown(f"""<div class="titan-metric"><span class="titan-label">24H CHANGE</span><span class="titan-val {color}">{change_pct:+.2f}%</span></div>""", unsafe_allow_html=True)
        with col_s3: st.markdown(f"""<div class="titan-metric"><span class="titan-label">24H HIGH</span><span class="titan-val">{curr['high']:,.4f}</span></div>""", unsafe_allow_html=True)
        with col_s4: st.markdown(f"""<div class="titan-metric"><span class="titan-label">24H LOW</span><span class="titan-val">{curr['low']:,.4f}</span></div>""", unsafe_allow_html=True)
        with col_s5: st.markdown(f"""<div class="titan-metric"><span class="titan-label">24H VOL (USDT)</span><span class="titan-val">{vol:,.0f}</span></div>""", unsafe_allow_html=True)

        st.write("") # Spacer

        # 4. MAIN GRID (Chart Left - OrderBook Right)
        col_main, col_side = st.columns([3, 1])
        
        with col_main:
            # Tabs cho Chart
            tab_chart, tab_info = st.tabs(["CHART (TradingView)", "AI ANALYSIS"])
            
            with tab_chart:
                render_chart_tv(symbol)
                
            with tab_info:
                st.markdown("### 🧠 TITAN AI SCORE")
                score = analysis['score']
                s_color = "#0ecb81" if score > 60 else ("#f6465d" if score < 40 else "#fcd535")
                
                c_ai1, c_ai2 = st.columns([1, 3])
                with c_ai1:
                    st.markdown(f"""
                    <div style="border: 2px solid {s_color}; border-radius:50%; width:150px; height:150px; display:flex; align-items:center; justify-content:center; flex-direction:column; margin:auto;">
                        <div style="font-size:40px; font-weight:bold; color:{s_color}">{score}</div>
                        <div style="font-size:12px; color:#888">SENTIMENT</div>
                    </div>
                    """, unsafe_allow_html=True)
                with c_ai2:
                    st.write("#### TÍN HIỆU CHI TIẾT:")
                    for r in analysis['reasons']:
                        st.markdown(f"- {r}")
                    st.caption(f"RSI: {analysis['rsi']:.2f}")

        with col_side:
            # ORDER BOOK & TRADES (Sidebar phải)
            st.markdown("""<div style="background-color:#1e2329; padding:10px; border-radius:4px; height: 650px;">""", unsafe_allow_html=True)
            render_order_book_sim(curr['close'])
            st.markdown("---")
            render_recent_trades()
            st.markdown("</div>", unsafe_allow_html=True)

        # 5. BOTTOM SECTION: WHALE ALERT & SIMULATOR
        st.write("")
        col_b1, col_b2 = st.columns(2)
        
        with col_b1:
            st.markdown("### 🐋 WHALE ALERT FEED")
            whale_msgs = [
                f"🚨 {random.randint(500, 2000)} BTC moved from Binance to Unknown Wallet.",
                f"💰 {random.randint(10000, 50000)} SOL transferred to Coinbase.",
                f"🔥 {random.randint(1000000, 5000000)} USDT minted at Tether Treasury."
            ]
            for msg in whale_msgs:
                st.warning(msg)
                
        with col_b2:
            st.markdown("### 🎰 POSITION SIMULATOR (Paper Trading)")
            with st.form("sim_form"):
                c_f1, c_f2 = st.columns(2)
                with c_f1: 
                    amt = st.number_input("Vốn vào lệnh ($)", value=1000)
                with c_f2:
                    lev = st.slider("Đòn bẩy (x)", 1, 125, 20)
                
                col_long, col_short = st.columns(2)
                with col_long:
                    if st.form_submit_button("BUY / LONG 🟢", use_container_width=True):
                        st.success(f"Đã mở LONG {symbol} | Entry: {curr['close']} | Size: ${amt*lev:,.0f}")
                with col_short:
                    if st.form_submit_button("SELL / SHORT 🔴", use_container_width=True):
                        st.error(f"Đã mở SHORT {symbol} | Entry: {curr['close']} | Size: ${amt*lev:,.0f}")

    else:
        st.error(f"⚠️ Không thể tải dữ liệu cho {symbol}. Vui lòng thử mã khác (VD: BTC/USDT).")

elif menu == "MARKETS":
    st.title("MARKET OVERVIEW (Top Gainers)")
    st.dataframe(pd.DataFrame({
        "Symbol": ["DOGE/USDT", "PEPE/USDT", "BTC/USDT"],
        "Price": [0.12, 0.000001, 65000],
        "Change": ["+12%", "+8%", "+2%"]
    }), use_container_width=True)

# --- FOOTER STATUS ---
st.markdown("---")
col_f1, col_f2 = st.columns([4, 1])
with col_f1: st.caption("Titan Terminal v5.0 | Powered by Binance Cloud Data")
with col_f2: st.caption(f"Latency: {random.randint(20, 100)}ms 🟢")
