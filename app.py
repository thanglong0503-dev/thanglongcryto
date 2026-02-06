import streamlit as st
import time
# Tìm dòng cũ: from backend.ai_forecast import run_prophet_forecast, plot_prophet_chart
# Thay bằng:
from backend.ai_forecast import run_ai_forecast, plot_ai_chart
# IMPORT MODULES
from frontend.styles import get_cyberpunk_css
from frontend.charts import render_chart
from backend.data_loader import fetch_data, fetch_global_indices, fetch_market_overview
from backend.logic import analyze_market

# 1. CẤU HÌNH TRANG
# Thay 🔮 bằng 💠
st.set_page_config(layout="wide", page_title="CYBER COMMANDER V42", page_icon="💠", initial_sidebar_state="expanded")
st.markdown(get_cyberpunk_css(), unsafe_allow_html=True)

def create_battle_plan_html(data):
    """
    V42 HTML: HIỂN THỊ 2 CHIẾN THUẬT (SWING & SCALP)
    """
    # --- 1. CHUẨN BỊ SỐ LIỆU SWING ---
    sw_entry = f"${data['swing_entry_low']:,.0f} - ${data['swing_entry_high']:,.0f}"
    sw_stop = f"${data['swing_sl']:,.2f}"
    sw_target = f"${data['swing_tp']:,.2f}"
    
    try:
        sw_risk = abs((data['swing_entry_high'] - data['swing_sl']) / data['swing_entry_high'] * 100)
        sw_reward = abs((data['swing_tp'] - data['swing_entry_high']) / data['swing_entry_high'] * 100)
    except: sw_risk = sw_reward = 0

    # --- 2. CHUẨN BỊ SỐ LIỆU SCALP ---
    sc_entry = f"${data['scalp_entry']:,.2f}"
    sc_stop = f"${data['scalp_sl']:,.2f}"
    sc_target = f"${data['scalp_tp']:,.2f}"
    
    # Màu sắc riêng cho Scalp (Vàng Neon cho nổi)
    c_scalp = "#fcee0a" 

    # --- 3. HTML CODE (VIẾT PHẲNG - KHÔNG THỤT DÒNG ĐỂ TRÁNH LỖI) ---
    return f"""
<div class="glass-card" style="border-left: 3px solid {data['color']};">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px">
<div class="metric-label" style="color:{data['color']}">🌊 SWING SETUP (DÀI HẠN)</div>
<div style="font-size:9px; background:#333; padding:2px 5px; border-radius:3px;">R:R 1:3</div>
</div>
<div style="font-family:'Share Tech Mono'; font-size:13px; color:#bbb; margin-bottom:15px">
<div style="background:rgba(255,255,255,0.05); padding:5px; border-radius:4px; margin-bottom:5px">
<div style="font-size:9px; color:#888">ENTRY ZONE (LIMIT)</div>
<strong style="color:#fff">{sw_entry}</strong>
</div>
<div style="display:flex; justify-content:space-between;">
<div><span style="color:#ff0055">SL: {sw_stop}</span> <span style="font-size:9px; color:#666">(-{sw_risk:.1f}%)</span></div>
<div><span style="color:#00ff9f">TP: {sw_target}</span> <span style="font-size:9px; color:#666">(+{sw_reward:.1f}%)</span></div>
</div>
</div>
<hr style="border-color:#444; border-style:dashed; margin:10px 0">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px">
<div class="metric-label" style="color:{c_scalp}">⚡ SCALP SETUP (TRONG NGÀY)</div>
<div style="font-size:9px; background:#333; padding:2px 5px; border-radius:3px; color:{c_scalp}">R:R 1:1.5</div>
</div>
<div style="font-family:'Share Tech Mono'; font-size:13px; color:#bbb;">
<div style="display:flex; justify-content:space-between; margin-bottom:4px">
<span>ENTRY (MARKET):</span> <span style="color:#fff">{sc_entry}</span>
</div>
<div style="display:flex; justify-content:space-between; margin-bottom:4px">
<span>STOP LOSS:</span> <span style="color:#ff0055">{sc_stop}</span>
</div>
<div style="display:flex; justify-content:space-between;">
<span>TAKE PROFIT:</span> <span style="color:#00ff9f">{sc_target}</span>
</div>
</div>
</div>
"""

