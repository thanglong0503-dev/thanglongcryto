import yfinance as yf
import pandas as pd
import requests

def fetch_data(symbol):
    """
    HYDRA ENGINE V2 (Hỗ trợ Crypto + Vàng + Forex)
    """
    symbol = symbol.upper()
    
    # 1. XỬ LÝ MÃ (SYMBOL MAPPING)
    # Nếu là Vàng, Dầu, Forex thì giữ nguyên mã Yahoo
    if symbol in ['GC=F', 'CL=F', '^GSPC', 'EURUSD=X', 'JPY=X']:
        yf_sym = symbol
        is_crypto = False
    else:
        # Nếu là Crypto thì thêm đuôi -USD
        yf_sym = symbol.replace('/', '-')
        if not yf_sym.endswith('-USD') and 'USD' not in yf_sym:
            yf_sym += '-USD'
        is_crypto = True
            
    # 2. GỌI API YAHOO (Ưu tiên)
    try:
        df = yf.download(yf_sym, period="1mo", interval="1h", progress=False)
        
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
            return df, "YAHOO_OK"
    except: pass

    # 3. GỌI API BINANCE (Chỉ dành cho Crypto dự phòng)
    if is_crypto:
        try:
            binance_sym = symbol.replace('/', '').replace('-', '').replace('USD', 'USDT')
            if not binance_sym.endswith('USDT'): binance_sym += 'USDT'
            
            url = f"https://api.binance.com/api/v3/klines?symbol={binance_sym}&interval=1h&limit=200"
            data = requests.get(url, timeout=3).json()
            
            if isinstance(data, list):
                df = pd.DataFrame(data, columns=['t', 'open', 'high', 'low', 'close', 'volume', 'T', 'q', 'n', 'V', 'Q', 'B'])
                df['t'] = pd.to_datetime(df['t'], unit='ms')
                df.set_index('t', inplace=True)
                cols = ['open', 'high', 'low', 'close', 'volume']
                df[cols] = df[cols].astype(float)
                return df, "BINANCE_OK"
        except: pass
        
    return None, "NO_DATA"
# ... (Giữ nguyên phần import và hàm fetch_data cũ ở trên) ...

def fetch_global_indices():
    """
    Lấy dữ liệu vĩ mô: Vàng, DXY, S&P 500, USD/VND
    """
    tickers = {
        'GOLD': 'GC=F',       # Vàng tương lai
        'DXY': 'DX-Y.NYB',    # Sức mạnh đồng Đô la
        'S&P500': '^GSPC',    # Chứng khoán Mỹ
        'USD/VND': 'VND=X'    # Tỷ giá Đô - Việt
    }
    
    try:
        # Tải 1 lần tất cả để tiết kiệm thời gian
        # Dùng period='2d' để tính % thay đổi so với hôm qua
        data = yf.download(list(tickers.values()), period="5d", progress=False)
        
        results = {}
        
        # Xử lý dữ liệu Yahoo (Nó hay trả về MultiIndex khó chịu)
        # Chúng ta chỉ quan tâm cột 'Close'
        if 'Close' in data.columns:
            closes = data['Close']
        else:
            # Fallback nếu cấu trúc khác
            closes = data
            
        for name, ticker in tickers.items():
            try:
                # Lấy chuỗi giá của mã này
                series = closes[ticker].dropna()
                
                if len(series) >= 2:
                    price_now = series.iloc[-1]
                    price_prev = series.iloc[-2]
                    change = (price_now - price_prev) / price_prev * 100
                    
                    # Format đẹp
                    fmt_price = f"{price_now:,.0f}" if name == 'USD/VND' else f"{price_now:,.2f}"
                    
                    results[name] = {
                        "price": fmt_price,
                        "change": change,
                        "color": "var(--neon-green)" if change >= 0 else "var(--neon-pink)"
                    }
                else:
                    results[name] = {"price": "N/A", "change": 0.0, "color": "#666"}
            except:
                results[name] = {"price": "ERROR", "change": 0.0, "color": "#666"}
                
        return results
    except Exception as e:
        print(f"Global Data Error: {e}")
        return None
