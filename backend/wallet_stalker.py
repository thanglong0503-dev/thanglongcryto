import requests
import pandas as pd
from datetime import datetime

# --- CẤU HÌNH ---
DEMO_KEY = "YourApiKeyToken"
PRICE_API = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum,bitcoin,binancecoin&vs_currencies=usd"

def get_current_prices():
    try:
        res = requests.get(PRICE_API, timeout=3).json()
        return {
            "ETH": res.get('ethereum', {}).get('usd', 0),
            "BTC": res.get('bitcoin', {}).get('usd', 0),
            "BNB": res.get('binancecoin', {}).get('usd', 0)
        }
    except: return {"ETH": 0, "BTC": 0}

def get_api_config(chain):
    if chain == "BSC":
        return {"url": "https://api.bscscan.com/api", "params_extra": {}}
    else: # ETH
        return {"url": "https://api.etherscan.io/v2/api", "params_extra": {"chainid": "1"}}

def get_native_symbol(chain):
    return "BNB" if chain == "BSC" else "ETH"

def get_wallet_balance(address, chain="ETH", api_key=None):
    # (Giữ nguyên logic cũ)
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
    """
    V53 UPDATE: QUÉT CẢ 2 LUỒNG (NATIVE + TOKEN) ĐỂ PHÂN BIỆT THẬT GIẢ
    """
    key = api_key if api_key and len(api_key) > 5 else DEMO_KEY
    config = get_api_config(chain)
    all_txs = []
    
    # 1. LẤY GIAO DỊCH NATIVE (ETH THẬT / BNB THẬT)
    # Endpoint: txlist
    url_native = f"{config['url']}?module=account&action=txlist&address={address}&page=1&offset=50&sort=desc&apikey={key}"
    for k, v in config['params_extra'].items(): url_native += f"&{k}={v}"
    
    try:
        res = requests.get(url_native, timeout=5).json()
        if res['status'] == '1' and res['result']:
            for tx in res['result']:
                val = float(tx.get('value', 0)) / 10**18
                if val > 0.001: # Chỉ lấy lệnh có giá trị
                    ts = int(tx.get('timeStamp', 0))
                    all_txs.append({
                        'TS': ts,
                        'TIME': datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"),
                        'SYMBOL': get_native_symbol(chain), # Tự điền ETH/BNB
                        'AMOUNT': val,
                        'TYPE': "IN" if tx['to'].lower() == address.lower() else "OUT",
                        'CLASS': "💎 REAL COIN", # Đánh dấu hàng thật
                        'HASH': tx.get('hash', '')
                    })
    except: pass

    # 2. LẤY GIAO DỊCH TOKEN (ERC-20)
    # Endpoint: tokentx
    url_token = f"{config['url']}?module=account&action=tokentx&address={address}&page=1&offset=50&sort=desc&apikey={key}"
    for k, v in config['params_extra'].items(): url_token += f"&{k}={v}"
    
    try:
        res = requests.get(url_token, timeout=5).json()
        if res['status'] == '1' and res['result']:
            for tx in res['result']:
                symbol = tx.get('tokenSymbol', '???')
                if len(symbol) > 10: continue
                try:
                    dec = int(tx.get('tokenDecimal', 18))
                    val = float(tx.get('value', 0)) / (10 ** dec)
                except: val = 0
                
                # NẾU TOKEN TÊN LÀ "ETH" MÀ NẰM Ở ĐÂY -> LÀ HÀNG FAKE
                token_class = "TOKEN"
                if symbol.upper() == "ETH": token_class = "⚠️ FAKE/SCAM" 
                
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
    
    # 3. GỘP VÀ SẮP XẾP LẠI THEO THỜI GIAN
    if all_txs:
        df = pd.DataFrame(all_txs)
        df = df.sort_values(by='TS', ascending=False).head(50) # Lấy 50 lệnh mới nhất của cả 2 loại
        
        # Xử lý màu sắc hiển thị
        def get_color(row):
            if row['CLASS'] == "💎 REAL COIN": return "#00b4ff" # Màu xanh biển cho hàng thật
            if "FAKE" in row['CLASS']: return "#ff0000" # Màu đỏ cảnh báo hàng giả
            return "#00ff9f" if row['TYPE'] == "IN" else "#ff0055"
            
        df['COLOR'] = df.apply(get_color, axis=1)
        return df, None
    
    return None, "No Data"
