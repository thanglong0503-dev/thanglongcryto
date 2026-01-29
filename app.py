# app.py
import streamlit as st
import time

# IMPORT MODULES
from frontend.styles import get_cyberpunk_css
from frontend.charts import render_chart
from backend.data_loader import fetch_data
from backend.logic import analyze_market

# 1. CẤU HÌNH TRANG (Full Width)
st.set_page_config(layout="wide", page_title="CYBERPUNK TERMINAL", page_icon="🔮", initial_sidebar_state="collapsed")
st.markdown(get_cyberpunk_css(), unsafe_allow_html=True)

# 2. HEADER KHỦNG (GLITCH EFFECT)
c_head, c_status = st.columns([3, 1])
with c_head:
    st.markdown('<div class="glitch-header">CYBER ORACLE <span style="font-size:20px; vertical-align:top">v17</span></div>', unsafe_allow_html=True)
with c_status:
    st.markdown(f"""
    <div style="text-align:right; font-family:'Share Tech Mono'; color:#00ff9f; padding-top:15px;">
        SERVER: ONLINE_ <span class="blinking-cursor"></span><br>
        <span style="font-size:10px; color:#666">LATENCY: 12ms</span>
    </div>
    """, unsafe_allow_html=True)

# 3. INPUT BAR (Như dòng lệnh)
col_search, col_pad = st.columns([1, 2])
with col_search:
    manual = st.text_input("COMMAND_LINE", value="BTC", placeholder="ENTER TARGET SYMBOL...", label_visibility="collapsed")
symbol = manual.upper()

# 4. MAIN INTERFACE
st.write("---")

# Container chính
main_container = st.container()

with main_container:
    # Gọi Backend
    with st.spinner(f"⚡ ESTABLISHING NEURAL LINK TO {symbol}..."):
        df, status_msg = fetch_data(symbol)
        
        if df is not None:
            data = analyze_market(df)
            
            if data:
                # --- HÀNG 1: 4 THẺ METRIC (HUD) ---
                m1, m2, m3, m4 = st.columns(4)
                
                with m1:
                    st.markdown(f"""
                    <div class="glass-card">
                        <div class="metric-label">ASSET PRICE</div>
                        <div class="metric-value" style="color:var(--neon-cyan)">${data['price']:,.2f}</div>
                    </div>""", unsafe_allow_html=True)
                
                with m2:
                    # Màu động cho Verdict
                    v_color = data['color'] # Lấy màu từ Logic
                    st.markdown(f"""
                    <div class="glass-card" style="box-shadow: inset 0 0 20px {v_color}20;">
                        <div class="metric-label" style="color:{v_color}">AI PREDICTION</div>
                        <div class="metric-value" style="color:{v_color}; font-size:24px">{data['signal']}</div>
                    </div>""", unsafe_allow_html=True)
                    
                with m3:
                    rsi_col = "#fff"
                    if data['rsi'] < 30: rsi_col = "var(--neon-green)"
                    elif data['rsi'] > 70: rsi_col = "var(--neon-pink)"
                    
                    st.markdown(f"""
                    <div class="glass-card">
                        <div class="metric-label">RSI MOMENTUM</div>
                        <div class="metric-value" style="color:{rsi_col}">{data['rsi']:.1f}</div>
                        <div style="height:4px; width:100%; background:#333; margin-top:5px;">
                            <div style="height:100%; width:{data['rsi']}%; background:{rsi_col}"></div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                    
                with m4:
                    st.markdown(f"""
                    <div class="glass-card">
                        <div class="metric-label">VOLATILITY STATE</div>
                        <div class="metric-value" style="font-size:22px; color:var(--neon-yellow)">{data['vol_state']}</div>
                    </div>""", unsafe_allow_html=True)

                # --- HÀNG 2: CHART + STRATEGY ---
                c_chart, c_side = st.columns([3, 1])
                
                with c_chart:
                    # Gọi Chart
                    render_chart(symbol)
                
                with c_side:
                    # Strategy Panel
                    st.markdown(f"""
                    <div class="glass-card">
                        <div class="metric-label">KEY LEVELS</div>
                        <div style="display:flex; justify-content:space-between; margin-top:10px; color:var(--neon-pink)">
                            <span>RESISTANCE</span>
                            <span style="font-weight:bold">${data['r1']:,.2f}</span>
                        </div>
                        <div style="width:100%; height:1px; background:#333; margin:10px 0"></div>
                        <div style="display:flex; justify-content:space-between; color:var(--neon-green)">
                            <span>SUPPORT</span>
                            <span style="font-weight:bold">${data['s1']:,.2f}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Log hành động
                    atr_sim = data['price'] * 0.02
                    sl = data['price'] - atr_sim if "UP" in data['signal'] else data['price'] + atr_sim
                    tp = data['price'] + (atr_sim*2) if "UP" in data['signal'] else data['price'] - (atr_sim*2)
                    
                    st.markdown(f"""
                    <div class="glass-card" style="border-left: 3px solid var(--neon-cyan);">
                        <div class="metric-label">>_ STRATEGY LOG</div>
                        <div style="font-family:'Share Tech Mono'; font-size:13px; color:#bbb; margin-top:10px; line-height:1.6;">
                            [TARGET]: {symbol}<br>
                            [MODE]: SCALPING<br>
                            ----------------<br>
                            <span style="color:#fff">ENTRY: ${data['price']:,.2f}</span><br>
                            <span style="color:var(--neon-pink)">STOP : ${sl:,.2f}</span><br>
                            <span style="color:var(--neon-green)">PROF : ${tp:,.2f}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        else:
            st.error(f"❌ CONNECTION ERROR: {status_msg}")
            st.info("System switching to Safe Mode... Try BTC or ETH.")

# FOOTER LOG
st.markdown("""
<div class="system-log">
    Running process: Oracle_v17.exe | Memory: 64TB | <span style="color:var(--neon-cyan)">CONNECTED TO NEURAL NET</span>
</div>
""", unsafe_allow_html=True)
