import yfinance as yf
import pandas as pd
import requests

def fetch_data(symbol):
    """
    HYDRA ENGINE V2 (Hỗ trợ Crypto + Vàng + Forex)
    """
    symbol = symbol.upper()
    
    # 1. XỬ LÝ MÃ (SYMBOL MAPPING)
    if symbol in ['GC=F', 'CL=F', '^GSPC', 'EURUSD=X', 'JPY=X']:
        yf_sym = symbol
        is_crypto = False
    else:
        yf_sym = symbol.replace('/', '-')
        if not yf_sym.endswith('-USD') and 'USD' not in yf_sym:
            yf_sym += '-USD'
        is_crypto = True
            
    # 2. GỌI API YAHOO (Ưu tiên cho Vàng/Macro)
    try:
        if not is_crypto:
            df = yf.download(yf_sym, period="1mo", interval="1h", progress=False)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
                return df, "YAHOO_OK"
    except: pass

    # 3. GỌI API BINANCE (Ưu tiên cho Crypto)
    if is_crypto:
        try:
            # Chuẩn hóa mã: BTC -> BTCUSDT
            clean_sym = symbol.replace('/', '').replace('-', '').replace('USD', '')
            # Fix lỗi: Nếu người dùng nhập BTCUSDT thì không thêm USDT nữa
            if not clean_sym.endswith('USDT'): clean_sym += 'USDT'
            
            url = f"https://api.binance.com/api/v3/klines?symbol={clean_sym}&interval=1h&limit=200"
            response = requests.get(url, timeout=3)
            
            # Check lỗi API trả về
            if response.status_code != 200:
                 return None, "BINANCE_SYMBOL_NOT_FOUND"

            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data, columns=['t', 'open', 'high', 'low', 'close', 'volume', 'T', 'q', 'n', 'V', 'Q', 'B'])
                df['t'] = pd.to_datetime(df['t'], unit='ms')
                df.set_index('t', inplace=True)
                cols = ['open', 'high', 'low', 'close', 'volume']
                df[cols] = df[cols].astype(float)
                return df, "BINANCE_OK"
        except Exception as e:
            return None, str(e)
        
    return None, "NO_DATA"

def fetch_global_indices():
    """Lấy dữ liệu vĩ mô (Vàng, DXY...) từ Yahoo"""
    tickers = {'GOLD': 'GC=F', 'DXY': 'DX-Y.NYB', 'S&P500': '^GSPC', 'USD/VND': 'VND=X'}
    try:
        data = yf.download(list(tickers.values()), period="5d", progress=False)
        results = {}
        # Xử lý MultiIndex phức tạp của Yahoo
        if 'Close' in data.columns: closes = data['Close']
        else: closes = data
        
        for name, ticker in tickers.items():
            try:
                series = closes[ticker].dropna()
                if len(series) >= 2:
                    curr = series.iloc[-1]
                    prev = series.iloc[-2]
                    change = (curr - prev) / prev * 100
                    fmt = f"{curr:,.0f}" if name == 'USD/VND' else f"{curr:,.2f}"
                    results[name] = {"price": fmt, "change": change}
            except: 
                results[name] = {"price": "N/A", "change": 0.0}
        return results
    except: return None

def fetch_market_overview():
    """
    GOD'S EYE V2: Quét trực tiếp từ Binance (Siêu nhanh - Không bị chặn)
    """
    # Danh sách các Coin muốn theo dõi
    target_coins = [
        "BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA", "LINK", 
        "AVAX", "SUI", "PEPE", "SHIB", "NEAR", "DOT", "LTC", "WIF"
    ]
    
    try:
        # Gọi API lấy ticker 24h của TOÀN BỘ thị trường (Chỉ tốn 1 request)
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, timeout=5)
        all_tickers = response.json()
        
        overview_data = []
        
        # Tạo từ điển để tra cứu nhanh
        ticker_map = {item['symbol']: item for item in all_tickers}
        
        for coin in target_coins:
            pair = f"{coin}USDT"
            if pair in ticker_map:
                item = ticker_map[pair]
                price = float(item['lastPrice'])
                change = float(item['priceChangePercent'])
                
                # Xác định Trend icon
                if change >= 5: trend = "🚀"
                elif change > 0: trend = "📈"
                elif change <= -5: trend = "🩸"
                else: trend = "📉"
                
                overview_data.append({
                    "SYMBOL": coin,
                    "PRICE ($)": price,
                    "24H %": change,
                    "TREND": trend
                })
                
        # Tạo DataFrame
        if overview_data:
            return pd.DataFrame(overview_data)
        return None
        
    except Exception as e:
        print(f"Binance Overview Error: {e}")
        return None
