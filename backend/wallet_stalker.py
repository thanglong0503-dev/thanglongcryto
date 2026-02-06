import requests
import pandas as pd
from datetime import datetime

# --- CẤU HÌNH ---
# Dùng API CoinGecko để lấy giá (Free, không cần Key)
PRICE_API = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum,bitcoin,binancecoin,tether,usd-coin&vs_currencies=usd"

def get_current_prices():
    """Lấy giá USD của các đồng coin chủ chốt"""
    try:
        res = requests.get(PRICE_API, timeout=3).json()
        return {
            "ETH": res.get('ethereum', {}).get('usd', 0),
            "BTC": res.get('bitcoin', {}).get('usd', 0),
            "BNB": res.get('binancecoin', {}).get('usd', 0),
            "USDT": 1.0,
            "USDC": 1.0,
            "DAI": 1.0
        }
    except:
        return {"ETH": 0, "BTC": 0, "BNB": 0} # Nếu lỗi thì trả về 0 để không crash app

# --- CẤU HÌNH API ETHERSCAN V2 ---
def get_api_config(chain):
    if chain == "BSC":
        return {"url": "https://api.bscscan.com/api", "params_extra": {}}
    else: # ETH
        return {"url": "https://api.etherscan.io/v2/api", "params_extra": {"chainid": "1"}}

def get_native_symbol(chain):
    return "BNB" if chain == "BSC" else "ETH"

def get_wallet_balance(address, chain="ETH", api_key=None):
    # (Giữ nguyên logic cũ, chỉ đổi tên hàm cho gọn)
    config = get_api_config(chain)
    url = f"{config['url']}?module=account&action=balance&address={address}&tag=latest"
    if api_key and len(api_key) > 5: url += f"&apikey={api_key}"
    for k, v in config['params_extra'].items(): url += f"&{k}={v}"
    
    try:
        res = requests.get(url, timeout=5).json()
        if res['status'] == '1':
            return float(res['result']) / 10**18, None
        return 0, f"Error: {res.get('message')}"
    except Exception as e:
        return 0, str(e)

def get_token_tx(address, chain="ETH", api_key=None):
    # (Logic cũ nhưng thêm cột Date để vẽ biểu đồ)
    config = get_api_config(chain)
    url = f"{config['url']}?module=account&action=tokentx&address={address}&page=1&offset=100&sort=desc" # Lấy 100 lệnh để vẽ biểu đồ cho đẹp
    if api_key and len(api_key) > 5: url += f"&apikey={api_key}"
    for k, v in config['params_extra'].items(): url += f"&{k}={v}"
    
    try:
        res = requests.get(url, timeout=5).json()
        if res['status'] == '1' and res['result']:
            txs = res['result']
            data = []
            for tx in txs:
                symbol = tx.get('tokenSymbol', '???')
                if len(symbol) > 10: continue
                try:
                    dec = int(tx.get('tokenDecimal', 18))
                    val = float(tx.get('value', 0)) / (10 ** dec)
                except: val = 0
                
                ts = int(tx.get('timeStamp', 0))
                time_obj = datetime.fromtimestamp(ts)
                
                direction = "IN" if tx['to'].lower() == address.lower() else "OUT"
                color = "#00ff9f" if direction == "IN" else "#ff0055"
                
                if val > 0:
                    data.append({
                        'TIME': time_obj.strftime("%Y-%m-%d %H:%M:%S"),
                        'DATE': time_obj.strftime("%Y-%m-%d"), # Cột này dùng để group biểu đồ
                        'SYMBOL': symbol,
                        'AMOUNT': val,
                        'TYPE': direction,
                        'COLOR': color
                    })
            return pd.DataFrame(data), None
        return None, "No Data"
    except Exception as e:
        return None, str(e)
