import streamlit as st
import time

# IMPORT MODULES
from frontend.styles import get_cyberpunk_css
from frontend.charts import render_chart
from backend.data_loader import fetch_data, fetch_global_indices, fetch_market_overview
from backend.logic import analyze_market

# 1. CẤU HÌNH TRANG (BẮT BUỘC PHẢI Ở DÒNG ĐẦU TIÊN CỦA STREAMLIT)
st.set_page_config(layout="wide", page_title="CYBERPUNK V21", page_icon="🔮", initial_sidebar_state="collapsed")
st.markdown(get_cyberpunk_css(), unsafe_allow_html=True)

# 2. HEADER (CHỈ GIỮ LẠI 1 CÁI NÀY THÔI)
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

# --- PHẦN 2: BẢNG ĐIỆN TỬ TỔNG HỢP ---
with st.expander("📊 LIVE MARKET OVERVIEW (TOP COINS)", expanded=True):
    df_overview = fetch_market_overview()
    
    if df_overview is not None:
        st.dataframe(
            df_overview,
            use_container_width=True,
            hide_index=True,
            column_config={
                "SYMBOL": st.column_config.TextColumn("Asset", help="Tên tài sản"),
                "PRICE ($)": st.column_config.NumberColumn("Price", format="$%.4f"),
                "24H %": st.column_config.NumberColumn("24h Change", format="%.2f%%"),
                "TREND": st.column_config.TextColumn("Trend")
            }
        )
    else:
        st.warning("⚠️ Market data syncing... Please wait.")

# --- PHẦN 3: INPUT VÀ LOGIC CHÍNH ---
col_search, col_pad = st.columns([1, 2])
with col_search:
    # DANH SÁCH TÀI SẢN
    ASSETS = {
        "🔥 POPULAR": ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "LINK"],
        "💰 COMMODITIES & FX": ["GC=F", "CL=F", "EURUSD=X", "^GSPC"], 
        "🚀 MEME & ALTS": ["PEPE", "SHIB", "BONK", "WIF", "FLOKI", "SUI", "APT", "ARB", "OP", "TIA", "SEI", "INJ", "RNDR", "FET", "NEAR", "AVAX", "DOT", "MATIC", "LTC", "BCH", "UNI", "FIL", "ATOM", "IMX", "VET", "GRT", "STX", "THETA", "RUNE", "AAVE", "ALGO", "EGLD", "SAND", "AXS", "MANA", "EOS", "XTZ", "NEO", "MKR", "SNX", "KCS", "LDO", "QNT", "FLOW", "GALA", "CHZ", "CRV", "MINA", "FXS", "KLAY", "HBAR", "FTM", "EOS", "IOTA", "XLM"]
    }
    
    flat_list = []
    for category, items in ASSETS.items():
        flat_list.extend(items)
    flat_list.append("...TYPE CUSTOM...")

    selected_asset = st.selectbox("SELECT ASSET", flat_list, index=0, label_visibility="collapsed")

    if selected_asset == "...TYPE CUSTOM...":
        manual_input = st.text_input("ENTER CUSTOM SYMBOL", "BTC")
        symbol = manual_input.upper()
    else:
        symbol = selected_asset

# MAIN INTERFACE
st.write("---")
main_container = st.container()

with main_container:
    with st.spinner(f"⚡ SCANNING DATA FOR {symbol}..."):
        df, status_msg = fetch_data(symbol)
        
        if df is not None:
            data = analyze_market(df)
            
            if data:
                # HÀNG 1: METRICS
                m1, m2, m3, m4 = st.columns(4)
                
                with m1: st.markdown(f"""<div class="glass-card"><div class="metric-label">PRICE</div><div class="metric-value" style="color:var(--neon-cyan)">${data['price']:,.2f}</div></div>""", unsafe_allow_html=True)
                
                with m2: st.markdown(f"""<div class="glass-card" style="border:1px solid {data['color']}"><div class="metric-label" style="color:{data['color']}">AI VERDICT</div><div class="metric-value" style="color:{data['color']}; font-size:20px">{data['signal']}</div></div>""", unsafe_allow_html=True)
                
                with m3:
                    # POC Metric
                    st.markdown(f"""<div class="glass-card"><div class="metric-label">POINT OF CONTROL</div><div class="metric-value" style="color:#ff0055">${data['poc']:,.2f}</div><div style="font-size:12px; color:#888">{data['poc_stat']}</div></div>""", unsafe_allow_html=True)
                    
                with m4:
                    rsi_col = "var(--neon-green)" if data['rsi'] < 30 else ("var(--neon-pink)" if data['rsi'] > 70 else "#fff")
                    st.markdown(f"""<div class="glass-card"><div class="metric-label">RSI</div><div class="metric-value" style="color:{rsi_col}">{data['rsi']:.1f}</div></div>""", unsafe_allow_html=True)

                # HÀNG 2: CHART & INFO
                c_chart, c_info = st.columns([3, 1])
                
                with c_chart:
                    render_chart(symbol)
                
                with c_info:
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
            st.info("Please select another asset.")
