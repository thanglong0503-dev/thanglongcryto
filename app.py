import streamlit as st
import time

# IMPORT
from frontend.styles import get_cyberpunk_css
from frontend.charts import render_chart
from backend.data_loader import fetch_data, fetch_global_indices, fetch_market_overview
from backend.logic import analyze_market

# 1. CẤU HÌNH
st.set_page_config(layout="wide", page_title="CYBER COMMANDER V26", page_icon="🔮", initial_sidebar_state="expanded")
st.markdown(get_cyberpunk_css(), unsafe_allow_html=True)

# 2. POPUP CHART & DATA (ĐÃ THÊM LẠI OSCILLATORS)
@st.dialog("TACTICAL VIEW", width="large")
def show_popup_data(symbol):
    # Header
    st.markdown(f'<div class="glitch-header" style="font-size:30px; margin-bottom:10px">{symbol}</div>', unsafe_allow_html=True)
    
    with st.spinner("CALCULATING STRATEGY..."):
        df, status = fetch_data(symbol)
        
    if df is not None:
        data = analyze_market(df)
        if data:
            # Hàng 1: Chỉ số chính (HUD)
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"""<div class="glass-card"><div class="metric-label">CURRENT PRICE</div><div class="metric-val">${data['price']:,.2f}</div></div>""", unsafe_allow_html=True)
            with c2: st.markdown(f"""<div class="glass-card" style="border-color:{data['color']}"><div class="metric-label" style="color:{data['color']}">AI SIGNAL</div><div class="metric-val" style="color:{data['color']}">{data['signal']}</div></div>""", unsafe_allow_html=True)
            with c3: st.markdown(f"""<div class="glass-card"><div class="metric-label">POINT OF CONTROL</div><div class="metric-val" style="color:#ff0055">${data['poc']:,.2f}</div></div>""", unsafe_allow_html=True)
            
            # Hàng 2: Chart & Chiến thuật
            c_chart, c_plan = st.columns([2, 1])
            
            with c_chart:
                render_chart(symbol, height=500)
                
            with c_plan:
                # 1. HỘP OSCILLATORS (ĐÃ KHÔI PHỤC)                 st.markdown(f"""
                <div class="glass-card">
                    <div class="metric-label">OSCILLATORS</div>
                    <div style="margin-top:10px; font-family:'Share Tech Mono'; color:#ccc; font-size:14px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                            <span>RSI (14)</span>
                            <span style="color:{'var(--neon-pink)' if data['rsi']>70 else 'var(--neon-cyan)'}">{data['rsi']:.1f}</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                            <span>Stoch K</span>
                            <span style="color:{'var(--neon-green)' if data['stoch_k']<20 else '#fff'}">{data['stoch_k']:.1f}</span>
                        </div>
                        <div style="height:1px; background:#333; margin:10px 0;"></div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                            <span>TREND</span>
                            <span style="color:{'var(--neon-green)' if data['trend']=='UPTREND' else 'var(--neon-pink)'}">{data['trend']}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 2. HỘP BATTLE PLAN (NẰM DƯỚI)
                st.markdown(f"""
                <div class="glass-card" style="border-left: 3px solid var(--neon-cyan);">
                    <div class="metric-label" style="color:var(--neon-cyan); margin-bottom:10px">>_ BATTLE PLAN</div>
                    
                    <div style="font-family:'Share Tech Mono'; font-size:13px; color:#bbb; line-height:1.6;">
                        <div style="font-size:11px; color:#666">ENTRY SETUP</div>
                        🚀 <strong>ENTRY:</strong> <span style="color:#fff">${data['price']:,.2f}</span><br>
                        🛑 <strong>STOP:</strong> <span style="color:#ff0055">${data['s1']*0.99:,.2f}</span><br>
                        💰 <strong>TARGET:</strong> <span style="color:#00ff9f">${data['r1']:,.2f}</span>
                        <hr style="border-color:#333; margin:8px 0">
                        <div style="font-size:11px; color:#666">MARKET SCAN</div>
                        <strong>ADX:</strong> {data['strength']}<br>
                        <strong>VOL:</strong> {data['vol_status']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.error("DATA FEED LOST")

# 3. SIDEBAR (MENU TRÁI)
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
            </div>
            """, unsafe_allow_html=True)

