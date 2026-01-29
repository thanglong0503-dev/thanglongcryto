import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# ==============================================================================
# 1. UI CONFIGURATION
# ==============================================================================
st.set_page_config(layout="wide", page_title="Crypto Terminal (Live Data)", page_icon="📈", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Rajdhani:wght@600;700&display=swap');

    :root {
        --bg-color: #0e1117;
        --card-bg: #161b22;
        --accent: #2962ff;
        --up: #00e676;
        --down: #ff1744;
        --text: #e6e6e6;
    }

    .stApp { background-color: var(--bg-color); font-family: 'Rajdhani', sans-serif; color: var(--text); }
    
    /* CARDS */
    .metric-card {
        background-color: var(--card-bg);
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-label { font-size: 12px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { font-size: 28px; font-weight: bold; font-family: 'Roboto Mono', monospace; }
    
    .text-up { color: var(--up); }
    .text-down { color: var(--down); }
    
    /* INPUTS */
    div[data-baseweb="input"] { background-color: #0d1117 !important; border: 1px solid #30363d !important; }
    input { color: #58a6ff !important; font-family: 'Roboto Mono' !important; font-weight: bold !important; }
    
    /* TABS */
    button[data-baseweb="tab"] { color: #8b949e; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #58a6ff; background-color: transparent; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CORE ENGINE: YFINANCE (DỮ LIỆU THẬT - KHÔNG BỊ CHẶN)
# ==============================================================================
class RealTimeEngine:
    def __init__(self):
        pass

    def get_real_data(self, symbol, period="1mo", interval="1h"):
        """
        Lấy dữ liệu thật từ Yahoo Finance.
        Yahoo rất trâu bò, không chặn IP vặt vãnh như Binance.
        """
        # Mapping symbol sang chuẩn Yahoo
        yf_symbol = symbol.upper().replace('/', '-').replace('USDT', 'USD')
        if not yf_symbol.endswith('-USD') and '-' not in yf_symbol:
            yf_symbol += '-USD'
            
        try:
            # Tải dữ liệu
            df = yf.download(tickers=yf_symbol, period=period, interval=interval, progress=False)
            
            if df.empty:
                return pd.DataFrame(), f"Không tìm thấy mã {yf_symbol} trên thị trường."
            
            # Xử lý MultiIndex của Yahoo (quan trọng)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Chuẩn hóa tên cột
            df = df.rename(columns={
                'Open': 'open', 'High': 'high', 'Low': 'low', 
                'Close': 'close', 'Volume': 'volume'
            })
            
            return df, "OK"
        except Exception as e:
            return pd.DataFrame(), str(e)

    def calculate_indicators(self, df):
        if df.empty: return df
        
        # 1. Bollinger Bands
        df.ta.bbands(length=20, std=2, append=True)
        # 2. RSI
        df.ta.rsi(length=14, append=True)
        # 3. MACD
        df.ta.macd(append=True)
        # 4. EMA Trend
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)
        
        return df

engine = RealTimeEngine()

# ==============================================================================
# 3. DASHBOARD UI
# ==============================================================================

# HEADER
c1, c2 = st.columns([1, 5])
with c1: st.markdown("## 📈")
with c2: st.markdown("## CRYPTO LIVE TERMINAL (Yahoo Core)")

# CONTROLS
col_in, col_tf = st.columns([2, 1])
with col_in:
    symbol_input = st.text_input("NHẬP MÃ (VD: BTC, ETH, SOL, DOGE)", value="BTC")
with col_tf:
    timeframe = st.selectbox("KHUNG GIỜ", ["1h", "90m", "1d"], index=0)

target = symbol_input.upper()

# --- MAIN LOGIC ---
if target:
    st.write("---")
    
    # 1. FETCH DATA
    with st.spinner(f"📡 Đang kết nối dữ liệu thật cho {target}..."):
        # Chuyển đổi khung giờ cho hợp lệ với Yahoo
        yf_interval = "1h" if timeframe == "1h" else ("90m" if timeframe == "90m" else "1d")
        period = "1mo" if timeframe == "1h" else "1y"
        
        df, status = engine.get_real_data(target, period=period, interval=yf_interval)
    
    if not df.empty:
        # 2. CALCULATE
        df = engine.calculate_indicators(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Lấy giá trị an toàn (tránh lỗi nếu chưa tính được)
        close_price = curr['close']
        prev_price = prev['close']
        change_pct = (close_price - prev_price) / prev_price * 100
        
        # 3. METRICS DISPLAY
        m1, m2, m3, m4 = st.columns(4)
        
        color_cls = "text-up" if change_pct >= 0 else "text-down"
        
        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">GIÁ HIỆN TẠI (USD)</div>
                <div class="metric-value {color_cls}">${close_price:,.2f}</div>
            </div>""", unsafe_allow_html=True)
            
        with m2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">BIẾN ĐỘNG (NẾN TRƯỚC)</div>
                <div class="metric-value {color_cls}">{change_pct:+.2f}%</div>
            </div>""", unsafe_allow_html=True)
            
        # RSI Check
        rsi_val = curr.get('RSI_14', 50)
        rsi_color = "text-up" if rsi_val < 30 else ("text-down" if rsi_val > 70 else "#fff")
        with m3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">RSI SỨC MẠNH</div>
                <div class="metric-value" style="color:{'#00e676' if rsi_val<30 else ('#ff1744' if rsi_val>70 else '#fff')}">{rsi_val:.1f}</div>
            </div>""", unsafe_allow_html=True)
            
        # Volatility
        vol_state = "BÌNH THƯỜNG"
        if 'BBU_20_2.0' in curr:
            bw = (curr['BBU_20_2.0'] - curr['BBL_20_2.0']) / curr['BBM_20_2.0']
            if bw < 0.05: vol_state = "NÉN CHẶT (SẮP BUNG)"
        
        with m4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">TRẠNG THÁI BB</div>
                <div class="metric-value" style="font-size:18px">{vol_state}</div>
            </div>""", unsafe_allow_html=True)

        # 4. CHARTING (Vẽ bằng Python Plotly - Dữ liệu của chúng ta)
        c_chart, c_sig = st.columns([3, 1])
        
        with c_chart:
            st.markdown("### 📊 BIỂU ĐỒ KỸ THUẬT (DỮ LIỆU THẬT)")
            
            fig = go.Figure()
            
            # Nến
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'],
                name='Price', increasing_line_color='#00e676', decreasing_line_color='#ff1744'
            ))
            
            # EMA
            if 'EMA_50' in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='#2962ff', width=2), name='EMA 50'))
            
            # BB
            if 'BBU_20_2.0' in df.columns:
                fig.add_trace(go.Scatter(x=df.index, y=df['BBU_20_2.0'], line=dict(color='rgba(255,255,255,0.3)', width=1), name='UBB'))
                fig.add_trace(go.Scatter(x=df.index, y=df['BBL_20_2.0'], line=dict(color='rgba(255,255,255,0.3)', width=1), fill='tonexty', name='LBB'))

            fig.update_layout(
                height=600, template="plotly_dark",
                paper_bgcolor="#161b22", plot_bgcolor="#161b22",
                xaxis_rangeslider_visible=False,
                margin=dict(l=10, r=10, t=10, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)

        # 5. SIGNAL BOX
        with c_sig:
            st.markdown("### 🚦 TÍN HIỆU")
            
            # Logic đơn giản
            signal = "QUAN SÁT"
            color = "#8b949e"
            
            if 'BBL_20_2.0' in curr:
                if close_price < curr['BBL_20_2.0'] and rsi_val < 35:
                    signal = "MUA (BẮT ĐÁY)"
                    color = "#00e676"
                elif close_price > curr['BBU_20_2.0'] and rsi_val > 65:
                    signal = "BÁN (CHỐT LỜI)"
                    color = "#ff1744"
                elif 'EMA_50' in curr and 'EMA_200' in curr:
                    if curr['EMA_50'] > curr['EMA_200'] and close_price > curr['EMA_50']:
                        signal = "XU HƯỚNG TĂNG"
                        color = "#2962ff"
            
            st.markdown(f"""
            <div class="metric-card" style="text-align:center; border-color: {color};">
                <div style="font-size:14px; color:#888;">KHUYẾN NGHỊ</div>
                <div style="font-size:24px; font-weight:bold; color:{color}; margin-top:10px;">{signal}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("💡 Mẹo: Nhập 'DOGE', 'SHIB', 'PEPE' đều được. Hệ thống tự tìm mã USD tương ứng.")

    else:
        st.error(f"❌ Lỗi: {status}")
        st.caption("Hãy kiểm tra lại tên mã coin. Ví dụ nhập: BTC, ETH, SOL...")

st.markdown("---")
st.caption("Data Source: Yahoo Finance (Reliable & Free) | Powered by Emo")
