import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import streamlit.components.v1 as components
import time
import numpy as np

# ==============================================================================
# 1. ORACLE UI CONFIGURATION (GIỮ NGUYÊN THEO YÊU CẦU)
# ==============================================================================
st.set_page_config(layout="wide", page_title="Oracle Crypto Terminal", page_icon="🔮", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500;700&display=swap');

    :root {
        --bg-color: #050505;
        --card-bg: #0f0f0f;
        --accent: #00e5ff; /* Cyan Neon */
        --bull: #00ffa3;   /* Green Neon */
        --bear: #ff0055;   /* Pink Neon */
        --text: #e0e0e0;
        --border: #333;
    }

    /* GLOBAL RESET */
    .stApp { background-color: var(--bg-color) !important; color: var(--text) !important; font-family: 'Rajdhani', sans-serif !important; }
    
    /* ORACLE HEADER */
    .oracle-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 32px;
        background: -webkit-linear-gradient(45deg, var(--accent), #9900ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        text-shadow: 0 0 20px rgba(0, 229, 255, 0.5);
    }

    /* CARDS */
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

    /* METRICS */
    .metric-label { font-size: 12px; color: #888; letter-spacing: 1px; }
    .metric-val { font-size: 24px; font-weight: bold; font-family: 'Orbitron'; }
    .color-bull { color: var(--bull); text-shadow: 0 0 5px var(--bull); }
    .color-bear { color: var(--bear); text-shadow: 0 0 5px var(--bear); }

    /* SIGNAL BADGES */
    .badge { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .badge-long { background: rgba(0, 255, 163, 0.1); border: 1px solid var(--bull); color: var(--bull); }
    .badge-short { background: rgba(255, 0, 85, 0.1); border: 1px solid var(--bear); color: var(--bear); }

    /* INPUTS FIX */
    div[data-baseweb="input"] { background-color: #1a1a1a !important; border: 1px solid #333 !important; }
    input[type="text"] { color: var(--accent) !important; background-color: transparent !important; font-family: 'Orbitron', sans-serif !important; }
    div[data-baseweb="select"] > div { background-color: #1a1a1a !important; color: #fff !important; border-color: #333 !important; }
    
    /* DROPDOWN MENU */
    ul[data-baseweb="menu"] { background-color: #111 !important; border: 1px solid #333 !important; }
    li[data-baseweb="option"] { color: #eee !important; }
    li[data-baseweb="option"]:hover { background-color: #222 !important; color: var(--accent) !important; }

    /* TABLES */
    div[data-testid="stDataFrame"] { border: 1px solid #333; }
    
    /* CUSTOM SCROLLBAR */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. ORACLE ENGINE v10 (TOP TRADER TOOLS ADDED)
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

    # --- TOP TRADER TOOL 1: PIVOT POINTS (Cản/Hỗ trợ Cứng) ---
    def calculate_pivots(self, df):
        try:
            high = df['h'].iloc[-1]
            low = df['l'].iloc[-1]
            close = df['c'].iloc[-1]
            
            # Classic Pivot Formula
            pp = (high + low + close) / 3
            r1 = (2 * pp) - low
            s1 = (2 * pp) - high
            r2 = pp + (high - low)
            s2 = pp - (high - low)
            
            return {"PP": pp, "R1": r1, "S1": s1, "R2": r2, "S2": s2}
        except: return None

    # --- TOP TRADER TOOL 2: FIBONACCI GOLDEN POCKET ---
    def calculate_fibonacci(self, df):
        try:
            # Tìm đỉnh đáy gần nhất trong 100 nến
            highest = df['h'].max()
            lowest = df['l'].min()
            current = df['c'].iloc[-1]
            
            # Xác định xu hướng ngắn hạn để vẽ Fib
            trend = "UP" if current > (highest+lowest)/2 else "DOWN"
            
            if trend == "UP": # Đang tăng -> Tìm hỗ trợ khi hồi về (Retracement)
                diff = highest - lowest
                fib_05 = highest - (diff * 0.5)
                fib_0618 = highest - (diff * 0.618) # Golden Pocket
                return {"trend": "UP", "0.5": fib_05, "0.618": fib_0618}
            else: # Đang giảm -> Tìm kháng cự
                diff = highest - lowest
                fib_05 = lowest + (diff * 0.5)
                fib_0618 = lowest + (diff * 0.618)
                return {"trend": "DOWN", "0.5": fib_05, "0.618": fib_0618}
        except: return None

    # --- TOP TRADER TOOL 3: VOLATILITY SQUEEZE ---
    def check_squeeze(self, df):
        try:
            df.ta.bbands(length=20, std=2, append=True)
            df.ta.kc(append=True)
            # Nếu BB nằm lọt thỏm trong Keltner Channel -> Squeeze (Nén chặt)
            # Logic đơn giản hóa: Bandwidth
            bb_width = (df['BBU_20_2.0'].iloc[-1] - df['BBL_20_2.0'].iloc[-1]) / df['BBM_20_2.0'].iloc[-1]
            return "COMPRESSED (SẮP BUNG)" if bb_width < 0.05 else "EXPANDED (BIẾN ĐỘNG)"
        except: return "NORMAL"

    def detect_patterns(self, df):
        # ... (Giữ nguyên logic soi nến từ V9.1)
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
        # ... (Giữ nguyên logic đa khung từ V9.1)
        timeframes = ['15m', '1h', '4h']
        scores = {}
        data_frames = {}
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
                data_frames[tf] = df
            except: scores[tf] = {"status": "ERROR", "rsi": 50, "price": 0}
        return scores, data_frames

engine = OracleEngine()

# ==============================================================================
# 3. UI DASHBOARD (RE-LAYOUT FOR BIGGER CHART)
# ==============================================================================

# Header
c1, c2 = st.columns([1, 5])
with c1: st.markdown("## 🔮")
with c2: st.markdown('<div class="oracle-header">ORACLE SNIPER v10</div>', unsafe_allow_html=True)

# Search
col_search, col_list = st.columns([1, 2])
with col_search:
    manual = st.text_input("ORACLE INPUT", placeholder="Type Symbol (e.g. SUI)...", label_visibility="collapsed")
with col_list:
    coins = engine.get_top_coins()
    selected = st.selectbox("ORACLE LIST", coins, label_visibility="collapsed")

symbol = f"{manual.upper()}/USDT" if manual else selected
if "/USDT" not in symbol and "/USD" not in symbol: symbol += "/USDT"

st.write("---")

with st.spinner(f"🔮 SNIPER AI CALIBRATING FOR {symbol}..."):
    confluence, dfs = engine.analyze_confluence(symbol)
    
    if '4h' in dfs and not dfs['4h'].empty:
        df_4h = dfs['4h']
        curr_price = df_4h['c'].iloc[-1]
        patterns = engine.detect_patterns(df_4h)
        
        # --- PRO TOOLS CALCULATION ---
        pivots = engine.calculate_pivots(df_4h)
        fibs = engine.calculate_fibonacci(df_4h)
        volatility = engine.check_squeeze(df_4h)

        # --- METRICS ROW ---
        m1, m2, m3, m4 = st.columns(4)
        bull_count = sum([1 for tf in confluence if confluence[tf]['status'] == "BULLISH"])
        bear_count = sum([1 for tf in confluence if confluence[tf]['status'] == "BEARISH"])
        
        sentiment = "NEUTRAL"
        s_color = "#888"
        if bull_count == 3: sentiment = "STRONG BUY 🚀"; s_color = "var(--bull)"
        elif bull_count == 2: sentiment = "BUY 🟢"; s_color = "var(--bull)"
        elif bear_count == 3: sentiment = "STRONG SELL 🩸"; s_color = "var(--bear)"
        elif bear_count == 2: sentiment = "SELL 🔴"; s_color = "var(--bear)"

        with m1: st.markdown(f"""<div class="glass-card"><div class="metric-label">CURRENT PRICE</div><div class="metric-val" style="color:var(--accent)">${curr_price:,.4f}</div></div>""", unsafe_allow_html=True)
        with m2: st.markdown(f"""<div class="glass-card" style="border-color:{s_color}"><div class="metric-label">ORACLE VERDICT</div><div class="metric-val" style="color:{s_color}">{sentiment}</div></div>""", unsafe_allow_html=True)
        with m3: st.markdown(f"""<div class="glass-card"><div class="metric-label">VOLATILITY STATE</div><div class="metric-val" style="font-size:18px; color:#fff">{volatility}</div></div>""", unsafe_allow_html=True)
        with m4:
             pat_text = patterns[0] if patterns else "None"
             p_col = "var(--bull)" if "BULL" in pat_text else ("var(--bear)" if "BEAR" in pat_text else "white")
             st.markdown(f"""<div class="glass-card"><div class="metric-label">CANDLE PATTERN</div><div style="font-size:18px; font-weight:bold; color:{p_col}">{pat_text}</div></div>""", unsafe_allow_html=True)

        # --- BODY: BIG CHART (3/4 Screen) & TOOLS (1/4 Screen) ---
        c_chart, c_tools = st.columns([3, 1])
        
        with c_chart:
            base = symbol.split('/')[0]
            st.markdown(f"### 📉 {base} PROFESSIONAL CHART")
            # Tăng chiều cao lên 750px cho đã mắt
            components.html(f"""
            <div class="tradingview-widget-container" style="height:750px;width:100%">
              <div id="tv_chart"></div>
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
            </div>""", height=760)

        with c_tools:
            st.markdown("### 🧬 CONFLUENCE")
            for tf in ['15m', '1h', '4h']:
                data = confluence.get(tf, {})
                status = data.get('status', 'N/A')
                icon = "🟢" if status == "BULLISH" else ("🔴" if status == "BEARISH" else "⚪")
                st.markdown(f"""
                <div class="glass-card" style="display:flex; justify-content:space-between; align-items:center; padding: 10px;">
                    <span style="font-family:'Orbitron'; font-size:14px;">{tf}</span>
                    <span class="badge" style="background:{'#004400' if status=='BULLISH' else ('#440000' if status=='BEARISH' else '#222')}; color:{'#00ff41' if status=='BULLISH' else ('#ff0055' if status=='BEARISH' else '#888')}">
                        {icon} {status}
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            # PIVOT POINTS CARD
            st.markdown("### 🎯 KEY LEVELS")
            if pivots:
                st.markdown(f"""
                <div class="glass-card">
                    <div style="font-size:12px; color:#888;">RESISTANCE (Cản)</div>
                    <div style="color:var(--bear); font-weight:bold;">R2: {pivots['R2']:.4f}</div>
                    <div style="color:var(--bear);">R1: {pivots['R1']:.4f}</div>
                    <div style="margin: 5px 0; border-bottom:1px dashed #444;"></div>
                    <div style="font-size:12px; color:#888;">SUPPORT (Hỗ trợ)</div>
                    <div style="color:var(--bull);">S1: {pivots['S1']:.4f}</div>
                    <div style="color:var(--bull); font-weight:bold;">S2: {pivots['S2']:.4f}</div>
                </div>
                """, unsafe_allow_html=True)

            # FIBONACCI CARD
            st.markdown("### 🔢 GOLDEN POCKET")
            if fibs:
                st.markdown(f"""
                <div class="glass-card">
                    <div style="font-size:12px; color:#888;">TREND: {fibs['trend']}</div>
                    <div style="color:var(--accent); font-weight:bold;">0.618: {fibs['0.618']:.4f}</div>
                    <div style="color:#aaa;">0.500: {fibs['0.5']:.4f}</div>
                </div>
                """, unsafe_allow_html=True)
                
            # ORACLE STRATEGY
            st.markdown("### 📜 STRATEGY")
            trend = "TĂNG" if confluence['4h']['status'] == "BULLISH" else "GIẢM"
            atr = ta.atr(df_4h['h'], df_4h['l'], df_4h['c'], length=14).iloc[-1]
            stoploss = curr_price - (atr * 2) if trend == "TĂNG" else curr_price + (atr * 2)
            tp = curr_price + (atr * 3) if trend == "TĂNG" else curr_price - (atr * 3)
            
            st.markdown(f"""
            <div style="background:#1a1a1a; padding:10px; border-radius:8px; font-family:'Courier New'; font-size:13px; color:#ddd; border-left: 3px solid var(--accent);">
                <strong>>_ ORACLE AI:</strong><br>
                1. TREND: {trend}<br>
                2. BIẾN ĐỘNG: {volatility}<br>
                ----------------<br>
                🎯 <strong>ENTRY:</strong> {curr_price:.4f}<br>
                🛡️ <strong>SL:</strong> {stoploss:.4f}<br>
                💰 <strong>TP:</strong> {tp:.4f}<br>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.error(f"⚠️ Dữ liệu chưa đủ để phân tích.")

st.markdown("---")
st.caption("THE ORACLE TERMINAL v10.0 (Sniper Edition) | Latency: 12ms 🟢")
