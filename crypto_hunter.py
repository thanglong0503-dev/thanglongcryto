import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import streamlit.components.v1 as components
import numpy as np
import time

# ==============================================================================
# 1. CYBERPUNK UI CONFIGURATION (GIAO DIỆN NGẦU LÒI CŨ)
# ==============================================================================
st.set_page_config(layout="wide", page_title="CYBERPUNK TERMINAL", page_icon="🔮", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* IMPORT FONT HACKER (Orbitron & Rajdhani) */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500;700&display=swap');

    :root {
        --bg-color: #050505; /* Đen thẳm */
        --card-bg: rgba(20, 20, 20, 0.7); /* Kính mờ */
        --accent: #00e5ff; /* Cyan Neon */
        --bull: #00ffa3;   /* Green Neon */
        --bear: #ff0055;   /* Pink Neon */
        --text: #e0e0e0;
        --border: #333;
    }

    /* GLOBAL RESET */
    .stApp { background-color: var(--bg-color) !important; color: var(--text) !important; font-family: 'Rajdhani', sans-serif !important; }
    
    /* HEADER HIỆU ỨNG NEON */
    .cyber-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 36px;
        background: -webkit-linear-gradient(45deg, var(--accent), #bd00ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        text-shadow: 0 0 20px rgba(0, 229, 255, 0.6);
        letter-spacing: 2px;
    }

    /* THẺ KÍNH (GLASSMORPHISM) */
    .glass-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 4px; /* Góc cạnh hơn chút cho Cyber */
        padding: 15px;
        backdrop-filter: blur(10px);
        margin-bottom: 15px;
        transition: 0.3s;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
    }
    .glass-card:hover { 
        border-color: var(--accent); 
        box-shadow: 0 0 15px rgba(0, 229, 255, 0.3); 
    }

    /* METRICS STYLE */
    .metric-label { font-size: 12px; color: #888; letter-spacing: 2px; text-transform: uppercase; font-family: 'Orbitron'; }
    .metric-val { font-size: 28px; font-weight: bold; font-family: 'Orbitron'; color: #fff; }
    
    /* BADGES */
    .badge { padding: 4px 8px; border-radius: 2px; font-weight: bold; font-size: 12px; font-family: 'Orbitron'; letter-spacing: 1px; }

    /* INPUT & SELECTBOX (TÙY CHỈNH MÀU TỐI) */
    div[data-baseweb="input"] { background-color: #111 !important; border: 1px solid #333 !important; }
    input[type="text"] { color: var(--accent) !important; font-family: 'Orbitron' !important; text-transform: uppercase; }
    div[data-baseweb="select"] > div { background-color: #111 !important; color: #fff !important; border-color: #333 !important; }
    
    /* CUSTOM SCROLLBAR */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb { background: var(--accent); }
    ::-webkit-scrollbar-track { background: #000; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CORE ENGINE: YAHOO FINANCE (ĐỂ KHÔNG BỊ LỖI)
# ==============================================================================
class CyberEngine:
    def __init__(self):
        pass

    def fetch_data(self, symbol):
        """Lấy dữ liệu thật từ Yahoo nhưng mapping cho giống Crypto"""
        # Mapping: BTC -> BTC-USD
        yf_sym = symbol.upper().replace('/', '-')
        if not yf_sym.endswith('-USD') and 'USD' not in yf_sym:
            yf_sym += '-USD'
        
        try:
            # Tải 1 tháng dữ liệu khung 1H
            df = yf.download(yf_sym, period="1mo", interval="1h", progress=False)
            
            if df.empty: return None, "NO_DATA"
            
            # Fix MultiIndex của Yahoo
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            # Rename cho chuẩn
            df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
            
            return df, "OK"
        except Exception as e:
            return None, str(e)

    def analyze(self, df):
        if df is None: return None
        
        # Tính chỉ báo
        try:
            df.ta.bbands(length=20, std=2, append=True)
            df.ta.rsi(length=14, append=True)
            df.ta.ema(length=50, append=True)
            df.ta.ema(length=200, append=True)
            
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Lấy giá trị an toàn
            price = curr['close']
            rsi = curr.get('RSI_14', 50)
            
            # Pivot Points (Classic)
            pp = (curr['high'] + curr['low'] + curr['close']) / 3
            r1 = (2 * pp) - curr['low']
            s1 = (2 * pp) - curr['high']
            
            # Tín hiệu
            signal = "NEUTRAL"
            verdict_color = "#888"
            
            # Logic đơn giản nhưng hiệu quả
            if 'EMA_50' in curr and 'EMA_200' in curr:
                if price > curr['EMA_50'] and curr['EMA_50'] > curr['EMA_200']:
                    signal = "STRONG UPTREND 🚀"
                    verdict_color = "var(--bull)"
                elif price < curr['EMA_50'] and curr['EMA_50'] < curr['EMA_200']:
                    signal = "STRONG DOWNTREND 🩸"
                    verdict_color = "var(--bear)"
            
            # RSI Overrides
            if rsi < 30: 
                signal = "OVERSOLD (BUY DIP) ⚡"
                verdict_color = "var(--accent)"
            elif rsi > 70:
                signal = "OVERBOUGHT (CAUTION) ⚠️"
                verdict_color = "#ff9100"

            return {
                "price": price,
                "change": (price - prev['close']) / prev['close'] * 100,
                "rsi": rsi,
                "signal": signal,
                "color": verdict_color,
                "r1": r1,
                "s1": s1,
                "vol_state": "SQUEEZE" if (curr.get('BBU_20_2.0', 0) - curr.get('BBL_20_2.0', 0)) < (price * 0.02) else "NORMAL"
            }
        except: return None

engine = CyberEngine()

# ==============================================================================
# 3. UI DASHBOARD (CYBERPUNK STYLE)
# ==============================================================================

# HEADER
c1, c2 = st.columns([1, 5])
with c1: st.markdown("## 🔮")
with c2: st.markdown('<div class="cyber-header">CYBER ORACLE v16</div>', unsafe_allow_html=True)

# INPUT BAR
col_search, col_list = st.columns([2, 1])
with col_search:
    manual = st.text_input("NETRUNNER INPUT", value="BTC", placeholder="TYPE SYMBOL...", label_visibility="collapsed")
with col_list:
    st.markdown("""
    <div style="text-align:right; font-family:'Orbitron'; color:var(--accent); padding-top:10px;">
        SYSTEM STATUS: ONLINE 🟢
    </div>
    """, unsafe_allow_html=True)

symbol = manual.upper()

# --- MAIN LOGIC ---
st.write("---")

with st.spinner(f"🔮 DECODING MATRIX FOR {symbol}..."):
    # 1. Fetch
    df, status = engine.fetch_data(symbol)
    
    if df is not None:
        data = engine.analyze(df)
        
        if data:
            # --- ROW 1: METRICS (GLASS CARDS) ---
            m1, m2, m3, m4 = st.columns(4)
            
            with m1:
                st.markdown(f"""
                <div class="glass-card">
                    <div class="metric-label">CURRENT PRICE</div>
                    <div class="metric-val" style="color:var(--accent);">${data['price']:,.2f}</div>
                </div>""", unsafe_allow_html=True)
            
            with m2:
                # Signal Box
                st.markdown(f"""
                <div class="glass-card" style="border: 1px solid {data['color']}; box-shadow: 0 0 10px {data['color']}40;">
                    <div class="metric-label">AI VERDICT</div>
                    <div class="metric-val" style="color:{data['color']}; font-size:20px;">{data['signal']}</div>
                </div>""", unsafe_allow_html=True)
                
            with m3:
                # RSI
                rsi_col = "var(--bull)" if data['rsi'] < 30 else ("var(--bear)" if data['rsi'] > 70 else "#fff")
                st.markdown(f"""
                <div class="glass-card">
                    <div class="metric-label">RSI INDEX</div>
                    <div class="metric-val" style="color:{rsi_col}">{data['rsi']:.1f}</div>
                </div>""", unsafe_allow_html=True)
                
            with m4:
                # Volatility
                st.markdown(f"""
                <div class="glass-card">
                    <div class="metric-label">VOLATILITY</div>
                    <div class="metric-val" style="font-size:20px;">{data['vol_state']}</div>
                </div>""", unsafe_allow_html=True)

            # --- ROW 2: GIANT CHART & STRATEGY ---
            c_chart, c_tools = st.columns([3, 1])
            
            with c_chart:
                st.markdown(f"### 📉 {symbol} VISUAL INTERFACE")
                # Mapping Symbol cho TradingView (Luôn dùng BINANCE cho đẹp nếu là Crypto)
                tv_symbol = f"BINANCE:{symbol}USDT"
                
                # Biểu đồ IMAX 900px
                components.html(f"""
                <div class="tradingview-widget-container" style="height:900px;width:100%">
                  <div id="tv_chart" style="height:100%;width:100%"></div>
                  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                  <script type="text/javascript">
                  new TradingView.widget({{
                  "autosize": true,
                  "symbol": "{tv_symbol}",
                  "interval": "60",
                  "timezone": "Asia/Ho_Chi_Minh",
                  "theme": "dark",
                  "style": "1",
                  "locale": "en",
                  "toolbar_bg": "#f1f3f6",
                  "enable_publishing": false,
                  "backgroundColor": "#050505", /* Màu nền đen Cyberpunk */
                  "gridColor": "rgba(0, 229, 255, 0.1)", /* Lưới màu Cyan nhạt */
                  "hide_top_toolbar": false,
                  "save_image": false,
                  "container_id": "tv_chart",
                  "studies": [
                    "SuperTrend@tv-basicstudies",
                    "MACD@tv-basicstudies",
                    "BB@tv-basicstudies"
                  ]
                  }});
                  </script>
                </div>
                """, height=910)
            
            with c_tools:
                st.markdown("### 🧬 KEY LEVELS")
                
                # Resistance Card
                st.markdown(f"""
                <div class="glass-card">
                    <div style="font-size:12px; color:#888;">RESISTANCE (R1)</div>
                    <div style="font-family:'Orbitron'; font-size:20px; color:var(--bear); font-weight:bold;">
                        ${data['r1']:,.2f}
                    </div>
                    <div style="margin:10px 0; border-bottom:1px dashed #444;"></div>
                    <div style="font-size:12px; color:#888;">SUPPORT (S1)</div>
                    <div style="font-family:'Orbitron'; font-size:20px; color:var(--bull); font-weight:bold;">
                        ${data['s1']:,.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Strategy Report
                st.markdown("### 📜 STRATEGY LOG")
                atr_sim = data['price'] * 0.02 # Giả lập ATR 2%
                sl = data['price'] - atr_sim if "UP" in data['signal'] else data['price'] + atr_sim
                tp = data['price'] + (atr_sim*2) if "UP" in data['signal'] else data['price'] - (atr_sim*2)
                
                st.markdown(f"""
                <div style="background:#111; padding:15px; border-radius:4px; border-left: 3px solid var(--accent); font-family:'Courier New'; color:#ccc; font-size:13px;">
                    <strong>>_ ORACLE PROTOCOL:</strong><br><br>
                    TARGET: {symbol}<br>
                    STATUS: {data['signal']}<br>
                    ----------------<br>
                    🎯 ENTRY: {data['price']:.2f}<br>
                    🛡️ SL: {sl:.2f}<br>
                    💰 TP: {tp:.2f}<br>
                </div>
                """, unsafe_allow_html=True)
                
                # Quick Action
                st.markdown("### ⚡ QUICK SCAN")
                if data['rsi'] < 30:
                    st.info("⚠️ OVERSOLD ALERT: Canh Buy ngay!")
                elif data['rsi'] > 70:
                    st.warning("⚠️ OVERBOUGHT: Coi chừng xả hàng!")
                else:
                    st.caption("Market is Stable.")

    else:
        st.error(f"❌ CONNECTION LOST: {status}")
        st.caption("Try symbols like: BTC, ETH, DOGE, SOL...")

st.markdown("---")
st.caption("CYBER ORACLE v16 | Powered by Yahoo Finance Core | No-Crash Guarantee")
