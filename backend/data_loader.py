import yfinance as yf
import pandas as pd
import requests # Dùng để gọi API trực tiếp nếu thư viện tạch

def fetch_data(symbol):
    """
    CHIẾN THUẬT HYDRA:
    1. Thử lấy từ Yahoo Finance.
    2. Nếu Yahoo tạch -> Lấy trực tiếp từ Binance HTTP API (Rất khó bị chặn).
    """
    symbol = symbol.upper()
    
    # --- CÁCH 1: YAHOO FINANCE ---
    try:
        yf_sym = symbol.replace('/', '-')
        if not yf_sym.endswith('-USD') and 'USD' not in yf_sym:
            yf_sym += '-USD'
            
        df = yf.download(yf_sym, period="1mo", interval="1h", progress=False)
        
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
            return df, "YAHOO_OK"
            
    except Exception as e:
        print(f"Yahoo failed: {e}")

    # --- CÁCH 2: BINANCE DIRECT API (Vũ khí bí mật) ---
    # Cách này gọi thẳng vào server Binance không qua thư viện trung gian, tỷ lệ sống 99%
    try:
        # Chuẩn hóa mã: BTC -> BTCUSDT
        binance_sym = symbol.replace('/', '').replace('-', '').replace('USD', 'USDT')
        if not binance_sym.endswith('USDT'):
            binance_sym += 'USDT'
            
        url = f"https://api.binance.com/api/v3/klines?symbol={binance_sym}&interval=1h&limit=200"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        # Nếu API trả về lỗi (dạng dictionary có code lỗi)
        if isinstance(data, dict) and 'code' in data:
            return None, f"BINANCE_ERROR: {data.get('msg')}"
            
        # Xử lý dữ liệu thô từ Binance
        df = pd.DataFrame(data, columns=['t', 'open', 'high', 'low', 'close', 'volume', 'T', 'q', 'n', 'V', 'Q', 'B'])
        df['t'] = pd.to_datetime(df['t'], unit='ms')
        df.set_index('t', inplace=True)
        
        # Ép kiểu số (quan trọng)
        cols = ['open', 'high', 'low', 'close', 'volume']
        df[cols] = df[cols].astype(float)
        
        return df, "BINANCE_DIRECT_OK"
        
    except Exception as e:
        return None, f"ALL_FAILED: {str(e)}"
