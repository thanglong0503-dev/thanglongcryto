import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import time
import streamlit.components.v1 as components
from datetime import datetime

# ==============================================================================
# 1. CẤU HÌNH GIAO DIỆN "FULL SCREEN"
# ==============================================================================
st.set_page_config(layout="wide", page_title="Binance Pro Replica", page_icon="💎", initial_sidebar_state="collapsed")

# CSS HACK: Xóa khoảng trắng thừa, ép giao diện dính sát lề như App Trading
st.markdown("""
<style>
    /* 1. RESET LAYOUT */
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
    header { visibility: hidden; }
    
    /* 2. COLOR PALETTE (Binance Dark) */
    :root {
        --bg: #161a1e;
        --card: #1e2329;
        --text: #eaecef;
        --green: #0ecb81;
        --red: #f6465d;
        --yellow: #fcd535;
    }
    
    /* 3. GLOBAL STYLE */
    .stApp { background-color: var(--bg); color: var(--text); }
    
    /* 4. ORDER BOOK STYLE */
    .ob-table { font-family: 'Consolas', monospace; font-size: 11px; width: 100%; border-collapse: collapse; }
    .ob-row { height: 18px; }
    .ask-price { color: var(--red); text-align: left; }
    .bid-price { color: var(--green); text-align: left; }
    .ob-amount { text-align: right; color: #848e9c; }
    
    /* 5. METRICS HEADER */
    .ticker-box { background: var(--card); padding: 10px; border-radius: 4px; border: 1px solid #2b3139; display: flex; justify-content: space-between; align-items: center; }
    .big-price { font-size: 24px; font-weight: bold; font-family: 'Arial', sans-serif; }
    
    /* 6. INPUT & BUTTONS */
    div[data-baseweb="input"] { background-color: #2b3139 !important; border: 1px solid #474d57 !important; }
    input { color: white !important; }
    button { border-radius: 4px !important; text-transform: uppercase; font-weight: bold !important; }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-thumb { background: #2b3139; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CORE ENGINE & STATE MANAGEMENT (LƯU TRẠNG THÁI VÍ)
# ==============================================================================
# Khởi tạo Ví tiền ảo nếu chưa có
if 'balance' not in st.session_state:
    st.session_state.balance = 10000.0 # Cấp vốn 10k USDT
if 'positions' not in st.session_state:
    st.session_state.positions = [] # Danh sách lệnh đang mở

# Kết nối Exchange (An toàn)
@st.cache_resource
def get_exchange():
    try: return ccxt.binanceus({'enableRateLimit': True})
    except: return ccxt.kraken({'enableRateLimit': True})

exchange = get_exchange()

# Hàm lấy dữ liệu thật (Snapshot)
def fetch_real_data(symbol):
    try:
        # 1. Lấy giá hiện tại & biến động 24h
        ticker = exchange.fetch_ticker(symbol)
        
        # 2. Lấy Order Book thật (Top 10)
        ob = exchange.fetch_order_book(symbol, limit=10)
        
        return ticker, ob
    except:
        return None, None

# Hàm đặt lệnh (Paper Trading Logic)
def execute_order(side, symbol, price, amount, leverage):
    cost = (price * amount) / leverage
    if cost > st.session_state.balance:
        st.error("❌ Số dư không đủ!")
        return

    st.session_state.balance -= cost
    new_pos = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "symbol": symbol,
        "side": side,
        "entry": price,
        "amount": amount,
        "leverage": leverage,
        "margin": cost
    }
    st.session_state.positions.append(new_pos)
    st.success(f"✅ Đã khớp lệnh {side} {symbol} tại {price}")

# ==============================================================================
# 3. UI LAYOUT: GRID SYSTEM (HỆ THỐNG LƯỚI CHẶT CHẼ)
# ==============================================================================

# --- A. HEADER BAR (TICKER) ---
# Chọn Coin (Nằm gọn trên cùng)
c_sel, c_info = st.columns([1, 5])
with c_sel:
    # List cứng để load cho nhanh
    symbol = st.selectbox("Market", ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "DOGE/USDT", "XRP/USDT"], label_visibility="collapsed")

# Lấy dữ liệu Real-time
ticker, orderbook = fetch_real_data(symbol)

if ticker:
    last_price = ticker['last']
    change_pct = ticker['percentage']
    color_cls = "color: #0ecb81" if change_pct >= 0 else "color: #f6465d"
    
    with c_info:
        st.markdown(f"""
        <div class="ticker-box">
            <div>
                <span style="font-size: 20px; font-weight: bold; color: #eaecef">{symbol}</span>
                <span style="font-size: 12px; color: #848e9c; margin-left: 10px">Perpetual</span>
            </div>
            <div>
                <span class="big-price" style="{color_cls}">{last_price:,.2f}</span>
            </div>
            <div>
                <span style="color: #848e9c; font-size:12px">24h Change</span><br>
                <span style="{color_cls}; font-weight:bold">{change_pct:+.2f}%</span>
            </div>
            <div>
                <span style="color: #848e9c; font-size:12px">24h High</span><br>
                <span style="color: #eaecef">{ticker['high']:,.2f}</span>
            </div>
            <div>
                <span style="color: #848e9c; font-size:12px">24h Low</span><br>
                <span style="color: #eaecef">{ticker['low']:,.2f}</span>
            </div>
            <div>
                <span style="color: #848e9c; font-size:12px">24h Vol(USDT)</span><br>
                <span style="color: #eaecef">{ticker['quoteVolume']/1000000:.2f}M</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("") # Spacer

    # --- B. MAIN WORKSPACE (CHIA 3 CỘT: CHART | ORDERBOOK | TRADE) ---
    col_chart, col_ob, col_trade = st.columns([5, 2, 2])
    
    # 1. CHART AREA (TradingView Advanced)
    with col_chart:
        tv_sym = f"BINANCE:{symbol.replace('/','')}"
        # Nhúng Widget Chart xịn nhất, tắt toolbar thừa
        html_chart = f"""
        <div class="tradingview-widget-container" style="height:550px;width:100%">
          <div id="tradingview_chart" style="height:100%;width:100%"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
          "autosize": true, "symbol": "{tv_sym}", "interval": "15", "timezone": "Asia/Ho_Chi_Minh",
          "theme": "dark", "style": "1", "locale": "vi_VN", "enable_publishing": false,
          "backgroundColor": "#161a1e", "gridColor": "rgba(43, 49, 57, 0.3)",
          "hide_top_toolbar": false, "hide_legend": false, "save_image": false,
          "studies": ["RSI@tv-basicstudies", "MACD@tv-basicstudies"],
          "container_id": "tradingview_chart"
          }});
          </script>
        </div>
        """
        components.html(html_chart, height=550)

    # 2. ORDER BOOK AREA (Dữ liệu thật từ CCXT)
    with col_ob:
        st.markdown(f"###### Order Book")
        if orderbook:
            # Tạo HTML table thủ công để giống sàn nhất (Streamlit dataframe bị viền trắng)
            ob_html = '<table class="ob-table">'
            
            # ASKS (Bán - Đỏ - Xếp ngược từ cao xuống thấp)
            asks = orderbook['asks'][::-1] # Đảo ngược để giá thấp nhất ở dưới (gần giá khớp)
            for price, amount in asks[-12:]: # Lấy 12 lệnh gần nhất
                ob_html += f'<tr class="ob-row"><td class="ask-price">{price:.2f}</td><td class="ob-amount">{amount:.4f}</td></tr>'
            
            # GIÁ Ở GIỮA
            ob_html += f'<tr style="font-size:16px; font-weight:bold; color:{("#0ecb81" if change_pct>=0 else "#f6465d")}"><td colspan="2" style="text-align:center; padding: 5px 0;">{last_price:.2f} <span style="font-size:10px">USD</span></td></tr>'
            
            # BIDS (Mua - Xanh)
            for price, amount in orderbook['bids'][:12]:
                ob_html += f'<tr class="ob-row"><td class="bid-price">{price:.2f}</td><td class="ob-amount">{amount:.4f}</td></tr>'
            
            ob_html += '</table>'
            st.markdown(ob_html, unsafe_allow_html=True)
        else:
            st.warning("Connecting...")

    # 3. TRADING FORM AREA (Chức năng thật - Ví ảo)
    with col_trade:
        st.markdown(f"###### Place Order")
        
        # Tab Mua/Bán
        tab_limit, tab_market = st.tabs(["Limit", "Market"])
        
        with tab_market:
            st.caption(f"Avail: {st.session_state.balance:,.2f} USDT")
            
            # Input Form
            lev = st.slider("Leverage", 1, 125, 20, key="lev_slider")
            amount_usdt = st.number_input("Size (USDT)", min_value=10.0, step=10.0, value=100.0)
            
            # Tính toán margin
            margin_req = amount_usdt / lev
            st.markdown(f"""
            <div style="font-size:12px; color:#848e9c; margin-top:5px; display:flex; justify-content:space-between;">
                <span>Cost:</span> <span style="color:#eaecef">{margin_req:.2f} USDT</span>
            </div>
            """, unsafe_allow_html=True)
            
            col_b, col_s = st.columns(2)
            with col_b:
                if st.button("BUY / LONG", type="primary", use_container_width=True):
                    execute_order("LONG", symbol, last_price, amount_usdt/last_price, lev)
                    st.rerun() # Refresh để cập nhật ví
                    
            with col_s:
                if st.button("SELL / SHORT", type="primary", use_container_width=True):
                    execute_order("SHORT", symbol, last_price, amount_usdt/last_price, lev)
                    st.rerun()

    # --- C. PORTFOLIO SECTION (BOTTOM) ---
    st.markdown("---")
    st.markdown("#### 💼 Positions & Assets")
    
    p_tab1, p_tab2 = st.tabs(["Open Positions", "Trade History"])
    
    with p_tab1:
        if st.session_state.positions:
            # Chuyển list positions thành DataFrame đẹp
            pos_df = pd.DataFrame(st.session_state.positions)
            
            # Tính PnL giả định (Mark Price - Entry Price)
            # Lưu ý: Đây là giả định đơn giản
            current_p = last_price
            
            def calc_pnl(row):
                if row['side'] == 'LONG':
                    pnl = (current_p - row['entry']) * row['amount']
                else:
                    pnl = (row['entry'] - current_p) * row['amount']
                return pnl

            pos_df['Unrealized PnL'] = pos_df.apply(lambda x: calc_pnl(x) if x['symbol'] == symbol else 0, axis=1)
            
            # Hiển thị bảng
            st.dataframe(
                pos_df[['time', 'symbol', 'side', 'leverage', 'entry', 'margin', 'Unrealized PnL']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No open positions. Start trading now!")

else:
    st.error("Data connection lost. Please refresh.")
