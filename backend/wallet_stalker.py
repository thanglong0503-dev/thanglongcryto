import requests
import pandas as pd
from datetime import datetime

# --- CẤU HÌNH V2 (UNIVERSAL) ---
# Dùng chung 1 cổng cho tất cả mạng
BASE_URL_V2 = "https://api.etherscan.io/v2/api"
DEMO_KEY = "YourApiKeyToken" 

def get_chain_id(chain):
    """Lấy ID mạng theo chuẩn V2"""
    if chain == "BSC": return "56"  # ID của Binance Smart Chain
    if chain == "ETH": return "1"   # ID của Ethereum
    return "1"

def get_native_symbol(chain):
    return "BNB" if chain == "BSC" else "ETH"

def get_wallet_balance(address, chain="BSC", api_key=None):
    """
    Lấy số dư qua cổng V2 (Chuẩn mới)
    """
    key = api_key if api_key and len(api_key) > 5 else DEMO_KEY
    chain_id = get_chain_id(chain)
    
    # URL chuẩn V2: Thêm tham số &chainid=...
    url = f"{BASE_URL_V2}?chainid={chain_id}&module=account&action=balance&address={address}&tag=latest&apikey={key}"
    
    try:
        res = requests.get(url, timeout=5).json()
        
        # STATUS 1 = OK
        if res['status'] == '1':
            val = float(res['result']) / 10**18
            return val, None
        else:
            return 0, f"API V2 Error: {res.get('message')} - {res.get('result')}"
            
    except Exception as e:
        return 0, f"Connect Error: {str(e)}"

def get_token_tx(address, chain="BSC", api_key=None):
    """
    Lấy giao dịch Token qua cổng V2
    """
    key = api_key if api_key and len(api_key) > 5 else DEMO_KEY
    chain_id = get_chain_id(chain)
    
    # URL chuẩn V2
    url = f"{BASE_URL_V2}?chainid={chain_id}&module=account&action=tokentx&address={address}&page=1&offset=50&sort=desc&apikey={key}"
    
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
                
                # Phân loại MUA/BÁN
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
            return None, f"API V2 Error: {res.get('message')} - {res.get('result')}"
            
    except Exception as e:
        return None, f"Connect Error: {str(e)}"
