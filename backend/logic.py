import pandas as pd
import pandas_ta as ta

def analyze_market(df):
    """
    V46 FINAL LOGIC: 
    1. Tự tính Bollinger Bands (Fix lỗi KeyError).
    2. Tích hợp chiến thuật Swing + Scalp (V42).
    """
    if df is None or df.empty: return None
    
    # ==============================================================================
    # 1. TÍNH TOÁN CHỈ BÁO (MANUAL FIX CHO BOLLINGER BANDS)
    # ==============================================================================
    
    # --- A. BOLLINGER BANDS (TỰ TÍNH ĐỂ KHÔNG BỊ LỖI TÊN CỘT) ---
    # Đường giữa (Mid) = SMA 20
    df['bb_mid'] = df['close'].rolling(window=20).mean()
    # Độ lệch chuẩn (Std)
    std_dev = df['close'].rolling(window=20).std()
    
    # Đường trên (Upper) và Đường dưới (Lower)
    df['bb_upper'] = df['bb_mid'] + (std_dev * 2)
    df['bb_lower'] = df['bb_mid'] - (std_dev * 2)
    
    # Lấp đầy dữ liệu trống (NaN) ở đầu để vẽ hình không bị đứt đoạn
    df['bb_upper'] = df['bb_upper'].fillna(method='bfill')
    df['bb_lower'] = df['bb_lower'].fillna(method='bfill')
    df['bb_mid'] = df['bb_mid'].fillna(method='bfill')

    # --- B. CÁC CHỈ BÁO KHÁC (DÙNG PANDAS_TA) ---
    # RSI 14
    df['rsi'] = df.ta.rsi(length=14)
    # Stochastic
    stoch = df.ta.stoch(k=14, d=3)
    df['stoch_k'] = stoch['STOCHk_14_3_3'] if stoch is not None else 50
    # ADX (Sức mạnh xu hướng)
    adx = df.ta.adx(length=14)
    df['adx'] = adx['ADX_14'] if adx is not None else 0
    # ATR (Độ biến động - Để tính SL/TP)
    df['atr'] = df.ta.atr(length=14)
    
    # EMA (Xu hướng)
    df['ema_34'] = df.ta.ema(length=34)
    df['ema_89'] = df.ta.ema(length=89)
    
    # Lấy cây nến cuối cùng để phân tích
    last = df.iloc[-1]
    
    # ==============================================================================
    # 2. PHÂN TÍCH XU HƯỚNG & SIGNAL
    # ==============================================================================
    if last['ema_34'] > last['ema_89']:
        trend = "UPTREND"
        signal = "BUY"
        color = "#00ff9f" # Xanh Neon
    else:
        trend = "DOWNTREND"
        signal = "SELL"
        color = "#ff0055" # Đỏ Neon

    # Point of Control (POC) - Ước lượng vùng volume lớn nhất
    poc = (df['close'] * df['volume']).sum() / df['volume'].sum()

    # ==============================================================================
    # 3. TÍNH TOÁN CHIẾN LƯỢC (BATTLE PLAN)
    # ==============================================================================
    current_price = last['close']
    atr = last['atr'] if pd.notna(last['atr']) else (current_price * 0.01) # Fallback nếu ATR lỗi

    # --- A. CHIẾN THUẬT SWING (SĂN SÓNG DÀI - R:R 1:3) ---
    if signal == "BUY":
        swing_entry_low = current_price - (atr * 0.2)
        swing_entry_high = current_price
        
        # Swing SL: Dưới đáy thấp nhất 20 nến - 0.5 ATR
        swing_low = df['low'].tail(20).min()
        swing_sl = swing_low - (atr * 0.5)
        # Ép SL tối thiểu 2 ATR nếu quá gần
        if (swing_entry_high - swing_sl) < (atr * 2): swing_sl = swing_entry_high - (atr * 2)
        
        swing_risk = swing_entry_high - swing_sl
        swing_tp = swing_entry_high + (swing_risk * 3) # Ăn 3
    else: # SELL
        swing_entry_low = current_price
        swing_entry_high = current_price + (atr * 0.2)
        
        # Swing SL: Trên đỉnh cao nhất 20 nến + 0.5 ATR
        swing_high = df['high'].tail(20).max()
        swing_sl = swing_high + (atr * 0.5)
        if (swing_sl - swing_entry_low) < (atr * 2): swing_sl = swing_entry_low + (atr * 2)
        
        swing_risk = swing_sl - swing_entry_low
        swing_tp = swing_entry_low - (swing_risk * 3) # Ăn 3

    # --- B. CHIẾN THUẬT SCALP (ĐÁNH NHANH - R:R 1:1.5) ---
    if signal == "BUY":
        scalp_entry = current_price
        scalp_sl = current_price - (atr * 1.0) # SL ngắn 1 ATR
        scalp_tp = current_price + ((current_price - scalp_sl) * 1.5) # TP 1.5R
    else:
        scalp_entry = current_price
        scalp_sl = current_price + (atr * 1.0)
        scalp_tp = current_price - ((scalp_sl - current_price) * 1.5)

    # ==============================================================================
    # 4. TRẢ VỀ KẾT QUẢ (DICTIONARY)
    # ==============================================================================
    return {
        "price": current_price,
        "signal": signal,
        "trend": trend,
        "color": color,
        "rsi": last['rsi'],
        "stoch_k": last['stoch_k'],
        "strength": "STRONG" if last['adx'] > 25 else "WEAK",
        "vol_status": "WHALE" if last['volume'] > df['volume'].mean()*1.5 else "NORMAL",
        
        # DATA SWING
        "swing_entry_low": swing_entry_low,
        "swing_entry_high": swing_entry_high,
        "swing_sl": swing_sl,
        "swing_tp": swing_tp,
        
        # DATA SCALP
        "scalp_entry": scalp_entry,
        "scalp_sl": scalp_sl,
        "scalp_tp": scalp_tp,
        
        # METRICS & BOLLINGER
        "poc": poc,
        "bb_upper": last['bb_upper'], # Dùng để check debug nếu cần
        
        # Tương thích code cũ
        "risk_reward": "1:3", 
        "s1": swing_sl,
        "r1": swing_tp,
        "smc": None
    }
