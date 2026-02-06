import requests
import pandas as pd
from datetime import datetime

# --- CẤU HÌNH ---
DEMO_KEY = "YourApiKeyToken"

def get_current_prices():
    """
    V56: GIÁ REAL-TIME TỪ BINANCE (KHÔNG HARDCODE)
    """
    # Khởi tạo giá bằng 0 (Nếu không lấy được thì hiện 0 để biết đường sửa)
    prices = {"ETH": 0, "BTC": 0, "BNB": 0}
    
    try:
        # GỌI TRỰC TIẾP BINANCE (Nhanh & Chính xác nhất)
        # Timeout cực ngắn (2s) để App không bị đơ
        eth_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT", timeout=2).json()
        btc_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=2).json()
        bnb_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT", timeout=2).json()
        
        # Cập nhật giá
        if 'price' in eth_res: prices["ETH"] = float(eth_res['price'])
        if 'price' in btc_res: prices["BTC"] = float(btc_res['price'])
        if 'price' in bnb_res: prices["BNB"] = float(bnb_res['price'])
        
    except Exception as e:
        # Nếu Binance chặn (hiếm khi), thử cứu cánh bằng CoinGecko
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum,bitcoin,binancecoin&vs_currencies=usd"
            res = requests.get(url, timeout=2).json()
            prices["ETH"] = res['ethereum']['usd']
            prices["BTC"] = res['bitcoin']['usd']
            prices["BNB"] = res['binancecoin']['usd']
        except:
            pass # Nếu cả 2 đều chết thì chấp nhận giá = 0 (Không bịa số)

    return prices

def get_api_config(chain):
    if chain == "BSC": return {"url": "https://api.bscscan.com/api", "params_extra": {}}
    else: return {"url": "https://api.etherscan.io/v2/api", "params_extra": {"chainid": "1"}}

def get_native_symbol(chain):
    return "BNB" if chain == "BSC" else "ETH"

def get_wallet_balance(address, chain="ETH", api_key=None):
    key = api_key if api_key and len(api_key) > 5 else DEMO_KEY
    config = get_api_config(chain)
    url = f"{config['url']}?module=account&action=balance&address={address}&tag=latest&apikey={key}"
    for k, v in config['params_extra'].items(): url += f"&{k}={v}"
    
    try:
        res = requests.get(url, timeout=5).json()
        if res['status'] == '1': return float(res['result']) / 10**18, None
        return 0, f"Error: {res.get('message')}"
    except Exception as e: return 0, str(e)

def get_token_tx(address, chain="ETH", api_key=None):
    key = api_key if api_key and len(api_key) > 5 else DEMO_KEY
    config = get_api_config(chain)
    all_txs = []
    
    # 1. NATIVE
    url_native = f"{config['url']}?module=account&action=txlist&address={address}&page=1&offset=50&sort=desc&apikey={key}"
    for k, v in config['params_extra'].items(): url_native += f"&{k}={v}"
    try:
        res = requests.get(url_native, timeout=4).json()
        if res['status'] == '1' and res['result']:
            for tx in res['result']:
                val = float(tx.get('value', 0)) / 10**18
                if val > 0.001:
                    ts = int(tx.get('timeStamp', 0))
                    all_txs.append({
                        'TS': ts,
                        'TIME': datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"),
                        'SYMBOL': get_native_symbol(chain),
                        'AMOUNT': val,
                        'TYPE': "IN" if tx['to'].lower() == address.lower() else "OUT",
                        'CLASS': "💎 REAL COIN",
                        'HASH': tx.get('hash', '')
                    })
    except: pass

    # 2. TOKENS
    url_token = f"{config['url']}?module=account&action=tokentx&address={address}&page=1&offset=50&sort=desc&apikey={key}"
    for k, v in config['params_extra'].items(): url_token += f"&{k}={v}"
    try:
        res = requests.get(url_token, timeout=4).json()
        if res['status'] == '1' and res['result']:
            for tx in res['result']:
                symbol = tx.get('tokenSymbol', '???')
                if len(symbol) > 10: continue
                try:
                    dec = int(tx.get('tokenDecimal', 18))
                    val = float(tx.get('value', 0)) / (10 ** dec)
                except: val = 0
                
                token_class = "TOKEN"
                if symbol.upper() == "ETH": token_class = "⚠️ FAKE"
                
                if val > 0:
                    ts = int(tx.get('timeStamp', 0))
                    all_txs.append({
                        'TS': ts,
                        'TIME': datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"),
                        'SYMBOL': symbol,
                        'AMOUNT': val,
                        'TYPE': "IN" if tx['to'].lower() == address.lower() else "OUT",
                        'CLASS': token_class,
                        'HASH': tx.get('hash', '')
                    })
    except: pass
    
    if all_txs:
        df = pd.DataFrame(all_txs)
        df = df.sort_values(by='TS', ascending=False).head(50)
        def get_color(row):
            if row['CLASS'] == "💎 REAL COIN": return "#00b4ff"
            if "FAKE" in row['CLASS']: return "#ff0000"
            return "#00ff9f" if row['TYPE'] == "IN" else "#ff0055"
        df['COLOR'] = df.apply(get_color, axis=1)
        return df, None
    
    return None, "No Data"
