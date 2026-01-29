import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import streamlit.components.v1 as components
import time
import numpy as np

# ==============================================================================
# 1. UI CONFIGURATION
# ==============================================================================
st.set_page_config(layout="wide", page_title="Oracle Omni-Connect", page_icon="⚡", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500;700&display=swap');

    :root {
        --bg-color: #050505;
        --card-bg: #0f0f0f;
        --accent: #ffeb3b; 
        --bull: #00ffa3;
        --bear: #ff0055;
        --text: #e0e0e0;
        --border: #333;
    }

    .stApp { background-color: var(--bg-color) !important; color: var(--text) !important; font-family: 'Rajdhani', sans-serif !important; }
    
    .oracle-header {
        font-family: 'Orbitron', sans-serif; font-size: 32px;
        background: -webkit-linear-gradient(45deg, var(--accent), #ff9100);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: bold; text-shadow: 0 0 20px rgba(255, 235, 59, 0.5);
    }

    .glass-card {
        background: rgba(20, 20, 20, 0.7); border: 1px solid var(--border);
        border-radius: 8px; padding: 15px; margin-bottom: 10px;
    }
    
    .metric-val { font-size: 24px; font-weight: bold; font-family: 'Orbitron'; }
    
    /* INPUT FIX */
    div[data-baseweb="input"] { background-color: #1a1a1a !important; border: 1px solid #333 !important; }
    input[type="text"] { color: var(--accent) !important; font-family: 'Orbitron', sans-serif !important; }
    div[data-baseweb="select"] > div { background-color: #1a1a1a !important; color: #fff !important; }
    ul[data-baseweb="menu"] { background-color: #111 !important; border: 1px solid #333 !important; }
    li[data-baseweb="option"] { color: #eee !important; }
    li[data-baseweb="option"]:hover { background-color: #222 !important; color: var(--accent) !important; }
    
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. OMNI ENGINE (MULTI-EXCHANGE ROUTING)
# ==============================================================================
class OmniEngine:
    def __init__(self):
        # Khởi tạo danh sách các sàn dự phòng (Public API)
        self.exchanges = [
            ccxt.binanceus({'enableRateLimit': True}), # Ưu tiên 1
            ccxt.bybit({'enableRateLimit': True}),     # Ưu tiên 2 (Rất mượt)
            ccxt.kraken({'enableRateLimit': True}),    # Ưu tiên 3
            ccxt.gateio({'enableRateLimit': True}),    # Ưu tiên 4
            ccxt.kucoin({'enableRateLimit': True})     # Ưu tiên 5
        ]

    def fetch_ohlcv_robust(self, symbol, timeframe, limit=200):
        """
        Hàm này sẽ thử từng sàn trong danh sách.
        Nếu sàn A lỗi -> Nhảy sang sàn B -> Sàn C...
        Đồng thời thử cả cặp /USDT và /USD
        """
        variations = [symbol, symbol.replace('USDT', 'USD'), symbol.replace('USD', 'USDT')]
        
        for exc in self.exchanges:
            for sym in variations:
                try:
                    # Thử tải dữ liệu
                    bars = exc.fetch_ohlcv(sym, timeframe, limit=limit)
                    if len(bars) > 50: # Nếu dữ liệu trả về đủ tốt
                        df = pd.DataFrame(bars, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                        df['t'] = pd.to_datetime(df['t'], unit='ms')
                        df.set_index('t', inplace=True)
                        return df, exc.name, sym # Trả về Data, Tên sàn, Mã coin
                except:
                    continue # Thử sàn tiếp theo hoặc mã tiếp theo
        
        return pd.DataFrame(), "None", symbol

    def get_safe_col(self, df, pattern):
        cols = [c for c in df.columns if c.startswith(pattern)]
        return cols[0] if cols else None

    def analyze_live(self, raw_symbol):
        # 1. Fetch Data (Auto-Routing)
        df, source_name, final_symbol = self.fetch_ohlcv_robust(raw_symbol, '1h', 200)
        
        if df.empty: return None, "Không tìm thấy dữ liệu ở bất kỳ sàn nào."
        
        # 2. Indicators Calculation (Safe Mode)
        try:
            df.ta.bbands(length=20, std=2, append=True)
            df.ta.rsi(length=14, append=True)
            
            curr = df.iloc[-1]
            bbl_col = self.get_safe_col(df, 'BBL')
            bbu_col = self.get_safe_col(df, 'BBU')
            rsi_col = self.get_safe_col(df, 'RSI')
            
            if not bbl_col or not bbu_col or not rsi_col: return None, "Lỗi tính chỉ báo."

            price = curr['c']
            bbl_val = curr[bbl_col]
            bbu_val = curr[bbu_col]
            rsi_val = curr[rsi_col]
            
            signal = "NEUTRAL (CHỜ)"
            if price < bbl_val and rsi_val < 35: signal = "SCALP BUY ⚡"
            elif price > bbu_val and rsi_val > 65: signal = "SCALP SELL ⚡"
                
            return {
                "signal": signal,
                "price": price,
                "rsi": rsi_val,
                "bbl": bbl_val,
                "bbu": bbu_val,
                "source": source_name,
                "symbol": final_symbol
            }, None
        except Exception as e:
            return None, str(e)

    def run_backtest(self, raw_symbol):
        # Dùng hàm Robust để lấy dữ liệu backtest luôn
        df, _, _ = self.fetch_ohlcv_robust(raw_symbol, '1h', 1000)
        
        if df.empty or len(df) < 50: return None, "Dữ liệu không đủ."
            
        try:
            df.ta.bbands(length=20, std=2, append=True)
            df['RSI'] = ta.rsi(df['c'], length=14)
        except: return None, "Lỗi tính chỉ báo."
            
        bbl_col = self.get_safe_col(df, 'BBL')
        bbm_col = self.get_safe_col(df, 'BBM')
        
        if not bbl_col: return None, "Không tìm thấy BB."

        capital = 1000
        position = None; entry_price = 0; stop_loss = 0
        trades = []; wins = 0; losses = 0
        
        for i in range(50, len(df)):
            row = df.iloc[i]
            long_cond = (row['c'] < row[bbl_col]) and (row['RSI'] < 30)
            tp_cond = (row['c'] >= row[bbm_col])
            
            if position == 'LONG':
                if row['l'] <= stop_loss:
                    capital *= 0.97; losses += 1; position = None
                    trades.append({'Result': 'LOSS 🛑', 'PnL': '-3%'})
                elif tp_cond:
                    pnl = (row['c'] - entry_price) / entry_price
                    capital *= (1 + pnl)
                    wins += 1; position = None
                    trades.append({'Result': 'WIN ✅', 'PnL': f'{pnl*100:.2f}%'})
            
            if position is None and long_cond:
                position = 'LONG'; entry_price = row['c']; stop_loss = entry_price * 0.97

        total = wins + losses
        winrate = (wins/total*100) if total > 0 else 0
        ret = (capital - 1000) / 1000 * 100
        
        return trades, {"final": capital, "return": ret, "winrate": winrate, "total": total}

engine = OmniEngine()

# ==============================================================================
# 3. UI DASHBOARD
# ==============================================================================

c1, c2 = st.columns([1, 5])
with c1: st.markdown("## ⚡")
with c2: st.markdown('<div class="oracle-header">OMNI SCALPER v13</div>', unsafe_allow_html=True)

col_search, col_list = st.columns([1, 2])
with col_search:
    manual = st.text_input("INPUT", placeholder="Type Symbol (e.g. SUI)...", label_visibility="collapsed")
with col_list:
    # List mẫu vì load dynamic có thể chậm
    coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'DOGE/USDT', 'SUI/USDT', 'PEPE/USDT']
    selected = st.selectbox("LIST", coins, label_visibility="collapsed")

target = f"{manual.upper()}/USDT" if manual else selected
if "/USDT" not in target and "/USD" not in target: target += "/USDT"

tab_live, tab_backtest = st.tabs(["🚀 LIVE SCALP", "🔙 BACKTEST"])

# ================= TAB 1: LIVE =================
with tab_live:
    st.write("---")
    with st.spinner(f"🌐 CONNECTING SATELLITES FOR {target}..."):
        data, err = engine.analyze_live(target)
        
        if data:
            curr_price = data['price']
            signal = data['signal']
            src = data['source']
            sym = data['symbol']
            
            # --- HIỂN THỊ NGUỒN DỮ LIỆU ---
            st.success(f"✅ Đã kết nối thành công tới: **{src.upper()}** | Cặp: {sym}")
            
            m1, m2, m3, m4 = st.columns(4)
            s_color = "#00ffa3" if "BUY" in signal else ("#ff0055" if "SELL" in signal else "#888")
            
            with m1: st.markdown(f"""<div class="glass-card"><div class="metric-label">PRICE</div><div class="metric-val" style="color:var(--accent)">${curr_price:,.4f}</div></div>""", unsafe_allow_html=True)
            with m2: st.markdown(f"""<div class="glass-card" style="border-color:{s_color}"><div class="metric-label">SIGNAL</div><div class="metric-val" style="color:{s_color}">{signal}</div></div>""", unsafe_allow_html=True)
            
            dist = (curr_price - data['bbl']) / curr_price * 100
            with m3: st.markdown(f"""<div class="glass-card"><div class="metric-label">DIST TO DIP</div><div class="metric-val" style="color:#fff">{dist:.2f}%</div></div>""", unsafe_allow_html=True)
            with m4: st.markdown(f"""<div class="glass-card"><div class="metric-label">RSI</div><div class="metric-val">{data['rsi']:.1f}</div></div>""", unsafe_allow_html=True)

            c_chart, c_tools = st.columns([3, 1])
            with c_chart:
                base = sym.split('/')[0]
                # Chart TradingView luôn dùng Binance (Data đẹp nhất)
                components.html(f"""
                <div class="tradingview-widget-container" style="height:700px;width:100%">
                <div id="tv_chart" style="height:100%;width:100%"></div>
                <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                <script type="text/javascript">
                new TradingView.widget({{
                "autosize": true, "symbol": "BINANCE:{base}USDT", "interval": "60", "timezone": "Asia/Ho_Chi_Minh",
                "theme": "dark", "style": "1", "locale": "vi_VN", "enable_publishing": false,
                "backgroundColor": "#0f0f0f", "gridColor": "rgba(40,40,40,0.5)",
                "hide_top_toolbar": false, "container_id": "tv_chart",
                "studies": ["BB@tv-basicstudies", "RSI@tv-basicstudies"]
                }});
                </script>
                </div>""", height=710)

            with c_tools:
                st.markdown("### ⚡ CHIẾN THUẬT")
                rec = "QUAN SÁT"
                if dist < 0.5 and data['rsi'] < 35: rec = "CHUẨN BỊ"
                if dist < 0 and data['rsi'] < 30: rec = "MUA NGAY"
                rec_col = "#00ffa3" if "MUA" in rec else "#fff"
                st.markdown(f"""<div class="glass-card" style="text-align:center"><div style="font-size:12px; color:#888;">TRẠNG THÁI</div><div style="font-size:20px; font-weight:bold; color:{rec_col}">{rec}</div></div>""", unsafe_allow_html=True)
        else:
            st.error(f"❌ Vẫn không lấy được dữ liệu: {err}")
            st.info("Gợi ý: Thử nhập thủ công mã khác như 'ETH' hoặc 'DOGE'.")

# ================= TAB 2: BACKTEST =================
with tab_backtest:
    if st.button("🚀 CHẠY BACKTEST"):
        trades, stats = engine.run_backtest(target)
        if stats:
            c1, c2, c3 = st.columns(3)
            c1.metric("LỢI NHUẬN", f"{stats['return']:.2f}%")
            c2.metric("WINRATE", f"{stats['winrate']:.1f}%")
            c3.metric("SỐ LỆNH", f"{stats['total']}")
            if trades: st.dataframe(pd.DataFrame(trades), use_container_width=True)
        else: st.error(stats)

st.markdown("---")
st.caption("OMNI SCALPER v13 | Multi-Exchange Routing Enabled")
