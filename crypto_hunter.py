import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import streamlit.components.v1 as components
import time
import numpy as np

# ==============================================================================
# 1. UI CONFIGURATION (GIỮ NGUYÊN GIAO DIỆN)
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
    
    /* INPUT FIX */
    div[data-baseweb="input"] { background-color: #1a1a1a !important; border: 1px solid #333 !important; }
    input[type="text"] { color: var(--accent) !important; background-color: transparent !important; font-family: 'Orbitron', sans-serif !important; }
    div[data-baseweb="select"] > div { background-color: #1a1a1a !important; color: #fff !important; border-color: #333 !important; }
    ul[data-baseweb="menu"] { background-color: #111 !important; border: 1px solid #333 !important; }
    li[data-baseweb="option"] { color: #eee !important; }
    li[data-baseweb="option"]:hover { background-color: #222 !important; color: var(--accent) !important; }
    
    div[data-testid="stDataFrame"] { border: 1px solid #333; }
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. ORACLE ENGINE V12.1 (SAFE MODE - FIX KEYERROR)
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

    # --- HÀM TÌM CỘT AN TOÀN (SAFE COLUMN FINDER) ---
    def get_safe_col(self, df, pattern):
        """Tìm cột bắt đầu bằng pattern (VD: 'BBL') để tránh lỗi tên"""
        cols = [c for c in df.columns if c.startswith(pattern)]
        return cols[0] if cols else None

    def analyze_live(self, symbol):
        # 1. Lấy dữ liệu
        df = self.fetch_ohlcv(symbol, '1h', 200)
        
        # 2. Kiểm tra độ dài dữ liệu (Chống lỗi Crash)
        if df.empty or len(df) < 50: 
            return None # Trả về None để UI biết mà xử lý
        
        # 3. Tính toán (Bọc trong try-except để an toàn tuyệt đối)
        try:
            df.ta.bbands(length=20, std=2, append=True)
            df.ta.rsi(length=14, append=True)
            
            curr = df.iloc[-1]
            
            # Tìm tên cột động
            bbl_col = self.get_safe_col(df, 'BBL')
            bbu_col = self.get_safe_col(df, 'BBU')
            rsi_col = self.get_safe_col(df, 'RSI')
            
            # Nếu không tính được chỉ báo -> Return None
            if not bbl_col or not bbu_col or not rsi_col:
                return None

            price = curr['c']
            bbl_val = curr[bbl_col]
            bbu_val = curr[bbu_col]
            rsi_val = curr[rsi_col]
            
            # Logic Scalp
            signal = "NEUTRAL (CHỜ)"
            if price < bbl_val and rsi_val < 35:
                signal = "SCALP BUY ⚡"
            elif price > bbu_val and rsi_val > 65:
                signal = "SCALP SELL ⚡"
                
            return {
                "signal": signal,
                "price": price,
                "rsi": rsi_val,
                "bbl": bbl_val,
                "bbu": bbu_val
            }
        except Exception as e:
            st.error(f"Lỗi tính toán: {e}")
            return None

    def run_backtest(self, symbol):
        df = self.fetch_ohlcv(symbol, '1h', limit=1000)
        
        if df.empty or len(df) < 50:
            return None, "Dữ liệu không đủ để Backtest."
            
        # Tính toán an toàn
        try:
            bb = df.ta.bbands(length=20, std=2)
            if bb is None: return None, "Lỗi tính BB"
            df = pd.concat([df, bb], axis=1)
            df['RSI'] = ta.rsi(df['c'], length=14)
        except:
            return None, "Lỗi thư viện chỉ báo."
            
        # Tìm cột
        bbl_col = self.get_safe_col(df, 'BBL')
        bbm_col = self.get_safe_col(df, 'BBM') # Middle Band
        
        if not bbl_col or not bbm_col: return None, "Không tìm thấy cột chỉ báo."

        initial_capital = 1000
        capital = initial_capital
        position = None
        entry_price = 0
        stop_loss = 0
        
        trades = []
        wins = 0
        losses = 0
        
        for i in range(50, len(df)):
            row = df.iloc[i]
            
            # Entry: Giá < BBL và RSI < 30
            long_condition = (row['c'] < row[bbl_col]) and (row['RSI'] < 30)
            
            # Exit: Giá > BBM (Hồi về giữa)
            tp_condition = (row['c'] >= row[bbm_col])
            
            if position == 'LONG':
                if row['l'] <= stop_loss:
                    pnl_amt = capital * -0.03
                    capital += pnl_amt
                    trades.append({'Type': 'STOP LOSS 🛑', 'PnL %': -3.0, 'Profit ($)': pnl_amt})
                    losses += 1
                    position = None
                elif tp_condition:
                    pnl_pct = (row['c'] - entry_price) / entry_price * 100
                    pnl_amt = capital * (pnl_pct/100)
                    capital += pnl_amt
                    trades.append({'Type': 'TAKE PROFIT ✅', 'PnL %': pnl_pct, 'Profit ($)': pnl_amt})
                    wins += 1
                    position = None
            
            if position is None and long_condition:
                position = 'LONG'
                entry_price = row['c']
                stop_loss = entry_price * 0.97
                trades.append({'Type': 'ENTRY LONG ⚡', 'Price': entry_price, 'Time': str(df.index[i])})

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
with c2: st.markdown('<div class="oracle-header">ALPHA SCALPER v12.1</div>', unsafe_allow_html=True)

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
            
            dist_lower = (curr_price - data['bbl']) / curr_price * 100
            
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
                st.markdown("### ⚡ CHIẾN THUẬT")
                st.info("Mua khi giá rớt khỏi dải dưới BB và RSI < 35. Bán khi giá hồi về đường giữa (SMA20).")
                
                rec = "QUAN SÁT (WAIT)"
                if dist_lower < 0.5 and data['rsi'] < 35: rec = "CHUẨN BỊ (READY)"
                if dist_lower < 0 and data['rsi'] < 30: rec = "MUA NGAY (ACTION)"
                
                rec_col = "#00ffa3" if "MUA" in rec else "#fff"
                st.markdown(f"""<div class="glass-card" style="text-align:center"><div style="font-size:12px; color:#888;">TRẠNG THÁI</div><div style="font-size:20px; font-weight:bold; color:{rec_col}">{rec}</div></div>""", unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ Đang chờ dữ liệu nến cho {symbol} (hoặc mạng đang chậm). Vui lòng thử lại sau vài giây hoặc chọn coin khác.")

# ================= TAB 2: BACKTEST =================
with tab_backtest:
    st.markdown(f"### 🔙 KIỂM TRA CHIẾN THUẬT ({symbol})")
    if st.button("🚀 CHẠY BACKTEST SCALP"):
        with st.spinner("⏳ Đang test..."):
            trades, stats = engine.run_backtest(symbol)
            if stats:
                b1, b2, b3, b4 = st.columns(4)
                res_color = "#00ffa3" if stats['return'] > 0 else "#ff0055"
                with b1: st.markdown(f"""<div class="glass-card"><div class="metric-label">LỢI NHUẬN</div><div class="metric-val" style="color:{res_color}">{stats['return']:.2f}%</div></div>""", unsafe_allow_html=True)
                with b2: st.markdown(f"""<div class="glass-card"><div class="metric-label">WINRATE</div><div class="metric-val" style="color:#ffeb3b">{stats['winrate']:.1f}%</div></div>""", unsafe_allow_html=True)
                with b3: st.markdown(f"""<div class="glass-card"><div class="metric-label">SỐ LỆNH THẮNG</div><div class="metric-val" style="color:#00ffa3">{stats['wins']}/{stats['total_trades']}</div></div>""", unsafe_allow_html=True)
                with b4: st.markdown(f"""<div class="glass-card"><div class="metric-label">VỐN CUỐI</div><div class="metric-val">${stats['final']:.2f}</div></div>""", unsafe_allow_html=True)
                
                if trades:
                    st.line_chart(pd.DataFrame(trades)['Profit ($)'].cumsum())
                    st.dataframe(pd.DataFrame(trades), use_container_width=True)
            else:
                st.error(f"Lỗi: {stats}")

st.markdown("---")
st.caption("ALPHA SCALPER v12.1 (Safe Mode) | Strategy: Bollinger Mean Reversion")
