import streamlit as st
import time

# IMPORT MODULES (CÁC PHẦN ĐÃ CHIA NHỎ)
from frontend.styles import get_css
from frontend.charts import render_chart
from backend.data_loader import fetch_data
from backend.logic import analyze_market

# 1. CẤU HÌNH
st.set_page_config(layout="wide", page_title="CYBER TERMINAL PRO", page_icon="🔮", initial_sidebar_state="collapsed")
st.markdown(get_css(), unsafe_allow_html=True)

# 2. GIAO DIỆN HEADER
c1, c2 = st.columns([1, 5])
with c1: st.markdown("## 🔮")
with c2: st.markdown('<div class="cyber-header">CYBER ORACLE v16 (MODULAR)</div>', unsafe_allow_html=True)

# 3. INPUT
col_search, col_status = st.columns([2, 1])
with col_search:
    manual = st.text_input("NETRUNNER INPUT", value="BTC", placeholder="TYPE SYMBOL...", label_visibility="collapsed")
with col_status:
    st.markdown('<div style="text-align:right; font-family:Orbitron; color:#00e5ff; padding-top:10px;">SYSTEM: ONLINE 🟢</div>', unsafe_allow_html=True)

symbol = manual.upper()

# 4. CHẠY LOGIC
st.write("---")
with st.spinner(f"🔮 DECODING MATRIX FOR {symbol}..."):
    # Gọi hàm từ Backend
    df, status = fetch_data(symbol)
    
    if df is not None:
        data = analyze_market(df)
        
        if data:
            # HIỂN THỊ METRICS
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.markdown(f"""<div class="glass-card"><div class="metric-label">PRICE</div><div class="metric-val" style="color:var(--accent)">${data['price']:,.2f}</div></div>""", unsafe_allow_html=True)
            with m2: st.markdown(f"""<div class="glass-card" style="border:1px solid {data['color']}"><div class="metric-label">VERDICT</div><div class="metric-val" style="color:{data['color']}">{data['signal']}</div></div>""", unsafe_allow_html=True)
            with m3: 
                rsi_col = "var(--bull)" if data['rsi'] < 30 else ("var(--bear)" if data['rsi'] > 70 else "#fff")
                st.markdown(f"""<div class="glass-card"><div class="metric-label">RSI</div><div class="metric-val" style="color:{rsi_col}">{data['rsi']:.1f}</div></div>""", unsafe_allow_html=True)
            with m4: st.markdown(f"""<div class="glass-card"><div class="metric-label">VOLATILITY</div><div class="metric-val">{data['vol_state']}</div></div>""", unsafe_allow_html=True)

            # HIỂN THỊ BIỂU ĐỒ & CÔNG CỤ
            c_chart, c_tools = st.columns([3, 1])
            with c_chart:
                render_chart(symbol) # Gọi hàm từ Frontend
            
            with c_tools:
                st.markdown("### 🧬 LEVELS")
                st.markdown(f"""<div class="glass-card"><div style="color:#888; font-size:12px">RESISTANCE</div><div style="color:var(--bear); font-weight:bold; font-size:20px">${data['r1']:,.2f}</div><div style="border-bottom:1px dashed #444; margin:10px 0"></div><div style="color:#888; font-size:12px">SUPPORT</div><div style="color:var(--bull); font-weight:bold; font-size:20px">${data['s1']:,.2f}</div></div>""", unsafe_allow_html=True)
    else:
        st.error(f"❌ CONNECTION LOST: {status}")
