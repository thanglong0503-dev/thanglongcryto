import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import time
import streamlit.components.v1 as components 

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="Crypto Terminal Pro", 
    page_icon="📊", 
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CSS "THUỐC ĐẶC TRỊ" (SỬA LỖI TRẮNG)
# ==========================================
st.markdown("""
<style>
    /* Import Font */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

    /* --- 1. ÉP NỀN TỐI TOÀN APP & XÓA VỆT TRẮNG HEADER --- */
    .stApp {
        background-color: #161a1e !important; 
        color: #eaecef !important;
        font-family: 'Roboto', sans-serif;
    }
    
    /* 🔥 ĐÂY LÀ ĐOẠN XÓA CÁI THANH TRẮNG TRÊN ĐẦU 🔥 */
    header[data-testid="stHeader"] {
        background-color: #161a1e !important;
        background: #161a1e !important;
    }
    
    /* --- 2. SỬA LỖI MENU "TÀNG HÌNH" (DROPDOWN) --- */
    /* Ép tất cả các hộp thoại (Popover) phải có nền đen */
    div[data-baseweb="popover"], div[data-baseweb="menu"], div[role="listbox"] {
        background-color: #1e2329 !important;
        border: 1px solid #474d57 !important;
    }
    
    /* Ép chữ trong menu thành màu trắng */
    li[data-baseweb="option"], div[role="option"] {
        color: #eaecef !important;
        background-color: #1e2329 !important;
    }
    
    /* Hiệu ứng khi rê chuột (Hover) */
    li[data-baseweb="option"]:hover, li[aria-selected="true"] {
        background-color: #2b3139 !important;
        color: #fcd535 !important; /* Chữ vàng */
    }

    /* Sửa lỗi ô chọn (Selectbox) khi chưa bấm */
    div[data-baseweb="select"] > div {
        background-color: #2b3139 !important;
        color: #eaecef !important;
        border: 1px solid #474d57 !important;
    }
    
    /* Sửa màu mũi tên xuống */
    svg[data-baseweb="icon"] {
        fill: #848e9c !important;
    }

    /* --- 3. SỬA LỖI MENU 3 CHẤM (SETTINGS/RERUN) --- */
    /* Cố gắng ép màu menu hệ thống (Lưu ý: Cái này khó can thiệp nhất nếu ko có config.toml) */
    div[data-testid="stToolbar"] {
        color: #eaecef !important;
    }
    button[kind="header"] {
        color: #eaecef !important;
    }

    /* --- 4. CÁC THÀNH PHẦN KHÁC --- */
    section[data-testid="stSidebar"] {
        background-color: #1e2329 !important; 
        border-right: 1px solid #2b3139;
    }
    
    h1, h2, h3, h4, span, p, label, .stMarkdown {
        color: #eaecef !important;
    }
    
    /* Thẻ Card thông số */
    .binance-card {
        background-color: #1e2329;
        border-radius: 4px;
        padding: 15px;
        border: 1px solid #2b3139;
        text-align: center;
    }
    
    /* Nút bấm Vàng */
    button[kind="primary"] {
        background-color: #fcd535 !important;
        border: none !important;
        border-radius: 4px !important;
    }
    button[kind="primary"] p {
        color: #1e2329 !important; /* Chữ đen trên nền vàng */
        font-weight: 700 !important;
    }

    /* Màu tăng giảm */
    .up-green { color: #0ecb81 !important; } 
    .down-red { color: #f6465d !important; }  
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. ENGINE KẾT NỐI (BINANCE US - ỔN ĐỊNH)
# ==========================================
@st.cache_resource
def init_exchange():
    """Sử dụng Binance US để tránh bị chặn IP tại Mỹ"""
    try:
        return ccxt.binanceus({'enableRateLimit': True})
    except:
        return ccxt.kraken({'enableRateLimit': True})

exchange = init_exchange()

@st.cache_data(ttl=300)
def get_market_symbols(limit=60):
    try:
        tickers = exchange.fetch_tickers()
        symbols = [s for s in tickers if '/USDT' in s or '/USD' in s]
        sorted_symbols = sorted(symbols, key=lambda x: tickers[x]['quoteVolume'] if 'quoteVolume' in tickers[x] else 0, reverse=True)
        if not symbols: return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
        return sorted_symbols[:limit]
    except:
        return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']

def fetch_candle_data_backend(symbol, timeframe, limit=50):
    try:
        for _ in range(3):
            try:
                bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
                if bars: break
            except: time.sleep(0.5)
        else: return pd.DataFrame()

        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except: return pd.DataFrame()

def analyze_data_backend(df):
    if df.empty: return df
    df.ta.rsi(length=14, append=True)
    return df

# ==========================================
# 4. TRADINGVIEW WIDGET
# ==========================================
def render_tradingview_widget(symbol):
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
      "studies": ["RSI@tv-basicstudies"],
      "container_id": "tradingview_b8d71"
      }}
      );
      </script>
    </div>
    """
    components.html(html_code, height=610)

# ==========================================
# 5. GIAO DIỆN CHÍNH
# ==========================================
# --- SIDEBAR ---
st.sidebar.markdown("### ⚙️ CONTROL PANEL")
app_mode = st.sidebar.radio("CHẾ ĐỘ:", ["📈 MARKET DASHBOARD", "📡 ALPHA SCANNER"])
st.sidebar.markdown("---")
st.sidebar.caption(f"Server: {exchange.name} (Secured)")

# --- HEADER ---
st.markdown("## 📊 CRYPTO TERMINAL PRO")

if app_mode == "📈 MARKET DASHBOARD":
    coins = get_market_symbols(60)

    # --- HYBRID SEARCH ---
    col_search, col_select = st.columns([1, 2])
    with col_search:
        st.markdown("<small>🔍 NHẬP MÃ (VD: DOGE)</small>", unsafe_allow_html=True)
        manual_search = st.text_input("Search Input", placeholder="...", label_visibility="collapsed")
        
    with col_select:
        st.markdown("<small>🏆 DANH SÁCH TOP</small>", unsafe_allow_html=True)
        safe_coins = coins if coins else ['BTC/USDT']
        selected_from_list = st.selectbox("List Select", safe_coins, index=0, label_visibility="collapsed")

    # LOGIC CHỌN
    if manual_search:
        raw_input = manual_search.upper().strip()
        symbol = f"{raw_input}/USDT" if "/USDT" not in raw_input else raw_input
        st.info(f"Đang xem mã nhập tay: **{symbol}**")
    else:
        symbol = selected_from_list
    
    # FETCH DATA
    with st.spinner(f"Đang tải dữ liệu {symbol}..."):
        df_backend = fetch_candle_data_backend(symbol, '1h', 50)
    
    if not df_backend.empty:
        df_backend = analyze_data_backend(df_backend)
        curr = df_backend.iloc[-1]
        prev = df_backend.iloc[-2]
        change_pct = (curr['close'] - prev['close']) / prev['close'] * 100
        
        # METRICS
        m1, m2, m3, m4 = st.columns(4)
        color_class = "up-green" if change_pct >= 0 else "down-red"
        
        with m1:
            st.markdown(f"""<div class="binance-card"><div style="color:#848e9c;font-size:12px;">GIÁ HIỆN TẠI</div><div style="font-size:24px;font-weight:bold;" class="{color_class}">{curr['close']:,.4f}</div></div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div class="binance-card"><div style="color:#848e9c;font-size:12px;">THAY ĐỔI 1H</div><div style="font-size:24px;font-weight:bold;" class="{color_class}">{change_pct:+.2f}%</div></div>""", unsafe_allow_html=True)
            
        rsi = curr['RSI_14']
        rsi_col = "up-green" if rsi < 30 else ("down-red" if rsi > 70 else "#eaecef")
        with m3:
            st.markdown(f"""<div class="binance-card"><div style="color:#848e9c;font-size:12px;">RSI (14)</div><div style="font-size:24px;font-weight:bold;color:{rsi_col}">{rsi:.1f}</div></div>""", unsafe_allow_html=True)
            
        with m4:
             st.markdown(f"""<div class="binance-card"><div style="color:#848e9c;font-size:12px;">VOL (Nến cuối)</div><div style="font-size:24px;font-weight:bold;color:#eaecef">{curr['volume']:,.0f}</div></div>""", unsafe_allow_html=True)

        st.write("")
        render_tradingview_widget(symbol)

    else:
        st.warning(f"⚠️ Không tìm thấy dữ liệu Backend cho **{symbol}**. (Mã này có thể không có trên Binance US).")
        st.caption("👇 Biểu đồ TradingView bên dưới vẫn hoạt động bình thường:")
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
st.caption("Crypto Terminal Pro | Powered by Binance Data & TradingView Charts")
