import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import time
import streamlit.components.v1 as components 

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG (V4 - HEDGE FUND UI)
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="Crypto Hedge Fund Terminal", 
    page_icon="🏦", 
    initial_sidebar_state="expanded"
)

# CSS "BÊ TÔNG CỐT THÉP" (Giữ nguyên từ V3.6 vì đã ổn định)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
    
    /* GLOBAL DARK THEME */
    .stApp { background-color: #0b0e11 !important; color: #eaecef !important; font-family: 'Roboto', sans-serif; }
    header[data-testid="stHeader"] { background: #0b0e11 !important; }

    /* INPUT & SELECTBOX FIX */
    div[data-baseweb="input"], div[data-baseweb="select"] > div {
        background-color: #2b3139 !important; border: 1px solid #474d57 !important; border-radius: 4px !important;
    }
    input[type="text"] { color: #eaecef !important; caret-color: #fcd535 !important; }
    
    /* MENU DROPDOWN FIX */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-baseweb="menu"] {
        background-color: #1e2329 !important; border: 1px solid #474d57 !important;
    }
    li[data-baseweb="option"] { color: #eaecef !important; background-color: #1e2329 !important; }
    li[data-baseweb="option"]:hover, li[aria-selected="true"] {
        background-color: #2b3139 !important; color: #fcd535 !important;
    }

    /* BUTTON STYLING */
    button[kind="primary"] {
        background-color: #fcd535 !important; border: none !important; border-radius: 4px !important;
    }
    button[kind="primary"] * { color: #000000 !important; font-weight: 800 !important; }
    button[kind="primary"]:hover { box-shadow: 0 0 10px rgba(252, 213, 53, 0.6); }

    /* SIGNAL BADGES */
    .badge-buy { background-color: #0ecb81; color: black; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    .badge-sell { background-color: #f6465d; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    .badge-neu { background-color: #474d57; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;}

    /* METRIC CARDS */
    .binance-card { background-color: #1e2329; border-radius: 6px; padding: 15px; border: 1px solid #2b3139; text-align: center; }
    .up-green { color: #0ecb81 !important; } 
    .down-red { color: #f6465d !important; }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] { background-color: #161a1e !important; border-right: 1px solid #2b3139; }
    h1, h2, h3, label, .stMarkdown { color: #eaecef !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ENGINE KẾT NỐI (US SECURE)
# ==========================================
@st.cache_resource
def init_exchange():
    try: return ccxt.binanceus({'enableRateLimit': True})
    except: return ccxt.kraken({'enableRateLimit': True})

exchange = init_exchange()

@st.cache_data(ttl=300)
def get_market_symbols(limit=60):
    try:
        tickers = exchange.fetch_tickers()
        symbols = [s for s in tickers if '/USDT' in s or '/USD' in s]
        sorted_symbols = sorted(symbols, key=lambda x: tickers[x]['quoteVolume'] if 'quoteVolume' in tickers[x] else 0, reverse=True)
        return sorted_symbols[:limit] if symbols else ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
    except: return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']

def fetch_candle_data_backend(symbol, timeframe, limit=100):
    try:
        # Retry logic
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

# ==========================================
# 3. BỘ NÃO PHÂN TÍCH (SMART ALPHA V4)
# ==========================================
def analyze_pro_signals(df):
    if df.empty or len(df) < 52: return df, {}
    
    # 1. EMA TREND (Golden Cross)
    df.ta.ema(length=50, append=True)
    df.ta.ema(length=200, append=True)
    
    # 2. RSI & Stochastic RSI
    df.ta.rsi(length=14, append=True)
    df.ta.stochrsi(length=14, append=True) # Trả về STOCHRSIk và STOCHRSId
    
    # 3. MACD
    df.ta.macd(append=True) # Trả về MACD_12_26_9, MACDh, MACDs
    
    # 4. SUPERTREND (Chỉ báo bắt trend siêu nhạy)
    # supertrend trả về: SUPERT_7_3.0, SUPERTd_7_3.0 (1=Up, -1=Down)
    st_data = df.ta.supertrend(length=10, multiplier=3, append=True)
    
    # 5. ICHIMOKU CLOUD (Chiến thuật Nhật Bản)
    # Trả về ISA, ISB (Mây), ITS (Tenkan), IKS (Kijun)
    ichi_data = df.ta.ichimoku(append=True)
    
    # --- LOGIC TỔNG HỢP TÍN HIỆU (SIGNAL AGGREGATION) ---
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    signals = {
        "score": 0,
        "details": []
    }
    
    # A. Phân tích Xu Hướng (Trend)
    ema50 = curr['EMA_50']
    ema200 = curr['EMA_200']
    if ema50 > ema200:
        signals["score"] += 1
        signals["details"].append("✅ Golden Trend (50>200)")
    elif ema50 < ema200:
        signals["score"] -= 1
        signals["details"].append("🔻 Death Trend (50<200)")
        
    # B. SuperTrend (Rất mạnh)
    st_dir_col = [c for c in df.columns if 'SUPERTd' in c][0] # Tìm cột direction
    if curr[st_dir_col] == 1:
        signals["score"] += 2 # Tín hiệu quan trọng
        signals["details"].append("🚀 SuperTrend: BULLISH")
    else:
        signals["score"] -= 2
        signals["details"].append("🐻 SuperTrend: BEARISH")
        
    # C. Ichimoku Breakout
    # Kiểm tra giá có nằm trên mây không (Span A và Span B)
    # Cần tìm tên cột ISA và ISB động
    isa_col = [c for c in df.columns if 'ISA_' in c][0]
    isb_col = [c for c in df.columns if 'ISB_' in c][0]
    
    if curr['close'] > curr[isa_col] and curr['close'] > curr[isb_col]:
        signals["score"] += 1
        signals["details"].append("☁️ Price > Ichimoku Cloud")
    elif curr['close'] < curr[isa_col] and curr['close'] < curr[isb_col]:
        signals["score"] -= 1
        signals["details"].append("⛈️ Price < Ichimoku Cloud")

    # D. RSI & Momentum
    rsi = curr['RSI_14']
    if rsi < 30: 
        signals["score"] += 1
        signals["details"].append(f"💎 RSI Oversold ({rsi:.0f})")
    elif rsi > 70:
        signals["score"] -= 1
        signals["details"].append(f"⚠️ RSI Overbought ({rsi:.0f})")
        
    # Đánh giá cuối cùng
    if signals["score"] >= 3: signals["rating"] = "STRONG BUY"
    elif signals["score"] >= 1: signals["rating"] = "BUY"
    elif signals["score"] <= -3: signals["rating"] = "STRONG SELL"
    elif signals["score"] <= -1: signals["rating"] = "SELL"
    else: signals["rating"] = "NEUTRAL"
    
    return df, signals

# ==========================================
# 4. TRADINGVIEW WIDGET (SMART MAPPING)
# ==========================================
def render_tradingview_widget(symbol):
    try: base_coin = symbol.split('/')[0]
    except: base_coin = symbol
    tv_symbol = f"BINANCE:{base_coin}USDT"
    
    html_code = f"""
    <div class="tradingview-widget-container" style="height:650px;width:100%">
      <div id="tradingview_b8d71" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
      "autosize": true,
      "symbol": "{tv_symbol}",
      "interval": "240", /* Mặc định 4H */
      "timezone": "Asia/Ho_Chi_Minh",
      "theme": "dark", 
      "style": "1", 
      "locale": "vi_VN", 
      "enable_publishing": false,
      "backgroundColor": "#0b0e11", 
      "gridColor": "rgba(43, 49, 57, 0.3)",
      "hide_top_toolbar": false,
      "hide_legend": false,
      "save_image": true,
      "toolbar_bg": "#1e2329",
      "studies": [
        "SuperTrend@tv-basicstudies", /* Thêm SuperTrend vào Chart */
        "MACD@tv-basicstudies"       /* Thêm MACD vào Chart */
      ],
      "container_id": "tradingview_b8d71"
      }}
      );
      </script>
    </div>
    """
    components.html(html_code, height=660)

# ==========================================
# 5. GIAO DIỆN CHÍNH
# ==========================================
st.sidebar.markdown("### 🏦 HEDGE FUND CONTROL")
app_mode = st.sidebar.radio("CHẾ ĐỘ:", ["📈 MARKET INTELLIGENCE", "📡 SMART SCANNER AI"])
st.sidebar.markdown("---")
st.sidebar.caption(f"Data: {exchange.name} | Strategy: Hybrid V4")

st.markdown("## 🏦 CRYPTO TERMINAL <span style='color:#fcd535'>HEDGE FUND</span>", unsafe_allow_html=True)

if app_mode == "📈 MARKET INTELLIGENCE":
    coins = get_market_symbols(60)

    # --- HYBRID SEARCH ---
    col_search, col_select = st.columns([1, 2])
    with col_search:
        st.markdown("<small>🔍 TRA CỨU MÃ (VD: PEPE)</small>", unsafe_allow_html=True)
        manual_search = st.text_input("search_input", placeholder="Nhập mã...", label_visibility="collapsed")
        
    with col_select:
        st.markdown("<small>🏆 DANH MỤC THEO DÕI</small>", unsafe_allow_html=True)
        safe_coins = coins if coins else ['BTC/USDT']
        selected_from_list = st.selectbox("list_select", safe_coins, index=0, label_visibility="collapsed")

    if manual_search:
        raw = manual_search.upper().strip()
        symbol = f"{raw}/USDT" if "/USDT" not in raw and "/USD" not in raw else raw
        st.info(f"Đang phân tích mã: **{symbol}**")
    else:
        symbol = selected_from_list
    
    # FETCH & ANALYZE
    with st.spinner(f"🤖 AI đang phân tích dữ liệu {symbol}..."):
        # Lấy nhiều nến hơn (200) để tính EMA200 chính xác
        df_backend = fetch_candle_data_backend(symbol, '4h', 250)
        
        # Logic Fallback nếu USDT không có
        if df_backend.empty and "/USDT" in symbol:
             fallback = symbol.replace("/USDT", "/USD")
             df_backend = fetch_candle_data_backend(fallback, '4h', 250)
             if not df_backend.empty: symbol = fallback
    
    if not df_backend.empty:
        df_backend, sigs = analyze_pro_signals(df_backend)
        curr = df_backend.iloc[-1]
        prev = df_backend.iloc[-2]
        change_pct = (curr['close'] - prev['close']) / prev['close'] * 100
        
        # --- HIỂN THỊ METRICS ---
        m1, m2, m3, m4 = st.columns(4)
        color_class = "up-green" if change_pct >= 0 else "down-red"
        
        with m1: st.markdown(f"""<div class="binance-card"><div style="color:#848e9c;font-size:12px;">GIÁ (4H)</div><div style="font-size:24px;font-weight:bold;" class="{color_class}">{curr['close']:,.4f}</div></div>""", unsafe_allow_html=True)
        with m2: st.markdown(f"""<div class="binance-card"><div style="color:#848e9c;font-size:12px;">BIẾN ĐỘNG</div><div style="font-size:24px;font-weight:bold;" class="{color_class}">{change_pct:+.2f}%</div></div>""", unsafe_allow_html=True)
        
        # Rating Card
        rating_color = "#fcd535" # Neutral
        if "BUY" in sigs['rating']: rating_color = "#0ecb81"
        elif "SELL" in sigs['rating']: rating_color = "#f6465d"
        
        with m3: st.markdown(f"""<div class="binance-card"><div style="color:#848e9c;font-size:12px;">ĐÁNH GIÁ AI</div><div style="font-size:24px;font-weight:bold;color:{rating_color}">{sigs['rating']}</div></div>""", unsafe_allow_html=True)
        with m4: st.markdown(f"""<div class="binance-card"><div style="color:#848e9c;font-size:12px;">ĐIỂM TÍN HIỆU</div><div style="font-size:24px;font-weight:bold;color:#eaecef">{sigs['score']}/5</div></div>""", unsafe_allow_html=True)

        # --- SIGNAL DETAILS ---
        with st.expander("🔎 CHI TIẾT TÍN HIỆU KỸ THUẬT (TOP TRADER STRATEGY)", expanded=True):
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                st.write("#### ✅ Tín hiệu Tích Cực")
                has_pos = False
                for s in sigs['details']:
                    if any(x in s for x in ['✅', '🚀', '☁️', '💎']):
                        st.markdown(f"- {s}")
                        has_pos = True
                if not has_pos: st.caption("Không có tín hiệu tích cực.")
            
            with s_col2:
                st.write("#### ⚠️ Tín hiệu Tiêu Cực")
                has_neg = False
                for s in sigs['details']:
                    if any(x in s for x in ['🔻', '🐻', '⛈️', '⚠️']):
                        st.markdown(f"- {s}")
                        has_neg = True
                if not has_neg: st.caption("An toàn, chưa có báo động đỏ.")

        st.write("")
        render_tradingview_widget(symbol)
    else:
        st.warning(f"⚠️ Dữ liệu chưa sẵn sàng cho {symbol}.")
        render_tradingview_widget(symbol)

elif app_mode == "📡 SMART SCANNER AI":
    st.markdown("### 📡 MÁY QUÉT CƠ HỘI ĐẦU TƯ (PRO)")
    st.caption("Quét dựa trên tổ hợp: SuperTrend + Ichimoku + RSI + EMA Cross")
    
    col_btn, col_set = st.columns([1, 3])
    with col_btn:
        start_scan = st.button("🚀 BẮT ĐẦU QUÉT NGAY", type="primary")
    
    if start_scan:
        scan_coins = get_market_symbols(40) # Quét Top 40
        results = []
        bar = st.progress(0)
        status_txt = st.empty()
        
        for i, sym in enumerate(scan_coins):
            bar.progress((i+1)/len(scan_coins))
            status_txt.text(f"AI đang phân tích: {sym}...")
            
            df = fetch_candle_data_backend(sym, '4h', 250)
            if not df.empty:
                try:
                    _, sigs = analyze_pro_signals(df)
                    
                    # Chỉ lấy các coin có tín hiệu rõ ràng (Bỏ qua Neutral)
                    if sigs['rating'] not in ["NEUTRAL"]:
                        results.append({
                            "COIN": sym,
                            "GIÁ": df.iloc[-1]['close'],
                            "RATING": sigs['rating'],
                            "SCORE": sigs['score'],
                            "CHI TIẾT": ", ".join([d.split(' ')[1] for d in sigs['details']][:2]) # Lấy 2 lý do chính
                        })
                except: continue
        
        bar.empty()
        status_txt.empty()
        
        if results:
            st.success(f"✅ Hoàn tất! Tìm thấy {len(results)} cơ hội đầu tư.")
            
            # Convert to DataFrame & Sort
            res_df = pd.DataFrame(results).sort_values(by="SCORE", ascending=False)
            
            # Styling function
            def style_table(val):
                color = '#eaecef'
                if 'STRONG BUY' in str(val): color = '#0ecb81'
                elif 'STRONG SELL' in str(val): color = '#f6465d'
                elif 'BUY' in str(val): color = '#66ffa6'
                return f'color: {color}; font-weight: bold'

            st.dataframe(
                res_df.style.map(style_table, subset=['RATING']),
                use_container_width=True,
                height=600
            )
        else:
            st.info("Thị trường đang đi ngang (Sideway). Chưa có tín hiệu mạnh.")

st.markdown("---")
st.caption("Crypto Hedge Fund Terminal | Powered by Binance Data & Smart Alpha AI")
