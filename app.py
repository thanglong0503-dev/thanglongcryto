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
    mode = st.radio("SYSTEM MODE", ["🌐 MARKET GRID", "🔮 DEEP SCANNER"], label_visibility="collapsed")
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
elif mode == "🔮 DEEP SCANNER":
    st.markdown('<div class="glitch-header">DEEP SCANNER</div>', unsafe_allow_html=True)
    
    col_search, col_pad = st.columns([1, 2])
    with col_search:
        HUGE_ASSETS = ["BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK", "PEPE", "SHIB", "WIF", "SUI", "NEAR", "APT", "DOT", "LTC"]
        selected_asset = st.selectbox("SELECT ASSET", HUGE_ASSETS + ["...CUSTOM..."], label_visibility="collapsed")
        symbol = st.text_input("TYPE SYMBOL", "BTC").upper() if selected_asset == "...CUSTOM..." else selected_asset

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
