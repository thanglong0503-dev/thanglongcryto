import streamlit as st
import time

# IMPORT MODULES
from frontend.styles import get_cyberpunk_css
from frontend.charts import render_chart
from backend.data_loader import fetch_data, fetch_global_indices, fetch_market_overview
from backend.logic import analyze_market

# 1. CẤU HÌNH
st.set_page_config(layout="wide", page_title="CYBER COMMANDER v22", page_icon="🔮", initial_sidebar_state="expanded")
st.markdown(get_cyberpunk_css(), unsafe_allow_html=True)

# --- SIDEBAR NAV (THANH ĐIỀU HƯỚNG BÊN TRÁI) ---
with st.sidebar:
    st.markdown('<div class="glitch-header" style="font-size:24px; margin-bottom:20px">CYBER<br>ORACLE</div>', unsafe_allow_html=True)
    
    # Menu chọn chế độ
    mode = st.radio(
        "NAVIGATION",
        ["🔮 SCANNER (Soi Kèo)", "🌐 MARKET GRID (Toàn Cảnh)"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    # Rada Vĩ Mô thu nhỏ vào Sidebar cho gọn
    st.markdown("<div style='color:#888; font-size:12px; margin-bottom:10px'>MACRO RADA</div>", unsafe_allow_html=True)
    macro = fetch_global_indices()
    if macro:
        for name, d in macro.items():
            color = "#00ffa3" if d['change'] >= 0 else "#ff0055"
            icon = "▲" if d['change'] >= 0 else "▼"
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; font-family:'Share Tech Mono'; font-size:13px; margin-bottom:8px">
                <span style="color:#ccc">{name}</span>
                <span style="color:{color}">{d['price']} ({icon})</span>
            </div>
            """, unsafe_allow_html=True)

# --- POPUP CHART FUNCTION (CỬA SỔ BẬT LÊN) ---
@st.dialog("QUICK CHART VIEW", width="large")
def show_popup_chart(symbol):
    st.markdown(f'<div style="font-family:Orbitron; font-size:24px; color:#00e5ff; margin-bottom:10px">{symbol} LIVE CHART</div>', unsafe_allow_html=True)
    # Vẽ chart nhỏ (height=500)
    render_chart(symbol, height=500)
    st.caption("Press Esc to close")

# ==============================================================================
# TRANG 1: 🌐 MARKET GRID (GIAO DIỆN BẢNG ĐIỆN TỬ MỚI)
# ==============================================================================
if mode == "🌐 MARKET GRID (Toàn Cảnh)":
    st.markdown('<div class="glitch-header">GLOBAL MARKET MONITOR</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    with col1: st.caption("Select a coin row to open Quick Chart.")
    with col2: 
        if st.button("🔄 REFRESH DATA"): st.rerun()

    # Lấy dữ liệu Top 20
    df_overview = fetch_market_overview()
    
    if df_overview is not None:
        # Cấu hình bảng xịn xò với tính năng "on_select"
        event = st.dataframe(
            df_overview,
            use_container_width=True,
            hide_index=True,
            height=800, # Bảng dài
            on_select="rerun", # <--- Kích hoạt tính năng chọn dòng
            selection_mode="single-row",
            column_config={
                "SYMBOL": st.column_config.TextColumn("Asset", help="Tên tài sản"),
                "PRICE ($)": st.column_config.NumberColumn("Price", format="$%.4f"),
                "24H %": st.column_config.NumberColumn("Change", format="%.2f%%"),
                "TREND": st.column_config.TextColumn("Trend")
            }
        )

        # LOGIC BẬT POPUP KHI CHỌN DÒNG
        if len(event.selection.rows) > 0:
            selected_index = event.selection.rows[0]
            selected_symbol = df_overview.iloc[selected_index]["SYMBOL"]
            
            # Gọi hàm bật cửa sổ (Dialog)
            show_popup_chart(selected_symbol)

# ==============================================================================
# TRANG 2: 🔮 SCANNER (GIAO DIỆN PHÂN TÍCH CŨ)
# ==============================================================================
elif mode == "🔮 SCANNER (Soi Kèo)":
    # (Đây là toàn bộ code giao diện cũ của Ngài)
    c_head, c_status = st.columns([3, 1])
    with c_head:
        st.markdown('<div class="glitch-header">DEEP SCANNER <span style="font-size:20px">v22</span></div>', unsafe_allow_html=True)
    with c_status:
        st.markdown('<div style="text-align:right; color:#00ff9f;">SYSTEM: ONLINE_ 🟢</div>', unsafe_allow_html=True)

    # INPUT CŨ
    col_search, col_pad = st.columns([1, 2])
    with col_search:
        ASSETS = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "PEPE", "SHIB", "WIF", "SUI", "APT", "NEAR", "LINK", "AVAX"]
        selected_asset = st.selectbox("SELECT ASSET", ASSETS + ["...CUSTOM..."], label_visibility="collapsed")
        if selected_asset == "...CUSTOM...":
            symbol = st.text_input("TYPE SYMBOL", "BTC").upper()
        else:
            symbol = selected_asset

    st.write("---")
    
    # LOGIC PHÂN TÍCH (Giữ nguyên)
    with st.spinner(f"⚡ ANALYZING {symbol}..."):
        df, status = fetch_data(symbol)
        if df is not None:
            data = analyze_market(df)
            if data:
                # 4 METRICS
                m1, m2, m3, m4 = st.columns(4)
                with m1: st.markdown(f"""<div class="glass-card"><div class="metric-label">PRICE</div><div class="metric-value" style="color:var(--neon-cyan)">${data['price']:,.2f}</div></div>""", unsafe_allow_html=True)
                with m2: st.markdown(f"""<div class="glass-card" style="border:1px solid {data['color']}"><div class="metric-label" style="color:{data['color']}">VERDICT</div><div class="metric-value" style="color:{data['color']}">{data['signal']}</div></div>""", unsafe_allow_html=True)
                with m3: st.markdown(f"""<div class="glass-card"><div class="metric-label">POC</div><div class="metric-value" style="color:#ff0055">${data['poc']:,.2f}</div><div style="font-size:12px; color:#888">{data['poc_stat']}</div></div>""", unsafe_allow_html=True)
                with m4: 
                    rsi_col = "var(--neon-green)" if data['rsi'] < 30 else ("var(--neon-pink)" if data['rsi'] > 70 else "#fff")
                    st.markdown(f"""<div class="glass-card"><div class="metric-label">RSI</div><div class="metric-value" style="color:{rsi_col}">{data['rsi']:.1f}</div></div>""", unsafe_allow_html=True)

                # CHART LỚN (900px)
                c_chart, c_info = st.columns([3, 1])
                with c_chart: render_chart(symbol, height=800)
                with c_info:
                    # INFO PANEL
                    st.markdown(f"""
                    <div class="glass-card">
                        <div class="metric-label">OSCILLATORS</div>
                        <div style="margin-top:10px; font-family:'Share Tech Mono'; color:#ccc; font-size:14px;">
                            <div style="display:flex; justify-content:space-between; margin-bottom:5px;"><span>Stoch K</span><span style="color:#fff">{data['stoch_k']:.1f}</span></div>
                            <div style="display:flex; justify-content:space-between;"><span>ADX</span><span style="color:#fff">{data['strength']}</span></div>
                        </div>
                    </div>
                    <div class="glass-card" style="border-left: 3px solid var(--neon-cyan);">
                        <div class="metric-label">>_ BATTLE PLAN</div>
                        <div style="font-family:'Share Tech Mono'; font-size:13px; color:#bbb; margin-top:10px;">
                            [TARGET]: {symbol}<br>
                            R1: ${data['r1']:,.2f}<br>
                            S1: ${data['s1']:,.2f}<br>
                            WHALE: {data['vol_status']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.error("NO DATA FOUND")
