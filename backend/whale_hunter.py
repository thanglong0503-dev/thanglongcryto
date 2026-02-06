import requests
import pandas as pd

def get_trader_positions(encrypted_uid):
    """
    Hàm gọi API ẩn của Binance Leaderboard để lấy vị thế.
    Yêu cầu: encrypted_uid (Lấy từ URL của Trader Profile).
    """
    # URL Cổng sau của Binance (Internal API)
    url = "https://www.binance.com/bapi/futures/v1/public/future/leaderboard/getOtherPosition"
    
    # Giả danh trình duyệt thật để không bị chặn
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Content-Type": "application/json"
    }
    
    # Dữ liệu gửi đi
    payload = {
        "encryptedUid": encrypted_uid,
        "tradeType": "PERPETUAL" # Chỉ lấy lệnh Futures vĩnh cửu
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        data = response.json()
        
        if data['success'] and data['data'] is not None:
            positions = data['data']['otherPositionRetList']
            if not positions:
                return None, "⚠️ Trader này đang KHÔNG có lệnh hoặc ĐÃ ẨN vị thế."
            
            # Chuyển thành DataFrame cho đẹp
            df = pd.DataFrame(positions)
            
            # Lọc và đổi tên cột cho dễ đọc
            df = df[['symbol', 'entryPrice', 'markPrice', 'amount', 'pnl', 'roe', 'updateTime']]
            df.columns = ['SYMBOL', 'ENTRY', 'MARK', 'SIZE', 'PNL ($)', 'ROI (%)', 'TIME']
            
            # Xử lý format số
            df['TIME'] = pd.to_datetime(df['TIME'], unit='ms')
            
            return df, "OK"
        else:
            return None, "❌ Không tìm thấy Trader hoặc UID sai."
            
    except Exception as e:
        return None, f"❌ LỖI KẾT NỐI: {str(e)}"
