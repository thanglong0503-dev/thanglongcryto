import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import plotly.graph_objects as go
import time

# ==========================================
# 1. SYSTEM CONFIGURATION (PROFESSIONAL MODE)
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="Terminal Pro", 
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# CSS: Bloomberg Terminal Style
st.markdown("""
<style>
    /* Global Font */
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Roboto Mono', monospace;
        background-color: #0e1117;
        color: #e0e0e0;
    }
    
    /* Metrics Styling */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 4px;
    }
    label[data-testid="stMetricLabel"] {
        color: #8b949e;
        font-size: 0.8rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
        color: #f0f6fc;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #010409;
        border-right: 1px solid #30363d;
    }
    
    /* Table Styling */
    div[data-testid="stDataFrame"] {
        border: 1px solid #30363d;
    }
    
    /* Buttons */
    button[kind="primary"] {
        background-color: #238636;
        border: none;
        border-radius: 4px;
        color: white;
        transition: 0.2s;
    }
    button[kind="primary"]:hover {
        background-color: #2ea043;
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Roboto Mono', monospace;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Alert Boxes */
    div.stAlert {
        border-radius: 4px;
        border: 1px solid #30363d;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA ENGINE (ROBUST FETCHING)
# ==========================================
@st.cache_resource
def init_exchange():
    """Initialize Binance connection securely"""
    return ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'} # Use Spot for better stability on public API
    })

exchange = init_exchange()

@st.cache_data(ttl=300)
def get_market_symbols(limit=50):
    """Fetch active USDT pairs"""
    try:
        if not exchange.has['fetchTickers']:
            return ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT']
            
        tickers = exchange.fetch_tickers()
        # Filter strictly for USDT pairs and sort by Volume
        symbols = [
            s for s in tickers 
            if '/USDT' in s and 'UP/' not in s and 'DOWN/' not in s
        ]
        sorted_symbols = sorted(symbols, key=lambda x: tickers[x]['quoteVolume'], reverse=True)
        return sorted_symbols[:limit]
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']

def fetch_ohlcv_data(symbol, timeframe, limit=100):
    """Fetch Candle Data with Error Handling"""
    try:
        # Retry mechanism
        for _ in range(3):
            try:
                bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
                break
            except ccxt.NetworkError:
                time.sleep(1)
        else:
            return pd.DataFrame() # Return empty if fails 3 times

        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        st.error(f"Data Fetch Error for {symbol}: {str(e)}")
        return pd.DataFrame()

# ==========================================
# 3. ANALYTICS ENGINE
# ==========================================
def calculate_indicators(df):
    if df.empty: return df
    
    # Trend Indicators
    df.ta.ema(length=50, append=True)  # Mid-term trend
    df.ta.ema(length=200, append=True) # Long-term trend
    
    # Momentum
    df.ta.rsi(length=14, append=True)
    
    # Volatility
    df.ta.bbands(length=20, std=2, append=True)
    
    return df

# ==========================================
# 4. PROFESSIONAL UI LAYOUT
# ==========================================

# --- SIDEBAR ---
st.sidebar.markdown("### ⚙️ SETTINGS")
app_mode = st.sidebar.selectbox("VIEW MODE", ["Market Dashboard", "Alpha Scanner"])
st.sidebar.markdown("---")
global_tf = st.sidebar.selectbox("TIMEFRAME", ['15m', '1h', '4h', '1d'], index=2)
global_limit = st.sidebar.slider("DATA POINTS", 50, 500, 200)

# --- MAIN: DASHBOARD ---
if app_mode == "Market Dashboard":
    st.title("MARKET OVERVIEW")
    
    # 1. Ticker Selection
    market_coins = get_market_symbols(50)
    selected_symbol = st.selectbox("SELECT ASSET", market_coins, index=0)
    
    # 2. Data Fetching
    with st.spinner("Fetching market data..."):
        df = fetch_ohlcv_data(selected_symbol, global_tf, global_limit)
        
    if not df.empty:
        df = calculate_indicators(df)
        last_close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2]
        pct_change = (last_close - prev_close) / prev_close * 100
        vol_24h = df['volume'].sum()
        
        # 3. Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("LAST PRICE", f"{last_close:,.4f}", f"{pct_change:+.2f}%")
        m2.metric("RSI (14)", f"{df['RSI_14'].iloc[-1]:.1f}")
        m3.metric("EMA Trend", "BULLISH" if last_close > df['EMA_200'].iloc[-1] else "BEARISH")
        m4.metric("VOLUME", f"{vol_24h:,.0f}")
        
        # 4. Professional Chart
        fig = go.Figure()
        
        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['open'], high=df['high'],
            low=df['low'], close=df['close'],
            name='Price',
            increasing_line_color='#238636', # Professional Green
            decreasing_line_color='#da3633'  # Professional Red
        ))
        
        # Indicators
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='#a371f7', width=1), name='EMA 50'))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], line=dict(color='#2f81f7', width=1.5), name='EMA 200'))
        
        # BB
        fig.add_trace(go.Scatter(x=df.index, y=df['BBU_20_2.0'], line=dict(color='rgba(139, 148, 158, 0.3)', width=1), name='UBB', showlegend=False))
        fig.add_trace(go.Scatter(x=df.index, y=df['BBL_20_2.0'], line=dict(color='rgba(139, 148, 158, 0.3)', width=1), name='LBB', showlegend=False, fill='tonexty'))

        fig.update_layout(
            height=600,
            template="plotly_dark",
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#30363d'),
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 5. Data Table
        with st.expander("RAW DATA & INDICATORS"):
            st.dataframe(df.sort_index(ascending=False).style.format("{:.4f}"), use_container_width=True)
            
    else:
        st.error(f"Unable to fetch data for {selected_symbol}. Possible network restriction on Streamlit Cloud.")
        st.info("Try refreshing the page or checking requirements.txt")

# --- MAIN: SCANNER ---
elif app_mode == "Alpha Scanner":
    st.title("ALPHA SCANNER")
    st.caption(f"Scanning Top 30 Assets | Timeframe: {global_tf}")
    
    if st.button("RUN SCAN", type="primary"):
        scan_list = get_market_symbols(30)
        results = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, symbol in enumerate(scan_list):
            progress_bar.progress((i+1)/len(scan_list))
            status_text.text(f"Analyzing {symbol}...")
            
            df = fetch_ohlcv_data(symbol, global_tf, limit=50)
            if not df.empty:
                df = calculate_indicators(df)
                curr = df.iloc[-1]
                
                # Logic
                rsi = curr['RSI_14']
                
                # Calculate Volume Spike
                vol_ma = df['volume'].rolling(20).mean().iloc[-1]
                vol_spike = curr['volume'] / vol_ma if vol_ma > 0 else 0
                
                # Signal Condition
                condition = "NEUTRAL"
                if rsi < 30: condition = "OVERSOLD"
                elif rsi > 70: condition = "OVERBOUGHT"
                
                results.append({
                    "TICKER": symbol,
                    "PRICE": curr['close'],
                    "RSI": rsi,
                    "VOL_SPIKE": vol_spike,
                    "EMA_CONDITION": "ABOVE EMA50" if curr['close'] > curr['EMA_50'] else "BELOW EMA50",
                    "SIGNAL": condition
                })
        
        progress_bar.empty()
        status_text.empty()
        
        # Display Results
        res_df = pd.DataFrame(results)
        if not res_df.empty:
            # Styling
            def color_signal(val):
                color = '#e0e0e0'
                if val == "OVERSOLD": color = '#238636' # Green
                elif val == "OVERBOUGHT": color = '#da3633' # Red
                return f'color: {color}; font-weight: bold'

            st.dataframe(
                res_df.style
                .map(color_signal, subset=['SIGNAL'])
                .format({"PRICE": "{:.4f}", "RSI": "{:.1f}", "VOL_SPIKE": "{:.2f}x"}),
                use_container_width=True,
                height=600
            )
        else:
            st.warning("No data returned from scan.")
