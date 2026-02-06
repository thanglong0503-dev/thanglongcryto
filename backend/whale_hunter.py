import requests
import pandas as pd
import json

# --- CẤU HÌNH HEADERS GIẢ LẬP CHROME THẬT ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Clienttype": "web",
    "Lang": "vi",
    "Origin": "https://www.binance.com",
    "Referer": "https://www.binance.com/vi/smart-money/profile"
}

def get_leaderboard_positions(encrypted_uid):
    """CÁCH 1: Leaderboard (Dùng cổng Friendly luôn cho chắc)"""
    url = "https://www.binance.com/bapi/futures/v1/friendly/future/leaderboard/getOtherPosition"
    payload = {"encryptedUid": encrypted_uid, "tradeType": "PERPETUAL"}
    
    try:
        res = requests.post(url, json=payload, headers=HEADERS, timeout=5).json()
        if res.get('success') and res.get('data'):
            return process_data(res['data']['otherPositionRetList'])
        return None, "⚠️ Không tìm thấy lệnh (Leaderboard)."
    except Exception as e:
        return None, f"❌ Lỗi Leaderboard: {str(e)}"

def get_copy_trade_positions(portfolio_id):
    """CÁCH 2: Smart Money (Copy Trade) - Cổng Friendly"""
    # Đổi sang cổng 'friendly' (dễ tính hơn public)
    url = "https://www.binance.com/bapi/futures/v1/friendly/future/copy-trade/lead-portfolio/position-list"
    payload = {"portfolioId": str(portfolio_id)}
    
    try:
        response = requests.post(url, json=payload, headers=HEADERS, timeout=5)
        
        # DEBUG: Nếu không phải JSON (bị chặn IP), in ra mã lỗi HTML
        try:
            res = response.json()
        except:
            return None, f"⚠️ Lỗi Phản Hồi (Not JSON): Status {response.status_code}"

        # Kiểm tra thành công (Code 000000)
        if res.get('success') is True or res.get('code') == '000000':
            data_list = res.get('data')
            if data_list is not None and len(data_list) > 0:
                return process_data_copy_trade(data_list)
            else:
                return None, "⚠️ Trader này đang KHÔNG CÓ LỆNH (Trống)."
        else:
            # In nguyên văn phản hồi của Binance để debug
            raw_err = json.dumps(res) 
            return None, f"⚠️ Binance Từ Chối: {raw_err}"
            
    except Exception as e:
        return None, f"❌ Lỗi Smart Money: {str(e)}"

def process_data(data_list):
    """Xử lý dữ liệu Leaderboard"""
    if not data_list: return None, "No Data"
    df = pd.DataFrame(data_list)
    cols = {'symbol': 'SYMBOL', 'entryPrice': 'ENTRY', 'markPrice': 'MARK', 'amount': 'SIZE', 'pnl': 'PNL ($)', 'roe': 'ROI (%)', 'updateTime': 'TIME'}
    df = df.rename(columns=cols)
    valid_cols = [c for c in cols.values() if c in df.columns]
    df = df[valid_cols]
    if 'TIME' in df.columns: df['TIME'] = pd.to_datetime(df['TIME'], unit='ms')
    return df, "OK"

def process_data_copy_trade(data_list):
    """Xử lý dữ liệu Copy Trade"""
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
