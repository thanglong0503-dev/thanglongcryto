import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import streamlit.components.v1 as components
import time
import numpy as np

# ==============================================================================
# 1. UI CONFIGURATION
# ==============================================================================
st.set_page_config(layout="wide", page_title="Oracle Alpha Scalper", page_icon="⚡", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500;700&display=swap');

    :root {
        --bg-color: #050505;
        --card-bg: #0f0f0f;
        --accent: #ffeb3b; /* YELLOW LIGHTNING */
        --bull: #00ffa3;
        --bear: #ff0055;
        --text: #e0e0e0;
        --border: #333;
    }

    .stApp { background-color: var(--bg-color) !important; color: var(--text) !important; font-family: 'Rajdhani', sans-serif !important; }
    
    .oracle-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 32px;
        background: -webkit-linear-gradient(45deg, var(--accent), #ff9100);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        text-shadow: 0 0 20px rgba(255, 235, 59, 0.5);
    }

    .glass-card {
        background: rgba(20, 20, 20, 0.7);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 15px;
        backdrop-filter: blur(10px);
        margin-bottom: 10px;
        transition: 0.3s;
    }
    .glass-card:hover { border-color: var(--accent); box-shadow: 0 0 15px rgba(255, 235, 59, 0.2); }

    .metric-label { font-size: 12px; color: #888; letter-spacing: 1px; }
    .metric-val { font-size: 24px; font-weight: bold; font-family: 'Orbitron'; }
    .color-bull { color: var(--bull); text-shadow: 0 0 5px var(--bull); }
    .color-bear { color: var(--bear); text-shadow: 0 0 5px var(--bear); }

    .badge { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    
    /* INPUT FIX */
    div[data-baseweb="input"] { background-color: #1a1a1a !important; border: 1px solid #333 !important; }
    input[type="text"] { color: var(--accent) !important; background-color: transparent !important; font-family: 'Orbitron', sans-serif !important; }
    div[data-baseweb="select"] > div { background-color: #1a1a1a !important; color: #fff !important; border-color: #333 !important; }
    ul[data-baseweb="menu"] { background-color: #111 !important; border: 1px solid #333 !important; }
    li[data-baseweb="option"] { color: #eee !important; }
    li[data-baseweb="option"]:hover { background-color: #222 !important; color: var(--accent) !important; }
    
    /* BACKTEST TABLE */
    div[data-testid="stDataFrame"] { border: 1px solid #333; }
    
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. ORACLE ENGINE V12 (NEW STRATEGY: BOLLINGER SCALP)
# ==============================================================================
class OracleEngine:
    def __init__(self):
        try: self.exchange = ccxt.binanceus({'enableRateLimit': True})
        except: self.exchange = ccxt.kraken({'enableRateLimit': True})

    @st.cache_data(ttl=300)
    def get_top_coins(_self):
        try:
            tickers = _self.exchange.fetch_tickers()
            syms = [s for s in tickers if '/USDT' in s]
            return sorted(syms, key=lambda x: tickers[x]['quoteVolume'], reverse=True)[:30]
        except: return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']

    def fetch_ohlcv(self, symbol, timeframe, limit=300):
        try:
            for _ in range(3):
                try:
                    bars = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                    if bars: break
                except: time.sleep(0.5)
            else: return pd.DataFrame()
            df = pd.DataFrame(bars, columns=['t', 'o', 'h', 'l', 'c', 'v'])
            df['t'] = pd.to_datetime(df['t'], unit='ms')
            df.set_index('t', inplace=True)
            return df
        except: return pd.DataFrame()

    # --- INDICATORS ---
    def calculate_pivots(self, df):
        try:
            h, l, c = df['h'].iloc[-1], df['l'].iloc[-1], df['c'].iloc[-1]
            pp = (h + l + c) / 3
            return {"R2": pp + (h-l), "R1": (2*pp)-l, "S1": (2*pp)-h, "S2": pp-(h-l)}
        except: return None

    def check_squeeze(self, df):
        try:
            df.ta.bbands(length=20, std=2, append=True)
            w = (df['BBU_20_2.0'].iloc[-1] - df['BBL_20_2.0'].iloc[-1]) / df['BBM_20_2.0'].iloc[-1]
            return "SQUEEZE (NÉN)" if w < 0.05 else "EXPANDED"
        except: return "NORMAL"

    def analyze_live(self, symbol):
        # Dùng khung 1H cho Scalping
        df = self.fetch_ohlcv(symbol, '1h', 200)
        if df.empty: return None
        
        # Calculate Indicators
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.rsi(length=14, append=True)
        
        curr = df.iloc[-1]
        
        # Logic Scalp
        # Mua: Giá < Lower Band & RSI < 35
        signal = "NEUTRAL"
        if curr['close'] < curr['BBL_20_2.0'] and curr['RSI_14'] < 35:
            signal = "SCALP BUY ⚡"
        # Bán: Giá > Upper Band & RSI > 65
        elif curr['close'] > curr['BBU_20_2.0'] and curr['RSI_14'] > 65:
            signal = "SCALP SELL ⚡"
            
        return {
            "df": df,
            "signal": signal,
            "price": curr['close'],
            "rsi": curr['RSI_14'],
            "bbl": curr['BBL_20_2.0'],
            "bbu": curr['BBU_20_2.0']
        }

    # --- 🔥 NEW: STRATEGY 2 (MEAN REVERSION) 🔥 ---
    def run_backtest(self, symbol):
        # Lấy dữ liệu 1H (tốt cho scalp hơn 4H)
        df = self.fetch_ohlcv(symbol, '1h', limit=1000)
        
        if df.empty or len(df) < 50:
            return None, "Không đủ dữ liệu."
            
        # 2. Tính chỉ báo BBands + RSI
        df.ta.bbands(length=20, std=2, append=True) # Tạo BBL, BBM, BBU
        df['RSI'] = ta.rsi(df['c'], length=14)
        
        # 3. Giả lập
        initial_capital = 1000
        capital = initial_capital
        position = None
        entry_price = 0
        stop_loss = 0
        
        trades = []
        wins = 0
        losses = 0
        
        # Loop
        for i in range(50, len(df)):
            row = df.iloc[i]
            
            # --- CHIẾN THUẬT MỚI: BẮT ĐÁY (Buy the Dip) ---
            # Entry: Giá đóng cửa THẤP HƠN Lower Band VÀ RSI < 30 (Quá bán nặng)
            long_condition = (row['c'] < row['BBL_20_2.0']) and (row['RSI'] < 30)
            
            # Exit (Take Profit): Giá hồi về đường giữa (Middle Band - SMA20) -> Chốt lời an toàn
            tp_condition = (row['c'] >= row['BBM_20_2.0'])
            
            # Xử lý Vị thế
            if position == 'LONG':
                # Check Stoploss (Cắt lỗ cứng 3%)
                if row['l'] <= stop_loss:
                    pnl_pct = -3.0
                    pnl_amt = capital * (pnl_pct/100)
                    capital += pnl_amt
                    trades.append({'Type': 'STOP LOSS 🛑', 'PnL %': pnl_pct, 'Profit ($)': pnl_amt})
                    losses += 1
                    position = None
                # Check Take Profit (Chạm Middle Band)
                elif tp_condition:
                    pnl_pct = (row['c'] - entry_price) / entry_price * 100
                    pnl_amt = capital * (pnl_pct/100)
                    capital += pnl_amt
                    trades.append({'Type': 'TAKE PROFIT ✅', 'PnL %': pnl_pct, 'Profit ($)': pnl_amt})
                    wins += 1
                    position = None
            
            # Vào lệnh mới
            if position is None and long_condition:
                position = 'LONG'
                entry_price = row['c']
                stop_loss = entry_price * 0.97 # SL 3%
                trades.append({'Type': 'ENTRY LONG ⚡', 'Price': entry_price, 'Time': str(df.index[i])})

        # Kết quả
        total_trades = wins + losses
        winrate = (wins / total_trades * 100) if total_trades > 0 else 0
        total_return = (capital - initial_capital) / initial_capital * 100
        
        return trades, {
            "initial": initial_capital,
            "final": capital,
            "return": total_return,
            "winrate": winrate,
            "total_trades": total_trades,
            "wins": wins
        }

engine = OracleEngine()

# ==============================================================================
# 3. UI DASHBOARD
# ==============================================================================

c1, c2 = st.columns([1, 5])
with c1: st.markdown("## ⚡")
with c2: st.markdown('<div class="oracle-header">ALPHA SCALPER v12</div>', unsafe_allow_html=True)

col_search, col_list = st.columns([1, 2])
with col_search:
    manual = st.text_input("INPUT", placeholder="Type Symbol...", label_visibility="collapsed")
with col_list:
    coins = engine.get_top_coins()
    selected = st.selectbox("LIST", coins, label_visibility="collapsed")

symbol = f"{manual.upper()}/USDT" if manual else selected
if "/USDT" not in symbol and "/USD" not in symbol: symbol += "/USDT"

tab_live, tab_backtest = st.tabs(["🚀 LIVE SCALP", "🔙 BACKTEST STRATEGY"])

# ================= TAB 1: LIVE ANALYSIS =================
with tab_live:
    st.write("---")
    with st.spinner(f"⚡ SCANNING FOR DIPS ON {symbol}..."):
        data = engine.analyze_live(symbol)
        
        if data:
            curr_price = data['price']
            signal = data['signal']
            
            m1, m2, m3, m4 = st.columns(4)
            s_color = "#00ffa3" if "BUY" in signal else ("#ff0055" if "SELL" in signal else "#888")
            
            with m1: st.markdown(f"""<div class="glass-card"><div class="metric-label">PRICE</div><div class="metric-val" style="color:var(--accent)">${curr_price:,.4f}</div></div>""", unsafe_allow_html=True)
            with m2: st.markdown(f"""<div class="glass-card" style="border-color:{s_color}"><div class="metric-label">SIGNAL (1H)</div><div class="metric-val" style="color:{s_color}">{signal}</div></div>""", unsafe_allow_html=True)
            
            # Distance to Bands
            dist_lower = (curr_price - data['bbl']) / curr_price * 100
            dist_upper = (data['bbu'] - curr_price) / curr_price * 100
            
            with m3: st.markdown(f"""<div class="glass-card"><div class="metric-label">DIST TO LOW BAND</div><div class="metric-val" style="color:#fff">{dist_lower:.2f}%</div></div>""", unsafe_allow_html=True)
            with m4: st.markdown(f"""<div class="glass-card"><div class="metric-label">RSI (1H)</div><div class="metric-val">{data['rsi']:.1f}</div></div>""", unsafe_allow_html=True)

            c_chart, c_tools = st.columns([3, 1])
            with c_chart:
                base = symbol.split('/')[0]
                components.html(f"""
                <div class="tradingview-widget-container" style="height:700px;width:100%">
                <div id="tv_chart" style="height:100%;width:100%"></div>
                <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                <script type="text/javascript">
                new TradingView.widget({{
                "autosize": true, "symbol": "BINANCE:{base}USDT", "interval": "60", "timezone": "Asia/Ho_Chi_Minh",
                "theme": "dark", "style": "1", "locale": "vi_VN", "enable_publishing": false,
                "backgroundColor": "#0f0f0f", "gridColor": "rgba(40,40,40,0.5)",
                "hide_top_toolbar": false, "container_id": "tv_chart",
                "studies": ["BB@tv-basicstudies", "RSI@tv-basicstudies"]
                }});
                </script>
                </div>""", height=710)

            with c_tools:
                st.markdown("### ⚡ CHIẾN THUẬT VỢT ĐÁY")
                st.info("""
                **NGUYÊN LÝ:**
                Mua khi giá rơi quá mạnh (Chạm dải dưới BB + RSI thấp). Bán khi giá hồi lại.
                
                **LUẬT CHƠI:**
                1. ✅ MUA: Giá < Dải Dưới BB VÀ RSI < 35.
                2. 🎯 CHỐT LỜI: Giá chạm Dải Giữa (Middle Band).
                3. 🛑 CẮT LỖ: 3% hoặc khi RSI phân kỳ âm tiếp.
                """)
                
                st.markdown("### 📊 KHUYẾN NGHỊ")
                rec = "QUAN SÁT (WAIT)"
                if dist_lower < 0.5 and data['rsi'] < 35: rec = "CHUẨN BỊ MUA (READY)"
                if dist_lower < 0 and data['rsi'] < 30: rec = "MUA NGAY (ACTION)"
                
                rec_col = "#00ffa3" if "MUA" in rec else "#fff"
                st.markdown(f"""
                <div class="glass-card" style="text-align:center">
                    <div style="font-size:12px; color:#888;">TRẠNG THÁI</div>
                    <div style="font-size:20px; font-weight:bold; color:{rec_col}">{rec}</div>
                </div>
                """, unsafe_allow_html=True)

# ================= TAB 2: BACKTEST =================
with tab_backtest:
    st.markdown(f"### 🔙 KIỂM TRA CHIẾN THUẬT SCALPING ({symbol})")
    st.caption("Chiến thuật: Bollinger Reversion (Mean Reversion) | Khung 1H | Vốn $1,000")
    
    if st.button("🚀 CHẠY BACKTEST SCALP"):
        with st.spinner("⏳ Đang test chiến thuật vợt đáy..."):
            trades, stats = engine.run_backtest(symbol)
            
            if stats:
                b1, b2, b3, b4 = st.columns(4)
                
                res_color = "#00ffa3" if stats['return'] > 0 else "#ff0055"
                
                with b1: st.markdown(f"""<div class="glass-card"><div class="metric-label">LỢI NHUẬN (ROI)</div><div class="metric-val" style="color:{res_color}">{stats['return']:.2f}%</div></div>""", unsafe_allow_html=True)
                with b2: st.markdown(f"""<div class="glass-card"><div class="metric-label">TỶ LỆ THẮNG (WINRATE)</div><div class="metric-val" style="color:#ffeb3b">{stats['winrate']:.1f}%</div></div>""", unsafe_allow_html=True)
                with b3: st.markdown(f"""<div class="glass-card"><div class="metric-label">SỐ LỆNH THẮNG</div><div class="metric-val" style="color:#00ffa3">{stats['wins']}/{stats['total_trades']}</div></div>""", unsafe_allow_html=True)
                with b4: st.markdown(f"""<div class="glass-card"><div class="metric-label">VỐN CUỐI CÙNG</div><div class="metric-val">${stats['final']:.2f}</div></div>""", unsafe_allow_html=True)

                st.line_chart(pd.DataFrame(trades)['Profit ($)'].cumsum() if trades else [])
                
                st.markdown("### 📝 NHẬT KÝ GIAO DỊCH")
                if trades:
                    st.dataframe(pd.DataFrame(trades), use_container_width=True)
                else:
                    st.warning("Không có tín hiệu khớp trong giai đoạn này (Thị trường có thể đang Trend mạnh, không có hồi quy).")
            else:
                st.error(stats)

st.markdown("---")
st.caption("ALPHA SCALPER v12 | Strategy: Bollinger Mean Reversion")
