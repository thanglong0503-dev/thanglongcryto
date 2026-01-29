import pandas_ta as ta
import pandas as pd
import numpy as np

def calculate_volume_profile(df, bins=50):
    """
    Thuật toán tìm POC (Point of Control) - Mức giá có Volume lớn nhất
    """
    try:
        # Lấy khoảng giá cao nhất và thấp nhất trong 200 nến gần nhất
        price_min = df['low'].min()
        price_max = df['high'].max()
        
        # Tạo các khoảng giá (Buckets)
        price_range = np.linspace(price_min, price_max, bins)
        
        # Tính tổng volume cho mỗi mức giá
        # (Đây là cách tính đơn giản hóa cho tốc độ Realtime)
        vol_profile = pd.cut(df['close'], bins=bins, labels=price_range[:-1])
        vol_by_price = df.groupby(vol_profile)['volume'].sum()
        
        # Tìm mức giá có Volume lớn nhất (POC)
        poc_price = vol_by_price.idxmax()
        
        return float(poc_price)
    except:
        return 0

def analyze_market(df):
    if df is None: return None
    
    try:
        # --- 1. CHỈ BÁO CƠ BẢN ---
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.ema(length=50, append=True)
        
        # --- 2. TÍNH VOLUME PROFILE (NEW V19) ---
        poc = calculate_volume_profile(df)
        
        curr = df.iloc[-1]
        price = curr['close']
        rsi = curr.get('RSI_14', 50)
        
        # Pivot Points
        pp = (curr['high'] + curr['low'] + curr['close']) / 3
        r1 = (2 * pp) - curr['low']
        s1 = (2 * pp) - curr['high']
        
        # --- 3. LOGIC SĂN CÁ MẬP ---
        signal = "NEUTRAL"
        color = "#888"
        
        # Kiểm tra giá so với POC (Nam châm hút giá)
        dist_to_poc = (price - poc) / price * 100
        
        poc_status = "FAR"
        if abs(dist_to_poc) < 0.5: # Nếu giá cách POC dưới 0.5%
            poc_status = "AT POC ZONE (Cân bằng)"
            # Tại vùng này, nếu có nến đảo chiều -> Đánh Breakout
        elif price > poc:
            poc_status = "ABOVE POC (Phe Mua nắm)"
        else:
            poc_status = "BELOW POC (Phe Bán nắm)"

        # Tín hiệu tổng hợp
        if poc_status == "ABOVE POC" and rsi < 40:
            signal = "PULLBACK TO POC (Canh Buy)"
            color = "var(--bull)"
        elif poc_status == "BELOW POC" and rsi > 60:
            signal = "REJECT POC (Canh Sell)" # Giống mô hình trong ảnh của Ngài
            color = "var(--bear)"
        elif abs(dist_to_poc) < 0.2:
            signal = "FIGHTING AT POC (Chờ)"
            color = "#fff"

        return {
            "price": price,
            "rsi": rsi,
            "signal": signal,
            "color": color,
            "r1": r1,
            "s1": s1,
            "poc": poc, # Trả về giá trị POC để hiển thị
            "poc_stat": poc_status,
            "vol_state": "NORMAL"
        }
    except Exception as e:
        print(f"Logic Error: {e}")
        return None
