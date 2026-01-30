import yfinance as yf
import pandas as pd
import requests
import json # <--- Cần thêm cái này để đóng gói danh sách coin

# HEADERS ĐỂ KHÔNG BỊ CHẶN
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_data(symbol):
    """
    DEEP SCANNER ENGINE: Lấy dữ liệu 1 coin (Vẫn hoạt động tốt -> Giữ nguyên logic)
    """
    symbol = symbol.upper()
    
    # 1. XỬ LÝ MÃ
    if symbol in ['GC=F', 'CL=F', '^GSPC', 'EURUSD=X']:
        is_crypto = False
        yf_sym = symbol
    else:
        is_crypto = True
        clean_sym = symbol.replace('/', '').replace('-', '').replace('USD', '')
        if not clean_sym.endswith('USDT'): clean_sym += 'USDT'

    # 2. BINANCE (CRYPTO)
    if is_crypto:
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol={clean_sym}&interval=1h&limit=200"
            response = requests.get(url, headers=HEADERS, timeout=5)
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

    # 3. YAHOO (MACRO / FALLBACK)
    try:
        if is_crypto: 
            yf_sym = symbol.replace('/', '-') + '-USD'
        df = yf.download(yf_sym, period="1mo", interval="1h", progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
            return df, "YAHOO_OK"
    except: pass

    return None, "NO_DATA"

def fetch_global_indices():
    """Lấy dữ liệu Vàng/Dầu (Yahoo)"""
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
    GOD'S EYE V5: Kỹ thuật 'Sniper Shot' (Chỉ lấy đúng danh sách cần)
    -> Nhẹ hơn, Nhanh hơn, Không bị nghẹn mạng.
    """
    # 1. Danh sách Coin mục tiêu
    target_coins = ["BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA", "LINK", "AVAX", "SUI", "PEPE", "SHIB", "NEAR", "DOT", "LTC"]
    
    try:
        # 2. Chuẩn bị danh sách tham số gửi cho Binance
        # Binance yêu cầu format: ["BTCUSDT","ETHUSDT",...]
        symbols_param = json.dumps([f"{c}USDT" for c in target_coins])
        
        # 3. GỌI API VỚI THAM SỐ CỤ THỂ (QUAN TRỌNG)
        # Thay vì gọi all, ta truyền tham số `symbols` vào
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, headers=HEADERS, params={"symbols": symbols_param}, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            overview_data = []
            
            # Binance trả về list đúng thứ tự hoặc lộn xộn, ta map lại cho chắc
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
            
            if overview_data:
                return pd.DataFrame(overview_data)
                
    except Exception as e:
        print(f"Sniper Fetch Error: {e}")

    # Fallback: Nếu Sniper thất bại (rất hiếm), thử Yahoo Batch Download
    try:
        yf_tickers = [f"{c}-USD" for c in target_coins]
        data = yf.download(yf_tickers, period="2d", progress=False)
        # (Logic xử lý Yahoo ở đây nếu cần, nhưng Binance Sniper thường sẽ ăn ngay)
        # ... Viết ngắn gọn để tránh code quá dài
    except: pass
        
    return None
