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

# 3. INPUT
col_search, col_pad = st.columns([1, 2])
with col_search:
    manual = st.text_input("COMMAND_LINE", value="BTC", placeholder="ENTER SYMBOL...", label_visibility="collapsed")
symbol = manual.upper()

# 4. DASHBOARD
st.write("---")
main_container = st.container()

with main_container:
    with st.spinner(f"⚡ SCANNING MARKET DATA FOR {symbol}..."):
        df, status_msg = fetch_data(symbol)
        
        if df is not None:
            data = analyze_market(df)
            
            if data:
                # --- HÀNG 1: METRICS CHÍNH (GIÁ & TÍN HIỆU) ---
                m1, m2, m3, m4 = st.columns(4)
                
                with m1: st.markdown(f"""<div class="glass-card"><div class="metric-label">ASSET PRICE</div><div class="metric-value" style="color:var(--neon-cyan)">${data['price']:,.2f}</div></div>""", unsafe_allow_html=True)
                
                with m2: 
                    st.markdown(f"""<div class="glass-card" style="border:1px solid {data['color']}"><div class="metric-label" style="color:{data['color']}">AI VERDICT</div><div class="metric-value" style="color:{data['color']}; font-size:24px">{data['signal']}</div></div>""", unsafe_allow_html=True)
                
                with m3:
                    adx_col = "var(--neon-green)" if data['strength'] == "STRONG" else "#666"
                    st.markdown(f"""<div class="glass-card"><div class="metric-label">TREND STRENGTH (ADX)</div><div class="metric-value" style="color:{adx_col}">{data['adx']:.1f} <span style="font-size:12px">({data['strength']})</span></div></div>""", unsafe_allow_html=True)
                    
                with m4:
                    vol_col = "var(--neon-pink)" if "WHALE" in data['vol_status'] else "#fff"
                    st.markdown(f"""<div class="glass-card"><div class="metric-label">VOLUME RADAR</div><div class="metric-value" style="color:{vol_col}; font-size:20px">{data['vol_status']}</div></div>""", unsafe_allow_html=True)

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
