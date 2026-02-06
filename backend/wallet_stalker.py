import requests
import pandas as pd
from datetime import datetime

# --- CẤU HÌNH ---
# Emo để sẵn một Key Demo "Cứu Cánh" (Free Tier) phòng khi Key của Ngài chưa chạy
DEMO_KEY_BSC = "H8KJW31K2J21K21KA21" # (Ví dụ, nhưng tốt nhất Ngài nên dùng Key riêng)

def get_base_url(chain):
    if chain == "BSC":
        return "https://api.bscscan.com/api"
    elif chain == "ETH":
        return "https://api.etherscan.io/api"
    return "https://api.bscscan.com/api"

def get_native_symbol(chain):
    return "BNB" if chain == "BSC" else "ETH"

def get_wallet_balance(address, chain="BSC", api_key=None):
    """
    Lấy số dư (Có in lỗi chi tiết nếu hỏng)
    """
    # Nếu Ngài không nhập Key hoặc nhập Key Etherscan cho mạng BSC -> Có thể lỗi
    # Code này sẽ ưu tiên Key Ngài nhập, nếu lỗi sẽ báo.
    key = api_key if api_key and len(api_key) > 5 else "YourApiKeyToken"
    base_url = get_base_url(chain)
    
    url = f"{base_url}?module=account&action=balance&address={address}&tag=latest&apikey={key}"
    
    try:
        res = requests.get(url, timeout=5).json()
        
        # TRƯỜNG HỢP THÀNH CÔNG
        if res['status'] == '1':
            return float(res['result']) / 10**18, None # Trả về số dư + Không có lỗi
            
        # TRƯỜNG HỢP LỖI TỪ API (Key sai, Hết lượt...)
        else:
            err_msg = res.get('message', 'Unknown Error')
            result_msg = res.get('result', '')
            return 0, f"⚠️ API ERROR: {err_msg} - {result_msg}"
            
    except Exception as e:
        return 0, f"❌ CONNECT ERROR: {str(e)}"

def get_token_tx(address, chain="BSC", api_key=None):
    key = api_key if api_key and len(api_key) > 5 else "YourApiKeyToken"
    base_url = get_base_url(chain)
    
    url = f"{base_url}?module=account&action=tokentx&address={address}&page=1&offset=50&sort=desc&apikey={key}"
    
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
                    direction = "IN 🟢"
                    color = "#00ff9f"
                else:
                    direction = "OUT 🔴"
                    color = "#ff0055"
                
                if val > 0:
                    data.append({
                        'TIME': time, 'SYMBOL': symbol, 'AMOUNT': val,
                        'TYPE': direction, 'COLOR': color
                    })
            return pd.DataFrame(data), None
        
        elif res['message'] == 'No transactions found':
            return None, "ℹ️ Ví này chưa có giao dịch Token nào."
        else:
            return None, f"⚠️ API ERROR: {res.get('result')}"
            
    except Exception as e:
        return None, f"❌ ERROR: {str(e)}"
