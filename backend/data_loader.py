import yfinance as yf
import pandas as pd
import requests
import json
import time

# HEADERS CHỐNG CHẶN
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_data(symbol):
    """
    ENGINE GỐC: Đã được kiểm chứng là hoạt động tốt.
    Giữ nguyên không sửa gì cả.
    """
    symbol = symbol.upper()
    
    if symbol in ['GC=F', 'CL=F', '^GSPC', 'EURUSD=X']:
        is_crypto = False
        yf_sym = symbol
    else:
        is_crypto = True
        clean_sym = symbol.replace('/', '').replace('-', '').replace('USD', '')
        if not clean_sym.endswith('USDT'): clean_sym += 'USDT'

    # 1. BINANCE
    if is_crypto:
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol={clean_sym}&interval=1h&limit=24" # Lấy 24 nến để tính % ngày
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

    # 2. YAHOO
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
    """Lấy dữ liệu Vĩ mô"""
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
    GOD'S EYE V6: MANUAL LOOP (FAILSAFE)
    Nếu Deep Scanner chạy được, hàm này CHẮC CHẮN chạy được.
    """
    # Danh sách rút gọn 10 con quan trọng nhất để load cho nhanh
    target_coins = ["BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA", "LINK", "AVAX", "PEPE"]
    
    overview_data = []
    
    # --- CÁCH 1: BINANCE BATCH (ƯU TIÊN - NẾU ĐƯỢC THÌ TỐT) ---
    try:
        symbols_param = json.dumps([f"{c}USDT" for c in target_coins])
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, headers=HEADERS, params={"symbols": symbols_param}, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            data_map = {item['symbol']: item for item in data}
            
            for coin in target_coins:
                pair = f"{coin}USDT"
                if pair in data_map:
                    item = data_map[pair]
                    p = float(item['lastPrice'])
                    c = float(item['priceChangePercent'])
                    
                    if c >= 5: t = "🚀"
                    elif c > 0: t = "📈"
                    elif c <= -5: t = "🩸"
                    else: t = "📉"
                    
                    overview_data.append({"SYMBOL": coin, "PRICE ($)": p, "24H %": c, "TREND": t})
            
            if len(overview_data) > 0:
                return pd.DataFrame(overview_data)
    except:
        pass # Nếu lỗi Batch, chuyển sang Cách 2 ngay lập tức

    # --- CÁCH 2: MANUAL LOOP (CÁCH NÀY LÀ BẤT TỬ) ---
    # Dùng chính hàm fetch_data lẻ tẻ để gom lại
    # Hơi chậm xíu nhưng bao sống
    
    manual_list = []
    for coin in target_coins:
        # Gọi lẻ từng con (Giống hệt Deep Scanner)
        df, status = fetch_data(coin)
        
        if df is not None and not df.empty:
            price_now = df['close'].iloc[-1]
            
            # Tính % thay đổi trong 24h qua (lấy giá của 24 cây nến trước)
            if len(df) >= 24:
                price_old = df['close'].iloc[-24]
            else:
                price_old = df['open'].iloc[0]
                
            change = (price_now - price_old) / price_old * 100
            
            if change >= 5: t = "🚀"
            elif change > 0: t = "📈"
            elif change <= -5: t = "🩸"
            else: t = "📉"
            
            manual_list.append({"SYMBOL": coin, "PRICE ($)": price_now, "24H %": change, "TREND": t})
    
    if len(manual_list) > 0:
        return pd.DataFrame(manual_list)

    return None
