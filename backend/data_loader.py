import yfinance as yf
import pandas as pd
import requests
import time

# --- CẤU HÌNH NGỤY TRANG (STEALTH HEADERS) ---
# Đây là chìa khóa để không bị Server chặn
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9'
}

def fetch_data(symbol):
    """
    HYDRA ENGINE V4: Real Data Only + Stealth Headers
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

    # 2. LẤY DATA TỪ BINANCE (ƯU TIÊN 1)
    if is_crypto:
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol={clean_sym}&interval=1h&limit=200"
            # Thêm headers để không bị chặn
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
        except Exception:
            pass # Lỗi thì lẳng lặng qua bước tiếp theo

    # 3. LẤY DATA TỪ YAHOO (DỰ PHÒNG)
    try:
        if is_crypto: 
            yf_sym = symbol.replace('/', '-') 
            if 'USD' not in yf_sym: yf_sym += '-USD'
            
        df = yf.download(yf_sym, period="1mo", interval="1h", progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
            return df, "YAHOO_OK"
    except Exception:
        pass

    return None, "NO_DATA"

def fetch_global_indices():
    """Lấy Vàng/Dầu/Indices"""
    tickers = {'GOLD': 'GC=F', 'DXY': 'DX-Y.NYB', 'S&P500': '^GSPC', 'USD/VND': 'VND=X'}
    results = {}
    try:
        data = yf.download(list(tickers.values()), period="5d", progress=False)
        if 'Close' in data.columns: closes = data['Close']
        else: closes = data
        
        for name, ticker in tickers.items():
            try:
                if ticker in closes:
                    series = closes[ticker].dropna()
                    if len(series) >= 2:
                        val = series.iloc[-1]
                        prev = series.iloc[-2]
                        change = (val - prev) / prev * 100
                        fmt = f"{val:,.0f}" if name == 'USD/VND' else f"{val:,.2f}"
                        results[name] = {"price": fmt, "change": change}
                        continue
            except: pass
            results[name] = {"price": "---", "change": 0.0}
    except:
        return {} # Trả về rỗng nếu lỗi
    return results

def fetch_market_overview():
    """
    GOD'S EYE V4: Real Data Only (Binance -> CoinGecko)
    """
    target_coins = ["BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA", "LINK", "AVAX", "SUI", "PEPE", "SHIB", "NEAR", "DOT", "LTC"]
    
    # --- CÁCH 1: BINANCE API (NHANH NHẤT) ---
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        response = requests.get(url, headers=HEADERS, timeout=5)
        
        if response.status_code == 200:
            all_tickers = response.json()
            overview_data = []
            ticker_map = {item['symbol']: item for item in all_tickers}
            
            for coin in target_coins:
                pair = f"{coin}USDT"
                if pair in ticker_map:
                    item = ticker_map[pair]
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
        print(f"Binance Overview Failed: {e}")

    # --- CÁCH 2: COINGECKO API (DỰ PHÒNG - CŨNG LÀ REAL DATA) ---
    try:
        # Map tên coin sang ID của CoinGecko
        cg_ids = "bitcoin,ethereum,binancecoin,solana,ripple,dogecoin,cardano,chainlink,avalanche-2,sui,pepe,shiba-inu,near,polkadot,litecoin"
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_ids}&vs_currencies=usd&include_24hr_change=true"
        
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            data = response.json()
            overview_data = []
            
            # Map lại ID sang Symbol hiển thị
            id_map = {
                "bitcoin": "BTC", "ethereum": "ETH", "binancecoin": "BNB", "solana": "SOL",
                "ripple": "XRP", "dogecoin": "DOGE", "cardano": "ADA", "chainlink": "LINK",
                "avalanche-2": "AVAX", "sui": "SUI", "pepe": "PEPE", "shiba-inu": "SHIB",
                "near": "NEAR", "polkadot": "DOT", "litecoin": "LTC"
            }
            
            for cid, sym in id_map.items():
                if cid in data:
                    item = data[cid]
                    p = item['usd']
                    c = item['usd_24h_change']
                    
                    if c >= 5: t = "🚀"
                    elif c > 0: t = "📈"
                    elif c <= -5: t = "🩸"
                    else: t = "📉"
                    
                    overview_data.append({"SYMBOL": sym, "PRICE ($)": p, "24H %": c, "TREND": t})
            
            if overview_data:
                return pd.DataFrame(overview_data)
    except Exception as e:
        print(f"CoinGecko Overview Failed: {e}")

    # NẾU CẢ 2 ĐỀU CHẾT -> TRẢ VỀ NONE (ĐỂ APP BÁO "SYNCING..." CHỨ KHÔNG HIỆN SỐ ẢO)
    return None
