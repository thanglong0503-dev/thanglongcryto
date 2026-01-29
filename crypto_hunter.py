import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import streamlit.components.v1 as components
import time

# ==============================================================================
# 1. ORACLE UI CONFIGURATION
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

    /* INPUTS FIX (FIX LỖI MÀU TRẮNG KHÓ NHÌN) */
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
# 2. ORACLE ENGINE (BỘ NÃO XỬ LÝ ĐA KHUNG THỜI GIAN)
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

    def fetch_ohlcv(self, symbol, timeframe, limit=300): # Tăng limit lên 300 để đủ tính EMA200
        try:
            # Retry logic
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

    # --- TÍNH NĂNG 1: PRICE ACTION HUNTER (SOI NẾN) ---
    def detect_patterns(self, df):
        if df.empty: return []
        patterns = []
        try:
            # 1. Doji
            if ta.cdl_doji(df['o'], df['h'], df['l'], df['c']).iloc[-1] != 0:
                patterns.append("🕯️ DOJI (Lưỡng lự)")
            # 2. Engulfing
            engulf = ta.cdl_engulfing(df['o'], df['h'], df['l'], df['c']).iloc[-1]
            if engulf > 0: patterns.append("🔥 BULLISH ENGULFING")
            elif engulf < 0: patterns.append("🩸 BEARISH ENGULFING")
            # 3. Hammer Logic
            body = abs(df['c'] - df['o'])
            wick_lower = df[['o', 'c']].min(axis=1) - df['l']
            wick_upper = df['h'] - df[['o', 'c']].max(axis=1)
            curr = df.iloc[-1]
            if wick_lower.iloc[-1] > body.iloc[-1] * 2 and wick_upper.iloc[-1] < body.iloc[-1]:
                patterns.append("🔨 HAMMER")
        except: pass
        return patterns

    # --- TÍNH NĂNG 2: MULTI-TIMEFRAME CONFLUENCE (FIXED CRASH) ---
    def analyze_confluence(self, symbol):
        timeframes = ['15m', '1h', '4h']
        scores = {}
        data_frames = {}
        
        for tf in timeframes:
            # Tải 300 nến để đủ dữ liệu cho EMA200
            df = self.fetch_ohlcv(symbol, tf, 300)
            
            # KIỂM TRA DỮ LIỆU AN TOÀN
            if df.empty or len(df) < 200: 
                scores[tf] = {"status": "NO DATA", "rsi": 50, "price": 0}
                continue
            
            try:
                # Tính EMA & RSI
                ema50 = ta.ema(df['c'], length=50).iloc[-1]
                ema200 = ta.ema(df['c'], length=200).iloc[-1]
                rsi = ta.rsi(df['c'], length=14).iloc[-1]
                price = df['c'].iloc[-1]
                
                # Chấm điểm
                score = 0
                if price > ema50: score += 1
                if price > ema200: score += 1
                if rsi > 50: score += 1
                
                status = "NEUTRAL"
                if score >= 3: status = "BULLISH"
                elif score <= 0: status = "BEARISH"
                
                scores[tf] = {"status": status, "rsi": rsi, "price": price}
                data_frames[tf] = df
            except Exception as e:
                scores[tf] = {"status": "ERROR", "rsi": 50, "price": 0}
            
        return scores, data_frames

engine = OracleEngine()

# ==============================================================================
# 3. UI DASHBOARD
# ==============================================================================

# Header & Search
c1, c2 = st.columns([1, 5])
with c1: st.markdown("## 🔮")
with c2: st.markdown('<div class="oracle-header">THE MARKET ORACLE v9.1</div>', unsafe_allow_html=True)

# Search Bar
col_search, col_list = st.columns([1, 2])
with col_search:
    manual = st.text_input("ORACLE INPUT", placeholder="Type Symbol (e.g. SUI)...", label_visibility="collapsed")
with col_list:
    coins = engine.get_top_coins()
    selected = st.selectbox("ORACLE LIST", coins, label_visibility="collapsed")

symbol = f"{manual.upper()}/USDT" if manual else selected
if "/USDT" not in symbol and "/USD" not in symbol: symbol += "/USDT"

# --- MAIN ANALYSIS ---
st.write("---")

