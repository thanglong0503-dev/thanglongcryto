import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import time
import streamlit.components.v1 as components 

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG & GIAO DIỆN CƯỜNG LỰC
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="Crypto Terminal Pro", 
    page_icon="📊", 
    initial_sidebar_state="expanded"
)

# CSS: FIX LỖI HIỂN THỊ TRÊN NỀN SÁNG
st.markdown("""
<style>
    /* Import Font */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

    /* --- 1. ÉP NỀN TỐI TOÀN APP --- */
    .stApp {
        background-color: #161a1e !important; 
        font-family: 'Roboto', sans-serif;
        color: #eaecef !important;
    }
    
    /* --- 2. XỬ LÝ MENU DROPDOWN (BỊ TRẮNG) --- */
    /* Ép nền của hộp menu thành màu đen xám */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-baseweb="menu"] {
        background-color: #1e2329 !important;
        color: #eaecef !important;
    }
    
    /* Ép màu chữ của các tùy chọn thành màu trắng */
    li[data-baseweb="option"], div[data-baseweb="option"] {
        color: #eaecef !important;
        background-color: #1e2329 !important;
    }
    
    /* Hiệu ứng khi rê chuột vào tùy chọn */
    li[data-baseweb="option"]:hover, li[aria-selected="true"] {
        background-color: #2b3139 !important;
        color: #fcd535 !important; /* Chữ vàng */
        font-weight: bold !important;
    }
    
    /* Xử lý cái ô hiển thị giá trị đã chọn */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background-color: #2b3139 !important;
        color: #eaecef !important;
        border: 1px solid #474d57 !important;
    }
    
    /* Màu chữ trong ô Input */
    input.st-bd {
        color: #eaecef !important;
    }
    
    /* --- 3. CÁC THÀNH PHẦN KHÁC --- */
    section[data-testid="stSidebar"] {
        background-color: #1e2329 !important; 
        border-right: 1px solid #2b3139;
    }
    
    h1, h2, h3, h4, span, p, label {
        color: #eaecef !important;
    }
    
    .binance-card {
        background-color: #1e2329;
        border-radius: 4px;
        padding: 15px;
        border: 1px solid #2b3139;
        text-align: center;
    }
    
    button[kind="primary"] {
        background-color: #fcd535 !important;
        color: #1e2329 !important;
        border: none !important;
        font-weight: bold !important;
    }
    
    /* Màu tăng giảm */
    .up-green { color: #0ecb81 !important; } 
    .down-red { color: #f6465d !important; }  
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ENGINE KẾT NỐI (QUAY VỀ BINANCE US ĐỂ ỔN ĐỊNH)
# ==========================================
@st.cache_resource
def init_exchange():
    """
    Sử dụng Binance US vì Server Streamlit đặt tại Mỹ.
    Tuyệt đối không dùng ccxt.binance() (Bản quốc tế) vì sẽ bị chặn IP.
    """
    try:
        return ccxt.binanceus({'enableRateLimit': True})
    except:
        return ccxt.kraken({'enableRateLimit': True})

exchange = init_exchange()

@st.cache_data(ttl=300)
def get_market_symbols(limit=60):
    """Lấy danh sách coin hỗ trợ tại Mỹ"""
    try:
        tickers = exchange.fetch_tickers()
        # Binance US dùng đuôi /USD hoặc /USDT
        symbols = [s for s in tickers if '/USDT' in s or '/USD' in s]
        
        # Sắp xếp theo thanh khoản
        sorted_symbols = sorted(symbols, key=lambda x: tickers[x]['quoteVolume'] if 'quoteVolume' in tickers[x] else 0, reverse=True)
        
        # Nếu danh sách rỗng (lỗi API), trả về danh sách cứng để App không chết
        if not symbols:
            return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'DOGE/USDT', 'ADA/USDT', 'BNB/USDT']
            
        return sorted_symbols[:limit]
    except:
        # Fallback an toàn tuyệt đối
        return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'DOGE/USDT']

def fetch_candle_data_backend(symbol, timeframe, limit=50):
    try:
        # Retry 3 lần nếu mạng lag
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

def analyze_data_backend(df):
    if df.empty: return df
    df.ta.rsi(length=14, append=True)
    return df

# ==========================================
# 3. GIAO DIỆN CHÍNH
# ==========================================
def render_tradingview_widget(symbol):
    # Format mã cho TradingView
    # Binance US dùng mã giống Binance QT trên TradingView
    clean_symbol = symbol.replace('/', '')
    # Mẹo: Luôn trỏ về BINANCE nguồn để có chart đẹp, dù backend lấy data từ Binance US
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
      "studies": ["RSI@tv-basicstudies"],
      "container_id": "tradingview_b8d71"
      }}
      );
      </script>
    </div>
    """
    components.html(html_code, height=610)

# --- SIDEBAR ---
st.sidebar.markdown("### ⚙️ CONTROL PANEL")
app_mode = st.sidebar.radio("CHẾ ĐỘ:", ["📈 MARKET DASHBOARD", "📡 ALPHA SCANNER"])
st.sidebar.markdown("---")
st.sidebar.caption(f"Server: {exchange.name} (US Safe)")

# --- HEADER ---
st.markdown("## 📊 CRYPTO TERMINAL PRO")

if app_mode == "📈 MARKET DASHBOARD":
    # Tải danh sách coin an toàn
    coins = get_market_symbols(60)

    # --- INPUT HYBRID ---
    col_search, col_select = st.columns([1, 2])
    with col_search:
        st.markdown("<small>🔍 NHẬP MÃ (VD: DOGE)</small>", unsafe_allow_html=True)
        manual_search = st.text_input("Search label", placeholder="...", label_visibility="collapsed")
        
    with col_select:
        st.markdown("<small>🏆 DANH SÁCH SẴN CÓ</small>", unsafe_allow_html=True)
        # Nếu danh sách rỗng (lỗi mạng), dùng list dự phòng để không bị crash
        safe_coins = coins if coins else ['BTC/USDT']
        selected_from_list = st.selectbox("Select label", safe_coins, index=0, label_visibility="collapsed")

    # --- LOGIC CHỌN MÃ ---
    if manual_search:
        raw_input = manual_search.upper().strip()
        symbol = f"{raw_input}/USDT" if "/USDT" not in raw_input else raw_input
        st.info(f"Đang tìm mã nhập tay: {symbol}")
    else:
        symbol = selected_from_list
    
    # Lấy dữ liệu
    with st.spinner(f"Kết nối dữ liệu {symbol}..."):
        df_backend = fetch_candle_data_backend(symbol, '1h', 50)
    
    if not df_backend.empty:
        df_backend = analyze_data_backend(df_backend)
        curr = df_backend.iloc[-1]
        prev = df_backend.iloc[-2]
        change_pct = (curr['close'] - prev['close']) / prev['close'] * 100
        
        # Metrics Cards
        m1, m2, m3, m4 = st.columns(4)
        color_class = "up-green" if change_pct >= 0 else "down-red"
        
        with m1:
            st.markdown(f"""
            <div class="binance-card">
                <div style="color:#848e9c; font-size:12px;">GIÁ HIỆN TẠI</div>
                <div style="font-size:24px; font-weight:bold;" class="{color_class}">{curr['close']:,.4f}</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="binance-card">
                <div style="color:#848e9c; font-size:12px;">THAY ĐỔI 1H</div>
                <div style="font-size:24px; font-weight:bold;" class="{color_class}">{change_pct:+.2f}%</div>
            </div>""", unsafe_allow_html=True)
            
        rsi = curr['RSI_14']
        rsi_col = "up-green" if rsi < 30 else ("down-red" if rsi > 70 else "#eaecef")
        with m3:
            st.markdown(f"""
            <div class="binance-card">
                <div style="color:#848e9c; font-size:12px;">RSI (14)</div>
                <div style="font-size:24px; font-weight:bold; color:{rsi_col}">{rsi:.1f}</div>
            </div>""", unsafe_allow_html=True)
            
        with m4:
             st.markdown(f"""
            <div class="binance-card">
                <div style="color:#848e9c; font-size:12px;">VOL (Nến cuối)</div>
                <div style="font-size:24px; font-weight:bold; color:#eaecef">{curr['volume']:,.0f}</div>
            </div>""", unsafe_allow_html=True)

        st.write("")
        render_tradingview_widget(symbol)

    else:
        st.warning(f"⚠️ Không lấy được dữ liệu Backend cho **{symbol}**. (Có thể mã này chưa niêm yết trên Binance US).")
        st.caption("👉 Biểu đồ TradingView bên dưới vẫn sẽ hiển thị nếu mã này tồn tại trên thị trường quốc tế:")
        render_tradingview_widget(symbol)

elif app_mode == "📡 ALPHA SCANNER":
    st.markdown("### 📡 MÁY QUÉT TÍN HIỆU")
    if st.button("BẮT ĐẦU QUÉT NGAY", type="primary"):
        scan_coins = get_market_symbols(30)
        results = []
        bar = st.progress(0)
        
        for i, sym in enumerate(scan_coins):
            bar.progress((i+1)/len(scan_coins))
            df = fetch_candle_data_backend(sym, '4h', 30)
            if not df.empty:
                df = analyze_data_backend(df)
                rsi = df.iloc[-1]['RSI_14']
                
                sig = ""
                if rsi < 30: sig = "MUA (Quá bán)"
                elif rsi > 70: sig = "BÁN (Quá mua)"
                
                if sig:
                    results.append({"COIN": sym, "GIÁ": df.iloc[-1]['close'], "RSI": rsi, "TÍN HIỆU": sig})
        
        bar.empty()
        if results:
            st.success(f"Tìm thấy {len(results)} tín hiệu!")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.info("Chưa có tín hiệu mạnh (RSI >70 hoặc <30) trong danh sách quét.")

st.markdown("---")
st.caption("System Status: Stable | Region: US Safe Mode")
