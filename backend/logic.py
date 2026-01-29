import pandas_ta as ta
import pandas as pd
import numpy as np

def analyze_market(df):
    if df is None: return None
    
    try:
        # --- 1. TÍNH TOÁN CHỈ BÁO (NẠP ĐẠN) ---
        # Cơ bản
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)
        
        # Nâng cao (V18 Features - ĐÂY LÀ PHẦN CŨ BỊ THIẾU)
        df.ta.adx(length=14, append=True) 
        df.ta.stochrsi(length=14, append=True)
        
        # Volume Average
        vol_ma = df['volume'].rolling(window=20).mean()
        
        # Lấy dữ liệu nến cuối
        curr = df.iloc[-1]
        
        price = curr['close']
        
        # Lấy chỉ báo an toàn (Dùng .get để không bị crash nếu thiếu cột)
        rsi = curr.get('RSI_14', 50)
        adx = curr.get('ADX_14', 0)
        
        # Lấy StochRSI (Tên cột của pandas_ta hơi dài, cần check kỹ)
        # Thường là STOCHRSIk_14_14_3_3 và STOCHRSId_14_14_3_3
        stoch_k = curr.get('STOCHRSIk_14_14_3_3', 0) 
        
        # Pivot Points
        pp = (curr['high'] + curr['low'] + curr['close']) / 3
        r1 = (2 * pp) - curr['low']
        s1 = (2 * pp) - curr['high']
        
        # --- 2. LOGIC PHÂN TÍCH (XỬ LÝ) ---
        signal = "NEUTRAL"
        color = "#888"
        
        # A. Logic Trend
        trend_status = "SIDEWAY"
        if 'EMA_50' in curr and 'EMA_200' in curr:
            if price > curr['EMA_50'] and curr['EMA_50'] > curr['EMA_200']:
                trend_status = "UPTREND"
            elif price < curr['EMA_50'] and curr['EMA_50'] < curr['EMA_200']:
                trend_status = "DOWNTREND"
        
        # B. Logic Sức mạnh (ADX)
        trend_strength = "WEAK"
        if adx > 25: trend_strength = "STRONG"
        if adx > 50: trend_strength = "SUPER STRONG"
        
        # C. Logic Volume
        curr_vol = curr['volume']
        avg_vol = vol_ma.iloc[-1]
        vol_spike = "NORMAL"
        if avg_vol > 0:
            ratio = curr_vol / avg_vol
            if ratio > 2.0: vol_spike = "🐋 WHALE ALERT"
            elif ratio > 1.5: vol_spike = "HIGH VOLUME"
            
        # D. Tín hiệu tổng hợp
        if trend_status == "UPTREND" and stoch_k < 20:
            signal = "PULLBACK BUY (Múc)"
            color = "var(--bull)"
        elif trend_status == "DOWNTREND" and stoch_k > 80:
            signal = "SHORT SELL (Xả)"
            color = "var(--bear)"
        elif rsi < 30:
            signal = "OVERSOLD (Bắt đáy)"
            color = "var(--accent)"
        elif rsi > 70:
            signal = "OVERBOUGHT (Cẩn thận)"
            color = "#ff9100"

        # --- 3. ĐÓNG GÓI DỮ LIỆU (TRẢ VỀ) ---
        # App.py cần key nào thì ở đây phải có key đó
        return {
            "price": price,
            "rsi": rsi,
            "adx": adx,
            "stoch_k": stoch_k,  # <--- CHÍNH LÀ CÁI KEY NÀY BỊ THIẾU LÚC NÃY
            "signal": signal,
            "color": color,
            "r1": r1,
            "s1": s1,
            "trend": trend_status,
            "strength": trend_strength,
            "vol_status": vol_spike
        }
    except Exception as e:
        print(f"Logic Error: {e}")
        return None
