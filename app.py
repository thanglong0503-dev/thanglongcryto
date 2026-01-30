import streamlit as st
import pandas as pd
import time

# --- 1. SETUP TRANG (PHẢI Ở DÒNG ĐẦU TIÊN) ---
st.set_page_config(page_title="CYBER COMMANDER", layout="wide", page_icon="💠")

# --- 2. IMPORT BACKEND (ĐÃ CHỈNH SỬA TÊN CHO KHỚP VỚI CÁC FILE MỚI) ---
try:
    from backend.data_loader import fetch_data, fetch_global_indices
    from backend.logic import analyze_market, create_battle_plan_html
    # Import 2 file mới chúng ta vừa tạo:
    from backend.plot_engine import create_chart 
    from backend.ai_forecast import prophet_forecast
    # Import News (Nếu có lỗi thì bỏ qua)
    try:
        from backend.news_engine import fetch_crypto_news
    except:
        fetch_crypto_news = None
except Exception as e:
    st.error(f"⚠️ SYSTEM ERROR: {e}")
    st.stop()

# --- 3. CSS GIAO DIỆN (CYBERPUNK THEME) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Share+Tech+Mono&display=swap');
    
    /* NỀN TỐI */
    .stApp { background-color: #050505; color: #e0e0e0; }
    
    /* FONT CHỮ */
    h1, h2, h3 { font-family: 'Orbitron', sans-serif !important; color: #00b4ff; text-shadow: 0 0 10px rgba(0, 180, 255, 0.5); }
    div, p, span { font-family: 'Share Tech Mono', monospace; }
    
    /* THẺ METRIC */
    .glass-card {
        background: rgba(20, 20, 20, 0.7);
        border: 1px solid #333;
        border-radius: 8px;
        padding: 15px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 10px;
    }
    .metric-label { font-size: 12px; color: #888; letter-spacing: 1px; }
    .metric-val { font-size: 24px; font-weight: bold; font-family: 'Orbitron'; margin-top: 5px; }
    
    /* HEADER HIỆU ỨNG GLITCH */
    .glitch-header {
        font-size: 36px; font-weight: bold; color: #fff;
        text-shadow: 2px 2px #ff0055, -2px -2px #00ff9f;
        animation: glitch 1s infinite alternate;
    }
    @keyframes glitch {
        0% { text-shadow: 2px 2px #ff0055, -2px -2px #00ff9f; }
        100% { text-shadow: -2px -2px #ff0055, 2px 2px #00ff9f; }
    }
</style>
""", unsafe_allow_html=True)

# --- 4. SIDEBAR (MENU BÊN TRÁI) ---
with st.sidebar:
    st.markdown('<div class="glitch-header" style="font-size:24px; margin-bottom:20px">CYBER<br>ORACLE</div>', unsafe_allow_html=True)
    
    # MENU CHÍNH
    mode = st.radio("SYSTEM MODE", ["💠 DEEP SCANNER", "📰 NEWS RADAR"], label_visibility="collapsed")
    st.markdown("---")
    
    # DỮ LIỆU VĨ MÔ
    st.caption("MACRO DATA STREAM")
    macro = fetch_global_indices()
    if macro:
        for name, d in macro.items():
            color = "#00ff9f" if d['change'] >= 0 else "#ff0055"
            st.markdown(f"""
            <div style="border-left:2px solid {color}; padding-left:8px; margin-bottom:8px">
                <div style="font-size:10px; color:#888">{name}</div>
                <div style="font-size:14px; color:#fff">{d['price']}</div>
            </div>
            """, unsafe_allow_html=True)

# ==============================================================================
# MODE 1: DEEP SCANNER (CHỨC NĂNG CHÍNH)
# ==============================================================================
if mode == "💠 DEEP SCANNER":
    st.markdown('<div class="glitch-header">💠 DEEP SCANNER</div>', unsafe_allow_html=True)
    
    # 1. THANH TÌM KIẾM
    col_search, col_pad = st.columns([1, 2])
    with col_search:
        # Danh sách tài sản hỗn hợp (Crypto + Vàng + Dầu)
        ASSETS = [
            "BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", # Crypto
            "GC=F", "SI=F", "CL=F", "^GSPC", "EURUSD=X" # Macro
        ]
        selected_asset = st.selectbox("SELECT ASSET", ASSETS + ["...CUSTOM..."], label_visibility="collapsed")
        
        if selected_asset == "...CUSTOM...":
            symbol = st.text_input("TYPE SYMBOL", "BTC").upper()
        else:
            symbol = selected_asset
            
    st.write("---")

    # 2. XỬ LÝ DỮ LIỆU
    with st.spinner(f"⚡ DECRYPTING {symbol}..."):
        # Tải dữ liệu
        df, status = fetch_data(symbol)
        
        # --- FIX: Tự động tải thêm dữ liệu nếu thiếu để chạy AI ---
        if df is not None and len(df) < 500:
            try:
                import requests
                clean_sym = symbol.replace('USDT','') + 'USDT'
                url = f"https://api.binance.com/api/v3/klines?symbol={clean_sym}&interval=1h&limit=1000"
                res = requests.get(url, timeout=2).json()
                if isinstance(res, list) and len(res) > 0:
                    df_fix = pd.DataFrame(res, columns=['t', 'open', 'high', 'low', 'close', 'volume', 'T', 'q', 'n', 'V', 'Q', 'B'])
                    df_fix['t'] = pd.to_datetime(df_fix['t'], unit='ms')
                    df_fix.set_index('t', inplace=True)
                    df_fix[['open','high','low','close','volume']] = df_fix[['open','high','low','close','volume']].astype(float)
                    df = df_fix
            except: pass
        # ---------------------------------------------------------

        if df is not None:
            # A. PHÂN TÍCH LOGIC
            plan = analyze_market(df)
            
            if plan:
                # B. HIỂN THỊ 4 METRICS TRÊN CÙNG
                m1, m2, m3, m4 = st.columns(4)
                with m1: st.markdown(f'<div class="glass-card"><div class="metric-label">PRICE</div><div class="metric-val" style="color:var(--neon-cyan)">${plan["price"]:,.2f}</div></div>', unsafe_allow_html=True)
                with m2: st.markdown(f'<div class="glass-card" style="border:1px solid {plan["color"]}"><div class="metric-label" style="color:{plan["color"]}">VERDICT</div><div class="metric-val" style="color:{plan["color"]}">{plan["signal"]}</div></div>', unsafe_allow_html=True)
                with m3: st.markdown(f'<div class="glass-card"><div class="metric-label">POC (VOLUME)</div><div class="metric-val" style="color:#ff0055">${plan["poc"]:,.2f}</div></div>', unsafe_allow_html=True)
                with m4: st.markdown(f'<div class="glass-card"><div class="metric-label">RSI (14)</div><div class="metric-val" style="color:#fff">{plan["rsi"]:.1f}</div></div>', unsafe_allow_html=True)

                st.write("---")

                # C. VẼ BIỂU ĐỒ (Gọi hàm từ plot_engine.py)
                try:
                    fig = create_chart(df, symbol)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"CHART ERROR: {e}")

                st.write("---")

                # D. KHU VỰC CHIẾN LƯỢC & AI
                c1, c2 = st.columns([1, 2])
                
                with c1:
                    st.markdown('<div class="metric-label">_ BATTLE PLAN</div>', unsafe_allow_html=True)
                    st.markdown(create_battle_plan_html(plan), unsafe_allow_html=True)
                    
                with c2:
                    st.markdown('<div class="metric-label">🔮 AI PROPHET (FUTURE VISION)</div>', unsafe_allow_html=True)
                    days = st.selectbox("FORECAST RANGE", [1, 3, 7], format_func=lambda x: f"{x * 24} Hours", label_visibility="collapsed")
                    
                    if st.button(f"RUN PREDICTION ({days*24}H)"):
                        try:
                            # Gọi hàm từ ai_forecast.py
                            fig_ai, text_ai = prophet_forecast(df, days)
                            st.plotly_chart(fig_ai, use_container_width=True)
                            st.info(text_ai)
                        except Exception as e:
                            st.error(f"AI ERROR: {e}")
            else:
                st.error("⚠️ DATA ERROR: Cannot analyze market structure.")
        else:
            st.error(f"❌ CONNECTION FAILED: Could not fetch data for {symbol}")

# ==============================================================================
# MODE 2: NEWS RADAR (TIN TỨC)
# ==============================================================================
elif mode == "📰 NEWS RADAR":
    st.markdown('<div class="glitch-header">📰 GLOBAL NEWS SENTIMENT</div>', unsafe_allow_html=True)
    if st.button("🔄 SCAN LATEST NEWS"):
        st.cache_data.clear()
        
    if fetch_crypto_news:
        news_df, mood, score = fetch_crypto_news()
        if not news_df.empty:
            color = "#00ff9f" if score > 0 else "#ff0055"
            st.markdown(f'<h2 style="color:{color}">MARKET MOOD: {mood}</h2>', unsafe_allow_html=True)
            for i, row in news_df.iterrows():
                st.markdown(f"**{row['source']}**: [{row['title']}]({row['link']}) ({row['sentiment']})")
        else:
            st.warning("No news signals intercepted.")
    else:
        st.info("News module is initializing...")
