import yfinance as yf
import pandas as pd
import requests
import json
import time

# HEADERS (Để không bị Binance chặn)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_data(symbol):
    """
    ENGINE GỐC: Đã nâng cấp limit lên 200 để phục vụ AI
    """
    symbol = symbol.upper()
    
    # Phân loại Crypto / Stocks
    if symbol in ['GC=F', 'CL=F', '^GSPC', 'EURUSD=X']:
        is_crypto = False
        yf_sym = symbol
    else:
        is_crypto = True
        clean_sym = symbol.replace('/', '').replace('-', '').replace('USD', '')
        if not clean_sym.endswith('USDT'): clean_sym += 'USDT'

    # 1. LẤY DATA TỪ BINANCE (CRYPTO)
    if is_crypto:
        try:
            # --- THAY ĐỔI QUAN TRỌNG Ở ĐÂY: limit=200 ---
            # Trước đây là 24 (làm AI chết đói), giờ tăng lên 200
            url = f"https://api.binance.com/api/v3/klines?symbol={clean_sym}&interval=1h&limit=200"
            
            response = requests.get(url, headers=HEADERS, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    df = pd.DataFrame(data, columns=['t', 'open', 'high', 'low', 'close', 'volume', 'T', 'q', 'n', 'V', 'Q', 'B'])
                    df['t'] = pd.to_datetime(df['t'], unit='ms')
                    df.set_index('t', inplace=True)
                    cols = ['open', 'high', 'low', 'close', 'volume']
                    df[cols] = df[cols].astype(float)
                    return df, "BINANCE_OK"
        except: pass

    # 2. LẤY DATA TỪ YAHOO (DỰ PHÒNG / STOCKS)
    try:
        if is_crypto: yf_sym = symbol.replace('/', '-') + '-USD'
        # Yahoo thì lấy hẳn 1 tháng (1mo) cho dư dả
        df = yf.download(yf_sym, period="1mo", interval="1h", progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
            return df, "YAHOO_OK"
    except: pass

    return None, "NO_DATA"

def fetch_global_indices():
    """Lấy dữ liệu Vĩ mô (Vàng, Dầu...)"""
    tickers = {'GOLD': 'GC=F', 'DXY': 'DX-Y.NYB', 'S&P500': '^GSPC', 'USD/VND': 'VND=X'}
    results = {}
    try:
        data = yf.download(list(tickers.values()), period="5d", progress=False)
        if 'Close' in data.columns: closes = data['Close']
        else: closes = data
        for name, ticker in tickers.items():
            try:
                if ticker in closes:
                    s = closes[ticker].dropna()
                    if len(s) >= 2:
                        val = s.iloc[-1]
                        prev = s.iloc[-2]
                        change = (val - prev) / prev * 100
                        fmt = f"{val:,.0f}" if name == 'USD/VND' else f"{val:,.2f}"
                        results[name] = {"price": fmt, "change": change}
                        continue
            except: pass
            results[name] = {"price": "---", "change": 0.0}
    except: return {}
    return results

def fetch_market_overview():
    """
    GOD'S EYE: Vẫn dùng Coingecko hoặc Fallback
    """
    # 1. Thử CoinGecko (Có Market Cap + Vol)
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd", "order": "market_cap_desc",
            "per_page": 20, "page": 1, "sparkline": "false"
        }
        response = requests.get(url, headers=HEADERS, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            overview_data = []
            for item in data:
                c = item.get('price_change_percentage_24h', 0)
                if c is None: c = 0
                
                # Format số lớn
                def fmt_large(n):
                    if not n: return "---"
                    if n >= 1e9: return f"${n/1e9:.1f}B"
                    if n >= 1e6: return f"${n/1e6:.1f}M"
                    return f"${n:,.0f}"

                overview_data.append({
                    "SYMBOL": item['symbol'].upper(),
                    "PRICE ($)": item['current_price'],
                    "24H %": c,
                    "TREND": "🚀" if c>=5 else ("📈" if c>0 else ("🩸" if c<=-5 else "📉")),
                    "VOL": fmt_large(item.get('total_volume', 0)),
                    "CAP": fmt_large(item.get('market_cap', 0))
                })
            return pd.DataFrame(overview_data)
    except: pass
        
    # 2. Fallback: Manual Loop Binance (Vẫn hoạt động tốt với limit=200)
    target_fallback = ["BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA", "LINK", "AVAX", "PEPE"]
    fallback_list = []
    
    for coin in target_fallback:
        df, s = fetch_data(coin)
        if df is not None and not df.empty:
            p_now = df['close'].iloc[-1]
            # Lấy giá 24h trước (dù có 200 nến thì -24 vẫn đúng)
            p_old = df['close'].iloc[-24] if len(df)>=24 else df['open'].iloc[0]
            change = (p_now - p_old)/p_old*100
            
            vol_24h = (df['close'] * df['volume']).sum() # Ước lượng
            def fmt_vol(n):
                if n >= 1e9: return f"${n/1e9:.1f}B"
                if n >= 1e6: return f"${n/1e6:.1f}M"
                return f"${n:,.0f}"

            fallback_list.append({
                "SYMBOL": coin, "PRICE ($)": p_now, "24H %": change, 
                "TREND": "📈" if change>0 else "📉",
                "VOL": fmt_vol(vol_24h), "CAP": "---"
            })
            
    if fallback_list: return pd.DataFrame(fallback_list)
    return None
