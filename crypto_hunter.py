import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import plotly.graph_objects as go
from datetime import datetime
import time

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG (SYSTEM CONFIG)
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="Crypto Hunter V1", 
    page_icon="🐲",
    initial_sidebar_state="expanded"
)

# Giao diện Dark Mode & Hacker Style
st.markdown("""
<style>
    /* Font chữ */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] {font-family: 'JetBrains Mono', monospace;}
    
    /* Card thông số */
    .metric-card {
        background-color: #111;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 0 10px rgba(0,255,0,0.1);
    }
    .metric-value {font-size: 24px; font-weight: bold; color: #00ff00;}
    .metric-label {font-size: 14px; color: #888;}
    
    /* Highlight Tín hiệu */
    .signal-buy {color: #00ff00; font-weight: bold; padding: 5px; border: 1px solid #00ff00; border-radius: 4px;}
    .signal-sell {color: #ff0000; font-weight: bold; padding: 5px; border: 1px solid #ff0000; border-radius: 4px;}
    
    /* Tinh chỉnh bảng */
    [data-testid="stDataFrame"] {border: 1px solid #333;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KẾT NỐI DỮ LIỆU (DATA ENGINE)
# ==========================================
@st.cache_resource
def init_exchange():
    """Khởi tạo kết nối Binance (Public API - Không cần Key)"""
    return ccxt.binance({
        'enableRateLimit': True, 
        'options': {'defaultType': 'future'} # Ưu tiên dữ liệu Futures (hoặc spot tùy chỉnh)
    })

exchange = init_exchange()

@st.cache_data(ttl=60) # Cache 60s để không bị sàn chặn IP
def get_top_coins(limit=30):
    """Lấy danh sách Top Coin theo Volume"""
    try:
        tickers = exchange.fetch_tickers()
        # Lọc cặp USDT và Volume lớn
        symbols = [s for s in tickers if s.endswith('/USDT')]
        sorted_symbols = sorted(symbols, key=lambda x: tickers[x]['quoteVolume'], reverse=True)
        return sorted_symbols[:limit]
    except:
        return ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT']

@st.cache_data(ttl=30)
def fetch_data(symbol, timeframe, limit=100):
    """Lấy dữ liệu nến OHLCV"""
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except:
        return pd.DataFrame()

# ==========================================
# 3. BỘ NÃO PHÂN TÍCH (AI ANALYZER)
# ==========================================
def analyze_market(df):
    """Tính toán chỉ báo kỹ thuật"""
    if df.empty: return None
    
    # RSI
    df.ta.rsi(length=14, append=True)
    # Bollinger Bands
    df.ta.bbands(length=20, std=2, append=True)
    # MACD
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    # EMA
    df.ta.ema(length=34, append=True)
    df.ta.ema(length=89, append=True)
    
    return df

def scan_worker(symbols, timeframe):
    """Máy quét hoạt động ngầm"""
    report = []
    my_bar = st.progress(0)
    
    for i, sym in enumerate(symbols):
        # Update progress
        my_bar.progress((i+1)/len(symbols))
        
        df = fetch_data(sym, timeframe, limit=50)
        if not df.empty:
            df = analyze_market(df)
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            # 1. Logic RSI
            rsi = curr['RSI_14']
            rsi_status = "Neutral"
            if rsi < 30: rsi_status = "Oversold (MUA)"
            elif rsi > 70: rsi_status = "Overbought (BÁN)"
            
            # 2. Logic Volume Đột biến
            vol_avg = df['volume'].rolling(20).mean().iloc[-1]
            vol_spike = curr['volume'] / vol_avg if vol_avg > 0 else 0
            
            # 3. Logic Xu Hướng (EMA)
            trend = "Tăng" if curr['close'] > curr['EMA_34'] else "Giảm"
            
            # Chỉ lấy những coin có biến động
            report.append({
                "Coin": sym,
                "Giá": curr['close'],
                "RSI": rsi,
                "Vol Spike": vol_spike,
                "Trend": trend,
                "Tín Hiệu": rsi_status
            })
            
    my_bar.empty()
    return pd.DataFrame(report)

# ==========================================
# 4. GIAO DIỆN NGƯỜI DÙNG (UI/UX)
# ==========================================
st.sidebar.title("🐲 CRYPTO HUNTER")
st.sidebar.write("---")

# Menu chọn chế độ
mode = st.sidebar.radio("CHẾ ĐỘ HOẠT ĐỘNG:", ["📊 Dashboard Realtime", "📡 Máy Quét (Scanner)"])

st.sidebar.write("---")
# Cấu hình chung
timeframe = st.sidebar.selectbox("Khung Thời Gian:", ['15m', '1h', '4h', '1d'], index=2)
top_n = st.sidebar.slider("Số lượng Coin quét:", 10, 50, 20)

# --- CHẾ ĐỘ 1: DASHBOARD ---
if mode == "📊 Dashboard Realtime":
    st.title(f"📊 DASHBOARD: {timeframe}")
    
    # Chọn Coin để soi
    available_coins = get_top_coins(50)
    selected_coin = st.selectbox("🔍 Chọn Coin để soi chart:", available_coins, index=0)
    
    if st.button("🔄 Cập nhật dữ liệu"):
        st.cache_data.clear()
        st.rerun()

    # Lấy dữ liệu
    df = fetch_data(selected_coin, timeframe, limit=150)
    
    if not df.empty:
        df = analyze_market(df)
        curr = df.iloc[-1]
        change_pct = (curr['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close'] * 100
        
        # 1. Hiển thị thông số Top
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-card"><div class="metric-label">Giá Hiện Tại</div><div class="metric-value">{curr["close"]:.4f}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-label">Thay đổi 1 nến</div><div class="metric-value" style="color: {"#00ff00" if change_pct>0 else "#ff0000"}">{change_pct:+.2f}%</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-label">RSI (14)</div><div class="metric-value">{curr["RSI_14"]:.1f}</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-label">Vol Spike</div><div class="metric-value">{curr["volume"]/df["volume"].rolling(20).mean().iloc[-1]:.1f}x</div></div>', unsafe_allow_html=True)
        
        # 2. Vẽ Chart Nến xịn sò
        fig = go.Figure()
        
        # Nến Nhật
        fig.add_trace(go.Candlestick(x=df.index,
                        open=df['open'], high=df['high'],
                        low=df['low'], close=df['close'],
                        name='Price'))
        
        # Bollinger Bands
        fig.add_trace(go.Scatter(x=df.index, y=df['BBU_20_2.0'], line=dict(color='rgba(255, 255, 255, 0.3)', width=1), name='Upper BB'))
        fig.add_trace(go.Scatter(x=df.index, y=df['BBL_20_2.0'], line=dict(color='rgba(255, 255, 255, 0.3)', width=1), name='Lower BB'))
        
        # EMA
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_34'], line=dict(color='#f0b90b', width=1.5), name='EMA 34 (Vàng)'))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_89'], line=dict(color='#00b894', width=1.5), name='EMA 89 (Xanh)'))

        fig.update_layout(
            height=650, 
            template="plotly_dark", 
            title=f"{selected_coin} - {timeframe}",
            xaxis_rangeslider_visible=False,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 3. Order Book & Data (Demo text)
        st.info("💡 Mẹo: RSI > 70 là vùng Quá Mua (cẩn thận Short), RSI < 30 là vùng Quá Bán (canh Long).")

# --- CHẾ ĐỘ 2: SCANNER ---
elif mode == "📡 Máy Quét (Scanner)":
    st.title("📡 MÁY QUÉT CÁ VOI (WHALE HUNTER)")
    st.write(f"Đang cấu hình quét: Top {top_n} Coins | Khung: {timeframe}")
    
    col_btn, col_info = st.columns([1, 4])
    with col_btn:
        start_scan = st.button("🚀 KÍCH HOẠT RADAR", type="primary")
    
    if start_scan:
        with st.spinner("Emo đang đi săn... Vui lòng không tắt trình duyệt..."):
            # 1. Lấy list coin
            scan_list = get_top_coins(top_n)
            
            # 2. Chạy quét
            result_df = scan_worker(scan_list, timeframe)
            
            # 3. Hiển thị kết quả
            if not result_df.empty:
                # Sắp xếp ưu tiên: Vol đột biến hoặc RSI dị biệt
                result_df['Score'] = abs(result_df['RSI'] - 50) + (result_df['Vol Spike'] * 10)
                result_df = result_df.sort_values(by='Score', ascending=False).drop(columns=['Score'])
                
                # Format màu sắc
                def highlight_row(val):
                    if val < 30: return 'color: #00ff00; font-weight: bold' # Xanh lá
                    elif val > 70: return 'color: #ff0000; font-weight: bold' # Đỏ
                    return ''

                def highlight_vol(val):
                    if val > 2.0: return 'color: #f0b90b; font-weight: bold' # Vàng
                    return ''

                st.subheader("🎯 MỤC TIÊU ĐÃ PHÁT HIỆN")
                st.dataframe(
                    result_df.style
                    .map(highlight_row, subset=['RSI'])
                    .map(highlight_vol, subset=['Vol Spike'])
                    .format({"Giá": "{:.4f}", "RSI": "{:.1f}", "Vol Spike": "{:.2f}x"}),
                    use_container_width=True,
                    height=600
                )
                
                # Báo cáo nhanh
                opportunities = result_df[(result_df['RSI'] < 30) | (result_df['RSI'] > 70) | (result_df['Vol Spike'] > 2.5)]
                if not opportunities.empty:
                    st.success(f"🔥 Phát hiện {len(opportunities)} tín hiệu mạnh!")
                    for i, row in opportunities.iterrows():
                        msg = f"**{row['Coin']}**: RSI {row['RSI']:.1f} | Vol {row['Vol Spike']:.1f}x -> {row['Tín Hiệu']}"
                        if "MUA" in row['Tín Hiệu']: st.markdown(f":green[{msg}]")
                        elif "BÁN" in row['Tín Hiệu']: st.markdown(f":red[{msg}]")
                        else: st.markdown(f":orange[{msg}]")
            else:
                st.warning("Không lấy được dữ liệu. Vui lòng thử lại sau.")

# Footer
st.markdown("---")
st.caption("Developed by ThangLong & Emo | Data provided by Binance")
