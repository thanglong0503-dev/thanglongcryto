import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import plotly.graph_objects as go
import time
from datetime import datetime

# ==============================================================================
# 1. CẤU HÌNH GIAO DIỆN "HACKER / SPY MODE"
# ==============================================================================
st.set_page_config(layout="wide", page_title="Emo Whale Hunter", page_icon="🦈", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* 1. THEME: DARK SPY */
    :root { --bg: #000000; --card: #111111; --text: #00ff41; --alert: #ff0055; --border: #333; }
    .stApp { background-color: var(--bg); color: var(--text); font-family: 'Courier New', monospace; }
    
    /* 2. TABLE MATRIX */
    div[data-testid="stDataFrame"] { border: 1px solid var(--border); }
    
    /* 3. METRIC BOXES */
    .spy-card {
        background: var(--card); border: 1px solid var(--border); padding: 15px; margin-bottom: 10px;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.1);
    }
    .spy-label { font-size: 12px; color: #888; text-transform: uppercase; }
    .spy-val { font-size: 24px; font-weight: bold; color: #fff; }
    .spy-alert { color: var(--alert); animation: blink 1s infinite; }
    
    @keyframes blink { 50% { opacity: 0; } }

    /* 4. SIGNAL BADGES */
    .badge-long { background: #004400; color: #00ff41; padding: 2px 8px; border: 1px solid #00ff41; border-radius: 4px; }
    .badge-short { background: #440000; color: #ff0055; padding: 2px 8px; border: 1px solid #ff0055; border-radius: 4px; }
    
    /* 5. CUSTOM BUTTON */
    button[kind="primary"] {
        background-color: var(--text) !important; color: black !important; font-weight: bold !important; border-radius: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SPY ENGINE (BỘ NÃO XỬ LÝ)
# ==============================================================================
@st.cache_resource
def get_exchange():
    try: return ccxt.binanceus({'enableRateLimit': True})
    except: return ccxt.kraken({'enableRateLimit': True})

exchange = get_exchange()

@st.cache_data(ttl=300)
def get_top_coins():
    try:
        tickers = exchange.fetch_tickers()
        syms = [s for s in tickers if '/USDT' in s]
        # Lấy Top 20 coin Volume lớn nhất để soi
        sorted_syms = sorted(syms, key=lambda x: tickers[x]['quoteVolume'] if 'quoteVolume' in tickers[x] else 0, reverse=True)
        return sorted_syms[:20]
    except: return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'DOGE/USDT']

def analyze_whale_activity(symbol):
    """
    Thuật toán soi Orderbook để tìm tường lệnh (Whale Walls)
    và phân tích RSI/Volume để tìm tín hiệu gom hàng.
    """
    try:
        # 1. Lấy dữ liệu nến (Technical)
        bars = exchange.fetch_ohlcv(symbol, '1h', limit=50)
        df = pd.DataFrame(bars, columns=['t', 'o', 'h', 'l', 'c', 'v'])
        
        # Chỉ báo
        rsi = ta.rsi(df['c'], length=14).iloc[-1]
        vol_ma = df['v'].rolling(20).mean().iloc[-1]
        curr_vol = df['v'].iloc[-1]
        vol_spike = curr_vol / vol_ma if vol_ma > 0 else 0
        
        # 2. Lấy Orderbook (Whale Data)
        ob = exchange.fetch_order_book(symbol, limit=20)
        bids = ob['bids']
        asks = ob['asks']
        
        bid_vol = sum([x[1] for x in bids])
        ask_vol = sum([x[1] for x in asks])
        pressure = (bid_vol / (bid_vol + ask_vol)) * 100 # % Mua áp đảo
        
        # Tìm tường lệnh khủng (Lệnh > 5% tổng vol orderbook)
        walls = []
        for p, q in bids:
            if q > bid_vol * 0.1: walls.append(f"🟢 BUY WALL: {q:.2f} @ {p}")
        for p, q in asks:
            if q > ask_vol * 0.1: walls.append(f"🔴 SELL WALL: {q:.2f} @ {p}")
            
        # TỔNG HỢP TÍN HIỆU
        signal = "WAIT"
        score = 0
        
        # Logic Cá Mập Gom Hàng: Giá giảm/đi ngang + Vol tăng + Tường Mua dày
        if rsi < 35 and pressure > 60: 
            signal = "WHALE ACCUM (LONG)"
            score = 90
        # Logic Cá Mập Xả Hàng: Giá tăng nóng + Tường Bán dày
        elif rsi > 70 and pressure < 40:
            signal = "WHALE DUMP (SHORT)"
            score = -90
        # Logic Breakout: Vol đột biến
        elif vol_spike > 2.5:
            signal = "VOL SPIKE (ALERT)"
            score = 50
            
        return {
            "symbol": symbol,
            "price": df['c'].iloc[-1],
            "rsi": rsi,
            "pressure": pressure,
            "vol_spike": vol_spike,
            "walls": walls,
            "signal": signal,
            "score": score
        }
    except: return None

# ==============================================================================
# 3. UI LAYOUT: THE HUNTER DASHBOARD
# ==============================================================================

# Header
c1, c2 = st.columns([1, 6])
with c1: st.markdown("# 🦈")
with c2: st.markdown("# EMO HUNTER <span style='color:#00ff41'>RADAR</span>", unsafe_allow_html=True)

# Control Panel
col_scan_btn, col_progress = st.columns([1, 3])
with col_scan_btn:
    scan = st.button("📡 QUÉT THỊ TRƯỜNG NGAY", type="primary")

# --- MAIN SCANNING LOGIC ---
if scan:
    coins = get_top_coins()
    results = []
    
    # Progress Bar Spy Style
    my_bar = st.progress(0)
    status = st.empty()
    
    for i, sym in enumerate(coins):
        my_bar.progress((i+1)/len(coins))
        status.markdown(f"`SCANNING NETWORK... TARGET: {sym}`")
        
        data = analyze_whale_activity(sym)
        if data:
            results.append(data)
            
    my_bar.empty()
    status.empty()
    
    # --- DISPLAY RESULTS ---
    
    # 1. ALERT SECTION (Các tín hiệu mạnh nhất)
    st.markdown("### 🚨 HIGH PRIORITY ALERTS (CÁ MẬP ĐANG HOẠT ĐỘNG)")
    
    alerts = [r for r in results if abs(r['score']) >= 50]
    
    if alerts:
        col_alerts = st.columns(len(alerts) if len(alerts) < 4 else 4)
        for idx, alert in enumerate(alerts):
            with col_alerts[idx % 4]:
                color = "#00ff41" if alert['score'] > 0 else "#ff0055"
                action = "GOM HÀNG" if alert['score'] > 0 else "XẢ HÀNG"
                st.markdown(f"""
                <div class="spy-card" style="border-left: 5px solid {color}">
                    <div class="spy-label">{alert['symbol']}</div>
                    <div class="spy-val" style="color:{color}">{action}</div>
                    <div style="font-size:12px; margin-top:5px;">RSI: {alert['rsi']:.1f}</div>
                    <div style="font-size:12px;">Vol: {alert['vol_spike']:.1f}x</div>
                    <div style="font-size:12px; color:{color}">Áp lực: {alert['pressure']:.0f}%</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Thị trường yên tĩnh. Cá mập đang ngủ.")

    # 2. MARKET MATRIX (Bảng tổng sắp)
    st.markdown("### 📟 SIGNAL MATRIX")
    
    # Chế biến Dataframe
    df_res = pd.DataFrame(results)
    df_res['SIGNAL_BADGE'] = df_res.apply(lambda x: 
        f"🟢 LONG" if x['score'] > 50 else (f"🔴 SHORT" if x['score'] < -50 else "⚪ WAIT"), axis=1)
    
    # Display Table with Highlighting
    st.dataframe(
        df_res[['symbol', 'price', 'rsi', 'pressure', 'vol_spike', 'SIGNAL_BADGE']].style
        .map(lambda v: 'color: #00ff41; font-weight: bold' if v > 60 else '', subset=['pressure'])
        .map(lambda v: 'color: #ff0055; font-weight: bold' if v < 40 else '', subset=['pressure'])
        .map(lambda v: 'color: #00ff41' if v < 30 else ('color: #ff0055' if v > 70 else ''), subset=['rsi'])
        .format({"price": "{:.4f}", "rsi": "{:.1f}", "pressure": "{:.1f}%", "vol_spike": "{:.2f}x"}),
        use_container_width=True,
        height=400
    )

    # 3. DEEP DIVE (Soi chi tiết 1 con)
    st.markdown("### 🔬 DEEP DIVE INSPECTOR")
    selected_coin = st.selectbox("Chọn coin để soi Tường Lệnh:", [r['symbol'] for r in results])
    
    target_data = next((item for item in results if item["symbol"] == selected_coin), None)
    
    if target_data:
        c_d1, c_d2 = st.columns([2, 1])
        
        with c_d1:
            # Vẽ biểu đồ tường lệnh (Text based cho nhanh và ngầu)
            st.markdown(f"**PHÂN TÍCH TƯỜNG LỆNH (WALLS) CỦA {selected_coin}**")
            if target_data['walls']:
                for wall in target_data['walls']:
                    st.code(wall)
            else:
                st.write("Không phát hiện tường lệnh lớn > 10% volume.")
                
        with c_d2:
            # Máy tính khuyến nghị
            rec = "NÊN ĐỨNG NGOÀI"
            color = "gray"
            if target_data['score'] > 50: 
                rec = "NÊN MUA (FOLLOW WHALE)"
                color = "#00ff41"
            elif target_data['score'] < -50:
                rec = "NÊN BÁN (WHALE DUMPING)"
                color = "#ff0055"
                
            st.markdown(f"""
            <div class="spy-card" style="text-align:center">
                <div class="spy-label">EMO KHUYẾN NGHỊ</div>
                <div style="font-size:20px; font-weight:bold; color:{color}">{rec}</div>
            </div>
            """, unsafe_allow_html=True)

else:
    st.info("👈 Bấm nút 'QUÉT THỊ TRƯỜNG NGAY' để Emo đi săn cá mập cho Ngài.")
    
    # Demo Ticker Tape
    st.markdown("---")
    st.markdown("""
    <marquee style="color: #00ff41; font-family: monospace;">
    [LIVE FEED] WHALE ALERT: 500 BTC moved to Binance ... LARGE BUY WALL detected on SOL/USDT @ 135.00 ... RSI Divergence on ETH/USDT [H4] ...
    </marquee>
    """, unsafe_allow_html=True)
