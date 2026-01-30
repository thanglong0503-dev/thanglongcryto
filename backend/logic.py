import pandas as pd
import pandas_ta as ta

def analyze_market(df):
    """
    V41 ENGINE: TREND HUNTER (SWING TRADING)
    Tính toán TP/SL dựa trên ATR và Cấu trúc sóng để ăn dày.
    """
    if df is None or df.empty: return None
    
    # 1. TÍNH TOÁN CHỈ BÁO CƠ BẢN
    df['rsi'] = df.ta.rsi(length=14)
    df['stoch_k'] = df.ta.stoch(k=14, d=3)['STOCHk_14_3_3']
    df['adx'] = df.ta.adx(length=14)['ADX_14']
    
    # 2. TÍNH ATR (ĐỂ ĐO ĐỘ BIẾN ĐỘNG - QUAN TRỌNG CHO SWING)
    # ATR giúp nới rộng SL khi thị trường bão bùng
    df['atr'] = df.ta.atr(length=14)
    
    # 3. XÁC ĐỊNH XU HƯỚNG (EMA 34 & 89 - KHUNG H4/D1 HAY DÙNG)
    df['ema_34'] = df.ta.ema(length=34)
    df['ema_89'] = df.ta.ema(length=89)
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Logic Xu hướng
    if last['ema_34'] > last['ema_89']:
        trend = "UPTREND"
        signal = "BUY"
        color = "#00ff9f" # Xanh
    else:
        trend = "DOWNTREND"
        signal = "SELL"
        color = "#ff0055" # Đỏ

    # 4. TÍNH TOÁN BATTLE PLAN (SWING MODE)
    current_price = last['close']
    atr = last['atr']
    
    # --- CHIẾN THUẬT SĂN SÓNG DÀI ---
    if signal == "BUY":
        # Entry: Mua tại vùng giá hiện tại hoặc chờ hồi nhẹ
        entry_zone_low = current_price - (atr * 0.2)
        entry_zone_high = current_price
        
        # SL: Đặt dưới đáy gần nhất (Swing Low) - 1.5 ATR (Cho thị trường thở)
        # Tìm đáy thấp nhất trong 20 nến gần đây
        swing_low = df['low'].tail(20).min()
        stop_loss = swing_low - (atr * 0.5) 
        
        # Nếu SL quá gần (do nến rụt râu), ép tối thiểu 2 ATR
        if (entry_zone_high - stop_loss) < (atr * 2):
            stop_loss = entry_zone_high - (atr * 2)

        # TP: Tỷ lệ R:R = 1:3 (Lỗ 1 ăn 3)
        risk = entry_zone_high - stop_loss
        take_profit = entry_zone_high + (risk * 3)
        
    else: # SELL
        # Entry: Bán tại vùng hiện tại hoặc chờ hồi lên
        entry_zone_low = current_price
        entry_zone_high = current_price + (atr * 0.2)
        
        # SL: Đặt trên đỉnh gần nhất (Swing High) + 1.5 ATR
        swing_high = df['high'].tail(20).max()
        stop_loss = swing_high + (atr * 0.5)
        
        # Ép tối thiểu 2 ATR
        if (stop_loss - entry_zone_low) < (atr * 2):
            stop_loss = entry_zone_low + (atr * 2)
            
        # TP: R:R = 1:3
        risk = stop_loss - entry_zone_low
        take_profit = entry_zone_low - (risk * 3)

    # 5. TÌM SMC (SMART MONEY CONCEPTS) - FVG
    # Tìm khoảng trống giá gần nhất
    smc = None
    # (Giữ logic cũ hoặc nâng cấp sau, ở đây ta focus vào Swing TP/SL)
    
    # 6. POINT OF CONTROL (POC) - Vùng thanh khoản lớn nhất
    # Ước lượng bằng giá trung bình trọng số Volume
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
        
        # DỮ LIỆU SWING MỚI
        "entry_low": entry_zone_low,
        "entry_high": entry_zone_high,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "risk_reward": "1:3",
        
        "poc": poc,
        "s1": stop_loss, # Tương thích code cũ
        "r1": take_profit, # Tương thích code cũ
        "smc": smc
    }
