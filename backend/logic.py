import pandas as pd
import pandas_ta as ta

# ==============================================================================
# 1. HÀM TÍNH TOÁN LOGIC (ĐÃ FIX LỖI BOLLINGER)
# ==============================================================================
def analyze_market(df):
    """
    Phân tích thị trường: Tính chỉ báo và đưa ra chiến lược Swing/Scalp
    """
    if df is None or df.empty: return None
    
    # --- A. TÍNH BOLLINGER BANDS (THỦ CÔNG - AN TOÀN TUYỆT ĐỐI) ---
    # Tự tính để tránh lỗi KeyError 'bb_upper'
    df['bb_mid'] = df['close'].rolling(window=20).mean()
    std_dev = df['close'].rolling(window=20).std()
    
    df['bb_upper'] = df['bb_mid'] + (std_dev * 2)
    df['bb_lower'] = df['bb_mid'] - (std_dev * 2)
    
    # Lấp đầy dữ liệu trống (NaN)
    df['bb_upper'] = df['bb_upper'].fillna(method='bfill')
    df['bb_lower'] = df['bb_lower'].fillna(method='bfill')
    df['bb_mid'] = df['bb_mid'].fillna(method='bfill')

    # --- B. CÁC CHỈ BÁO KHÁC ---
    df['rsi'] = df.ta.rsi(length=14)
    stoch = df.ta.stoch(k=14, d=3)
    df['stoch_k'] = stoch['STOCHk_14_3_3'] if stoch is not None else 50
    df['adx'] = df.ta.adx(length=14)['ADX_14']
    df['atr'] = df.ta.atr(length=14)
    
    df['ema_34'] = df.ta.ema(length=34)
    df['ema_89'] = df.ta.ema(length=89)
    
    last = df.iloc[-1]
    
    # --- C. XÁC ĐỊNH XU HƯỚNG ---
    if last['ema_34'] > last['ema_89']:
        trend = "UPTREND"
        signal = "BUY"
        color = "#00ff9f"
    else:
        trend = "DOWNTREND"
        signal = "SELL"
        color = "#ff0055"

    poc = (df['close'] * df['volume']).sum() / df['volume'].sum()

    # --- D. TÍNH CHIẾN LƯỢC (BATTLE PLAN) ---
    current_price = last['close']
    atr = last['atr'] if pd.notna(last['atr']) else (current_price * 0.01)

    # SWING (1:3)
    if signal == "BUY":
        swing_entry_low = current_price - (atr * 0.2)
        swing_entry_high = current_price
        swing_sl = swing_entry_high - (atr * 2)
        swing_tp = swing_entry_high + (atr * 6)
    else:
        swing_entry_low = current_price
        swing_entry_high = current_price + (atr * 0.2)
        swing_sl = swing_entry_low + (atr * 2)
        swing_tp = swing_entry_low - (atr * 6)

    # SCALP (1:1.5)
    if signal == "BUY":
        scalp_entry = current_price
        scalp_sl = current_price - (atr * 0.8)
        scalp_tp = current_price + (atr * 1.2)
    else:
        scalp_entry = current_price
        scalp_sl = current_price + (atr * 0.8)
        scalp_tp = current_price - (atr * 1.2)

    return {
        "price": current_price,
        "signal": signal,
        "trend": trend,
        "color": color,
        "rsi": last['rsi'],
        "poc": poc,
        
        # SWING
        "swing_entry_low": swing_entry_low,
        "swing_entry_high": swing_entry_high,
        "swing_sl": swing_sl,
        "swing_tp": swing_tp,
        
        # SCALP
        "scalp_entry": scalp_entry,
        "scalp_sl": scalp_sl,
        "scalp_tp": scalp_tp
    }

# ==============================================================================
# 2. HÀM TẠO GIAO DIỆN HTML (ĐÂY LÀ CÁI ĐANG THIẾU!)
# ==============================================================================
def create_battle_plan_html(plan):
    """
    Tạo mã HTML để hiển thị bảng Battle Plan đẹp mắt
    """
    if not plan: return ""
    
    color = plan['color']
    
    html = f"""
    <div style="border: 1px solid {color}; border-radius: 10px; padding: 15px; background: rgba(0,0,0,0.5); margin-bottom: 20px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; border-bottom:1px solid #333; padding-bottom:5px">
            <span style="color:{color}; font-weight:bold; font-size:16px">🌊 SWING SETUP (DÀI HẠN)</span>
            <span style="background:#333; color:#fff; padding:2px 6px; border-radius:4px; font-size:10px">R:R 1:3</span>
        </div>
        
        <div style="margin-bottom:10px">
            <div style="color:#888; font-size:10px">ENTRY ZONE (LIMIT)</div>
            <div style="color:#fff; font-size:18px; font-weight:bold; font-family:'Orbitron'">
                ${plan['swing_entry_low']:,.2f} - ${plan['swing_entry_high']:,.2f}
            </div>
        </div>
        <div style="display:flex; justify-content:space-between;">
            <div>
                <span style="color:#ff0055; font-size:12px">SL: </span>
                <span style="color:#ff0055; font-weight:bold">${plan['swing_sl']:,.2f}</span>
            </div>
            <div>
                <span style="color:#00ff9f; font-size:12px">TP: </span>
                <span style="color:#00ff9f; font-weight:bold">${plan['swing_tp']:,.2f}</span>
            </div>
        </div>

        <div style="margin: 15px 0; border-top: 1px dashed #444;"></div>

        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <span style="color:#ffcc00; font-weight:bold; font-size:16px">⚡ SCALP SETUP (TRONG NGÀY)</span>
            <span style="background:#333; color:#fff; padding:2px 6px; border-radius:4px; font-size:10px">R:R 1:1.5</span>
        </div>
        
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px">
            <div><div style="color:#888; font-size:10px">ENTRY (MARKET)</div><div style="color:#fff">${plan['scalp_entry']:,.2f}</div></div>
            <div><div style="color:#888; font-size:10px">STOP LOSS</div><div style="color:#ff0055">${plan['scalp_sl']:,.2f}</div></div>
            <div><div style="color:#888; font-size:10px">TAKE PROFIT</div><div style="color:#00ff9f">${plan['scalp_tp']:,.2f}</div></div>
        </div>
    </div>
    """
    return html
