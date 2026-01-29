import streamlit as st
import time

# IMPORT
from frontend.styles import get_cyberpunk_css
from frontend.charts import render_chart
from backend.data_loader import fetch_data, fetch_global_indices, fetch_market_overview
from backend.logic import analyze_market

# 1. CẤU HÌNH
st.set_page_config(layout="wide", page_title="CYBER COMMANDER V25", page_icon="🔮", initial_sidebar_state="expanded")
st.markdown(get_cyberpunk_css(), unsafe_allow_html=True)

# 2. POPUP CHART & DATA (ĐÃ KHÔI PHỤC BATTLE PLAN)
@st.dialog("TACTICAL VIEW", width="large")
def show_popup_data(symbol):
    # Header
    st.markdown(f'<div class="glitch-header" style="font-size:30px; margin-bottom:10px">{symbol}</div>', unsafe_allow_html=True)
    
    # Lấy dữ liệu chi tiết ngay trong Popup
    with st.spinner("CALCULATING STRATEGY..."):
        df, status = fetch_data(symbol)
        
    if df is not None:
        data = analyze_market(df)
        if data:
            # Hàng 1: Chỉ số chính
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"""<div class="glass-card"><div class="metric-label">CURRENT PRICE</div><div class="metric-val">${data['price']:,.2f}</div></div>""", unsafe_allow_html=True)
            with c2: st.markdown(f"""<div class="glass-card" style="border-color:{data['color']}"><div class="metric-label" style="color:{data['color']}">AI SIGNAL</div><div class="metric-val" style="color:{data['color']}">{data['signal']}</div></div>""", unsafe_allow_html=True)
            with c3: 
                rsi_c = "var(--neon-green)" if data['rsi'] < 30 else "var(--neon-pink)" if data['rsi'] > 70 else "#fff"
                st.markdown(f"""<div class="glass-card"><div class="metric-label">RSI / STOCH</div><div class="metric-val" style="color:{rsi_c}">{data['rsi']:.0f} / {data['stoch_k']:.0f}</div></div>""", unsafe_allow_html=True)
            
            # Hàng 2: Chart & Battle Plan
            c_chart, c_plan = st.columns([2, 1])
            
            with c_chart:
                render_chart(symbol, height=450)
                
            with c_plan:
                # KHÔI PHỤC BẢNG KẾ HOẠCH (TP/SL)
                st.markdown(f"""
                <div class="glass-card" style="height: 460px; border-left: 3px solid var(--neon-cyan);">
                    <div class="metric-label" style="color:var(--neon-cyan); margin-bottom:15px">>_ BATTLE PLAN</div>
                    
                    <div style="font-family:'Share Tech Mono'; font-size:14px; color:#ccc; line-height:1.8;">
                        <strong>TREND:</strong> <span style="color:{'#00ff9f' if data['trend']=='UPTREND' else '#ff0055'}">{data['trend']}</span><br>
                        <strong>ADX:</strong> {data['strength']}<br>
                        <strong>WHALE:</strong> {data['vol_status']}<br>
                        <hr style="border-color:#333">
                        <div style="font-size:12px; color:#888">KEY LEVELS</div>
                        🚀 <strong>RESIST (R1):</strong> <span style="color:#ff0055">${data['r1']:,.2f}</span><br>
                        🛡️ <strong>SUPPORT (S1):</strong> <span style="color:#00ff9f">${data['s1']:,.2f}</span><br>
                        <hr style="border-color:#333">
                        <div style="font-size:12px; color:#888">ENTRY SETUP</div>
                        🎯 <strong>ENTRY:</strong> ${data['price']:,.2f}<br>
                        🛑 <strong>STOPLOSS:</strong> ${data['s1']*0.99:,.2f}<br>
                        💰 <strong>TARGET:</strong> ${data['r1']:,.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.error("DATA FEED LOST")

# 3. SIDEBAR (ĐÃ SỬA LỖI HIỂN THỊ %)
with st.sidebar:
    st.markdown('<div class="glitch-header" style="font-size:24px; margin-bottom:20px">CYBER<br>ORACLE</div>', unsafe_allow_html=True)
    
    mode = st.radio("SYSTEM MODE", ["🌐 MARKET GRID", "🔮 DEEP SCANNER"], label_visibility="collapsed")
    
    st.markdown("---")
    st.caption("MACRO DATA STREAM")
    
    # Fix hiển thị %
    macro = fetch_global_indices()
    if macro:
        for name, d in macro.items():
            col_c = "#00ffa3" if d['change'] >= 0 else "#ff0055"
            icon = "▲" if d['change'] >= 0 else "▼"
            # Thêm phần {d['change']:.2f}% vào dòng dưới
            st.markdown(f"""
            <div style="margin-bottom:10px; border-left:2px solid {col_c}; padding-left:8px">
                <div style="font-family:'Share Tech Mono'; font-size:10px; color:#888">{name}</div>
                <div style="font-family:'Orbitron'; font-size:14px; color:#fff">{d['price']}</div>
                <div style="font-family:'Share Tech Mono'; font-size:11px; color:{col_c}">{icon} {d['change']:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

# ==============================================================================
# MODE 1: MARKET GRID (BẢNG ĐEN)
# ==============================================================================
if mode == "🌐 MARKET GRID":
    st.markdown('<div class="glitch-header">GLOBAL MARKET MONITOR</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns([6, 1])
    with c1: st.caption("LIVE FEED | CLICK 'SCAN' FOR BATTLE PLAN")
    with c2: 
        if st.button("🔄 REFRESH"): st.rerun()

    df = fetch_market_overview()
    
    if df is not None:
        # Header
        st.markdown("""
        <div style="display:flex; padding:10px; background:#000; border-bottom:1px solid #333; color:#666; font-family:'Share Tech Mono'; font-size:12px">
            <div style="width:15%">ASSET</div>
            <div style="width:25%; text-align:right">PRICE</div>
            <div style="width:20%; text-align:right">24H %</div>
            <div style="width:15%; text-align:center">TREND</div>
            <div style="width:25%; text-align:right">PROTOCOL</div>
        </div>
        """, unsafe_allow_html=True)

        for index, row in df.iterrows():
            sym = row['SYMBOL']
            price = row['PRICE ($)']
            change = row['24H %']
            trend = row['TREND']
            
            color = "#00ffa3" if change >= 0 else "#ff0055"
            
            # Cột
            c_asset, c_price, c_change, c_trend, c_btn = st.columns([1.5, 2.5, 2.0, 1.5, 2.5])
            
            with c_asset: st.markdown(f"<div style='font-family:Orbitron; font-weight:bold; color:#fff; padding-top:12px'>{sym}</div>", unsafe_allow_html=True)
            with c_price: st.markdown(f"<div style='font-family:Share Tech Mono; text-align:right; font-size:16px; color:#e0e0e0; padding-top:12px'>${price:,.4f}</div>", unsafe_allow_html=True)
            with c_change: st.markdown(f"<div style='font-family:Share Tech Mono; text-align:right; color:{color}; padding-top:12px'>{change:+.2f}%</div>", unsafe_allow_html=True)
            with c_trend: st.markdown(f"<div style='text-align:center; font-size:18px; padding-top:8px'>{trend}</div>", unsafe_allow_html=True)
            with c_btn:
                if st.button(f"⚡ SCAN", key=f"btn_{sym}"):
                    show_popup_data(sym) # Gọi hàm Popup xịn
            
            st.markdown("<div style='height:1px; background:#111; margin:0'></div>", unsafe_allow_html=True)

# ==============================================================================
# MODE 2: DEEP SCANNER (GIỮ NGUYÊN BẢN CŨ CỦA NGÀI)
# ==============================================================================
elif mode == "🔮 DEEP SCANNER":
    # (Phần này giữ nguyên logic cũ, chỉ đổi lại tên biến cho gọn)
    st.markdown('<div class="glitch-header">DEEP SCANNER</div>', unsafe_allow_html=True)
    
    col_search, col_pad = st.columns([1, 2])
    with col_search:
        ASSETS = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "PEPE", "SHIB", "WIF"]
        selected_asset = st.selectbox("SELECT ASSET", ASSETS + ["...CUSTOM..."], label_visibility="collapsed")
        if selected_asset == "...CUSTOM...":
            symbol = st.text_input("TYPE SYMBOL", "BTC").upper()
        else:
            symbol = selected_asset

    st.write("---")
    
    with st.spinner(f"⚡ DECRYPTING {symbol}..."):
        df, status = fetch_data(symbol)
        if df is not None:
            data = analyze_market(df)
            if data:
                # 4 Metrics
                m1, m2, m3, m4 = st.columns(4)
                with m1: st.markdown(f"""<div class="glass-card"><div class="metric-label">PRICE</div><div class="metric-val" style="color:var(--neon-cyan)">${data['price']:,.2f}</div></div>""", unsafe_allow_html=True)
                with m2: st.markdown(f"""<div class="glass-card" style="border:1px solid {data['color']}"><div class="metric-label" style="color:{data['color']}">VERDICT</div><div class="metric-val" style="color:{data['color']}">{data['signal']}</div></div>""", unsafe_allow_html=True)
                with m3: st.markdown(f"""<div class="glass-card"><div class="metric-label">POC</div><div class="metric-val" style="color:#ff0055">${data['poc']:,.2f}</div></div>""", unsafe_allow_html=True)
                with m4: st.markdown(f"""<div class="glass-card"><div class="metric-label">RSI</div><div class="metric-val" style="color:#fff">{data['rsi']:.1f}</div></div>""", unsafe_allow_html=True)
                
                # Chart + Plan
                c_chart, c_info = st.columns([3, 1])
                with c_chart: render_chart(symbol, height=800)
                with c_info:
                    st.markdown(f"""
                    <div class="glass-card" style="border-left: 3px solid var(--neon-cyan);">
                        <div class="metric-label">>_ BATTLE PLAN</div>
                        <div style="font-family:'Share Tech Mono'; font-size:13px; color:#bbb; margin-top:10px; line-height:1.6">
                            [TARGET]: {symbol}<br>
                            R1: ${data['r1']:,.2f}<br>
                            S1: ${data['s1']:,.2f}<br>
                            WHALE: {data['vol_status']}<br>
                            ADX: {data['strength']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