def create_oscillators_html(data):
    c_stoch = 'var(--neon-green)' if data['stoch_k'] < 20 else '#fff'
    str_rsi = f"{data['rsi']:.1f}"
    str_stoch = f"{data['stoch_k']:.1f}"
    
    return f"""
    <div class="glass-card">
        <div class="metric-label">OSCILLATORS</div>
        <div style="margin-top:10px; font-family:'Share Tech Mono'; color:#ccc; font-size:14px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span>RSI (14)</span> <span>{str_rsi}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span>Stoch K</span> <span style="color:{c_stoch}">{str_stoch}</span>
            </div>
            <div style="height:1px; background:#333; margin:10px 0;"></div>
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span>TREND</span> <span>{data['trend']}</span>
            </div>
        </div>
    </div>
    """

# 2. POPUP CHART & DATA
@st.dialog("TACTICAL VIEW", width="large")
def show_popup_data(symbol):
    st.markdown(f'<div class="glitch-header" style="font-size:30px; margin-bottom:10px">{symbol}</div>', unsafe_allow_html=True)
    
    with st.spinner("CALCULATING STRATEGY..."):
        df, status = fetch_data(symbol)
        
    if df is not None:
        data = analyze_market(df)
        if data:
            c_signal = data['color']
            str_price = f"${data['price']:,.2f}"
            str_poc = f"${data['poc']:,.2f}"
            
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"""<div class="glass-card"><div class="metric-label">CURRENT PRICE</div><div class="metric-val">{str_price}</div></div>""", unsafe_allow_html=True)
            with c2: st.markdown(f"""<div class="glass-card" style="border-color:{c_signal}"><div class="metric-label" style="color:{c_signal}">AI SIGNAL</div><div class="metric-val" style="color:{c_signal}">{data['signal']}</div></div>""", unsafe_allow_html=True)
            with c3: st.markdown(f"""<div class="glass-card"><div class="metric-label">POINT OF CONTROL</div><div class="metric-val" style="color:#ff0055">{str_poc}</div></div>""", unsafe_allow_html=True)
            
            c_chart, c_plan = st.columns([2, 1])
            with c_chart: render_chart(symbol, height=500)
            with c_plan:
                st.markdown(create_oscillators_html(data), unsafe_allow_html=True)
                st.markdown(create_battle_plan_html(data), unsafe_allow_html=True)
    else:
        st.error("DATA FEED LOST")

# 3. SIDEBAR
with st.sidebar:
    st.markdown('<div class="glitch-header" style="font-size:24px; margin-bottom:20px">CYBER<br>ORACLE</div>', unsafe_allow_html=True)
    # Thêm "📰 NEWS RADAR" vào danh sách chọn
    mode = st.radio("SYSTEM MODE", ["🌐 MARKET GRID", "💠 DEEP SCANNER", "📰 NEWS RADAR", "🐋 WHALE TRACKER"], label_visibility="collapsed")
    st.markdown("---")
    st.caption("MACRO DATA STREAM")
    macro = fetch_global_indices()
    if macro:
        for name, d in macro.items():
            col_c = "#00ffa3" if d['change'] >= 0 else "#ff0055"
            icon = "▲" if d['change'] >= 0 else "▼"
            st.markdown(f"""
            <div style="margin-bottom:10px; border-left:2px solid {col_c}; padding-left:8px">
                <div style="font-family:'Share Tech Mono'; font-size:10px; color:#888">{name}</div>
                <div style="font-family:'Orbitron'; font-size:14px; color:#fff">{d['price']}</div>
                <div style="font-family:'Share Tech Mono'; font-size:11px; color:{col_c}">{icon} {d['change']:.2f}%</div>
            </div>""", unsafe_allow_html=True)

