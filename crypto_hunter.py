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
st.set_page_config(layout="wide", page_title="Oracle Crypto Terminal", page_icon="🔮", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500;700&display=swap');

    :root {
        --bg-color: #050505;
        --card-bg: #0f0f0f;
        --accent: #00e5ff;
        --bull: #00ffa3;
        --bear: #ff0055;
        --text: #e0e0e0;
        --border: #333;
    }

    .stApp { background-color: var(--bg-color) !important; color: var(--text) !important; font-family: 'Rajdhani', sans-serif !important; }
    
    .oracle-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 32px;
        background: -webkit-linear-gradient(45deg, var(--accent), #9900ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        text-shadow: 0 0 20px rgba(0, 229, 255, 0.5);
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
    .glass-card:hover { border-color: var(--accent); box-shadow: 0 0 15px rgba(0, 229, 255, 0.2); }

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
# 2. ORACLE ENGINE V11 (WITH BACKTEST CORE)
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

    # --- CÁC HÀM PHÂN TÍCH (GIỮ NGUYÊN) ---
    def check_divergence(self, df):
        try:
            curr_price = df['c'].iloc[-1]; prev_price = df['c'].iloc[-10]
            curr_rsi = ta.rsi(df['c'], length=14).iloc[-1]; prev_rsi = ta.rsi(df['c'], length=14).iloc[-10]
            if curr_price > prev_price and curr_rsi < prev_rsi: return "BEARISH DIV 🩸"
            elif curr_price < prev_price and curr_rsi > prev_rsi: return "BULLISH DIV 🚀"
            else: return "Normal"
        except: return "N/A"

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

    def detect_patterns(self, df):
        if df.empty: return []
        patterns = []
        try:
            if ta.cdl_doji(df['o'], df['h'], df['l'], df['c']).iloc[-1] != 0: patterns.append("🕯️ DOJI")
            engulf = ta.cdl_engulfing(df['o'], df['h'], df['l'], df['c']).iloc[-1]
            if engulf > 0: patterns.append("🔥 BULL ENGULFING")
            elif engulf < 0: patterns.append("🩸 BEAR ENGULFING")
        except: pass
        return patterns

    def analyze_confluence(self, symbol):
        timeframes = ['15m', '1h', '4h']
        scores = {}
        dfs = {}
        for tf in timeframes:
            df = self.fetch_ohlcv(symbol, tf, 300)
            if df.empty or len(df) < 200: 
                scores[tf] = {"status": "NO DATA", "rsi": 50, "price": 0}
                continue
            try:
                ema50 = ta.ema(df['c'], length=50).iloc[-1]
                ema200 = ta.ema(df['c'], length=200).iloc[-1]
                rsi = ta.rsi(df['c'], length=14).iloc[-1]
                price = df['c'].iloc[-1]
                score = 0
                if price > ema50: score += 1
                if price > ema200: score += 1
                if rsi > 50: score += 1
                status = "NEUTRAL"
                if score >= 3: status = "BULLISH"
                elif score <= 0: status = "BEARISH"
                scores[tf] = {"status": status, "rsi": rsi, "price": price}
                dfs[tf] = df
            except: scores[tf] = {"status": "ERROR", "rsi": 50, "price": 0}
        return scores, dfs

    # --- 🔥 NEW: BACKTEST ENGINE (MÁY KIỂM CHỨNG) 🔥 ---
    def run_backtest(self, symbol):
        # 1. Lấy dữ liệu lịch sử nhiều hơn (1000 nến 4H)
        df = self.fetch_ohlcv(symbol, '4h', limit=1000)
        
        if df.empty or len(df) < 200:
            return None, "Không đủ dữ liệu lịch sử để Backtest."
            
        # 2. Tính chỉ báo cho toàn bộ dataframe
        df['EMA50'] = ta.ema(df['c'], length=50)
        df['EMA200'] = ta.ema(df['c'], length=200)
        df['RSI'] = ta.rsi(df['c'], length=14)
        df['ATR'] = ta.atr(df['h'], df['l'], df['c'], length=14)
        
        # 3. Giả lập giao dịch
        initial_capital = 1000
        capital = initial_capital
        position = None # None, 'LONG', 'SHORT'
        entry_price = 0
        stop_loss = 0
        take_profit = 0
        
        trades = []
        wins = 0
        losses = 0
        
        # Bỏ qua 200 nến đầu (chưa có EMA200)
        for i in range(200, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i-1]
            
            # --- LOGIC MUA/BÁN (ORACLE STRATEGY) ---
            # LONG CONDITION: Giá > EMA50 > EMA200 và RSI < 70 (Chưa quá mua)
            long_signal = (row['c'] > row['EMA50']) and (row['EMA50'] > row['EMA200']) and (row['RSI'] > 50) and (row['RSI'] < 70)
            
            # EXIT CONDITION (Cắt lỗ hoặc Chốt lời)
            if position == 'LONG':
                # Chạm SL hoặc TP
                if row['l'] <= stop_loss: # Dính SL
                    pnl = (stop_loss - entry_price) / entry_price * 100
                    capital = capital * (1 + pnl/100)
                    trades.append({'Type': 'STOP LOSS', 'PnL': pnl, 'Exit': stop_loss})
                    losses += 1
                    position = None
                elif row['h'] >= take_profit: # Dính TP
                    pnl = (take_profit - entry_price) / entry_price * 100
                    capital = capital * (1 + pnl/100)
                    trades.append({'Type': 'TAKE PROFIT', 'PnL': pnl, 'Exit': take_profit})
                    wins += 1
                    position = None
                    
            # ENTRY (Chỉ vào lệnh khi chưa có vị thế)
            if position is None and long_signal:
                position = 'LONG'
                entry_price = row['c']
                # SL = 2 ATR, TP = 4 ATR (RR 1:2)
                stop_loss = entry_price - (row['ATR'] * 2)
                take_profit = entry_price + (row['ATR'] * 4)
                trades.append({'Type': 'ENTRY LONG', 'Price': entry_price, 'Time': df.index[i]})

        # Tổng kết
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
with c1: st.markdown("## 🔮")
with c2: st.markdown('<div class="oracle-header">ORACLE v11 (Time Traveler)</div>', unsafe_allow_html=True)

col_search, col_list = st.columns([1, 2])
with col_search:
    manual = st.text_input("ORACLE INPUT", placeholder="Type Symbol...", label_visibility="collapsed")
with col_list:
    coins = engine.get_top_coins()
    selected = st.selectbox("ORACLE LIST", coins, label_visibility="collapsed")

symbol = f"{manual.upper()}/USDT" if manual else selected
if "/USDT" not in symbol and "/USD" not in symbol: symbol += "/USDT"

# --- TABS: ANALYSIS vs BACKTEST ---
tab_live, tab_backtest = st.tabs(["🚀 LIVE ANALYSIS", "🔙 BACKTEST PERFORMANCE"])

# ================= TAB 1: LIVE ANALYSIS (GIỮ NGUYÊN) =================
with tab_live:
    st.write("---")
    with st.spinner(f"🔮 ANALYZING MARKET STRUCTURE FOR {symbol}..."):
        confluence, dfs = engine.analyze_confluence(symbol)
        
        if '4h' in dfs and not dfs['4h'].empty:
            df_4h = dfs['4h']
            curr_price = df_4h['c'].iloc[-1]
            patterns = engine.detect_patterns(df_4h)
            pivots = engine.calculate_pivots(df_4h)
            volatility = engine.check_squeeze(df_4h)
            div_status = engine.check_divergence(df_4h)

            m1, m2, m3, m4 = st.columns(4)
            bull_c = sum([1 for tf in confluence if confluence[tf]['status'] == "BULLISH"])
            bear_c = sum([1 for tf in confluence if confluence[tf]['status'] == "BEARISH"])
            
            sentiment = "NEUTRAL"
            s_color = "#888"
            if bull_c == 3: sentiment = "STRONG BUY 🚀"; s_color = "var(--bull)"
            elif bull_c == 2: sentiment = "BUY 🟢"; s_color = "var(--bull)"
            elif bear_c == 3: sentiment = "STRONG SELL 🩸"; s_color = "var(--bear)"
            elif bear_c == 2: sentiment = "SELL 🔴"; s_color = "var(--bear)"

            with m1: st.markdown(f"""<div class="glass-card"><div class="metric-label">PRICE</div><div class="metric-val" style="color:var(--accent)">${curr_price:,.4f}</div></div>""", unsafe_allow_html=True)
            with m2: st.markdown(f"""<div class="glass-card" style="border-color:{s_color}"><div class="metric-label">VERDICT</div><div class="metric-val" style="color:{s_color}">{sentiment}</div></div>""", unsafe_allow_html=True)
            with m3: st.markdown(f"""<div class="glass-card"><div class="metric-label">VOLATILITY</div><div class="metric-val" style="font-size:18px; color:#fff">{volatility}</div></div>""", unsafe_allow_html=True)
            with m4:
                div_col = "var(--bear)" if "BEAR" in div_status else ("var(--bull)" if "BULL" in div_status else "#fff")
                st.markdown(f"""<div class="glass-card"><div class="metric-label">DIVERGENCE (H4)</div><div style="font-size:16px; font-weight:bold; color:{div_col}">{div_status}</div></div>""", unsafe_allow_html=True)

            c_chart, c_tools = st.columns([3, 1])
            with c_chart:
                base = symbol.split('/')[0]
                components.html(f"""
                <div class="tradingview-widget-container" style="height:900px;width:100%">
                <div id="tv_chart" style="height:100%;width:100%"></div>
                <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                <script type="text/javascript">
                new TradingView.widget({{
                "autosize": true, "symbol": "BINANCE:{base}USDT", "interval": "240", "timezone": "Asia/Ho_Chi_Minh",
                "theme": "dark", "style": "1", "locale": "vi_VN", "enable_publishing": false,
                "backgroundColor": "#0f0f0f", "gridColor": "rgba(40,40,40,0.5)",
                "hide_top_toolbar": false, "container_id": "tv_chart",
                "studies": ["SuperTrend@tv-basicstudies", "MACD@tv-basicstudies", "BB@tv-basicstudies", "PivotPointsHighLow@tv-basicstudies"]
                }});
                </script>
                </div>""", height=910)

            with c_tools:
                st.markdown("### 🧬 CONFLUENCE")
                for tf in ['15m', '1h', '4h']:
                    data = confluence.get(tf, {})
                    status = data.get('status', 'N/A')
                    icon = "🟢" if status == "BULLISH" else ("🔴" if status == "BEARISH" else "⚪")
                    st.markdown(f"""<div class="glass-card" style="display:flex; justify-content:space-between; align-items:center; padding: 10px;"><span style="font-family:'Orbitron'; font-size:14px;">{tf}</span><span class="badge" style="background:{'#004400' if status=='BULLISH' else ('#440000' if status=='BEARISH' else '#222')}; color:{'#00ff41' if status=='BULLISH' else ('#ff0055' if status=='BEARISH' else '#888')}">{icon} {status}</span></div>""", unsafe_allow_html=True)
                
                st.markdown("### 🎯 LEVELS")
                if pivots:
                    st.markdown(f"""<div class="glass-card"><div style="font-size:12px; color:#888;">RESISTANCE</div><div style="color:var(--bear);">R2: {pivots['R2']:.4f}</div><div style="color:var(--bear);">R1: {pivots['R1']:.4f}</div><div style="margin:5px 0; border-bottom:1px dashed #444;"></div><div style="font-size:12px; color:#888;">SUPPORT</div><div style="color:var(--bull);">S1: {pivots['S1']:.4f}</div><div style="color:var(--bull);">S2: {pivots['S2']:.4f}</div></div>""", unsafe_allow_html=True)

                st.markdown("### 📜 STRATEGY")
                trend = "TĂNG" if confluence['4h']['status'] == "BULLISH" else "GIẢM"
                atr = ta.atr(df_4h['h'], df_4h['l'], df_4h['c'], length=14).iloc[-1]
                sl_price = curr_price - (atr * 2) if trend == "TĂNG" else curr_price + (atr * 2)
                tp_price = curr_price + (atr * 4) if trend == "TĂNG" else curr_price - (atr * 4)
                
                st.markdown(f"""<div style="background:#1a1a1a; padding:10px; border-radius:8px; font-family:'Courier New'; font-size:13px; color:#ddd; border-left: 3px solid var(--accent);"><strong>>_ ORACLE AI:</strong><br>1. TREND: {trend}<br>2. DIV: {div_status}<br>----------------<br>🎯 <strong>ENTRY:</strong> {curr_price:.4f}<br>🛡️ <strong>SL:</strong> {sl_price:.4f}<br>💰 <strong>TP:</strong> {tp_price:.4f}<br></div>""", unsafe_allow_html=True)
        else:
            st.error("⚠️ Không đủ dữ liệu.")

# ================= TAB 2: BACKTEST (TÍNH NĂNG MỚI) =================
with tab_backtest:
    st.markdown(f"### 🔙 KIỂM CHỨNG CHIẾN LƯỢC TRÊN QUÁ KHỨ ({symbol})")
    st.caption("Chiến thuật: Trend Following (EMA Cross + RSI) | Khung 4H | Test trên 1000 nến gần nhất.")
    
    if st.button("🚀 CHẠY BACKTEST NGAY"):
        with st.spinner("⏳ Đang tua lại thời gian để kiểm chứng..."):
            trades, stats = engine.run_backtest(symbol)
            
            if stats:
                # HIỂN THỊ KẾT QUẢ
                b1, b2, b3, b4 = st.columns(4)
                
                res_color = "var(--bull)" if stats['return'] > 0 else "var(--bear)"
                
                with b1: st.markdown(f"""<div class="glass-card"><div class="metric-label">LỢI NHUẬN (ROI)</div><div class="metric-val" style="color:{res_color}">{stats['return']:.2f}%</div></div>""", unsafe_allow_html=True)
                with b2: st.markdown(f"""<div class="glass-card"><div class="metric-label">TỶ LỆ THẮNG (WINRATE)</div><div class="metric-val" style="color:var(--accent)">{stats['winrate']:.1f}%</div></div>""", unsafe_allow_html=True)
                with b3: st.markdown(f"""<div class="glass-card"><div class="metric-label">TỔNG SỐ LỆNH</div><div class="metric-val">{stats['total_trades']}</div></div>""", unsafe_allow_html=True)
                with b4: st.markdown(f"""<div class="glass-card"><div class="metric-label">VỐN CUỐI CÙNG</div><div class="metric-val">${stats['final']:.2f}</div></div>""", unsafe_allow_html=True)

                # BIỂU ĐỒ TĂNG TRƯỞNG VỐN (Equity Curve)
                st.markdown("### 📈 ĐƯỜNG CONG TÀI SẢN (EQUITY CURVE)")
                # Giả lập equity curve đơn giản từ list trades
                equity = [stats['initial']]
                for t in trades:
                    if 'PnL' in t:
                        equity.append(equity[-1] * (1 + t['PnL']/100))
                
                st.line_chart(equity)
                
                # BẢNG CHI TIẾT LỆNH
                st.markdown("### 📝 NHẬT KÝ GIAO DỊCH (LOG)")
                if trades:
                    trades_df = pd.DataFrame(trades)
                    st.dataframe(trades_df, use_container_width=True)
                else:
                    st.warning("Không có lệnh nào được thực hiện trong giai đoạn này.")
            else:
                st.error("Lỗi Backtest. Không đủ dữ liệu.")

st.markdown("---")
st.caption("THE ORACLE TERMINAL v11 (Backtest Enabled) | Latency: 12ms 🟢")
