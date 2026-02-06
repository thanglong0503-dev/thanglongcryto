import requests
import pandas as pd
from datetime import datetime

# --- CẤU HÌNH ---
DEMO_KEY = "YourApiKeyToken"

def get_api_config(chain):
    """
    CHIẾN THUẬT HYBRID:
    - ETH: Dùng cổng Etherscan V2 (Chuẩn mới)
    - BSC: Dùng cổng BscScan V1 (Chuẩn cũ nhưng MIỄN PHÍ)
    """
    if chain == "BSC":
        # Cổng BscScan truyền thống (Free Tier chạy ngon)
        return {
            "url": "https://api.bscscan.com/api",
            "params_extra": {} # BscScan V1 không cần chainid
        }
    else: # ETH
        # Cổng Etherscan V2
        return {
            "url": "https://api.etherscan.io/v2/api",
            "params_extra": {"chainid": "1"} # ETH ID = 1
        }

def get_native_symbol(chain):
    return "BNB" if chain == "BSC" else "ETH"

def get_wallet_balance(address, chain="BSC", api_key=None):
    key = api_key if api_key and len(api_key) > 5 else DEMO_KEY
    config = get_api_config(chain)
    
    # Tạo URL
    url = f"{config['url']}?module=account&action=balance&address={address}&tag=latest&apikey={key}"
    # Thêm tham số phụ (chainid nếu là ETH)
    for k, v in config['params_extra'].items():
        url += f"&{k}={v}"
    
    try:
        res = requests.get(url, timeout=5).json()
        
        if res['status'] == '1':
            val = float(res['result']) / 10**18
            return val, None
        else:
            return 0, f"{chain} API Error: {res.get('message')} - {res.get('result')}"
            
    except Exception as e:
        return 0, f"Connect Error: {str(e)}"

def get_token_tx(address, chain="BSC", api_key=None):
    key = api_key if api_key and len(api_key) > 5 else DEMO_KEY
    config = get_api_config(chain)
    
    url = f"{config['url']}?module=account&action=tokentx&address={address}&page=1&offset=50&sort=desc&apikey={key}"
    for k, v in config['params_extra'].items():
        url += f"&{k}={v}"
    
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
                
                time = datetime.fromtimestamp(int(tx.get('timeStamp', 0)))
                
                if tx['to'].lower() == address.lower():
                    direction = "IN (BUY) 🟢"
                    color = "#00ff9f"
                else:
                    direction = "OUT (SELL) 🔴"
                    color = "#ff0055"
                
                if val > 0:
                    data.append({
                        'TIME': time,
                        'SYMBOL': symbol,
                        'AMOUNT': val,
                        'TYPE': direction,
                        'COLOR': color,
                        'HASH': tx.get('hash', '')
                    })
            
            return pd.DataFrame(data), None
        
        elif res['message'] == 'No transactions found':
            return None, "ℹ️ Ví này chưa có giao dịch Token nào."
        else:
            return None, f"{chain} API Error: {res.get('message')} - {res.get('result')}"
            
    except Exception as e:
        return None, f"Connect Error: {str(e)}"