# ==============================================================================
# MODE 1: MARKET GRID
# ==============================================================================
if mode == "🌐 MARKET GRID":
    st.markdown('<div class="glitch-header">GLOBAL MARKET MONITOR</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([6, 1])
    with c1: st.caption("LIVE FEED | CLICK 'SCAN' FOR BATTLE PLAN")
    with c2: 
        if st.button("🔄 REFRESH"): st.rerun()

    df = fetch_market_overview()
    if df is not None:
        st.markdown("""
        <div style="display:flex; padding:10px; background:#000; border-bottom:1px solid #333; color:#666; font-family:'Share Tech Mono'; font-size:12px">
            <div style="width:10%">ASSET</div>
            <div style="width:20%; text-align:right">PRICE</div>
            <div style="width:15%; text-align:right">24H %</div>
            <div style="width:15%; text-align:right">VOL (24H)</div>
            <div style="width:15%; text-align:right">M.CAP</div>
            <div style="width:10%; text-align:center">TREND</div>
            <div style="width:15%; text-align:right">ACTION</div>
        </div>""", unsafe_allow_html=True)

        for index, row in df.iterrows():
            sym = row['SYMBOL']
            price = row['PRICE ($)']
            change = row['24H %']
            trend = row['TREND']
            vol = row.get('VOL', '---')
            cap = row.get('CAP', '---')
            color = "#00ffa3" if change >= 0 else "#ff0055"
            
            c_asset, c_price, c_change, c_vol, c_cap, c_trend, c_btn = st.columns([1.0, 2.0, 1.5, 1.5, 1.5, 1.0, 1.5])
            
            with c_asset: st.markdown(f"<div style='font-family:Orbitron; font-weight:bold; color:#fff; padding-top:12px'>{sym}</div>", unsafe_allow_html=True)
            with c_price: st.markdown(f"<div style='font-family:Share Tech Mono; text-align:right; font-size:16px; color:#e0e0e0; padding-top:12px'>${price:,.4f}</div>", unsafe_allow_html=True)
            with c_change: st.markdown(f"<div style='font-family:Share Tech Mono; text-align:right; color:{color}; padding-top:12px'>{change:+.2f}%</div>", unsafe_allow_html=True)
            with c_vol: st.markdown(f"<div style='font-family:Share Tech Mono; text-align:right; color:#888; padding-top:12px; font-size:14px'>{vol}</div>", unsafe_allow_html=True)
            with c_cap: st.markdown(f"<div style='font-family:Share Tech Mono; text-align:right; color:#aaa; padding-top:12px; font-size:14px'>{cap}</div>", unsafe_allow_html=True)
            with c_trend: st.markdown(f"<div style='text-align:center; font-size:18px; padding-top:8px'>{trend}</div>", unsafe_allow_html=True)
            with c_btn:
                if st.button(f"⚡ SCAN", key=f"btn_{sym}"): show_popup_data(sym)
            st.markdown("<div style='height:1px; background:#111; margin:0'></div>", unsafe_allow_html=True)

# ==============================================================================
# ==============================================================================
# MODE 2: DEEP SCANNER (V38: TELESCOPE MODE)
# ==============================================================================
elif mode == "💠 DEEP SCANNER":
    st.markdown('<div class="glitch-header">DEEP SCANNER</div>', unsafe_allow_html=True)
    
    col_search, col_pad = st.columns([1, 2])
    with col_search:
        # --- 1. DANH SÁCH CRYPTO (MỞ RỘNG) ---
        CRYPTO = [
            "BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK", "TRX", "TON",
            "PEPE", "SHIB", "WIF", "BONK", "FLOKI", "BOME",
            "SUI", "NEAR", "APT", "DOT", "LTC", "ARB", "OP", "TIA", "SEI", "INJ"
        ]
        
        # --- 2. DANH SÁCH VÀNG & CHỨNG KHOÁN (YAHOO TICKERS) ---
        MACRO = [
            "GC=F",     # 🥇 VÀNG (Gold Futures)
            "SI=F",     # 🥈 BẠC (Silver Futures)
            "CL=F",     # 🛢️ DẦU (Crude Oil)
            "^GSPC",    # 🇺🇸 S&P 500 (Mỹ)
            "^IXIC",    # 💻 NASDAQ (Công nghệ)
            "^DJI",     # 🏭 DOW JONES (Công nghiệp)
            "EURUSD=X", # 💶 EURO vs USD
            "JPY=X",    # 💴 USD vs YÊN NHẬT
            "GBPUSD=X"  # 💷 BẢNG ANH vs USD
        ]
        
        # Gộp danh sách
        FULL_LIST = CRYPTO + MACRO
        
        selected_asset = st.selectbox("SELECT ASSET", FULL_LIST + ["...CUSTOM..."], label_visibility="collapsed")
        
        if selected_asset == "...CUSTOM...":
            symbol = st.text_input("TYPE SYMBOL (Ex: BTC, GC=F)", "BTC").upper()
        else:
            symbol = selected_asset

    st.write("---")
    
    with st.spinner(f"⚡ DECRYPTING {symbol}..."):
        # 1. Gọi hàm tải dữ liệu
        df, status = fetch_data(symbol)
        
        # === 🚑 EMERGENCY FIX V2: TẢI 1000 NẾN CHO DỰ BÁO 30 NGÀY ===
        # Nếu ít dữ liệu, tải thẳng từ Binance với limit=1000
        if df is not None and len(df) < 200:
            try:
                import requests
                import pandas as pd
                clean_sym = symbol.replace('USDT','') + 'USDT'
                # Tăng limit lên 1000 để đủ sức soi 30 ngày (720h)
                url_fix = f"https://api.binance.com/api/v3/klines?symbol={clean_sym}&interval=1h&limit=1000"
                res_fix = requests.get(url_fix, timeout=3).json()
                
                if isinstance(res_fix, list) and len(res_fix) > 0:
                    df_fix = pd.DataFrame(res_fix, columns=['t', 'open', 'high', 'low', 'close', 'volume', 'T', 'q', 'n', 'V', 'Q', 'B'])
                    df_fix['t'] = pd.to_datetime(df_fix['t'], unit='ms')
                    df_fix.set_index('t', inplace=True)
                    cols = ['open', 'high', 'low', 'close', 'volume']
                    df_fix[cols] = df_fix[cols].astype(float)
                    df = df_fix
            except: pass
        # =============================================================

        if df is not None:
            data = analyze_market(df)
            if data:
                c_signal = data['color']
                str_price = f"${data['price']:,.2f}"
                str_poc = f"${data['poc']:,.2f}"
                str_rsi = f"{data['rsi']:.1f}"
                
                m1, m2, m3, m4 = st.columns(4)
                with m1: st.markdown(f"""<div class="glass-card"><div class="metric-label">PRICE</div><div class="metric-val" style="color:var(--neon-cyan)">{str_price}</div></div>""", unsafe_allow_html=True)
                with m2: st.markdown(f"""<div class="glass-card" style="border:1px solid {c_signal}"><div class="metric-label" style="color:{c_signal}">VERDICT</div><div class="metric-val" style="color:{c_signal}">{data['signal']}</div></div>""", unsafe_allow_html=True)
                with m3: st.markdown(f"""<div class="glass-card"><div class="metric-label">POC</div><div class="metric-val" style="color:#ff0055">{str_poc}</div></div>""", unsafe_allow_html=True)
                with m4: st.markdown(f"""<div class="glass-card"><div class="metric-label">RSI</div><div class="metric-val" style="color:#fff">{str_rsi}</div></div>""", unsafe_allow_html=True)
                
                c_chart, c_info = st.columns([3, 1])
                with c_chart: render_chart(symbol, height=800)
                with c_info:
                    st.markdown(create_oscillators_html(data), unsafe_allow_html=True)
                    st.markdown(create_battle_plan_html(data), unsafe_allow_html=True)
                
                # === 🧠 AI SECTION (V40: H4 AGGREGATION) ===
                st.write("---")
                st.markdown('<div class="glitch-header" style="font-size:20px; color:#00b4ff">🔮 AI PROPHET (H4 VISION)</div>', unsafe_allow_html=True)
                
                col_opt1, col_opt2 = st.columns([1, 4])
                with col_opt1:
                    # Các mốc thời gian hợp lý với khung H4
                    horizon = st.selectbox("HORIZON", ["24 Hours", "3 Days", "7 Days", "14 Days"], index=1, label_visibility="collapsed")
                
                # Quy đổi ra số lượng nến H4 (periods)
                if horizon == "24 Hours": periods = 6   # 6 x 4h = 24h
                elif horizon == "3 Days": periods = 18  # 18 x 4h = 72h
                elif horizon == "7 Days": periods = 42  # 42 x 4h = 1 tuần
                else: periods = 84                      # 2 tuần
                
                if st.button(f"RUN PREDICTION ({horizon})", key="btn_prophet"):
                    with st.spinner(f"⚡ AGGREGATING H4 CANDLES & PREDICTING..."):
                        from backend.ai_forecast import run_ai_forecast, plot_ai_chart
                        
                        ai_res = run_ai_forecast(df, periods=periods)
                        
                        if ai_res:
                            c_ai1, c_ai2 = st.columns([1, 3])
                            with c_ai1:
                                diff_color = "#00ff9f" if ai_res['diff_pct'] > 0 else "#ff0055"
                                st.markdown(f"""
                                <div class="glass-card" style="border: 1px solid #00b4ff; text-align:center">
                                    <div style="font-size:12px; color:#00b4ff; margin-bottom:5px">TARGET ({horizon})</div>
                                    <div style="font-family:'Orbitron'; font-size:20px; color:#fff">${ai_res['predicted_price']:,.2f}</div>
                                    <div style="font-family:'Share Tech Mono'; font-size:14px; color:{diff_color}; margin-top:5px">
                                        {ai_res['trend']} ({ai_res['diff_pct']:+.2f}%)
                                    </div>
                                    <div style="font-size:10px; color:#666; margin-top:10px">Mode: Aggressive (H4)<br>Sensitivity: High</div>
                                </div>
                                """, unsafe_allow_html=True)
                            with c_ai2:
                                fig_ai = plot_ai_chart(symbol, ai_res)
                                # BẬT TÍNH NĂNG SCROLL ZOOM (LĂN CHUỘT)
                                st.plotly_chart(fig_ai, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
                        else:
                            st.error("AI ERROR: Could not aggregate data. Try refreshing.")
# ==============================================================================
# MODE 3: NEWS SENTIMENT RADAR (GROK STYLE)
# ==============================================================================
elif mode == "📰 NEWS RADAR":
    st.markdown('<div class="glitch-header">📰 GLOBAL NEWS SENTIMENT</div>', unsafe_allow_html=True)
    
    if st.button("🔄 SCAN LATEST NEWS", type="primary"):
        st.cache_data.clear() # Xóa cache để lấy tin mới nhất
        
    with st.spinner("📡 INTERCEPTING SIGNALS FROM GLOBAL MEDIA..."):
        from backend.news_engine import fetch_crypto_news
        news_df, mood, score = fetch_crypto_news()
        
        if not news_df.empty:
            # 1. BẢNG ĐIỀU KHIỂN TÂM LÝ (DASHBOARD)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div class="glass-card" style="text-align:center">
                    <div class="metric-label">MARKET MOOD</div>
                    <div style="font-size:24px; color:#fff; font-weight:bold">{mood}</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                # Màu thanh sentiment
                bar_color = "#00ff9f" if score > 0 else "#ff0055"
                st.markdown(f"""
                <div class="glass-card" style="text-align:center">
                    <div class="metric-label">SENTIMENT SCORE</div>
                    <div style="font-size:24px; color:{bar_color}">{score:.4f}</div>
                    <div style="font-size:10px; color:#888">-1 (Bear) to +1 (Bull)</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="glass-card" style="text-align:center">
                    <div class="metric-label">SOURCES SCANNED</div>
                    <div style="font-size:24px; color:var(--neon-cyan)">{len(news_df)} ARTICLES</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.write("---")
            
            # 2. DANH SÁCH TIN TỨC (NEWS FEED)
            for index, row in news_df.iterrows():
                st.markdown(f"""
                <div class="glass-card" style="border-left: 4px solid {row['color']}; margin-bottom:10px">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="color:#aaa; font-size:12px">📡 {row['source']}</span>
                        <span style="color:#666; font-size:12px">{row['published']}</span>
                    </div>
                    <div style="font-size:16px; font-weight:bold; color:#fff; margin:5px 0">
                        <a href="{row['link']}" target="_blank" style="text-decoration:none; color:#fff">{row['title']}</a>
                    </div>
                    <div style="display:flex; align-items:center gap:10px">
                        <span style="background:{row['color']}22; color:{row['color']}; padding:2px 8px; border-radius:4px; font-size:12px; border:1px solid {row['color']}">
                            {row['sentiment']}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.error("⚠️ SIGNAL LOST: Cannot connect to News Feed. Check internet connection.")

# ==============================================================================
# ==============================================================================
# MODE 4: ON-CHAIN COMMAND CENTER (V58 - FULL FEATURES)
# ==============================================================================
elif mode == "🐋 WHALE TRACKER": 
    st.markdown('<div class="glitch-header">🦈 ON-CHAIN COMMAND CENTER</div>', unsafe_allow_html=True)
    
    try:
        from backend.wallet_manager import load_book, add_shark, delete_shark
        from backend.wallet_stalker import get_wallet_balance, get_token_tx, get_native_symbol, get_current_prices
        import plotly.express as px 
        saved_sharks = load_book()
        prices = get_current_prices() 
    except: st.stop()

    # --- KHU VỰC 1: CHỌN VÍ & NHẬP LIỆU ---
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f"**NETWORK: ETH**") 
        shark_names = ["🔍 ...Type Manually..."] + [f"{s['name']}" for s in saved_sharks]
        selected_shark = st.selectbox("📂 BOOKMARKS", shark_names)
    with c2:
        default_val = ""
        if selected_shark != "🔍 ...Type Manually...":
            for s in saved_sharks:
                if s['name'] == selected_shark: default_val = s['address']
        target_wallet = st.text_input("TARGET WALLET:", value=default_val, placeholder="0x...")

    # --- KHU VỰC 2: QUẢN LÝ DANH BẠ (ĐÃ KHÔI PHỤC) ---
    with st.expander("⚙️ QUẢN LÝ DANH BẠ (THÊM / XÓA VÍ)"):
        col_add, col_del = st.columns(2)
        
        # Thêm ví mới
        with col_add:
            st.markdown("**➕ THÊM VÍ MỚI**")
            new_name = st.text_input("Tên gợi nhớ (Ví dụ: Cá mập gom PEPE)", key="new_name")
            new_addr = st.text_input("Địa chỉ ví (0x...)", key="new_addr")
            if st.button("LƯU LẠI"):
                if new_name and new_addr:
                    ok, msg = add_shark(new_name, new_addr)
                    if ok: st.success(msg)
                    else: st.warning(msg)
                    st.rerun() 
                else:
                    st.warning("Nhập đủ tên và ví nhé!")

        # Xóa ví đang chọn
        with col_del:
            st.markdown("**🗑️ XÓA VÍ ĐANG CHỌN**")
            if selected_shark != "🔍 ...Type Manually...":
                st.write(f"Đang chọn: **{selected_shark}**")
                if st.button("XÓA KHỎI SỔ"):
                    addr_to_del = next((s['address'] for s in saved_sharks if s['name'] == selected_shark), None)
                    if addr_to_del:
                        ok, msg = delete_shark(addr_to_del)
                        if ok: st.success(msg)
                        st.rerun()
            else:
                st.info("Hãy chọn một ví trong danh sách để xóa.")

    # --- KHU VỰC 3: QUÉT & PHÂN TÍCH (GIỮ NGUYÊN V57) ---
    user_api = st.text_input("API KEY (Optional):", type="password")

    if st.button("🛰️ ANALYZE MONEY FLOW"):
        if len(target_wallet) == 42:
            with st.spinner("CALCULATING NET WORTH..."):
                
                # 1. LẤY SỐ DƯ & GIÁ TRỊ GỐC
                native_bal, err = get_wallet_balance(target_wallet, "ETH", user_api)
                native_usd = native_bal * prices['ETH']
                
                # 2. LẤY GIAO DỊCH & TÍNH TOÁN USD
                df, err_tx = get_token_tx(target_wallet, "ETH", user_api)
                
                max_wealth_detected = native_usd 
                
                if df is not None and not df.empty:
                    # Hàm tính giá
                    def calc_usd(row):
                        sym = row['SYMBOL'].upper()
                        amt = row['AMOUNT']
                        if sym in ["USDT", "USDC", "DAI", "FDUSD", "TUSD", "PYUSD", "GUSD"]: return amt
                        if sym in ["WBTC", "BTC", "CBTC", "TBTC"]: return amt * prices['BTC']
                        if sym in ["WETH", "ETH", "STETH", "RETH", "WSTETH"]: return amt * prices['ETH']
                        if sym in ["BNB", "WBNB"]: return amt * prices['BNB']
                        return 0 
                    
                    df['USD_VALUE'] = df.apply(calc_usd, axis=1)
                    max_tx = df['USD_VALUE'].max()
                    if max_tx > max_wealth_detected: max_wealth_detected = max_tx

                # 3. XẾP HẠNG
                rank_title = "🦐 PLANKTON (Vi Sinh)"
                rank_color = "#888"
                if max_wealth_detected > 1000: rank_title = "🦀 CRAB (Cua)"
                if max_wealth_detected > 10000: rank_title = "🐙 OCTOPUS (Bạch Tuộc)"; rank_color = "#00b4ff"
                if max_wealth_detected > 100000: rank_title = "🐬 DOLPHIN (Cá Heo)"; rank_color = "#00ff9f"
                if max_wealth_detected > 1000000: rank_title = "🦈 SHARK (Cá Mập)"; rank_color = "#ffcc00"
                if max_wealth_detected > 10000000: rank_title = "🐋 WHALE (Cá Voi)"; rank_color = "#ff0055"
                if max_wealth_detected > 100000000: rank_title = "👑 LEVIATHAN (Thủy Quái)"; rank_color = "#aa00ff"

                # HIỂN THỊ THẺ TÀI SẢN
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; background:#111; padding:20px; border-radius:10px; border:1px solid #333; margin-bottom:20px">
                    <div>
                        <div style="color:#888; font-size:12px">NATIVE BALANCE</div>
                        <div style="font-size:32px; font-weight:bold; color:#fff">{native_bal:,.4f} ETH</div>
                        <div style="color:#00ff9f; font-size:16px">≈ ${native_usd:,.2f} USD</div>
                    </div>
                    <div style="text-align:right">
                        <div style="color:#aaa; font-size:12px">DETECTED RANK</div>
                        <div style="font-size:28px; font-weight:bold; color:{rank_color}; text-shadow: 0 0 10px {rank_color}">{rank_title}</div>
                        <div style="color:#666; font-size:10px">Highest Value: ${max_wealth_detected:,.0f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 4. BIỂU ĐỒ & TOP MOVES
                if df is not None and not df.empty:
                    col_chart, col_top = st.columns(2)
                    
                    with col_chart:
                        st.markdown("### 📊 REAL PORTFOLIO (USD)")
                        df_chart = df[(df['TYPE'].str.contains("IN")) & (df['USD_VALUE'] > 10)]
                        if not df_chart.empty:
                            df_pie = df_chart.groupby('SYMBOL')['USD_VALUE'].sum().reset_index()
                            fig = px.pie(df_pie, values='USD_VALUE', names='SYMBOL', 
                                         hole=0.5, color_discrete_sequence=px.colors.sequential.Plasma_r)
                            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"},
                                              showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Chưa đủ dữ liệu định giá để vẽ biểu đồ.")

                    with col_top:
                        st.markdown("### 🏆 BIGGEST MOVES")
                        df_top = df[df['USD_VALUE'] > 0].sort_values(by='USD_VALUE', ascending=False).head(5)
                        for index, row in df_top.iterrows():
                            st.markdown(f"""
                            <div style="background:rgba(255,255,255,0.05); border-radius:8px; padding:10px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; border-left:3px solid #ffcc00">
                                <div>
                                    <div style="color:#fff; font-weight:bold">{row['SYMBOL']}</div>
                                    <div style="color:#888; font-size:11px">{row['TIME']}</div>
                                </div>
                                <div style="text-align:right">
                                    <div style="color:#ffcc00; font-weight:bold; font-size:16px">${row['USD_VALUE']:,.0f}</div>
                                    <div style="color:#aaa; font-size:11px">{row['TYPE']}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # LOG CHI TIẾT
                    st.markdown("### 📜 FULL ACTIVITY LOG")
                    for index, row in df.iterrows():
                        val_display = f"${row['USD_VALUE']:,.0f}" if row['USD_VALUE'] > 0 else "---"
                        st.markdown(f"""
                        <div class="glass-card" style="border-left: 4px solid {row['COLOR']}; margin-bottom:8px; padding:10px; display:flex; justify-content:space-between; align-items:center">
                            <div style="display:flex; align-items:center; gap:12px">
                                <span style="font-weight:bold; font-size:18px; color:#fff">{row['SYMBOL']}</span>
                                <div><div style="font-size:12px; color:#888">{row['TIME']}</div></div>
                            </div>
                            <div style="text-align:right">
                                <div style="color:{row['COLOR']}; font-weight:bold; font-size:12px">{row['TYPE']}</div>
                                <div style="color:#fff; font-size:16px; font-weight:bold">{row['AMOUNT']:,.4f}</div>
                                <div style="color:#666; font-size:12px">{val_display}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Vui lòng nhập địa chỉ ví hợp lệ!")
# FOOTER: ĐÁNH DẤU CHỦ QUYỀN (LUÔN HIỆN Ở DƯỚI CÙNG)
# ==============================================================================
st.markdown("""
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background: rgba(0, 0, 0, 0.8); /* Màu đen trong suốt */
    color: #888;
    text-align: center;
    padding: 8px;
    font-family: 'Share Tech Mono'; 
    font-size: 12px;
    border-top: 1px solid #333;
    z-index: 9999; /* Luôn nổi lên trên cùng */
    backdrop-filter: blur(5px); /* Hiệu ứng mờ kính */
}
</style>
<div class="footer">
    🚀 CYBER COMMANDER V42  |  DEVELOPED BY <strong style="color:#00ff9f; font-family:'Orbitron'">THANGLONG</strong>  |  © 2026
</div>
""", unsafe_allow_html=True)
