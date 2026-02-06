import requests
import pandas as pd

# --- CẤU HÌNH HEADERS ĐỂ GIẢ LẬP TRÌNH DUYỆT ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Clienttype": "web"
}

def get_leaderboard_positions(encrypted_uid):
    """CÁCH 1: Lấy lệnh từ Leaderboard (UID có chữ và số)"""
    url = "https://www.binance.com/bapi/futures/v1/public/future/leaderboard/getOtherPosition"
    payload = {"encryptedUid": encrypted_uid, "tradeType": "PERPETUAL"}
    
    try:
        res = requests.post(url, json=payload, headers=HEADERS, timeout=5).json()
        if res['success'] and res['data']:
            return process_data(res['data']['otherPositionRetList'])
        return None, "⚠️ Không tìm thấy vị thế (Leaderboard)."
    except Exception as e:
        return None, f"❌ Lỗi kết nối: {str(e)}"

def get_copy_trade_positions(portfolio_id):
    """CÁCH 2: Lấy lệnh từ Smart Money/Copy Trade (ID toàn số)"""
    # API Cổng sau của Smart Money
    url = "https://www.binance.com/bapi/futures/v1/public/future/copy-trade/lead-portfolio/position-list"
    payload = {"portfolioId": str(portfolio_id)}
    
    try:
        res = requests.post(url, json=payload, headers=HEADERS, timeout=5).json()
        if res['success'] and res['data']:
            # Copy Trade trả về cấu trúc hơi khác, cần map lại
            raw_list = res['data']
            return process_data_copy_trade(raw_list)
        return None, "⚠️ Trader này đang ẩn lệnh hoặc không có vị thế."
    except Exception as e:
        return None, f"❌ Lỗi kết nối Smart Money: {str(e)}"

def process_data(data_list):
    """Xử lý dữ liệu Leaderboard chuẩn"""
    if not data_list: return None, "Trader đang cầm tiền mặt (No Positions)."
    df = pd.DataFrame(data_list)
    df = df[['symbol', 'entryPrice', 'markPrice', 'amount', 'pnl', 'roe', 'updateTime']]
    df.columns = ['SYMBOL', 'ENTRY', 'MARK', 'SIZE', 'PNL ($)', 'ROI (%)', 'TIME']
    df['TIME'] = pd.to_datetime(df['TIME'], unit='ms')
    return df, "OK"

def process_data_copy_trade(data_list):
    """Xử lý dữ liệu Copy Trade (Cấu trúc khác)"""
    if not data_list: return None, "Trader đang cầm tiền mặt (No Positions)."
    
    # Map các trường của Copy Trade sang chuẩn chung
    # api copy trade: symbol, entryPrice, breakEvenPrice, positionAmount, unrealizedProfit, unrealizedProfitRate
    cleaned = []
    for item in data_list:
        cleaned.append({
            'SYMBOL': item.get('symbol'),
            'ENTRY': item.get('entryPrice'),
            'MARK': item.get('markPrice', 0), # Đôi khi không có mark price
            'SIZE': item.get('positionAmount'),
            'PNL ($)': item.get('unrealizedProfit'),
            'ROI (%)': float(item.get('unrealizedProfitRate', 0)) * 100, # Nó trả về số thập phân (0.3 -> 30%)
            'TIME': pd.Timestamp.now() # Copy trade API ko trả về updateTime, lấy giờ hiện tại
        })
        
    df = pd.DataFrame(cleaned)
    return df, "OK"

def scan_whale(input_id):
    """
    BỘ NÃO TRUNG TÂM: Tự động phân loại ID
    - Nếu toàn số -> Gọi Copy Trade API
    - Nếu có chữ -> Gọi Leaderboard API
    """
    input_id = str(input_id).strip()
    
    if input_id.isdigit():
        # Đây là Portfolio ID (Smart Money)
        return get_copy_trade_positions(input_id)
    else:
        # Đây là Encrypted UID (Leaderboard)
        return get_leaderboard_positions(input_id)
