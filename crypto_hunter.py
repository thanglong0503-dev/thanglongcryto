import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import time
import streamlit.components.v1 as components # Thư viện để nhúng TradingView

# ==========================================
# 1. CẤU HÌNH GIAO DIỆN CHUẨN BINANCE
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="Crypto Terminal Pro", 
    page_icon="📊", # Icon chuyên nghiệp hơn
    initial_sidebar_state="expanded"
)

# CSS: BINANCE DARK THEME
st.markdown("""
<style>
    /* Import Font Roboto chuẩn sàn */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

    /* Nền tảng chính */
    .stApp {
        background-color: #161a1e !important; /* Màu nền Binance */
        font-family: 'Roboto', sans-serif;
        color: #eaecef;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1e2329 !important; /* Màu sidebar Binance */
        border-right: 1px solid #2b3139;
    }
    
    /* Tiêu đề & Chữ */
    h1, h2, h3, label, span, div {
        color: #eaecef !important;
    }
    .stCaption { color: #848e9c !important; }

    /* Input & Selectbox */
    div[data-baseweb="select"] > div, .stTextInput > div > div {
        background-color: #2b3139 !important;
        color: #eaecef !important;
        border: 1px solid #474d57 !important;
        border-radius: 4px;
    }

    /* Nút bấm chuẩn Binance (Vàng) */
    button[kind="primary"] {
        background-color: #fcd535 !important;
        color: #1e2329 !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 4px !important;
        transition: all 0.2s;
    }
    button[kind="primary"]:hover {
        background-color: #e5c230 !important;
        box-shadow: 0 0 10px rgba(252, 213, 53, 0.3);
    }
    
    /* Custom Metric Card (Thẻ thông số trên đầu) */
    .binance-card {
        background-color: #1e2329;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #2b3139;
        text-align: center;
    }
    .metric-label { color: #848e9c; font-size: 13px; margin-bottom: 5px; }
    .metric-value { font-size: 22px; font-weight: 600; }
    
    /* Màu sắc chuẩn Binance */
    .up-green { color: #0ecb81 !important; } /* Xanh tăng */
    .down-red { color: #f6465d !important; }  /* Đỏ giảm */
    
    /* Bảng dữ liệu */
    div[data-testid="stDataFrame"] {
        border: 1px solid #2b3139;
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BACKEND XỬ LÝ DỮ LIỆU (Vẫn giữ để chạy Scanner & Metrics)
# ==========================================
@st.cache_resource
def init_exchange():
    """Kết nối Binance US/Kraken để tránh bị chặn IP"""
    try:
        return ccxt.binanceus({'enableRateLimit': True})
    except:
        return ccxt.kraken({'enableRateLimit': True})

exchange = init_exchange()

@st.cache_data(ttl=300)
def get_market_symbols(limit=50):
    """Lấy danh sách cặp tiền USDT thanh khoản cao"""
    try:
        tickers = exchange.fetch_tickers()
        # Ưu tiên cặp USDT trên Binance
        symbols = [s for s in tickers if '/USDT' in s]
        if not symbols: # Fallback nếu dùng Kraken (ví dụ)
            symbols = [s for s in tickers if '/USD' in s]
            
        sorted_symbols = sorted(symbols, key=lambda x: tickers[x]['quoteVolume'] if 'quoteVolume' in tickers[x] else 0, reverse=True)
        return sorted_symbols[:limit]
    except:
        return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']

def fetch_candle_data_backend(symbol, timeframe, limit=50):
    """Lấy dữ liệu nhẹ cho Backend tính toán (không dùng để vẽ chart nữa)"""
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except:
        return pd.DataFrame()

def analyze_data_backend(df):
    if df.empty: return df
    df.ta.rsi(length=14, append=True)
    return df

# ==========================================
# 3. HÀM NHÚNG TRADINGVIEW WIDGET
# ==========================================
def render_tradingview_widget(symbol):
    # Chuyển đổi format symbol: BTC/USDT -> BINANCE:BTCUSDT
    tv_symbol = f"BINANCE:{symbol.replace('/', '')}"
    
    # Mã HTML nhúng Widget Advanced Real-Time Chart
    html_code = f"""
    <div class="tradingview-widget-container" style="height:600px;width:100%">
      <div id="tradingview_b8d71" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
      "autosize": true,
      "symbol": "{tv_symbol}",
      "interval": "60", /* Mặc định khung 1H */
      "timezone": "Asia/Ho_Chi_Minh",
      "theme": "dark", /* Giao diện tối */
      "style": "1", /* Kiểu nến Nhật */
      "locale": "vi_VN", /* Tiếng Việt */
      "enable_publishing": false,
      "backgroundColor": "#161a1e", /* Màu nền trùng khớp App */
      "gridColor": "rgba(43, 49, 57, 0.6)",
      "hide_top_toolbar": false,
      "hide_legend": false,
      "save_image": true,
      "toolbar_bg": "#1e2329",
      "studies": [
        "RSI@tv-basicstudies", /* Thêm sẵn RSI */
        "MASimple@tv-basicstudies" /* Thêm sẵn MA */
      ],
      "container_id": "tradingview_b8d71"
      }}
      );
      </script>
    </div>
    """
    # Render widget bằng components.html
    components.html(html_code, height=610)

# ==========================================
# 4. GIAO DIỆN NGƯỜI DÙNG (MAIN UI)
# ==========================================
# --- SIDEBAR ---
st.sidebar.markdown("### ⚙️ CONTROL PANEL")
app_mode = st.sidebar.radio("CHẾ ĐỘ:", ["📈 MARKET DASHBOARD", "📡 ALPHA SCANNER"])
st.sidebar.markdown("---")
st.sidebar.caption(f"Connected: {exchange.name.upper()}")

# --- MAIN HEADER ---
st.markdown("## 📊 CRYPTO TERMINAL PRO")

if app_mode == "📈 MARKET DASHBOARD":
    col_sel, col_blank = st.columns([2, 3])
    with col_sel:
        # 1. Chọn Coin
        coins = get_market_symbols(60)
        symbol = st.selectbox("CHỌN CẶP GIAO DỊCH", coins, index=0)
    
    # 2. Lấy dữ liệu Backend để hiển thị số liệu (Metrics)
    # Chúng ta vẫn cần backend để tính % thay đổi và RSI chính xác
    with st.spinner("Đang tải dữ liệu..."):
        df_backend = fetch_candle_data_backend(symbol, '1h', 100) # Mặc định lấy khung 1H cho metrics
    
    if not df_backend.empty:
        df_backend = analyze_data_backend(df_backend)
        curr = df_backend.iloc[-1]
        prev = df_backend.iloc[-2]
        change_pct = (curr['close'] - prev['close']) / prev['close'] * 100
        
        # 3. Hiển thị Metrics (Style Binance Cards)
        m1, m2, m3, m4 = st.columns(4)
        
        # Helper xác định màu
        color_class = "up-green" if change_pct >= 0 else "down-red"
        sign = "+" if change_pct >= 0 else ""
        
        with m1:
            st.markdown(f"""
            <div class="binance-card">
                <div class="metric-label">GIÁ GẦN NHẤT</div>
                <div class="metric-value {color_class}">{curr['close']:,.4f}</div>
            </div>""", unsafe_allow_html=True)
            
        with m2:
            st.markdown(f"""
            <div class="binance-card">
                <div class="metric-label">THAY ĐỔI 1H</div>
                <div class="metric-value {color_class}">{sign}{change_pct:.2f}%</div>
            </div>""", unsafe_allow_html=True)

        rsi_val = curr['RSI_14']
        rsi_color = "up-green" if rsi_val < 30 else ("down-red" if rsi_val > 70 else "#eaecef")
        with m3:
            st.markdown(f"""
            <div class="binance-card">
                <div class="metric-label">RSI (14)</div>
                <div class="metric-value" style="color: {rsi_color}">{rsi_val:.1f}</div>
            </div>""", unsafe_allow_html=True)
            
        vol_24h_est = df_backend['volume'].sum() * curr['close'] # Ước tính Vol USDT
        with m4:
             st.markdown(f"""
            <div class="binance-card">
                <div class="metric-label">VOLUME (Ước tính)</div>
                <div class="metric-value">{vol_24h_est:,.0f}$</div>
            </div>""", unsafe_allow_html=True)

        # 4. NHÚNG TRADINGVIEW WIDGET
        st.write("") # Khoảng cách
        st.markdown("### BIỂU ĐỒ KỸ THUẬT (TradingView)")
        # Gọi hàm render widget
        render_tradingview_widget(symbol)
        st.caption("💡 Mẹo: Sử dụng thanh công cụ bên trái và phía trên biểu đồ để vẽ và thêm chỉ báo.")

    else:
        st.error("⚠️ Không thể kết nối đến Backend dữ liệu. Vui lòng kiểm tra lại kết nối mạng hoặc requirements.txt")

elif app_mode == "📡 ALPHA SCANNER":
    st.markdown("### 📡 MÁY QUÉT TÍN HIỆU (RSI EXTREME)")
    st.caption("Quét Top 30 đồng coin thanh khoản cao trên khung 4H")
    
    if st.button("BẮT ĐẦU QUÉT", type="primary"):
        scan_coins = get_market_symbols(30)
        results = []
        
        scan_bar = st.progress(0)
        status_txt = st.empty()
        
        # Quét trên khung 4H cho tín hiệu uy tín hơn
        scan_tf = '4h' 
        
        for i, sym in enumerate(scan_coins):
            scan_bar.progress((i+1)/len(scan_coins))
            status_txt.text(f"Đang phân tích: {sym}...")
            
            # Lấy ít dữ liệu thôi cho nhanh
            df = fetch_candle_data_backend(sym, scan_tf, 30) 
            if not df.empty:
                df = analyze_data_backend(df)
                curr = df.iloc[-1]
                rsi = curr['RSI_14']
                
                sig = "CHỜ"
                # Tăng độ khó tín hiệu
                if rsi < 25: sig = "MUA MẠNH (Quá bán sâu)"
                elif rsi < 30: sig = "MUA (Quá bán)"
                elif rsi > 75: sig = "BÁN MẠNH (Quá mua đỉnh)"
                elif rsi > 70: sig = "BÁN (Quá mua)"
                
                if sig != "CHỜ":
                    results.append({
                        "CẶP GIAO DỊCH": sym,
                        "GIÁ": curr['close'],
                        "RSI (4H)": rsi,
                        "TÍN HIỆU": sig
                    })
        
        scan_bar.empty()
        status_txt.empty()
        
        if results:
            st.success(f"✅ Tìm thấy {len(results)} cơ hội tiềm năng!")
            res_df = pd.DataFrame(results)
            
            # Tô màu bảng kết quả chuẩn Binance
            def style_binance_scan(val):
                color = '#eaecef'
                if 'MUA' in str(val): color = '#0ecb81' # Xanh Binance
                elif 'BÁN' in str(val): color = '#f6465d' # Đỏ Binance
                return f'color: {color}; font-weight: 600'

            st.dataframe(
                res_df.style.map(style_binance_scan, subset=['TÍN HIỆU'])
                .format({"GIÁ": "{:.4f}", "RSI (4H)": "{:.1f}"}),
                use_container_width=True,
                height=500
            )
        else:
            st.info("Hiện tại thị trường đang Sideway, chưa có tín hiệu RSI quá mua/quá bán mạnh trong Top 30.")

st.markdown("---")
st.caption("Crypto Terminal Pro | Powered by Binance Data & TradingView Charts")
