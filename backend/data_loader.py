import yfinance as yf
import pandas as pd
import requests
import json
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_data(symbol):
    """ENGINE GỐC: Giữ nguyên để phục vụ Deep Scanner"""
    symbol = symbol.upper()
    
    if symbol in ['GC=F', 'CL=F', '^GSPC', 'EURUSD=X']:
        is_crypto = False; yf_sym = symbol
    else:
        is_crypto = True
        clean_sym = symbol.replace('/', '').replace('-', '').replace('USD', '')
        if not clean_sym.endswith('USDT'): clean_sym += 'USDT'

    if is_crypto:
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol={clean_sym}&interval=1h&limit=24"
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

    try:
        if is_crypto: yf_sym = symbol.replace('/', '-') + '-USD'
        df = yf.download(yf_sym, period="2d", interval="1h", progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
            return df, "YAHOO_OK"
    except: pass
    return None, "NO_DATA"

def fetch_global_indices():
    """Giữ nguyên hàm lấy Vĩ mô"""
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
                        val = s.iloc[-1]; prev = s.iloc[-2]
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
    GOD'S EYE V7: COINGECKO TOP 20 MARKET CAP
    Lấy dữ liệu Top 20 Vốn hóa + Volume chuẩn chỉ.
    """
    try:
        # Gọi API CoinGecko lấy Top 20 theo Market Cap
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 20,
            "page": 1,
            "sparkline": "false"
        }
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            overview_data = []
            
            for item in data:
                # Xử lý Trend icon
                c = item.get('price_change_percentage_24h', 0)
                if c is None: c = 0
                if c >= 5: t = "🚀"
                elif c > 0: t = "📈"
                elif c <= -5: t = "🩸"
                else: t = "📉"

                # Format số lớn (Billion/Million) cho gọn
                mcap = item.get('market_cap', 0)
                vol = item.get('total_volume', 0)
                
                # Hàm làm gọn số (Ví dụ: 1,000,000,000 -> 1.0B)
                def format_large(n):
                    if n >= 1e9: return f"${n/1e9:.1f}B"
                    if n >= 1e6: return f"${n/1e6:.1f}M"
                    return f"${n:,.0f}"

                overview_data.append({
                    "SYMBOL": item['symbol'].upper(),
                    "PRICE ($)": item['current_price'],
                    "24H %": c,
                    "TREND": t,
                    "VOL": format_large(vol),       # Thêm Volume
                    "CAP": format_large(mcap)       # Thêm Market Cap
                })
            
            return pd.DataFrame(overview_data)
            
    except Exception as e:
        print(f"CoinGecko Error: {e}")
        
    # --- FALLBACK: NẾU COINGECKO LỖI THÌ DÙNG LẠI MANUAL LOOP BINANCE ---
    # (Để đảm bảo không bao giờ trắng bảng)
    target_fallback = ["BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA", "LINK", "AVAX", "PEPE"]
    fallback_list = []
    
    for coin in target_fallback:
        df, s = fetch_data(coin)
        if df is not None and not df.empty:
            p_now = df['close'].iloc[-1]
            p_old = df['close'].iloc[-24] if len(df)>=24 else df['open'].iloc[0]
            change = (p_now - p_old)/p_old*100
            
            # Tính Volume 24h (Tương đối)
            vol_24h = (df['close'] * df['volume']).sum()
            def fmt_vol(n):
                if n >= 1e9: return f"${n/1e9:.1f}B"
                if n >= 1e6: return f"${n/1e6:.1f}M"
                return f"${n:,.0f}"

            fallback_list.append({
                "SYMBOL": coin, "PRICE ($)": p_now, "24H %": change, 
                "TREND": "📈" if change>0 else "📉",
                "VOL": fmt_vol(vol_24h),
                "CAP": "---" # Binance không có Cap
            })
            
    if fallback_list: return pd.DataFrame(fallback_list)
    return None