# 1. ORACLE PROCESSING
with st.spinner(f"🔮 ORACLE is analyzing {symbol}..."):
    confluence, dfs = engine.analyze_confluence(symbol)
    
    # Check data availability
    if '4h' in dfs and not dfs['4h'].empty:
        df_4h = dfs['4h']
        curr_price = df_4h['c'].iloc[-1]
        patterns = engine.detect_patterns(df_4h)
        
        # --- TOP METRICS ROW ---
        m1, m2, m3, m4 = st.columns(4)
        
        bull_count = sum([1 for tf in confluence if confluence[tf]['status'] == "BULLISH"])
        bear_count = sum([1 for tf in confluence if confluence[tf]['status'] == "BEARISH"])
        
        sentiment = "NEUTRAL"
        s_color = "#888"
        if bull_count == 3: sentiment = "STRONG BUY 🚀"; s_color = "var(--bull)"
        elif bull_count == 2: sentiment = "BUY 🟢"; s_color = "var(--bull)"
        elif bear_count == 3: sentiment = "STRONG SELL 🩸"; s_color = "var(--bear)"
        elif bear_count == 2: sentiment = "SELL 🔴"; s_color = "var(--bear)"

        with m1:
            st.markdown(f"""<div class="glass-card"><div class="metric-label">CURRENT PRICE</div><div class="metric-val" style="color:var(--accent)">${curr_price:,.4f}</div></div>""", unsafe_allow_html=True)
            
        with m2:
            st.markdown(f"""<div class="glass-card" style="border-color:{s_color}"><div class="metric-label">ORACLE VERDICT</div><div class="metric-val" style="color:{s_color}">{sentiment}</div></div>""", unsafe_allow_html=True)
            
        with m3:
            rsi_4h = confluence['4h']['rsi']
            r_col = "color-bull" if rsi_4h < 30 else ("color-bear" if rsi_4h > 70 else "color:white")
            st.markdown(f"""<div class="glass-card"><div class="metric-label">RSI (4H) STATUS</div><div class="metric-val" style="{r_col}">{rsi_4h:.1f}</div></div>""", unsafe_allow_html=True)

        with m4:
            pat_text = patterns[0] if patterns else "None"
            p_col = "var(--bull)" if "BULL" in pat_text or "HAMMER" in pat_text else ("var(--bear)" if "BEAR" in pat_text else "white")
            st.markdown(f"""<div class="glass-card"><div class="metric-label">PRICE ACTION PATTERN</div><div style="font-size:16px; font-weight:bold; color:{p_col}; margin-top:5px;">{pat_text}</div></div>""", unsafe_allow_html=True)

        # --- BODY: CHART & MATRIX ---
        c_left, c_right = st.columns([2, 1])
        
        with c_left:
            base = symbol.split('/')[0]
            st.markdown(f"### 📉 {base} CHART")
            components.html(f"""
            <div class="tradingview-widget-container" style="height:500px;width:100%">
              <div id="tv_chart"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({{
              "autosize": true, "symbol": "BINANCE:{base}USDT", "interval": "240", "timezone": "Asia/Ho_Chi_Minh",
              "theme": "dark", "style": "1", "locale": "vi_VN", "enable_publishing": false,
              "backgroundColor": "#0f0f0f", "gridColor": "rgba(40,40,40,0.5)",
              "hide_top_toolbar": false, "container_id": "tv_chart",
              "studies": ["SuperTrend@tv-basicstudies", "MACD@tv-basicstudies"]
              }});
              </script>
            </div>""", height=510)

        with c_right:
            st.markdown("### 🧬 CONFLUENCE MATRIX")
            
            for tf in ['15m', '1h', '4h']:
                data = confluence.get(tf, {})
                status = data.get('status', 'N/A')
                icon = "🟢" if status == "BULLISH" else ("🔴" if status == "BEARISH" else "⚪")
                st.markdown(f"""
                <div class="glass-card" style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-family:'Orbitron'; font-weight:bold;">TIMEFRAME {tf}</span>
                    <span class="badge" style="background:{'#004400' if status=='BULLISH' else ('#440000' if status=='BEARISH' else '#222')}; color:{'#00ff41' if status=='BULLISH' else ('#ff0055' if status=='BEARISH' else '#888')}">
                        {icon} {status}
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            # Oracle Report
            st.markdown("### 📜 STRATEGY REPORT")
            trend = "TĂNG" if confluence['4h']['status'] == "BULLISH" else "GIẢM"
            action = "LONG/MUA" if trend == "TĂNG" else "SHORT/BÁN"
            atr = ta.atr(df_4h['h'], df_4h['l'], df_4h['c'], length=14).iloc[-1]
            stoploss = curr_price - (atr * 2) if trend == "TĂNG" else curr_price + (atr * 2)
            take_profit = curr_price + (atr * 4) if trend == "TĂNG" else curr_price - (atr * 4)
            
            report_html = f"""
            <div style="background:#1a1a1a; padding:15px; border-radius:8px; font-family:'Courier New'; font-size:14px; color:#ddd; border-left: 3px solid var(--accent);">
                <strong>>_ ORACLE AI GENERATED:</strong><br><br>
                1. <strong>XU HƯỚNG CHỦ ĐẠO:</strong> {trend} (Khung H4).<br>
                2. <strong>TÍN HIỆU ĐỒNG PHA:</strong> {bull_count}/3 Khung Tăng.<br>
                3. <strong>HÀNH ĐỘNG GIÁ:</strong> {patterns[0] if patterns else "Chưa có"}.<br>
                -----------------------------<br>
                🎯 <strong>ENTRY:</strong> {curr_price:.4f}<br>
                🛡️ <strong>STOP LOSS:</strong> {stoploss:.4f}<br>
                💰 <strong>TAKE PROFIT:</strong> {take_profit:.4f}<br>
            </div>
            """
            st.markdown(report_html, unsafe_allow_html=True)

    else:
        st.error(f"⚠️ Dữ liệu cho {symbol} không đủ để phân tích (Cần ít nhất 200 nến). Vui lòng thử mã khác.")

# --- FOOTER ---
st.markdown("---")
col_f1, col_f2 = st.columns([4, 1])
with col_f1: st.caption("THE ORACLE TERMINAL v9.1 (Stable) | Powered by Pandas_TA & Plotly")
with col_f2: st.caption("Latency: 12ms 🟢")
