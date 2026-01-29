import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import plotly.graph_objects as go
import time

# ==========================================
# 1. CẤU HÌNH GIAO DIỆN (HIGH CONTRAST UI)
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="Terminal Pro", 
    page_icon="📟",
    initial_sidebar_state="expanded"
)

# CSS: Ép buộc giao diện Dark Mode & Tăng tương phản
st.markdown("""
<style>
    /* 1. Ép nền đen tuyệt đối */
    .stApp {
        background-color: #000000 !important;
        font-family: 'Consolas', 'Courier New', monospace;
    }
    
    /* 2. Chỉnh màu chữ toàn bộ hệ thống */
    h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #e0e0e0 !important;
    }
    
    /* 3. Sidebar tương phản cao */
    section[data-testid="stSidebar"] {
        background-color: #111111 !important;
        border-right: 2px solid #333 !important;
    }
    
    /* 4. Các Box thông số (Metrics) */
    div[data-testid="stMetric"] {
        background-color: #1a1a1a !important;
        border: 1px solid #444 !important;
        padding: 10px;
        border-radius: 0px; /* Vuông vức kiểu Terminal */
    }
    div[data-testid="stMetricValue"] {
        font-weight: bold !important;
    }
    
    /* 5. Bảng dữ liệu (Dataframe) */
    div[data-testid="stDataFrame"] {
        background-color: #111 !important;
        border: 1px solid #333 !important;
    }
    
    /* 6. Input & Selectbox */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #222 !important;
        color: white !important;
        border-radius: 0px;
        border: 1px solid #555;
    }
    
    /* 7. Nút bấm (Button) */
    button[kind="primary"] {
        background-color: #00ff41 !important; /* Hacker Green */
        color: black !important;
        font-weight: bold !important;
        border-radius: 0px !important;
        border: none !important;
        text-transform: uppercase;
    }
    button[kind="primary"]:hover {
        box-shadow: 0 0 10px #00ff41;
    }
    
    /* Màu tín hiệu */
    .color-up { color: #00ff41 !important; }
    .color-down { color: #ff0055 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. XỬ LÝ KẾT NỐI (FIX GEO-BLOCKING)
# ==========================================
@st.cache_resource
def init_exchange():
    """
    Sử dụng Binance US để tránh bị chặn IP khi chạy trên Cloud Server (Mỹ).
    Nếu Binance US lỗi, tự động chuyển sang Kraken.
    """
    try:
        # Ưu tiên 1: Binance US (Hỗ trợ tốt IP Mỹ)
        return ccxt.binanceus({'enableRateLimit': True})
    except:
        # Ưu tiên 2: Kraken (Rất ổn định tại Mỹ)
        return ccxt.kraken({'enableRateLimit': True})

exchange = init_exchange()

@st.cache_data(ttl=300)
def get_market_symbols(limit=50):
    """Lấy danh sách cặp tiền USDT"""
    try:
        tickers = exchange.fetch_tickers()
        # Lọc cặp tiền /USDT (Binance US) hoặc /USD (Kraken)
        symbols = [s for s in tickers if '/USDT' in s or '/USD' in s]
        
        # Sắp xếp theo Volume để lấy coin thanh khoản cao
        sorted_symbols = sorted(symbols, key=lambda x: tickers[x]['quoteVolume'] if 'quoteVolume' in tickers[x] else 0, reverse=True)
        return sorted_symbols[:limit]
    except Exception as e:
        # Fallback danh sách cứng nếu API lỗi
        return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'DOGE/USDT', 'ADA/USDT']

def fetch_candle_data(symbol, timeframe, limit=100):
    """Lấy dữ liệu nến an toàn"""
    try:
        # Thử lại 3 lần nếu mạng lag
        for _ in range(3):
            try:
                bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
                if bars: break
            except:
                time.sleep(0.5)
        else:
            return pd.DataFrame()

        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except:
        return pd.DataFrame()

# ==========================================
# 3. LOGIC PHÂN TÍCH (CORE ENGINE)
# ==========================================
def analyze_data(df):
    if df.empty: return df
    # Tính chỉ báo
    df.ta.rsi(length=14, append=True)
    df.ta.ema(length=50, append=True)
    df.ta.bbands(length=20, std=2, append=True)
    return df

# ==========================================
# 4. GIAO DIỆN (TERMINAL STYLE)
# ==========================================
# --- SIDEBAR ---
st.sidebar.markdown("### 📡 SYSTEM CONTROL")
app_mode = st.sidebar.radio("MODE", ["MARKET DASHBOARD", "ALPHA SCANNER"])
st.sidebar.markdown("---")
tf = st.sidebar.selectbox("TIMEFRAME", ['15m', '1h', '4h', '1d'], index=2)

# --- HEADER ---
st.markdown(f"## 📟 CRYPTO TERMINAL <span style='font-size:14px; color:#666'>:: {exchange.name.upper()} LINKED</span>", unsafe_allow_html=True)

if app_mode == "MARKET DASHBOARD":
    # 1. Chọn Coin
    coins = get_market_symbols(50)
    symbol = st.selectbox("SELECT ASSET", coins)
    
    # 2. Lấy dữ liệu
    df = fetch_candle_data(symbol, tf, 200)
    
    if not df.empty:
        df = analyze_data(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        change = (curr['close'] - prev['close']) / prev['close'] * 100
        
        # 3. Hiển thị thông số (High Contrast)
        c1, c2, c3, c4 = st.columns(4)
        
        # Helper tô màu
        color_price = "#00ff41" if change >= 0 else "#ff0055"
        
        c1.markdown(f"""
        <div style="border:1px solid #444; padding:10px; background:#111;">
            <div style="color:#888; font-size:12px;">LAST PRICE</div>
            <div style="font-size:24px; color:{color_price}; font-weight:bold;">{curr['close']:,.4f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        c2.markdown(f"""
        <div style="border:1px solid #444; padding:10px; background:#111;">
            <div style="color:#888; font-size:12px;">24H CHANGE</div>
            <div style="font-size:24px; color:{color_price}; font-weight:bold;">{change:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
        
        rsi_val = curr['RSI_14']
        rsi_color = "#00ff41" if rsi_val < 30 else ("#ff0055" if rsi_val > 70 else "#e0e0e0")
        c3.markdown(f"""
        <div style="border:1px solid #444; padding:10px; background:#111;">
            <div style="color:#888; font-size:12px;">RSI (14)</div>
            <div style="font-size:24px; color:{rsi_color}; font-weight:bold;">{rsi_val:.1f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        vol_state = "HIGH" if curr['volume'] > df['volume'].mean() else "LOW"
        c4.markdown(f"""
        <div style="border:1px solid #444; padding:10px; background:#111;">
            <div style="color:#888; font-size:12px;">VOLUME STATE</div>
            <div style="font-size:24px; color:#e0e0e0; font-weight:bold;">{vol_state}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 4. Biểu đồ Chuyên nghiệp
        st.write("") # Spacer
        fig = go.Figure()
        
        # Nến
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['open'], high=df['high'],
            low=df['low'], close=df['close'],
            name='Price',
            increasing_line_color='#00ff41', # Neon Green
            decreasing_line_color='#ff0055'  # Neon Red
        ))
        
        # EMA
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='#00d9ff', width=1), name='EMA 50'))
        
        # Layout tối giản
        fig.update_layout(
            height=600,
            template="plotly_dark",
            paper_bgcolor="#000000",
            plot_bgcolor="#000000",
            margin=dict(l=0, r=0, t=20, b=0),
            xaxis=dict(showgrid=False, linecolor='#333'),
            yaxis=dict(showgrid=True, gridcolor='#222', side='right'), # Giá bên phải cho chuyên nghiệp
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.error("⚠️ Connection Failed. Retrying...")

elif app_mode == "ALPHA SCANNER":
    st.markdown("### 📡 SCANNING PROTOCOL INIT...")
    if st.button("EXECUTE SCAN", type="primary"):
        coins = get_market_symbols(30)
        results = []
        
        # Progress Bar phong cách Terminal
        my_bar = st.progress(0)
        status = st.empty()
        
        for i, sym in enumerate(coins):
            my_bar.progress((i+1)/len(coins))
            status.code(f"SCANNING >> {sym} ...")
            
            df = fetch_candle_data(sym, tf, 50)
            if not df.empty:
                df = analyze_data(df)
                curr = df.iloc[-1]
                rsi = curr['RSI_14']
                
                sig = "WAIT"
                if rsi < 30: sig = "OVERSOLD (BUY)"
                elif rsi > 70: sig = "OVERBOUGHT (SELL)"
                
                if sig != "WAIT": # Chỉ lấy tín hiệu
                    results.append({
                        "SYMBOL": sym,
                        "PRICE": curr['close'],
                        "RSI": rsi,
                        "SIGNAL": sig
                    })
        
        my_bar.empty()
        status.empty()
        
        if results:
            st.success(f"FOUND {len(results)} SIGNALS")
            res_df = pd.DataFrame(results)
            
            # Tô màu bảng kết quả
            def style_scan(val):
                color = 'white'
                if 'BUY' in str(val): color = '#00ff41'
                elif 'SELL' in str(val): color = '#ff0055'
                return f'color: {color}; font-weight: bold'

            st.dataframe(
                res_df.style.map(style_scan, subset=['SIGNAL']),
                use_container_width=True,
                height=500
            )
        else:
            st.info("NO EXTREME SIGNALS FOUND IN TOP 30 ASSETS.")

st.markdown("---")
st.caption("SYSTEM STATUS: ONLINE | SERVER: US-EAST | DATA: BINANCE.US / KRAKEN")
