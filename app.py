import streamlit as st
import time

# IMPORT MODULES
from frontend.styles import get_cyberpunk_css
from frontend.charts import render_chart
from backend.data_loader import fetch_data
from backend.logic import analyze_market

# 1. CẤU HÌNH
st.set_page_config(layout="wide", page_title="CYBERPUNK v18", page_icon="🔮", initial_sidebar_state="collapsed")
st.markdown(get_cyberpunk_css(), unsafe_allow_html=True)

# 2. HEADER
c_head, c_status = st.columns([3, 1])
with c_head:
    st.markdown('<div class="glitch-header">CYBER ORACLE <span style="font-size:20px; color:var(--neon-green)">v18 PRO</span></div>', unsafe_allow_html=True)
with c_status:
    st.markdown('<div style="text-align:right; font-family:Share Tech Mono; color:#00ff9f; padding-top:15px;">SYSTEM: ONLINE_ <span class="blinking-cursor"></span></div>', unsafe_allow_html=True)
# ... (Phần Import giữ nguyên) ...
# NHỚ THÊM import fetch_market_overview VÀO DÒNG NÀY NHÉ:
from backend.data_loader import fetch_data, fetch_global_indices, fetch_market_overview

# ... (Phần set_page_config và CSS giữ nguyên) ...

# 2. HEADER
c_head, c_status = st.columns([3, 1])
with c_head:
    st.markdown('<div class="glitch-header">CYBER ORACLE <span style="font-size:20px; color:var(--neon-green)">v21</span></div>', unsafe_allow_html=True)
with c_status:
    st.markdown('<div style="text-align:right; font-family:Share Tech Mono; color:#00ff9f; padding-top:15px;">SYSTEM: ONLINE_ <span class="blinking-cursor"></span></div>', unsafe_allow_html=True)

# --- PHẦN 1: RADA VĨ MÔ (VÀNG/DẦU) ---
st.write("")
with st.spinner("🌍 SCANNING GLOBAL MARKETS..."):
    macro_data = fetch_global_indices()

if macro_data:
    g1, g2, g3, g4 = st.columns(4)
    def macro_card(label, data):
        symbol = "▲" if data['change'] >= 0 else "▼"
        return f"""
        <div style="background: rgba(20,20,20,0.6); border-left: 3px solid {data['color']}; padding: 10px; border-radius: 4px; margin-bottom: 10px;">
            <div style="font-size:10px; color:#888;">{label}</div>
            <div style="font-size:18px; font-weight:bold; color:#fff; font-family:'Orbitron'">{data['price']}</div>
            <div style="font-size:12px; color:{data['color']};">{symbol} {data['change']:.2f}%</div>
        </div>"""
    with g1: st.markdown(macro_card("GOLD (XAU)", macro_data['GOLD']), unsafe_allow_html=True)
    with g2: st.markdown(macro_card("USD INDEX (DXY)", macro_data['DXY']), unsafe_allow_html=True)
    with g3: st.markdown(macro_card("S&P 500", macro_data['S&P500']), unsafe_allow_html=True)
    with g4: st.markdown(macro_card("USD/VND", macro_data['USD/VND']), unsafe_allow_html=True)

# --- PHẦN 2: BẢNG ĐIỆN TỬ TỔNG HỢP (TÍNH NĂNG MỚI) ---
# Tạo một Expandable (có thể thu gọn) để không chiếm chỗ nếu không cần
with st.expander("📊 LIVE MARKET OVERVIEW (TOP COINS)", expanded=True):
    df_overview = fetch_market_overview()
    
    if df_overview is not None:
        # Dùng tính năng Dataframe Column Config của Streamlit để tô màu xanh/đỏ
        st.dataframe(
            df_overview,
            use_container_width=True,
            hide_index=True,
            column_config={
                "SYMBOL": st.column_config.TextColumn("Asset", help="Tên tài sản"),
                "PRICE ($)": st.column_config.NumberColumn("Price", format="$%.4f"), # Định dạng tiền tệ
                "24H %": st.column_config.NumberColumn(
                    "24h Change",
                    format="%.2f%%",
                    help="Biến động trong 24h qua"
                ),
                "TREND": st.column_config.TextColumn("Trend")
            }
        )
    else:
        st.warning("⚠️ Market data syncing... Please wait.")

# --- PHẦN 3: INPUT VÀ PHÂN TÍCH CHI TIẾT (GIỮ NGUYÊN CODE CŨ TỪ ĐÂY TRỞ XUỐNG) ---
col_search, col_pad = st.columns([1, 2])
# ... (Tiếp tục code cũ) ...

