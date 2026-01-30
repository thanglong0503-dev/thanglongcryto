import pandas as pd
import pandas_ta as ta

def analyze_market(df):
    """
    V46 FIX: BỔ SUNG TÍNH TOÁN BOLLINGER BANDS ĐỂ KHÔNG BỊ LỖI VẼ HÌNH
    """
    if df is None or df.empty: return None
    
    # --- 1. TÍNH TOÁN CHỈ BÁO (QUAN TRỌNG: PHẢI CÓ ĐOẠN NÀY) ---
    # Bollinger Bands (20, 2)
    bb = df.ta.bbands(length=20, std=2)
    # Gán vào DataFrame để Plot Engine dùng
    # Lưu ý: pandas_ta trả về tên cột kiểu BBL_20_2.0, BBM_20_2.0, BBU_20_2.0
    # Chúng ta đổi tên cho gọn để plot_engine dễ gọi
    df['bb_upper'] = bb['BBU_20_2.0']
    df['bb_lower'] = bb['BBL_20_2.0']
    df['bb_mid'] = bb['BBM_20_2.0']

    # RSI, Stoch, ADX, ATR (Giữ nguyên code cũ)
    df['rsi'] = df.ta.rsi(length=14)
    df['stoch_k'] = df.ta.stoch(k=14, d=3)['STOCHk_14_3_3']
    df['adx'] = df.ta.adx(length=14)['ADX_14']
    df['atr'] = df.ta.atr(length=14)
    
    # EMA (Giữ nguyên)
    df['ema_34'] = df.ta.ema(length=34)
    df['ema_89'] = df.ta.ema(length=89)
    
    # ... (Phần logic bên dưới giữ nguyên không đổi) ...
    last = df.iloc[-1]
    # ...
    
    # Xác định Xu hướng
    if last['ema_34'] > last['ema_89']:
        trend = "UPTREND"
        signal = "BUY"
        color = "#00ff9f" # Xanh
    else:
        trend = "DOWNTREND"
        signal = "SELL"
        color = "#ff0055" # Đỏ

    current_price = last['close']
    atr = last['atr']

    # ======================================================
    # A. CHIẾN THUẬT SWING (SĂN SÓNG DÀI - R:R 1:3)
    # ======================================================
    if signal == "BUY":
        swing_entry_low = current_price - (atr * 0.2)
        swing_entry_high = current_price
        
        # Swing SL: Dưới đáy cũ - 2 ATR (Rộng rãi)
        swing_low = df['low'].tail(20).min()
        swing_sl = swing_low - (atr * 0.5)
        if (swing_entry_high - swing_sl) < (atr * 2): swing_sl = swing_entry_high - (atr * 2)
        
        swing_risk = swing_entry_high - swing_sl
        swing_tp = swing_entry_high + (swing_risk * 3) # Ăn 3
    else:
        swing_entry_low = current_price
        swing_entry_high = current_price + (atr * 0.2)
        
        # Swing SL: Trên đỉnh cũ + 2 ATR
        swing_high = df['high'].tail(20).max()
        swing_sl = swing_high + (atr * 0.5)
        if (swing_sl - swing_entry_low) < (atr * 2): swing_sl = swing_entry_low + (atr * 2)
        
        swing_risk = swing_sl - swing_entry_low
        swing_tp = swing_entry_low - (swing_risk * 3) # Ăn 3

    # ======================================================
    # B. CHIẾN THUẬT SCALP (ĐÁNH NHANH - R:R 1:1.5)
    # ======================================================
    # Scalp SL: Chỉ 1 ATR (Chặt chẽ)
    # Scalp TP: 1.5 ATR (Nhanh gọn)
    
    if signal == "BUY":
        scalp_entry = current_price
        scalp_sl = current_price - (atr * 1.0) # SL ngắn
        scalp_tp = current_price + ((current_price - scalp_sl) * 1.5) # TP ngắn
    else:
        scalp_entry = current_price
        scalp_sl = current_price + (atr * 1.0) # SL ngắn
        scalp_tp = current_price - ((scalp_sl - current_price) * 1.5) # TP ngắn

    # POC
    poc = (df['close'] * df['volume']).sum() / df['volume'].sum()

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
        
        # DATA SCALP (MỚI)
        "scalp_entry": scalp_entry,
        "scalp_sl": scalp_sl,
        "scalp_tp": scalp_tp,
        
        "poc": poc,
        "s1": swing_sl, # Tương thích
        "r1": swing_tp, # Tương thích
        "smc": None
    }
