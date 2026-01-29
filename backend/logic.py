import pandas_ta as ta
import pandas as pd
import numpy as np

def calculate_volume_profile(df, bins=100):
    """
    FIXED: Sử dụng Numpy Histogram để tính POC chính xác 100%
    """
    try:
        # 1. Chuyển dữ liệu sang dạng mảng số (Array) cho nhanh
        prices = df['close'].values
        volumes = df['volume'].values

        # 2. Kiểm tra dữ liệu rỗng
        if len(prices) == 0 or len(volumes) == 0:
            return 0.0

        # 3. Dùng Histogram để gom giá vào 100 cái xô (bins)
        # weights=volumes nghĩa là: đếm giá dựa trên khối lượng giao dịch
        counts, bin_edges = np.histogram(prices, bins=bins, weights=volumes)

        # 4. Tìm cái xô nào chứa nhiều Volume nhất
        max_index = counts.argmax()

        # 5. POC chính là giá trung tâm của cái xô đó
        poc_price = (bin_edges[max_index] + bin_edges[max_index+1]) / 2

        return float(poc_price)
    except Exception as e:
        print(f"POC Error: {e}")
        return 0.0

def analyze_market(df):
    if df is None: return None
    
    try:
        # --- 1. TÍNH TOÁN CHỈ BÁO ---
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)
        
        # Stoch & ADX
        df.ta.adx(length=14, append=True) 
        df.ta.stochrsi(length=14, append=True)
        
        # --- QUAN TRỌNG: TÍNH POC BẰNG THUẬT TOÁN MỚI ---
        poc = calculate_volume_profile(df, bins=100)
        
        # Volume Average
        vol_ma = df['volume'].rolling(window=20).mean()
        
        # --- 2. LẤY DỮ LIỆU ---
        curr = df.iloc[-1]
        price = curr['close']
        
        # Lấy chỉ số an toàn
        rsi = curr.get('RSI_14', 50)
        adx = curr.get('ADX_14', 0)
        stoch_k = curr.get('STOCHRSIk_14_14_3_3', 0)
        
        # Pivot Points
        pp = (curr['high'] + curr['low'] + curr['close']) / 3
        r1 = (2 * pp) - curr['low']
        s1 = (2 * pp) - curr['high']
        
        # --- 3. LOGIC PHÂN TÍCH ---
        signal = "NEUTRAL"
        color = "#888"
        
        # A. Logic Trend
        trend_status = "SIDEWAY"
        if 'EMA_50' in curr and 'EMA_200' in curr:
            if price > curr['EMA_50'] and curr['EMA_50'] > curr['EMA_200']: trend_status = "UPTREND"
            elif price < curr['EMA_50'] and curr['EMA_50'] < curr['EMA_200']: trend_status = "DOWNTREND"
            
        # B. Logic Strength (ADX)
        trend_strength = "WEAK"
        if adx > 25: trend_strength = "STRONG"
        if adx > 50: trend_strength = "SUPER"
        
        # C. Logic Volume (Whale)
        avg_vol = vol_ma.iloc[-1]
        vol_status = "NORMAL"
        if avg_vol > 0 and (curr['volume'] / avg_vol) > 2.0:
            vol_status = "🐋 WHALE"
            
        # D. Logic POC (Volume Profile)
        # Fix lỗi chia cho 0 nếu POC = 0 (trường hợp hiếm)
        if poc > 0:
            dist_poc = (price - poc) / price * 100
            if abs(dist_poc) < 0.5: poc_stat = "AT POC"
            elif price > poc: poc_stat = "ABOVE"
            else: poc_stat = "BELOW"
        else:
            poc_stat = "CALC..."
            dist_poc = 0

        # E. Tín hiệu Tổng hợp
        if poc_stat == "BELOW" and rsi > 60:
            signal = "REJECT POC (Sell)"
            color = "var(--bear)"
        elif trend_status == "UPTREND" and stoch_k < 20:
            signal = "PULLBACK (Buy)"
            color = "var(--bull)"
        elif rsi < 30:
            signal = "OVERSOLD (Buy)"
            color = "var(--accent)"
        elif rsi > 70:
            signal = "OVERBOUGHT (Sell)"
            color = "#ff9100"

        return {
            "price": price,
            "rsi": rsi,
            "adx": adx,
            "stoch_k": stoch_k,
            "poc": poc,
            "poc_stat": poc_stat,
            "signal": signal,
            "color": color,
            "r1": r1,
            "s1": s1,
            "trend": trend_status,
            "strength": trend_strength,
            "vol_status": vol_status,
            "vol_state": "SQUEEZE" if (curr.get('BBU_20_2.0',0) - curr.get('BBL_20_2.0',0)) < (price*0.02) else "NORMAL"
        }
    except Exception as e:
        print(f"Logic Error: {e}")
        return None
