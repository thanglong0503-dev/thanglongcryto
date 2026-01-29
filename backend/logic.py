import pandas_ta as ta

def analyze_market(df):
    if df is None: return None
    
    try:
        # Tính chỉ báo
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        price = curr['close']
        rsi = curr.get('RSI_14', 50)
        
        # Pivot Points
        pp = (curr['high'] + curr['low'] + curr['close']) / 3
        r1 = (2 * pp) - curr['low']
        s1 = (2 * pp) - curr['high']
        
        # Logic Tín hiệu
        signal = "NEUTRAL"
        color = "#888"
        
        # Trend
        if 'EMA_50' in curr and 'EMA_200' in curr:
            if price > curr['EMA_50'] and curr['EMA_50'] > curr['EMA_200']:
                signal = "STRONG UPTREND 🚀"
                color = "var(--bull)"
            elif price < curr['EMA_50'] and curr['EMA_50'] < curr['EMA_200']:
                signal = "STRONG DOWNTREND 🩸"
                color = "var(--bear)"
        
        # RSI Override
        if rsi < 30: 
            signal = "OVERSOLD (BUY DIP) ⚡"
            color = "var(--accent)"
        elif rsi > 70:
            signal = "OVERBOUGHT (CAUTION) ⚠️"
            color = "#ff9100"

        return {
            "price": price,
            "rsi": rsi,
            "signal": signal,
            "color": color,
            "r1": r1,
            "s1": s1,
            "vol_state": "SQUEEZE" if (curr.get('BBU_20_2.0', 0) - curr.get('BBL_20_2.0', 0)) < (price * 0.02) else "NORMAL"
        }
    except: return None