# ==============================================================================
# MODE 1: MARKET GRID (BẢNG ĐIỆN TỬ ĐEN)
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
            
            c_asset, c_price, c_change, c_trend, c_btn = st.columns([1.5, 2.5, 2.0, 1.5, 2.5])
            
            with c_asset: st.markdown(f"<div style='font-family:Orbitron; font-weight:bold; color:#fff; padding-top:12px'>{sym}</div>", unsafe_allow_html=True)
            with c_price: st.markdown(f"<div style='font-family:Share Tech Mono; text-align:right; font-size:16px; color:#e0e0e0; padding-top:12px'>${price:,.4f}</div>", unsafe_allow_html=True)
            with c_change: st.markdown(f"<div style='font-family:Share Tech Mono; text-align:right; color:{color}; padding-top:12px'>{change:+.2f}%</div>", unsafe_allow_html=True)
            with c_trend: st.markdown(f"<div style='text-align:center; font-size:18px; padding-top:8px'>{trend}</div>", unsafe_allow_html=True)
            with c_btn:
                if st.button(f"⚡ SCAN", key=f"btn_{sym}"):
                    show_popup_data(sym)
            
            st.markdown("<div style='height:1px; background:#111; margin:0'></div>", unsafe_allow_html=True)

# ==============================================================================
# MODE 2: DEEP SCANNER (BẢN CŨ ĐẦY ĐỦ)
# ==============================================================================
elif mode == "🔮 DEEP SCANNER":
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
                m1, m2, m3, m4 = st.columns(4)
                with m1: st.markdown(f"""<div class="glass-card"><div class="metric-label">PRICE</div><div class="metric-val" style="color:var(--neon-cyan)">${data['price']:,.2f}</div></div>""", unsafe_allow_html=True)
                with m2: st.markdown(f"""<div class="glass-card" style="border:1px solid {data['color']}"><div class="metric-label" style="color:{data['color']}">VERDICT</div><div class="metric-val" style="color:{data['color']}">{data['signal']}</div></div>""", unsafe_allow_html=True)
                with m3: st.markdown(f"""<div class="glass-card"><div class="metric-label">POC</div><div class="metric-val" style="color:#ff0055">${data['poc']:,.2f}</div></div>""", unsafe_allow_html=True)
                with m4: st.markdown(f"""<div class="glass-card"><div class="metric-label">RSI</div><div class="metric-val" style="color:#fff">{data['rsi']:.1f}</div></div>""", unsafe_allow_html=True)
                
                c_chart, c_info = st.columns([3, 1])
                with c_chart: render_chart(symbol, height=800)
                with c_info:
                    st.markdown(f"""
                    <div class="glass-card">
                        <div class="metric-label">OSCILLATORS</div>
                        <div style="margin-top:10px; font-family:'Share Tech Mono'; color:#ccc; font-size:14px;">
                            <div style="display:flex; justify-content:space-between;"><span>Stoch K</span><span style="color:#fff">{data['stoch_k']:.1f}</span></div>
                            <div style="display:flex; justify-content:space-between;"><span>TREND</span><span style="color:#fff">{data['trend']}</span></div>
                        </div>
                    </div>
                    <div class="glass-card" style="border-left: 3px solid var(--neon-cyan);">
                        <div class="metric-label">>_ BATTLE PLAN</div>
                        <div style="font-family:'Share Tech Mono'; font-size:13px; color:#bbb; margin-top:10px;">
                            [TARGET]: {symbol}<br>
                            R1: ${data['r1']:,.2f}<br>
                            S1: ${data['s1']:,.2f}<br>
                            ADX: {data['strength']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