# 3. INPUT BAR (NÂNG CẤP V20)
col_search, col_pad = st.columns([1, 2])
with col_search:
    # DANH SÁCH TÀI SẢN KHỔNG LỒ
    ASSETS = {
        "🔥 POPULAR": ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "LINK"],
        "💰 COMMODITIES & FX": ["GC=F", "CL=F", "EURUSD=X", "^GSPC"], # Vàng, Dầu, Euro, S&P500
        "🚀 MEME & ALTS": ["PEPE", "SHIB", "BONK", "WIF", "FLOKI", "SUI", "APT", "ARB", "OP", "TIA", "SEI", "INJ", "RNDR", "FET", "NEAR", "AVAX", "DOT", "MATIC", "LTC", "BCH", "UNI", "FIL", "ATOM", "IMX", "VET", "GRT", "STX", "THETA", "RUNE", "AAVE", "ALGO", "EGLD", "SAND", "AXS", "MANA", "EOS", "XTZ", "NEO", "MKR", "SNX", "KCS", "LDO", "QNT", "FLOW", "GALA", "CHZ", "CRV", "MINA", "FXS", "KLAY", "HBAR", "FTM", "EOS", "IOTA", "XLM"]
    }
    
    # Gộp lại thành 1 list phẳng để tìm kiếm
    flat_list = []
    for category, items in ASSETS.items():
        flat_list.extend(items)
    
    # Thêm tùy chọn nhập tay nếu muốn
    flat_list.append("...TYPE CUSTOM...")

    # Widget chọn (Có thể gõ phím để tìm)
    selected_asset = st.selectbox(
        "SELECT ASSET", 
        flat_list, 
        index=0, 
        label_visibility="collapsed"
    )

    # Logic xử lý
    if selected_asset == "...TYPE CUSTOM...":
        manual_input = st.text_input("ENTER CUSTOM SYMBOL", "BTC")
        symbol = manual_input.upper()
    else:
        # Nếu chọn Vàng (GC=F) thì giữ nguyên, còn lại là Coin
        symbol = selected_asset

# ... (Tiếp tục phần MAIN INTERFACE bên dưới như cũ) ...

# 4. DASHBOARD
st.write("---")
main_container = st.container()

with main_container:
    with st.spinner(f"⚡ SCANNING MARKET DATA FOR {symbol}..."):
        df, status_msg = fetch_data(symbol)
        
        if df is not None:
            data = analyze_market(df)
            
            if data:
                # --- HÀNG 1: METRICS CHÍNH ---
                m1, m2, m3, m4 = st.columns(4)
                
                with m1: st.markdown(f"""<div class="glass-card"><div class="metric-label">PRICE</div><div class="metric-value" style="color:var(--neon-cyan)">${data['price']:,.2f}</div></div>""", unsafe_allow_html=True)
                
                with m2: 
                    st.markdown(f"""<div class="glass-card" style="border:1px solid {data['color']}"><div class="metric-label" style="color:{data['color']}">AI VERDICT</div><div class="metric-value" style="color:{data['color']}; font-size:20px">{data['signal']}</div></div>""", unsafe_allow_html=True)
                
                with m3:
                    # HIỂN THỊ POC (MỚI)
                    st.markdown(f"""
                    <div class="glass-card">
                        <div class="metric-label">POINT OF CONTROL (POC)</div>
                        <div class="metric-value" style="color:#ff0055">${data['poc']:,.2f}</div>
                        <div style="font-size:12px; color:#888">{data['poc_stat']}</div>
                    </div>""", unsafe_allow_html=True)
                    
                with m4:
                    rsi_col = "var(--neon-green)" if data['rsi'] < 30 else ("var(--neon-pink)" if data['rsi'] > 70 else "#fff")
                    st.markdown(f"""<div class="glass-card"><div class="metric-label">RSI</div><div class="metric-value" style="color:{rsi_col}">{data['rsi']:.1f}</div></div>""", unsafe_allow_html=True)

                # --- HÀNG 2: BIỂU ĐỒ & CHI TIẾT KỸ THUẬT ---
                c_chart, c_info = st.columns([3, 1])
                
                with c_chart:
                    render_chart(symbol)
                
                with c_info:
                    # BẢNG KỸ THUẬT (MỚI)
                    st.markdown(f"""
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
                    
                    # LOG CHIẾN LƯỢC
                    st.markdown(f"""
                    <div class="glass-card" style="border-left: 3px solid var(--neon-cyan);">
                        <div class="metric-label">>_ BATTLE PLAN</div>
                        <div style="font-family:'Share Tech Mono'; font-size:13px; color:#bbb; margin-top:10px; line-height:1.6;">
                            [TARGET]: {symbol}<br>
                            [R1] RESIST: <span style="color:var(--neon-pink)">${data['r1']:,.2f}</span><br>
                            [S1] SUPPRT: <span style="color:var(--neon-green)">${data['s1']:,.2f}</span><br>
                            ----------------<br>
                            ADX STATUS: {data['strength']}<br>
                            WHALE SCAN: {data['vol_status']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        else:
            st.error(f"❌ DATA ERROR: {status_msg}")
            st.info("System fallback active. Try BTC, ETH, SOL.")
