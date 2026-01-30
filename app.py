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
st.set_page_config(layout="wide", page_title="CYBER COMMANDER V35", page_icon="🔮", initial_sidebar_state="expanded")
st.markdown(get_cyberpunk_css(), unsafe_allow_html=True)

# --- HÀM TẠO HTML (FIX LỖI HIỂN THỊ) ---
def create_battle_plan_html(data):
    """Hàm này tạo mã HTML sạch, không bị lỗi thụt dòng"""
    # 1. Chuẩn bị số liệu
    str_entry = f"${data['price']:,.2f}"
    str_stop = f"${data['s1']*0.99:,.2f}"
    str_target = f"${data['r1']:,.2f}"
    
    # 2. Xử lý SMC
    smc_info = data.get('smc')
    if smc_info:
        smc_text = f"{smc_info['type']}<br>Range: ${smc_info['bottom']:,.2f} - ${smc_info['top']:,.2f}"
        smc_color = "#00ff9f" if "BULL" in smc_info['type'] else "#ff0055"
    else:
        smc_text = "NO CLEAR ZONE"
        smc_color = "#444"

    # 3. Trả về HTML (Viết liền mạch để không bị lỗi Markdown)
    return f"""
    <div class="glass-card" style="border-left: 3px solid var(--neon-cyan);">
        <div class="metric-label" style="color:var(--neon-cyan); margin-bottom:10px">>_ BATTLE PLAN</div>
        <div style="font-family:'Share Tech Mono'; font-size:13px; color:#bbb; line-height:1.6;">
            <div style="border:1px dashed {smc_color}; background:rgba(0,0,0,0.3); padding:8px; margin-bottom:12px; border-radius:4px; text-align:center">
                <div style="font-size:10px; color:{smc_color}; letter-spacing:1px; margin-bottom:4px">🦈 SMART MONEY ZONE</div>
                <strong style="color:#fff; font-size:13px">{smc_text}</strong>
            </div>
            <div style="font-size:11px; color:#666">ENTRY SETUP</div>
            🚀 <strong>ENTRY:</strong> <span style="color:#fff">{str_entry}</span><br>
            🛑 <strong>STOP:</strong> <span style="color:#ff0055">{str_stop}</span><br>
            💰 <strong>TARGET:</strong> <span style="color:#00ff9f">{str_target}</span>
            <hr style="border-color:#333; margin:8px 0">
            <div style="font-size:11px; color:#666">MARKET SCAN</div>
            <strong>ADX:</strong> {data['strength']}<br>
            <strong>VOL:</strong> {data['vol_status']}
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
# MODE 2: DEEP SCANNER
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
        df, status = fetch_data(symbol)
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
# ... (Sau khi kết thúc with c_info của code cũ) ...

                st.write("---")
                
                st.write("---")
                
                # NÚT KÍCH HOẠT AI (PHIÊN BẢN SCIKIT-LEARN)
                st.markdown('<div class="glitch-header" style="font-size:20px; color:#bc13fe">🧠 CYBER AI CORE</div>', unsafe_allow_html=True)
                
                if st.button("RUN NEURAL PREDICTION"):
                    with st.spinner("⚡ AI IS COMPUTING (RANDOM FOREST)..."):
                        # Gọi hàm mới
                        ai_res = run_ai_forecast(df)
                        
                        if ai_res:
                            col_ai1, col_ai2 = st.columns([1, 3])
                            
                            with col_ai1:
                                diff_color = "#00ff9f" if ai_res['diff_pct'] > 0 else "#ff0055"
                                st.markdown(f"""
                                <div class="glass-card" style="border: 1px solid #bc13fe; text-align:center">
                                    <div style="font-size:12px; color:#bc13fe; margin-bottom:5px">AI TARGET (12H)</div>
                                    <div style="font-family:'Orbitron'; font-size:24px; color:#fff">${ai_res['predicted_price']:,.2f}</div>
                                    <div style="font-family:'Share Tech Mono'; font-size:16px; color:{diff_color}; margin-top:5px">
                                        {ai_res['trend']} ({ai_res['diff_pct']:+.2f}%)
                                    </div>
                                    <div style="font-size:10px; color:#666; margin-top:10px">Model: Random Forest</div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                            with col_ai2:
                                # Vẽ biểu đồ mới
                                fig_ai = plot_ai_chart(symbol, ai_res)
                                st.plotly_chart(fig_ai, use_container_width=True)
                        else:
                            st.error("NOT ENOUGH DATA FOR AI TRAINING")
