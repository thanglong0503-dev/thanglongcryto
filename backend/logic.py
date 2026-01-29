import pandas_ta as ta

def analyze_market(df):
    if df is None: return None
    
    try:
        # --- 1. TÍNH TOÁN CHỈ BÁO NÂNG CAO ---
        # Cơ bản
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)
        
        # Nâng cao (V18 Features)
        df.ta.adx(length=14, append=True) # Trend Strength
        df.ta.stochrsi(length=14, append=True) # Momentum nhanh
        
        # Volume Average
        vol_ma = df['volume'].rolling(window=20).mean()
        
        # Lấy dữ liệu nến cuối
        curr = df.iloc[-1]
        
        price = curr['close']
        rsi = curr.get('RSI_14', 50)
        
        # Lấy ADX (Cẩn thận tên cột)
        adx = curr.get('ADX_14', 0)
        
        # Lấy StochRSI (pandas_ta trả về 2 cột k và d)
        stoch_k = curr.get('STOCHRSIk_14_14_3_3', 0)
        stoch_d = curr.get('STOCHRSId_14_14_3_3', 0)
        
        # Pivot Points
        pp = (curr['high'] + curr['low'] + curr['close']) / 3
        r1 = (2 * pp) - curr['low']
        s1 = (2 * pp) - curr['high']
        
        # --- 2. LOGIC PHÂN TÍCH (THE BRAIN) ---
        signal = "NEUTRAL"
        color = "#888"
        
        # A. Logic Trend (EMA)
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
        
        # C. Logic Volume (Whale Detector)
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

        return {
            "price": price,
            "rsi": rsi,
            "adx": adx,
            "stoch_k": stoch_k,
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
