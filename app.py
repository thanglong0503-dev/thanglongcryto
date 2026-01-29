import streamlit as st
import time

# IMPORT
from frontend.styles import get_cyberpunk_css
from frontend.charts import render_chart
from backend.data_loader import fetch_data, fetch_global_indices, fetch_market_overview
from backend.logic import analyze_market

# 1. CẤU HÌNH
st.set_page_config(layout="wide", page_title="CYBER COMMANDER V23", page_icon="🔮", initial_sidebar_state="expanded")
st.markdown(get_cyberpunk_css(), unsafe_allow_html=True)

# 2. POPUP CHART (GIỮ NGUYÊN)
@st.dialog("LIVE CHART", width="large")
def show_popup_chart(symbol):
    st.markdown(f'<div style="font-family:Orbitron; font-size:24px; color:#00e5ff; margin-bottom:10px">{symbol} / USDT</div>', unsafe_allow_html=True)
    render_chart(symbol, height=500)

# 3. SIDEBAR (MENU TRÁI)
with st.sidebar:
    st.markdown('<div class="glitch-header" style="font-size:24px; margin-bottom:20px">CYBER<br>ORACLE</div>', unsafe_allow_html=True)
    
    # Nút chọn chế độ
    mode = st.radio("MAIN MENU", ["🌐 MARKET GRID", "🔮 DEEP SCANNER"], label_visibility="collapsed")
    
    st.markdown("---")
    st.caption("MACRO DATA")
    
    # Rada Vĩ Mô (Mini)
    macro = fetch_global_indices()
    if macro:
        for name, d in macro.items():
            col_c = "#00ffa3" if d['change'] >= 0 else "#ff0055"
            icon = "▲" if d['change'] >= 0 else "▼"
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; font-family:'Share Tech Mono'; font-size:12px; margin-bottom:5px; border-bottom:1px solid #222; padding-bottom:2px">
                <span style="color:#888">{name}</span>
                <span style="color:{col_c}">{d['price']}</span>
            </div>
            """, unsafe_allow_html=True)

# ==============================================================================
# MODE 1: MARKET GRID (BẢNG ĐIỆN TỬ ĐEN TUYỀN)
# ==============================================================================
if mode == "🌐 MARKET GRID":
    st.markdown('<div class="glitch-header">GLOBAL MARKET MONITOR</div>', unsafe_allow_html=True)
    
    # Header Tools
    c1, c2 = st.columns([5, 1])
    with c1: st.caption("Realtime Market Data | Click 'SCAN' for details")
    with c2: 
        if st.button("🔄 RELOAD"): st.rerun()

    # Load dữ liệu
    df = fetch_market_overview()
    
    if df is not None:
        # VẼ TIÊU ĐỀ BẢNG (Header Row)
        st.markdown("""
        <div style="display:flex; padding:10px; background:#111; border-bottom:2px solid #333; font-weight:bold; color:#888; font-family:'Orbitron'; margin-bottom:10px">
            <div style="width:15%">ASSET</div>
            <div style="width:25%; text-align:right">PRICE</div>
            <div style="width:25%; text-align:right">24H CHANGE</div>
            <div style="width:10%">TREND</div>
            <div style="width:25%; text-align:right">ACTION</div>
        </div>
        """, unsafe_allow_html=True)

        # VẼ TỪNG DÒNG (LOOP)
        for index, row in df.iterrows():
            sym = row['SYMBOL']
            price = row['PRICE ($)']
            change = row['24H %']
            trend = row['TREND']
            
            # Màu sắc động
            color = "#00ffa3" if change >= 0 else "#ff0055" # Xanh / Đỏ
            bg_flash = "rgba(0, 255, 163, 0.1)" if change >= 0 else "rgba(255, 0, 85, 0.1)"
            
            # Layout 5 cột cho mỗi dòng
            c_asset, c_price, c_change, c_trend, c_btn = st.columns([1.5, 2.5, 2.5, 1, 2.5])
            
            with c_asset:
                st.markdown(f"<div style='font-family:Orbitron; font-weight:bold; color:#fff; padding-top:10px'>{sym}</div>", unsafe_allow_html=True)
            
            with c_price:
                st.markdown(f"<div style='font-family:Share Tech Mono; text-align:right; font-size:18px; color:#fff; padding-top:10px'>${price:,.4f}</div>", unsafe_allow_html=True)
                
            with c_change:
                st.markdown(f"<div style='font-family:Share Tech Mono; text-align:right; color:{color}; padding-top:10px'>{change:+.2f}%</div>", unsafe_allow_html=True)
                
            with c_trend:
                st.markdown(f"<div style='text-align:center; font-size:20px; padding-top:5px'>{trend}</div>", unsafe_allow_html=True)
            
            with c_btn:
                # Nút bấm riêng cho từng dòng
                if st.button(f"⚡ SCAN", key=f"btn_{sym}"):
                    show_popup_chart(sym)
            
            # Đường kẻ mờ ngăn cách
            st.markdown("<div style='height:1px; background:#222; margin:5px 0'></div>", unsafe_allow_html=True)

# ==============================================================================
# MODE 2: DEEP SCANNER (GIỮ NGUYÊN CODE CŨ CỦA NGÀI)
# ==============================================================================
elif mode == "🔮 DEEP SCANNER":
    # (Phần này giữ nguyên code cũ, Emo chỉ copy lại để đảm bảo không mất)
    c_head, c_status = st.columns([3, 1])
    with c_head: st.markdown('<div class="glitch-header">DEEP SCANNER</div>', unsafe_allow_html=True)
    with c_status: st.markdown('<div style="text-align:right; color:#00ff9f;">SYSTEM: ONLINE_ 🟢</div>', unsafe_allow_html=True)

    col_search, col_pad = st.columns([1, 2])
    with col_search:
        ASSETS = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "PEPE", "SHIB", "WIF"]
        selected_asset = st.selectbox("SELECT ASSET", ASSETS + ["...CUSTOM..."], label_visibility="collapsed")
        if selected_asset == "...CUSTOM...":
            symbol = st.text_input("TYPE SYMBOL", "BTC").upper()
        else:
            symbol = selected_asset

    st.write("---")
    
    with st.spinner(f"⚡ ANALYZING {symbol}..."):
        df, status = fetch_data(symbol)
        if df is not None:
            data = analyze_market(df)
            if data:
                # Metrics Row
                m1, m2, m3, m4 = st.columns(4)
                with m1: st.markdown(f"""<div class="glass-card"><div class="metric-label">PRICE</div><div class="metric-value" style="color:var(--neon-cyan)">${data['price']:,.2f}</div></div>""", unsafe_allow_html=True)
                with m2: st.markdown(f"""<div class="glass-card" style="border:1px solid {data['color']}"><div class="metric-label" style="color:{data['color']}">VERDICT</div><div class="metric-value" style="color:{data['color']}">{data['signal']}</div></div>""", unsafe_allow_html=True)
                with m3: st.markdown(f"""<div class="glass-card"><div class="metric-label">POC</div><div class="metric-value" style="color:#ff0055">${data['poc']:,.2f}</div></div>""", unsafe_allow_html=True)
                with m4: st.markdown(f"""<div class="glass-card"><div class="metric-label">RSI</div><div class="metric-value" style="color:#fff">{data['rsi']:.1f}</div></div>""", unsafe_allow_html=True)
                
                # Chart
                render_chart(symbol, height=800)
