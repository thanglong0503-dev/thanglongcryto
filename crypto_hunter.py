import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import time
import streamlit.components.v1 as components 

# ==========================================
# 1. CẤU HÌNH GIAO DIỆN (ĐÃ FIX TOÀN DIỆN UI)
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="Crypto Terminal Pro", 
    page_icon="📊", 
    initial_sidebar_state="expanded"
)

# CSS: BINANCE DARK THEME + FIX LỖI DROPDOWN TRẮNG
st.markdown("""
<style>
    /* Import Font Roboto chuẩn sàn */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

    /* Nền tảng chính */
    .stApp {
        background-color: #161a1e !important; 
        font-family: 'Roboto', sans-serif;
        color: #eaecef;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1e2329 !important; 
        border-right: 1px solid #2b3139;
    }
    
    /* Tiêu đề & Chữ */
    h1, h2, h3, h4, h5, h6, span, div, label, .stMarkdown {
        color: #eaecef !important;
    }
    .stCaption, small { color: #848e9c !important; }

    /* --- 🔥 FIX TRIỆT ĐỂ MENU DROPDOWN BỊ TRẮNG --- */
    /* 1. Hộp chứa danh sách xổ xuống */
    div[data-baseweb="popover"], div[data-baseweb="menu"] {
        background-color: #1e2329 !important;
        border: 1px solid #474d57 !important;
    }
    
    /* 2. Các tùy chọn bên trong danh sách */
    li[data-baseweb="option"] {
        color: #eaecef !important;
        background-color: transparent !important;
    }
    
    /* 3. Hiệu ứng Hover & Selected chuẩn Binance */
    li[data-baseweb="option"]:hover, li[aria-selected="true"] {
        background-color: #2b3139 !important;
        color: #fcd535 !important; /* Chữ vàng khi chọn */
    }

    /* --- INPUT & SELECTBOX STYLE --- */
    /* Ô nhập liệu và ô chọn khi chưa bấm vào */
    div[data-baseweb="select"] > div, .stTextInput > div > div {
        background-color: #2b3139 !important;
        color: #eaecef !important;
        border: 1px solid #474d57 !important;
        border-radius: 4px;
    }
    /* Màu chữ khi gõ vào ô Input */
    input[type="text"] {
        color: #eaecef !important;
    }
    
    /* Chỉnh màu icon mũi tên */
    svg[data-baseweb="icon"] {
        fill: #848e9c !important;
    }

    /* --- NÚT BẤM (BUTTON) --- */
    button[kind="primary"] {
        background-color: #fcd535 !important;
        border: none !important;
        border-radius: 4px !important;
        transition: all 0.2s;
    }
    /* Ép chữ trong nút thành màu ĐEN ĐẬM */
    button[kind="primary"] p {
        color: #1e2329 !important;
        font-weight: 700 !important;
    }
    button[kind="primary"]:hover {
        background-color: #e5c230 !important;
        box-shadow: 0 0 10px rgba(252, 213, 53, 0.3);
    }
    
    /* Custom Metric Card */
    .binance-card {
        background-color: #1e2329;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #2b3139;
        text-align: center;
    }
    .metric-label { color: #848e9c !important; font-size: 13px; margin-bottom: 5px; }
    .metric-value { font-size: 22px; font-weight: 600; color: #eaecef !important; }
    
    /* Màu sắc chuẩn Binance */
    .up-green { color: #0ecb81 !important; } 
    .down-red { color: #f6465d !important; }  
    
    /* Bảng dữ liệu */
    div[data-testid="stDataFrame"] {
        border: 1px solid #2b3139;
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BACKEND XỬ LÝ DỮ LIỆU
# ==========================================
@st.cache_resource
def init_exchange():
    """Kết nối Binance US/Kraken"""
    try:
        # Thử kết nối public để lấy nhiều coin hơn
        return ccxt.binance({'enableRateLimit': True})
    except:
        # Fallback nếu bị chặn
        return ccxt.kraken({'enableRateLimit': True})

exchange = init_exchange()

@st.cache_data(ttl=300)
def get_market_symbols(limit=60):
    try:
        tickers = exchange.fetch_tickers()
        symbols = [s for s in tickers if s.endswith('/USDT')]
        if not symbols: 
            symbols = [s for s in tickers if '/USD' in s]
        sorted_symbols = sorted(symbols, key=lambda x: tickers[x]['quoteVolume'] if 'quoteVolume' in tickers[x] else 0, reverse=True)
        return sorted_symbols[:limit]
    except:
        return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']

def fetch_candle_data_backend(symbol, timeframe, limit=50):
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
    # Format symbol: BTC/USDT -> BINANCE:BTCUSDT
    clean_symbol = symbol.replace('/', '')
    tv_symbol = f"BINANCE:{clean_symbol}"
    
    html_code = f"""
    <div class="tradingview-widget-container" style="height:600px;width:100%">
      <div id="tradingview_b8d71" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
      "autosize": true,
      "symbol": "{tv_symbol}",
      "interval": "60", 
      "timezone": "Asia/Ho_Chi_Minh",
      "theme": "dark", 
      "style": "1", 
      "locale": "vi_VN", 
      "enable_publishing": false,
      "backgroundColor": "#161a1e", 
      "gridColor": "rgba(43, 49, 57, 0.6)",
      "hide_top_toolbar": false,
      "hide_legend": false,
      "save_image": true,
      "toolbar_bg": "#1e2329",
      "studies": [
        "RSI@tv-basicstudies",
        "MASimple@tv-basicstudies" 
      ],
      "container_id": "tradingview_b8d71"
      }}
      );
      </script>
    </div>
    """
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
    # Tải danh sách coin trước
    coins = get_market_symbols(60)

    # --- KHU VỰC TÌM KIẾM HYBRID (MỚI) ---
    col_search, col_select = st.columns([2, 3])
    
    with col_search:
        # Ô nhập tay
        st.markdown("<small>🔍 TÌM KIẾM NHANH (VD: DOGE, SHIB)</small>", unsafe_allow_html=True)
        manual_search = st.text_input("Search label", placeholder="Nhập mã...", label_visibility="collapsed")
        
    with col_select:
        # Ô chọn danh sách Top
        st.markdown("<small>🏆 DANH SÁCH TOP VOL</small>", unsafe_allow_html=True)
        selected_from_list = st.selectbox("Select label", coins, index=0, label_visibility="collapsed")

    # --- LOGIC XỬ LÝ ƯU TIÊN ---
    if manual_search:
        # Nếu người dùng nhập tay, ưu tiên cái nhập tay
        raw_input = manual_search.upper().strip()
        # Tự động thêm đuôi /USDT nếu chưa có
        if "/USDT" not in raw_input:
             symbol = f"{raw_input}/USDT"
        else:
             symbol = raw_input
        st.caption(f"👉 Đang xem mã nhập tay: **{symbol}**")
    else:
        # Nếu không nhập, dùng cái chọn trong danh sách
        symbol = selected_from_list
    # ------------------------------------
    
    with st.spinner(f"Đang tải dữ liệu cho {symbol}..."):
        df_backend = fetch_candle_data_backend(symbol, '1h', 100)
    
    if not df_backend.empty:
        df_backend = analyze_data_backend(df_backend)
        curr = df_backend.iloc[-1]
        prev = df_backend.iloc[-2]
        change_pct = (curr['close'] - prev['close']) / prev['close'] * 100
        
        # 3. Metrics
        m1, m2, m3, m4 = st.columns(4)
        
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
            
        vol_24h_est = df_backend['volume'].sum() * curr['close']
        with m4:
             st.markdown(f"""
            <div class="binance-card">
                <div class="metric-label">VOLUME (Ước tính)</div>
                <div class="metric-value">{vol_24h_est:,.0f}$</div>
            </div>""", unsafe_allow_html=True)

        # 4. BIỂU ĐỒ TRADINGVIEW
        st.write("") 
        st.markdown("### BIỂU ĐỒ KỸ THUẬT")
        render_tradingview_widget(symbol)

    else:
        st.error(f"⚠️ Không tìm thấy dữ liệu cho mã **{symbol}**. Vui lòng kiểm tra lại tên mã (có thể mã này không có cặp USDT trên Binance).")

elif app_mode == "📡 ALPHA SCANNER":
    # (Phần code Scanner giữ nguyên như cũ)
    st.markdown("### 📡 MÁY QUÉT TÍN HIỆU (RSI EXTREME)")
    st.caption("Quét Top 30 đồng coin thanh khoản cao trên khung 4H")
    
    if st.button("BẮT ĐẦU QUÉT", type="primary"):
        scan_coins = get_market_symbols(30)
        results = []
        
        scan_bar = st.progress(0)
        status_txt = st.empty()
        
        scan_tf = '4h' 
        
        for i, sym in enumerate(scan_coins):
            scan_bar.progress((i+1)/len(scan_coins))
            status_txt.text(f"Đang phân tích: {sym}...")
            
            df = fetch_candle_data_backend(sym, scan_tf, 30) 
            if not df.empty:
                df = analyze_data_backend(df)
                curr = df.iloc[-1]
                rsi = curr['RSI_14']
                
                sig = "CHỜ"
                if rsi < 25: sig = "MUA MẠNH"
                elif rsi < 30: sig = "MUA"
                elif rsi > 75: sig = "BÁN MẠNH"
                elif rsi > 70: sig = "BÁN"
                
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
            
            def style_binance_scan(val):
                color = '#eaecef'
                if 'MUA' in str(val): color = '#0ecb81' 
                elif 'BÁN' in str(val): color = '#f6465d' 
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
