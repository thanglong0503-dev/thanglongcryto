import pandas_ta as ta
import pandas as pd
import numpy as np

# --- 1. THUẬT TOÁN SĂN CÁ MẬP (SMC) ---
def detect_smart_money(df):
    """Tìm các vùng mất cân bằng thanh khoản (FVG)"""
    gaps = []
    # Quét 50 nến gần nhất
    for i in range(len(df)-50, len(df)):
        if i < 2: continue
        curr = df.iloc[i]; prev = df.iloc[i-1]; prev2 = df.iloc[i-2]
        
        # Bullish FVG (Hỗ trợ - Xanh)
        if prev2['high'] < curr['low']:
            gap = curr['low'] - prev2['high']
            if gap > (curr['close'] * 0.0005): # Lọc gap nhiễu
                gaps.append({"type": "🟢 BULL FVG", "top": curr['low'], "bottom": prev2['high']})
                
        # Bearish FVG (Kháng cự - Đỏ)
        elif prev2['low'] > curr['high']:
            gap = prev2['low'] - curr['high']
            if gap > (curr['close'] * 0.0005):
                gaps.append({"type": "🔴 BEAR FVG", "top": prev2['low'], "bottom": curr['high']})
    
    # Chỉ lấy vùng gần giá hiện tại nhất
    if not gaps: return None
    return gaps[-1] # Trả về vùng mới nhất

# --- 2. BỘ NÃO PHÂN TÍCH CHÍNH ---
def analyze_market(df):
    if df is None: return None
    try:
        # Chỉ báo cơ bản
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.adx(length=14, append=True)
        df.ta.stochrsi(length=14, append=True)
        
        # POC (Volume Profile) - Fix lỗi chia 0
        price_min = df['low'].min(); price_max = df['high'].max()
        hist, bin_edges = np.histogram(df['close'], bins=100, weights=df['volume'])
        poc = (bin_edges[hist.argmax()] + bin_edges[hist.argmax()+1]) / 2

        # Lấy dữ liệu nến cuối
        curr = df.iloc[-1]
        price = curr['close']
        rsi = curr.get('RSI_14', 50)
        adx = curr.get('ADX_14', 0)
        stoch_k = curr.get('STOCHRSIk_14_14_3_3', 0)
        
        # Pivot Points
        pp = (curr['high'] + curr['low'] + curr['close']) / 3
        r1 = (2 * pp) - curr['low']
        s1 = (2 * pp) - curr['high']
        
        # --- GỌI SỨC MẠNH SMC ---
        smc_zone = detect_smart_money(df)

        # Logic Trend
        trend = "SIDEWAY"
        if 'EMA_50' in df.columns: # Nếu có EMA
            pass # (Giản lược logic trend để code gọn, tập trung vào SMC)
        
        # Đánh giá Trend đơn giản qua RSI/Price
        if rsi > 55: trend = "UPTREND"
        elif rsi < 45: trend = "DOWNTREND"

        # Tín hiệu
        signal = "WAIT"
        color = "#888"
        
        if smc_zone:
            # Nếu giá đang ở trong vùng FVG -> Tín hiệu cực mạnh
            if smc_zone['bottom'] <= price <= smc_zone['top']:
                if "BULL" in smc_zone['type']: 
                    signal = "SMC BUY ZONE"
                    color = "var(--neon-green)"
                else: 
                    signal = "SMC SELL ZONE"
                    color = "var(--neon-pink)"
            else:
                # Logic thường
                if rsi < 30: signal = "OVERSOLD"; color = "var(--neon-green)"
                elif rsi > 70: signal = "OVERBOUGHT"; color = "var(--neon-pink)"
        else:
             if rsi < 30: signal = "OVERSOLD"; color = "var(--neon-green)"
             elif rsi > 70: signal = "OVERBOUGHT"; color = "var(--neon-pink)"

        return {
            "price": price, "rsi": rsi, "stoch_k": stoch_k, 
            "adx": adx, "poc": poc, "r1": r1, "s1": s1,
            "trend": trend, "signal": signal, "color": color,
            "strength": "STRONG" if adx > 25 else "WEAK",
            "vol_status": "NORMAL",
            "smc": smc_zone # Truyền dữ liệu SMC ra ngoài
        }
    except Exception as e:
        print(f"Logic Err: {e}")
        return None
