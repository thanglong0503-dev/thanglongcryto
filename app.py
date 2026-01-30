import streamlit as st
import time

# IMPORT
from frontend.styles import get_cyberpunk_css
from frontend.charts import render_chart
from backend.data_loader import fetch_data, fetch_global_indices, fetch_market_overview
from backend.logic import analyze_market

# 1. CẤU HÌNH
st.set_page_config(layout="wide", page_title="CYBER COMMANDER V27", page_icon="🔮", initial_sidebar_state="expanded")
st.markdown(get_cyberpunk_css(), unsafe_allow_html=True)

# 2. POPUP CHART & DATA (ĐÃ SỬA LỖI TRIỆT ĐỂ)
@st.dialog("TACTICAL VIEW", width="large")
def show_popup_data(symbol):
    # Header
    st.markdown(f'<div class="glitch-header" style="font-size:30px; margin-bottom:10px">{symbol}</div>', unsafe_allow_html=True)
    
    with st.spinner("CALCULATING STRATEGY..."):
        df, status = fetch_data(symbol)
        
    if df is not None:
        data = analyze_market(df)
        if data:
            # --- BƯỚC 1: CHUẨN BỊ BIẾN SỐ (ĐỂ TRÁNH LỖI HTML) ---
            # Màu sắc
            c_signal = data['color']
            c_rsi = 'var(--neon-green)' if data['rsi'] < 30 else ('var(--neon-pink)' if data['rsi'] > 70 else '#fff')
            c_stoch = 'var(--neon-green)' if data['stoch_k'] < 20 else '#fff'
            c_trend = 'var(--neon-green)' if data['trend'] == 'UPTREND' else 'var(--neon-pink)'
            
            # Giá trị hiển thị (Format chuỗi trước)
            str_price = f"${data['price']:,.2f}"
            str_poc = f"${data['poc']:,.2f}"
            str_rsi = f"{data['rsi']:.1f}"
            str_stoch = f"{data['stoch_k']:.1f}"
            
            # Battle Plan Values
            str_entry = f"${data['price']:,.2f}"
            str_stop = f"${data['s1']*0.99:,.2f}"
            str_target = f"${data['r1']:,.2f}"

            # --- BƯỚC 2: HIỂN THỊ GIAO DIỆN ---
            
            # Hàng 1: HUD
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"""<div class="glass-card"><div class="metric-label">CURRENT PRICE</div><div class="metric-val">{str_price}</div></div>""", unsafe_allow_html=True)
            with c2: st.markdown(f"""<div class="glass-card" style="border-color:{c_signal}"><div class="metric-label" style="color:{c_signal}">AI SIGNAL</div><div class="metric-val" style="color:{c_signal}">{data['signal']}</div></div>""", unsafe_allow_html=True)
            with c3: st.markdown(f"""<div class="glass-card"><div class="metric-label">POINT OF CONTROL</div><div class="metric-val" style="color:#ff0055">{str_poc}</div></div>""", unsafe_allow_html=True)
            
            # Hàng 2: Chart & Plan
            c_chart, c_plan = st.columns([2, 1])
            
            with c_chart:
                render_chart(symbol, height=500)
                
            with c_plan:
                # --- BƯỚC 1: CHUẨN BỊ SỐ LIỆU & MÀU SẮC (SMC) ---
                smc_info = data.get('smc')
                if smc_info:
                    # Nếu tìm thấy dấu chân cá mập
                    smc_text = f"{smc_info['type']}<br>Range: ${smc_info['bottom']:,.2f} - ${smc_info['top']:,.2f}"
                    smc_color = "#00ff9f" if "BULL" in smc_info['type'] else "#ff0055"
                else:
                    # Nếu không thấy
                    smc_text = "NO CLEAR ZONE"
                    smc_color = "#444"

                # Chuẩn bị các biến giá (Entry, Stop, Target)
                str_entry = f"${data['price']:,.2f}"
                str_stop = f"${data['s1']*0.99:,.2f}"
                str_target = f"${data['r1']:,.2f}"
                
                # Màu Stoch
                c_stoch = 'var(--neon-green)' if data['stoch_k'] < 20 else '#fff'

                # --- BƯỚC 2: VẼ GIAO DIỆN BATTLE PLAN (QUAN TRỌNG: unsafe_allow_html=True) ---
                st.markdown(f"""
                <div class="glass-card">
                    <div class="metric-label">OSCILLATORS</div>
                    <div style="font-family:'Share Tech Mono'; color:#ccc; font-size:13px; margin-top:5px">
                        <div style="display:flex; justify-content:space-between;"><span>RSI (14)</span><span>{data['rsi']:.1f}</span></div>
                        <div style="display:flex; justify-content:space-between;"><span>Stoch K</span><span style="color:{c_stoch}">{data['stoch_k']:.1f}</span></div>
                    </div>
                </div>
                
                <div class="glass-card" style="border-left: 3px solid var(--neon-cyan);">
                    <div class="metric-label" style="color:var(--neon-cyan); margin-bottom:10px">>_ BATTLE PLAN</div>
                    
                    <div style="font-family:'Share Tech Mono'; font-size:13px; color:#bbb; line-height:1.6;">
                        <div style="border:1px dashed {smc_color}; background:rgba(0,0,0,0.3); padding:8px; margin-bottom:12px; border-radius:4px; text-align:center">
                            <div style="font-size:10px; color:{smc_color}; letter-spacing:1px; margin-bottom:4px">🦈 SMART MONEY ZONE</div>
                            <strong style="color:#fff; font-size:14px">{smc_text}</strong>
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
                """, unsafe_allow_html=True)
                # --- PHẦN LOGIC SMC (Thêm đoạn này vào trước st.markdown) ---
                smc_info = data.get('smc')
                if smc_info:
                    # Nếu tìm thấy dấu chân cá mập
                    smc_text = f"{smc_info['type']}<br>Range: ${smc_info['bottom']:,.2f} - ${smc_info['top']:,.2f}"
                    smc_color = "#00ff9f" if "BULL" in smc_info['type'] else "#ff0055"
                else:
                    # Nếu không thấy gì
                    smc_text = "NO CLEAR ZONE"
                    smc_color = "#444" # Màu xám tối

                # --- PHẦN HIỂN THỊ (SMC RADAR + BATTLE PLAN) ---
                st.markdown(f"""
                <div class="glass-card" style="border-left: 3px solid var(--neon-cyan);">
                    <div class="metric-label" style="color:var(--neon-cyan); margin-bottom:10px">>_ BATTLE PLAN</div>
                    
                    <div style="font-family:'Share Tech Mono'; font-size:13px; color:#bbb; line-height:1.6;">
                        <div style="border:1px dashed {smc_color}; background:rgba(0,0,0,0.3); padding:8px; margin-bottom:12px; border-radius:4px; text-align:center">
                            <div style="font-size:10px; color:{smc_color}; letter-spacing:1px; margin-bottom:4px">🦈 SMART MONEY ZONE</div>
                            <strong style="color:#fff; font-size:14px">{smc_text}</strong>
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
                """, unsafe_allow_html=True)

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
            </div>
            """, unsafe_allow_html=True)

# ==============================================================================
# ==============================================================================
# MODE 1: MARKET GRID
# ==============================================================================
if mode == "🌐 MARKET GRID":
    st.markdown('<div class="glitch-header">GLOBAL MARKET MONITOR</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([6, 1])
    with c1: st.caption("TOP 20 MARKET CAP | CLICK 'SCAN' FOR BATTLE PLAN")
    with c2: 
        if st.button("🔄 REFRESH"): st.rerun()

    df = fetch_market_overview()
    if df is not None:
        # Cập nhật Header thêm cột CAP và VOL
        st.markdown("""
        <div style="display:flex; padding:10px; background:#000; border-bottom:1px solid #333; color:#666; font-family:'Share Tech Mono'; font-size:12px">
            <div style="width:10%">ASSET</div>
            <div style="width:20%; text-align:right">PRICE</div>
            <div style="width:15%; text-align:right">24H %</div>
            <div style="width:15%; text-align:right">VOL (24H)</div>  <div style="width:15%; text-align:right">M.CAP</div>      <div style="width:10%; text-align:center">TREND</div>
            <div style="width:15%; text-align:right">ACTION</div>
        </div>
        """, unsafe_allow_html=True)

        for index, row in df.iterrows():
            sym = row['SYMBOL']
            price = row['PRICE ($)']
            change = row['24H %']
            trend = row['TREND']
            vol = row.get('VOL', '---') # Lấy giá trị Volume
            cap = row.get('CAP', '---') # Lấy giá trị Cap
            
            color = "#00ffa3" if change >= 0 else "#ff0055"
            
            # Chia lại tỷ lệ cột (Layout 7 cột)
            c_asset, c_price, c_change, c_vol, c_cap, c_trend, c_btn = st.columns([1.0, 2.0, 1.5, 1.5, 1.5, 1.0, 1.5])
            
            with c_asset: st.markdown(f"<div style='font-family:Orbitron; font-weight:bold; color:#fff; padding-top:12px'>{sym}</div>", unsafe_allow_html=True)
            with c_price: st.markdown(f"<div style='font-family:Share Tech Mono; text-align:right; font-size:16px; color:#e0e0e0; padding-top:12px'>${price:,.4f}</div>", unsafe_allow_html=True)
            with c_change: st.markdown(f"<div style='font-family:Share Tech Mono; text-align:right; color:{color}; padding-top:12px'>{change:+.2f}%</div>", unsafe_allow_html=True)
            
            # --- HIỂN THỊ CỘT MỚI ---
            with c_vol: st.markdown(f"<div style='font-family:Share Tech Mono; text-align:right; color:#888; padding-top:12px; font-size:14px'>{vol}</div>", unsafe_allow_html=True)
            with c_cap: st.markdown(f"<div style='font-family:Share Tech Mono; text-align:right; color:#aaa; padding-top:12px; font-size:14px'>{cap}</div>", unsafe_allow_html=True)
            
            with c_trend: st.markdown(f"<div style='text-align:center; font-size:18px; padding-top:8px'>{trend}</div>", unsafe_allow_html=True)
            with c_btn:
                if st.button(f"⚡ SCAN", key=f"btn_{sym}"): show_popup_data(sym)
            
            st.markdown("<div style='height:1px; background:#111; margin:0'></div>", unsafe_allow_html=True)

# ==============================================================================
# ... (Phần code trên giữ nguyên) ...

# ==============================================================================
# MODE 2: DEEP SCANNER
# ==============================================================================
elif mode == "🔮 DEEP SCANNER":
    st.markdown('<div class="glitch-header">DEEP SCANNER</div>', unsafe_allow_html=True)
    
    col_search, col_pad = st.columns([1, 2])
    with col_search:
        # --- DANH SÁCH COIN KHỔNG LỒ (ĐÃ ĐƯỢC PHÂN LOẠI) ---
        HUGE_ASSETS = [
            # 👑 TOP KINGS
            "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "AVAX", "DOT", "LINK", "TRX", "TON",
            # 🚀 MEME GODS
            "DOGE", "SHIB", "PEPE", "WIF", "BONK", "FLOKI", "BOME", "MEME", "TURBO", "BRETT", "POPCAT", "NEIRO",
            # 🤖 AI & DATA
            "FET", "RNDR", "WLD", "NEAR", "TAO", "JASMY", "ARKM", "GRT", "THETA", "OCEAN", "AGIX",
            # ⛓️ LAYER 1 & 2
            "SUI", "APT", "ARB", "OP", "MATIC", "SEI", "INJ", "TIA", "KAS", "FTM", "ALGO", "ATOM", "HBAR", "ICP", "ETC", "LTC", "BCH",
            # 🏦 DEFI & RWA
            "UNI", "AAVE", "MKR", "LDO", "ONDO", "PENDLE", "JUP", "RUNE", "SNX", "CRV", "DYDX", "GMX",
            # 🎮 GAME & METAVERSE
            "IMX", "GALA", "SAND", "MANA", "AXS", "APE", "BEAM", "PIXEL", "XAI", "NOT"
        ]
        
        # Sắp xếp theo bảng chữ cái cho dễ tìm (Trừ BTC, ETH, SOL ở đầu)
        top_3 = ["BTC", "ETH", "SOL"]
        others = sorted([x for x in HUGE_ASSETS if x not in top_3])
        FINAL_LIST = top_3 + others

        # Widget chọn (Có thể gõ phím để tìm kiếm trong list này)
        selected_asset = st.selectbox(
            "SELECT ASSET", 
            FINAL_LIST + ["...CUSTOM..."], # Vẫn giữ Custom để nhập con lạ
            label_visibility="collapsed"
        )

        # Logic xử lý nhập tay
        if selected_asset == "...CUSTOM...":
            symbol = st.text_input("TYPE SYMBOL (Ex: BTC)", "BTC").upper()
        else:
            symbol = selected_asset

    st.write("---")
    
    # ... (Phần logic tải dữ liệu và hiển thị bên dưới GIỮ NGUYÊN) ...
    with st.spinner(f"⚡ DECRYPTING {symbol}..."):
        df, status = fetch_data(symbol)
        # ... (Code cũ của Ngài ở đoạn dưới này vẫn dùng tốt) ...
        if df is not None:
            data = analyze_market(df)
            if data:
                # Metrics
                c_signal = data['color']
                str_price = f"${data['price']:,.2f}"
                str_poc = f"${data['poc']:,.2f}"
                str_rsi = f"{data['rsi']:.1f}"

                m1, m2, m3, m4 = st.columns(4)
                with m1: st.markdown(f"""<div class="glass-card"><div class="metric-label">PRICE</div><div class="metric-val" style="color:var(--neon-cyan)">{str_price}</div></div>""", unsafe_allow_html=True)
                with m2: st.markdown(f"""<div class="glass-card" style="border:1px solid {c_signal}"><div class="metric-label" style="color:{c_signal}">VERDICT</div><div class="metric-val" style="color:{c_signal}">{data['signal']}</div></div>""", unsafe_allow_html=True)
                with m3: st.markdown(f"""<div class="glass-card"><div class="metric-label">POC</div><div class="metric-val" style="color:#ff0055">{str_poc}</div></div>""", unsafe_allow_html=True)
                with m4: st.markdown(f"""<div class="glass-card"><div class="metric-label">RSI</div><div class="metric-val" style="color:#fff">{str_rsi}</div></div>""", unsafe_allow_html=True)
                
                # Chart
                c_chart, c_info = st.columns([3, 1])
                with c_chart: render_chart(symbol, height=800)
                with c_info:
                    # Tái sử dụng logic biến số để an toàn
                    c_stoch = 'var(--neon-green)' if data['stoch_k'] < 20 else '#fff'
                    st.markdown(f"""
                    <div class="glass-card">
                        <div class="metric-label">OSCILLATORS</div>
                        <div style="margin-top:10px; font-family:'Share Tech Mono'; color:#ccc; font-size:14px;">
                            <div style="display:flex; justify-content:space-between;"><span>Stoch K</span><span style="color:{c_stoch}">{data['stoch_k']:.1f}</span></div>
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
