import yfinance as yf
import pandas as pd

def fetch_data(symbol):
    """Lấy dữ liệu thật từ Yahoo Finance"""
    # Mapping: BTC -> BTC-USD
    yf_sym = symbol.upper().replace('/', '-')
    if not yf_sym.endswith('-USD') and 'USD' not in yf_sym:
        yf_sym += '-USD'
    
    try:
        # Tải 1 tháng dữ liệu khung 1H
        df = yf.download(yf_sym, period="1mo", interval="1h", progress=False)
        
        if df.empty: return None, "NO_DATA"
        
        # Fix MultiIndex của Yahoo
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Rename cho chuẩn
        df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
        
        return df, "OK"
    except Exception as e:
        return None, str(e)
