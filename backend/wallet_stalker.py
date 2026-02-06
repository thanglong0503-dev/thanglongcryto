import requests
import pandas as pd
from datetime import datetime

def get_base_url(chain):
    """Chọn Server dựa trên mạng muốn soi"""
    if chain == "BSC":
        return "https://api.bscscan.com/api"
    elif chain == "ETH":
        return "https://api.etherscan.io/api"
    return "https://api.bscscan.com/api"

def get_native_symbol(chain):
    return "BNB" if chain == "BSC" else "ETH"

def get_wallet_balance(address, chain="BSC", api_key=None):
    """Xem số dư BNB/ETH"""
    # Nếu Ngài không nhập Key, dùng Key Demo (Hên xui)
    key = api_key if api_key else "YourApiKeyToken" 
    base_url = get_base_url(chain)
    
    url = f"{base_url}?module=account&action=balance&address={address}&tag=latest&apikey={key}"
    
    try:
        res = requests.get(url, timeout=5).json()
        if res['status'] == '1':
            val = float(res['result']) / 10**18
            return val
        return 0
    except:
        return 0

def get_token_tx(address, chain="BSC", api_key=None):
    """Lấy lịch sử giao dịch Token (BEP-20 hoặc ERC-20)"""
    key = api_key if api_key else "YourApiKeyToken"
    base_url = get_base_url(chain)
    
    # Lấy 50 giao dịch gần nhất
    url = f"{base_url}?module=account&action=tokentx&address={address}&page=1&offset=50&sort=desc&apikey={key}"
    
    try:
        res = requests.get(url, timeout=5).json()
        if res['status'] == '1' and res['result']:
            txs = res['result']
            data = []
            
            for tx in txs:
                symbol = tx['tokenSymbol']
                # Lọc rác
                if not symbol or len(symbol) > 15: continue
                
                # Tính số lượng (Chia cho decimal)
                try:
                    decimals = int(tx['tokenDecimal'])
                    value = float(tx['value']) / (10 ** decimals)
                except:
                    value = 0
                
                time = datetime.fromtimestamp(int(tx['timeStamp']))
                
                # Xác định Mua/Bán
                if tx['to'].lower() == address.lower():
                    direction = "IN (BUY) 🟢"
                    color = "#00ff9f"
                else:
                    direction = "OUT (SELL) 🔴"
                    color = "#ff0055"
                
                # Chỉ hiển thị giao dịch có giá trị
                if value > 0.0001:
                    data.append({
                        'TIME': time,
                        'SYMBOL': symbol,
                        'AMOUNT': value,
                        'TYPE': direction,
                        'COLOR': color,
                        'HASH': tx['hash']
                    })
            
            return pd.DataFrame(data)
        return None
    except Exception as e:
        return None
