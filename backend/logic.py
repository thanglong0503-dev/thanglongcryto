import pandas_ta as ta
import pandas as pd
import numpy as np

def calculate_volume_profile(df, bins=50):
    """Tính toán POC (Point of Control) - Mức giá Volume lớn nhất"""
    try:
        price_min = df['low'].min()
        price_max = df['high'].max()
        price_range = np.linspace(price_min, price_max, bins)
        vol_profile = pd.cut(df['close'], bins=bins, labels=price_range[:-1])
        vol_by_price = df.groupby(vol_profile)['volume'].sum()
        return float(vol_by_price.idxmax())
    except:
        return 0.0

def analyze_market(df):
    if df is None: return None
    
    try:
        # --- 1. TÍNH TOÁN CHỈ BÁO (FULL OPTION) ---
        # Cơ bản
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)
        
        # Nâng cao (V18: Stoch & ADX)
        df.ta.adx(length=14, append=True) 
        df.ta.stochrsi(length=14, append=True)
        
        # Volume Profile (V19: POC)
        poc = calculate_volume_profile(df)
        
        # Volume Average (V18: Cá mập)
        vol_ma = df['volume'].rolling(window=20).mean()
        
        # --- 2. LẤY DỮ LIỆU ---
        curr = df.iloc[-1]
        price = curr['close']
        
        # Lấy chỉ số an toàn
        rsi = curr.get('RSI_14', 50)
        adx = curr.get('ADX_14', 0)
        
        # Lấy StochRSI (Tên cột thường khá dài, cần lấy đúng)
        # Pandas TA thường đặt tên là STOCHRSIk... và STOCHRSId...
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
        dist_poc = (price - poc) / price * 100
        poc_stat = "AT POC" if abs(dist_poc) < 0.5 else ("ABOVE" if price > poc else "BELOW")
        
        # E. Tín hiệu Tổng hợp (Signal)
        # Ưu tiên tín hiệu POC Rejection (Mô hình Ngài gửi)
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

        # --- 4. TRẢ VỀ KẾT QUẢ (QUAN TRỌNG: PHẢI CÓ ĐỦ KEY) ---
        return {
            "price": price,
            "rsi": rsi,
            "adx": adx,
            "stoch_k": stoch_k,   # Khắc phục lỗi KeyError: 'stoch_k'
            "poc": poc,           # Khắc phục lỗi KeyError: 'poc'
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
