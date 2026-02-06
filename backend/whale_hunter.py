import requests
import pandas as pd
import json
import random

# --- CẤU HÌNH HEADERS GIẢ LẬP ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Clienttype": "web",
}

# DANH SÁCH CÁC CỬA SAU (MIRROR DOMAINS)
# Nếu .com bị chặn (do IP Mỹ), ta thử lách qua .me hoặc .info
DOMAINS = [
    "https://www.binance.me",      # Thường dùng để né chặn
    "https://www.binance.info",    # Cổng thông tin
    "https://www.binance.com",     # Cổng chính (dễ bị chặn ở Mỹ)
]

def make_request(endpoint, payload):
    """Hàm bắn thử vào từng tên miền cho đến khi thủng"""
    for domain in DOMAINS:
        url = f"{domain}{endpoint}"
        # Cập nhật Origin/Referer theo domain đang thử
        current_headers = HEADERS.copy()
        current_headers["Origin"] = domain
        current_headers["Referer"] = f"{domain}/vi/smart-money/profile"
        
        try:
            res = requests.post(url, json=payload, headers=current_headers, timeout=5)
            data = res.json()
            
            # Kiểm tra xem có bị chặn địa lý không
            if data.get('code') == '000000' or data.get('success') is True:
                return data, None # Thành công
            
            # Nếu bị chặn địa lý, thử domain tiếp theo
            if "restricted location" in str(data.get('msg', '')):
                continue 
                
        except:
            continue
            
    return None, "❌ Đã thử tất cả các cổng nhưng Server IP này (Mỹ) bị Binance chặn hoàn toàn."

def get_leaderboard_positions(encrypted_uid):
    endpoint = "/bapi/futures/v1/friendly/future/leaderboard/getOtherPosition"
    payload = {"encryptedUid": encrypted_uid, "tradeType": "PERPETUAL"}
    
    data, err = make_request(endpoint, payload)
    if data:
        if data.get('data'):
            return process_data(data['data']['otherPositionRetList'])
        return None, "⚠️ Trader này đang ẩn danh sách hoặc không có lệnh."
    return None, err

def get_copy_trade_positions(portfolio_id):
    endpoint = "/bapi/futures/v1/friendly/future/copy-trade/lead-portfolio/position-list"
    payload = {"portfolioId": str(portfolio_id)}
    
    data, err = make_request(endpoint, payload)
    if data:
        if data.get('data'):
            return process_data_copy_trade(data.get('data'))
        return None, "⚠️ Danh sách lệnh TRỐNG."
    return None, err

# --- CÁC HÀM XỬ LÝ DỮ LIỆU (GIỮ NGUYÊN) ---
def process_data(data_list):
    if not data_list: return None, "No Data"
    df = pd.DataFrame(data_list)
    cols = {'symbol': 'SYMBOL', 'entryPrice': 'ENTRY', 'markPrice': 'MARK', 'amount': 'SIZE', 'pnl': 'PNL ($)', 'roe': 'ROI (%)', 'updateTime': 'TIME'}
    df = df.rename(columns=cols)
    valid_cols = [c for c in cols.values() if c in df.columns]
    df = df[valid_cols]
    if 'TIME' in df.columns: df['TIME'] = pd.to_datetime(df['TIME'], unit='ms')
    return df, "OK"

def process_data_copy_trade(data_list):
    cleaned = []
    for item in data_list:
        cleaned.append({
            'SYMBOL': item.get('symbol'),
            'ENTRY': float(item.get('entryPrice', 0)),
            'MARK': float(item.get('markPrice', 0)),
            'SIZE': float(item.get('positionAmount', 0)),
            'PNL ($)': float(item.get('unrealizedProfit', 0)),
            'ROI (%)': float(item.get('unrealizedProfitRate', 0)) * 100,
            'TIME': "Live"
        })
    df = pd.DataFrame(cleaned)
    return df, "OK"

def scan_whale(input_id):
    input_id = str(input_id).strip()
    if input_id.isdigit():
        return get_copy_trade_positions(input_id)
    else:
        return get_leaderboard_positions(input_id)
