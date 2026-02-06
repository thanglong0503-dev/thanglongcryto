import requests
import pandas as pd

# --- CẤU HÌNH HEADERS (QUAN TRỌNG ĐỂ KHÔNG BỊ CHẶN) ---
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
        # Leaderboard dùng key 'success'
        if res.get('success') and res.get('data'):
            return process_data(res['data']['otherPositionRetList'])
        return None, "⚠️ Không tìm thấy vị thế hoặc Trader ẩn danh sách."
    except Exception as e:
        return None, f"❌ Lỗi Leaderboard: {str(e)}"

def get_copy_trade_positions(portfolio_id):
    """CÁCH 2: Lấy lệnh từ Smart Money/Copy Trade (ID toàn số)"""
    url = "https://www.binance.com/bapi/futures/v1/public/future/copy-trade/lead-portfolio/position-list"
    payload = {"portfolioId": str(portfolio_id)}
    
    try:
        res = requests.post(url, json=payload, headers=HEADERS, timeout=5).json()
        
        # --- FIX LỖI: KIỂM TRA LINH HOẠT CẢ 'success' VÀ 'code' ---
        # Binance Smart Money đôi khi trả về 'code': '000000' thay vì 'success': True
        is_success = (res.get('success') is True) or (res.get('code') == '000000')
        
        if is_success:
            data_list = res.get('data')
            if data_list and len(data_list) > 0:
                return process_data_copy_trade(data_list)
            else:
                return None, "⚠️ Trader này đang KHÔNG CÓ LỆNH (Trống)."
        else:
            # Nếu API trả về lỗi, in ra message của Binance để debug
            err_msg = res.get('message', 'Unknown Error')
            return None, f"⚠️ Binance chặn: {err_msg}"
            
    except Exception as e:
        return None, f"❌ Lỗi Smart Money: {str(e)}"

def process_data(data_list):
    """Xử lý dữ liệu Leaderboard"""
    if not data_list: return None, "No Data"
    df = pd.DataFrame(data_list)
    # Lọc cột an toàn (chỉ lấy nếu tồn tại)
    cols = {'symbol': 'SYMBOL', 'entryPrice': 'ENTRY', 'markPrice': 'MARK', 'amount': 'SIZE', 'pnl': 'PNL ($)', 'roe': 'ROI (%)', 'updateTime': 'TIME'}
    # Đổi tên các cột khớp
    df = df.rename(columns=cols)
    # Chỉ giữ lại các cột cần thiết có trong df
    valid_cols = [c for c in cols.values() if c in df.columns]
    df = df[valid_cols]
    
    if 'TIME' in df.columns:
        df['TIME'] = pd.to_datetime(df['TIME'], unit='ms')
    return df, "OK"

def process_data_copy_trade(data_list):
    """Xử lý dữ liệu Copy Trade (Cấu trúc khác biệt)"""
    cleaned = []
    for item in data_list:
        # Map dữ liệu thủ công để tránh lỗi thiếu cột
        cleaned.append({
            'SYMBOL': item.get('symbol'),
            'ENTRY': float(item.get('entryPrice', 0)),
            'MARK': float(item.get('markPrice', 0)),
            'SIZE': float(item.get('positionAmount', 0)),
            'PNL ($)': float(item.get('unrealizedProfit', 0)),
            # Copy trade trả về ROI dạng thập phân (0.3), cần nhân 100
            'ROI (%)': float(item.get('unrealizedProfitRate', 0)) * 100,
            'TIME': "Live" # Copy trade API không trả về time update
        })
        
    df = pd.DataFrame(cleaned)
    return df, "OK"

def scan_whale(input_id):
    """BỘ NÃO: Tự động chọn API dựa vào input"""
    input_id = str(input_id).strip()
    if input_id.isdigit():
        return get_copy_trade_positions(input_id)
    else:
        return get_leaderboard_positions(input_id)
