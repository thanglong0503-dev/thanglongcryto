import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import time
import streamlit.components.v1 as components 

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG (V5 - WHALE RADAR)
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="Crypto Terminal Pro", 
    page_icon="🏦", 
    initial_sidebar_state="expanded"
)

# CSS "BÊ TÔNG CỐT THÉP" (Giữ nguyên từ V3.6)
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

    /* METRIC CARDS */
    .binance-card { background-color: #1e2329; border-radius: 6px; padding: 15px; border: 1px solid #2b3139; text-align: center; }
    .up-green { color: #0ecb81 !important; } 
    .down-red { color: #f6465d !important; }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] { background-color: #161a1e !important; border-right: 1px solid #2b3139; }
    h1, h2, h3, label, .stMarkdown { color: #eaecef !important; }
    
    /* WHALE BAR */
    .whale-bar-container { width: 100%; height: 20px; background-color: #f6465d; border-radius: 10px; overflow: hidden; margin-top: 5px;}
    .whale-bar-fill { height: 100%; background-color: #0ecb81; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ENGINE KẾT NỐI
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
# 3. TÍNH NĂNG MỚI: WHALE RADAR (SOI ORDER BOOK)
# ==========================================
def analyze_order_book(symbol):
    """Phân tích sổ lệnh để tìm Cá mập và áp lực Mua/Bán"""
    try:
        # Lấy sổ lệnh 50 dòng đầu tiên (Top 50 Orders)
        ob = exchange.fetch_order_book(symbol, limit=50)
        
        bids = ob['bids'] # Lệnh chờ MUA
        asks = ob['asks'] # Lệnh chờ BÁN
        
        if not bids or not asks: return None

        # Tổng lượng tiền đang chờ Mua vs Bán (Volume)
        total_bid_vol = sum([bid[1] for bid in bids]) # Giá x Số lượng
        total_ask_vol = sum([ask[1] for ask in asks])
        
        # Tính tỷ lệ áp lực mua (%)
        total_vol = total_bid_vol + total_ask_vol
        buy_pressure_pct = (total_bid_vol / total_vol) * 100
        
        # Tìm tường lệnh (Whale Wall) - Lệnh nào chiếm > 5% tổng volume
        walls = []
        for bid in bids:
            if bid[1] > total_bid_vol * 0.05:
                walls.append(f"🟢 BUY WALL: {bid[1]:.2f} coin tại giá {bid[0]}")
        for ask in asks:
            if ask[1] > total_ask_vol * 0.05:
                walls.append(f"🔴 SELL WALL: {ask[1]:.2f} coin tại giá {ask[0]}")
                
        return {
            "buy_pct": buy_pressure_pct,
            "sell_pct": 100 - buy_pressure_pct,
            "total_bid": total_bid_vol,
            "total_ask": total_ask_vol,
            "walls": walls[:3] # Lấy 3 tường to nhất
        }
    except Exception as e:
        return None

# ==========================================
# 4. BỘ NÃO PHÂN TÍCH KỸ THUẬT (V4)
# ==========================================
def analyze_pro_signals(df):
    if df.empty or len(df) < 52: return df, {}
    
    df.ta.ema(length=50, append=True)
    df.ta.ema(length=200, append=True)
    df.ta.rsi(length=14, append=True)
    df.ta.supertrend(length=10, multiplier=3, append=True)
    
    curr = df.iloc[-1]
    signals = {"score": 0, "details": []}
    
    # Logic chấm điểm
    if curr['EMA_50'] > curr['EMA_200']: signals["score"] += 1
    elif curr['EMA_50'] < curr['EMA_200']: signals["score"] -= 1
        
    st_dir = [c for c in df.columns if 'SUPERTd' in c][0]
    if curr[st_dir] == 1: signals["score"] += 2; signals["details"].append("🚀 SuperTrend BULL")
    else: signals["score"] -= 2; signals["details"].append("🐻 SuperTrend BEAR")
        
    rsi = curr['RSI_14']
    if rsi < 30: signals["score"] += 1; signals["details"].append(f"💎 RSI Oversold ({rsi:.0f})")
    elif rsi > 70: signals["score"] -= 1; signals["details"].append(f"⚠️ RSI Overbought ({rsi:.0f})")
        
    if signals["score"] >= 3: signals["rating"] = "STRONG BUY"
    elif signals["score"] >= 1: signals["rating"] = "BUY"
    elif signals["score"] <= -3: signals["rating"] = "STRONG SELL"
    elif signals["score"] <= -1: signals["rating"] = "SELL"
    else: signals["rating"] = "NEUTRAL"
    
    return df, signals

# ==========================================
# 5. TRADINGVIEW WIDGET
# ==========================================
def render_tradingview_widget(symbol):
    try: base_coin = symbol.split('/')[0]
    except: base_coin = symbol
    tv_symbol = f"BINANCE:{base_coin}USDT"
    
    html_code = f"""
    <div class="tradingview-widget-container" style="height:600px;width:100%">
      <div id="tradingview_b8d71" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
      "autosize": true,
      "symbol": "{tv_symbol}",
      "interval": "240", 
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
      "studies": ["SuperTrend@tv-basicstudies", "MACD@tv-basicstudies"],
      "container_id": "tradingview_b8d71"
      }}
      );
      </script>
    </div>
    """
    components.html(html_code, height=610)

# ==========================================
# 6. GIAO DIỆN CHÍNH
# ==========================================
st.sidebar.markdown("### 🏦 HEDGE FUND CONTROL")
app_mode = st.sidebar.radio("CHẾ ĐỘ:", ["📈 MARKET INTELLIGENCE", "📡 SMART SCANNER AI"])
st.sidebar.markdown("---")
st.sidebar.caption(f"Data Source: {exchange.name}")

st.markdown("## 🏦 CRYPTO TERMINAL <span style='color:#fcd535'>WHALE EDITION</span>", unsafe_allow_html=True)

if app_mode == "📈 MARKET INTELLIGENCE":
    coins = get_market_symbols(60)

    col_search, col_select = st.columns([1, 2])
    with col_search:
        st.markdown("<small>🔍 TRA CỨU MÃ</small>", unsafe_allow_html=True)
        manual_search = st.text_input("search_input", placeholder="Nhập mã...", label_visibility="collapsed")
    with col_select:
        st.markdown("<small>🏆 DANH MỤC</small>", unsafe_allow_html=True)
        safe_coins = coins if coins else ['BTC/USDT']
        selected_from_list = st.selectbox("list_select", safe_coins, index=0, label_visibility="collapsed")

    if manual_search:
        raw = manual_search.upper().strip()
        symbol = f"{raw}/USDT" if "/USDT" not in raw and "/USD" not in raw else raw
    else:
        symbol = selected_from_list
    
    st.info(f"Đang phân tích dòng tiền & kỹ thuật: **{symbol}**")
    
    # 1. FETCH DATA (KỸ THUẬT)
    df_backend = fetch_candle_data_backend(symbol, '4h', 200)
    # Fallback logic
    if df_backend.empty and "/USDT" in symbol:
        fallback = symbol.replace("/USDT", "/USD")
        df_backend = fetch_candle_data_backend(fallback, '4h', 200)
        if not df_backend.empty: symbol = fallback

    # 2. FETCH DATA (DÒNG TIỀN - WHALE)
    whale_data = analyze_order_book(symbol)

    if not df_backend.empty:
        df_backend, sigs = analyze_pro_signals(df_backend)
        curr = df_backend.iloc[-1]
        prev = df_backend.iloc[-2]
        change_pct = (curr['close'] - prev['close']) / prev['close'] * 100
        
        # --- METRICS ---
        m1, m2, m3, m4 = st.columns(4)
        color_class = "up-green" if change_pct >= 0 else "down-red"
        
        with m1: st.markdown(f"""<div class="binance-card"><div style="color:#848e9c;font-size:12px;">GIÁ (4H)</div><div style="font-size:24px;font-weight:bold;" class="{color_class}">{curr['close']:,.4f}</div></div>""", unsafe_allow_html=True)
        with m2: st.markdown(f"""<div class="binance-card"><div style="color:#848e9c;font-size:12px;">BIẾN ĐỘNG</div><div style="font-size:24px;font-weight:bold;" class="{color_class}">{change_pct:+.2f}%</div></div>""", unsafe_allow_html=True)
        
        rating_color = "#fcd535"
        if "BUY" in sigs['rating']: rating_color = "#0ecb81"
        elif "SELL" in sigs['rating']: rating_color = "#f6465d"
        
        with m3: st.markdown(f"""<div class="binance-card"><div style="color:#848e9c;font-size:12px;">AI SIGNAL</div><div style="font-size:24px;font-weight:bold;color:{rating_color}">{sigs['rating']}</div></div>""", unsafe_allow_html=True)
        with m4: st.markdown(f"""<div class="binance-card"><div style="color:#848e9c;font-size:12px;">SCORE</div><div style="font-size:24px;font-weight:bold;color:#eaecef">{sigs['score']}/5</div></div>""", unsafe_allow_html=True)

        # --- PHẦN MỚI: WHALE RADAR ---
        st.write("")
        st.markdown("### 🐋 PHÂN TÍCH DÒNG TIỀN & CÁ MẬP (ORDER BOOK)")
        
        if whale_data:
            c1, c2 = st.columns([3, 1])
            with c1:
                buy_pct = whale_data['buy_pct']
                # Vẽ thanh áp lực mua bán
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; color:#848e9c; font-size:12px; margin-bottom:5px;">
                    <span>LỰC MUA: {buy_pct:.1f}%</span>
                    <span>LỰC BÁN: {whale_data['sell_pct']:.1f}%</span>
                </div>
                <div class="whale-bar-container">
                    <div class="whale-bar-fill" style="width: {buy_pct}%;"></div>
                </div>
                """, unsafe_allow_html=True)
                
                # Nhận xét dòng tiền
                if buy_pct > 60: st.caption("🔥 Phe Mua đang áp đảo (Cá mập gom hàng)")
                elif buy_pct < 40: st.caption("🩸 Phe Bán đang xả mạnh")
                else: st.caption("⚖️ Thị trường cân bằng")
                
            with c2:
                st.markdown(f"""
                <div class="binance-card" style="padding:10px;">
                    <small>TƯỜNG LỆNH LỚN</small><br>
                    {'<br>'.join([w for w in whale_data['walls']]) if whale_data['walls'] else '<span style="color:#888">Không có tường lớn</span>'}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Không lấy được dữ liệu Sổ lệnh (Order Book).")

        st.write("")
        render_tradingview_widget(symbol)
    else:
        st.warning(f"Dữ liệu chưa sẵn sàng cho {symbol}.")
        render_tradingview_widget(symbol)

elif app_mode == "📡 SMART SCANNER AI":
    st.markdown("### 📡 MÁY QUÉT CƠ HỘI ĐẦU TƯ")
    
    if st.button("🚀 BẮT ĐẦU QUÉT", type="primary"):
        scan_coins = get_market_symbols(30)
        results = []
        bar = st.progress(0)
        
        for i, sym in enumerate(scan_coins):
            bar.progress((i+1)/len(scan_coins))
            
            df = fetch_candle_data_backend(sym, '4h', 100)
            if not df.empty:
                try:
                    _, sigs = analyze_pro_signals(df)
                    # Thêm phân tích dòng tiền vào Scanner luôn
                    w_data = analyze_order_book(sym)
                    buy_pressure = w_data['buy_pct'] if w_data else 50
                    
                    if sigs['rating'] != "NEUTRAL":
                        results.append({
                            "COIN": sym,
                            "GIÁ": df.iloc[-1]['close'],
                            "RATING": sigs['rating'],
                            "LỰC MUA (%)": f"{buy_pressure:.1f}%",
                            "SCORE": sigs['score']
                        })
                except: continue
        
        bar.empty()
        
        if results:
            st.success(f"Tìm thấy {len(results)} cơ hội!")
            res_df = pd.DataFrame(results).sort_values(by="SCORE", ascending=False)
            
            def style_table(val):
                if 'STRONG BUY' in str(val): return 'color: #0ecb81; font-weight: bold'
                if 'STRONG SELL' in str(val): return 'color: #f6465d; font-weight: bold'
                return ''

            st.dataframe(res_df.style.map(style_table, subset=['RATING']), use_container_width=True)
        else:
            st.info("Chưa có tín hiệu mạnh.")

st.markdown("---")
st.caption("Crypto Hedge Fund Terminal | Whale Edition")
