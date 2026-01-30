import pandas as pd
from prophet import Prophet
import plotly.graph_objects as go
import logging

# Tắt log rác
logging.getLogger('prophet').setLevel(logging.WARNING)
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)

def run_ai_forecast(df, periods=6):
    """
    V40 ENGINE: Gộp nến H4 để AI bắt trend tốt hơn + Tăng độ nhạy
    periods = số lượng nến H4 tương lai (VD: 6 nến H4 = 24 giờ)
    """
    try:
        # 1. CHUẨN BỊ DỮ LIỆU
        data = df.copy().reset_index()
        
        # Đổi tên cột chuẩn
        time_col = data.columns[0]
        data.rename(columns={time_col: 'ds', 'close': 'y'}, inplace=True)
        
        # Xóa múi giờ
        if data['ds'].dt.tz is not None:
            data['ds'] = data['ds'].dt.tz_localize(None)

        # === 🔑 KỸ THUẬT GỘP NẾN (RESAMPLING) ===
        # Chuyển từ H1 -> H4 (4 Giờ 1 nến)
        # Giúp AI nhìn được bức tranh tổng thể, đỡ bị nhiễu, vẽ đẹp hơn
        data.set_index('ds', inplace=True)
        df_resampled = data['y'].resample('4H').last().dropna().reset_index()
        
        # Lấy dữ liệu train (Vẫn lấy 300 nến, nhưng giờ là 300 nến H4 = 50 ngày)
        # -> Đủ dài để thấy trend tuần!
        train_data = df_resampled.tail(300).copy()

        # 2. CẤU HÌNH PROPHET (AGGRESSIVE MODE)
        m = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True, # BẬT LẠI ĐƯỢC VÌ DỮ LIỆU ĐÃ ĐỦ DÀI
            yearly_seasonality=False,
            changepoint_prior_scale=0.5, # TĂNG ĐỘ NHẠY (Mặc định 0.05 -> Giờ là 0.5) -> Hết bị đi ngang
            seasonality_mode='multiplicative' # Chế độ nhân (biến động mạnh theo giá)
        )
        m.fit(train_data)
        
        # 3. DỰ BÁO
        future = m.make_future_dataframe(periods=periods, freq='4H') # Dự báo theo khung H4
        forecast = m.predict(future)
        
        # 4. KẾT QUẢ
        future_forecast = forecast.tail(periods)
        predicted_price = future_forecast.iloc[-1]['yhat']
        current_price = train_data.iloc[-1]['y']
        
        diff_pct = ((predicted_price - current_price) / current_price) * 100
        
        return {
            "forecast_df": forecast,
            "original_data": train_data, # Dữ liệu H4
            "predicted_price": predicted_price,
            "trend": "BULLISH 🚀" if diff_pct > 0 else "BEARISH 🩸",
            "diff_pct": diff_pct
        }

    except Exception as e:
        print(f"Prophet Error: {e}")
        return None

def plot_ai_chart(symbol, ai_result):
    """
    VẼ BIỂU ĐỒ BLUE CLOUD (GIỐNG STOCK DASHBOARD)
    """
    if not ai_result: return None
    
    fc = ai_result['forecast_df']
    orig = ai_result['original_data']
    
    # Hiển thị khoảng 20 ngày quá khứ + tương lai
    display_len = 120 + len(fc) - len(orig)
    fc_cut = fc.tail(display_len)
    orig_cut = orig[orig['ds'] >= fc_cut['ds'].min()]

    fig = go.Figure()

    # 1. VÙNG MÂY (UNCERTAINTY) - QUAN TRỌNG ĐỂ NHÌN GIỐNG STOCK APP
    fig.add_trace(go.Scatter(
        x=fc_cut['ds'], y=fc_cut['yhat_upper'],
        mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'
    ))
    fig.add_trace(go.Scatter(
        x=fc_cut['ds'], y=fc_cut['yhat_lower'],
        mode='lines', line=dict(width=0),
        fill='tonexty',
        fillcolor='rgba(0, 180, 255, 0.2)', # Xanh mây
        showlegend=False, hoverinfo='skip'
    ))

    # 2. ĐƯỜNG DỰ BÁO (TREND)
    fig.add_trace(go.Scatter(
        x=fc_cut['ds'], y=fc_cut['yhat'],
        mode='lines', name='AI Trend (H4)',
        line=dict(color='#00b4ff', width=3)
    ))

    # 3. CHẤM TRÒN DỮ LIỆU THỰC
    fig.add_trace(go.Scatter(
        x=orig_cut['ds'], y=orig_cut['y'],
        mode='markers', name='Actual (H4)',
        marker=dict(color='#00ffa3', size=5, line=dict(width=1, color='black'))
    ))

    fig.update_layout(
        title=dict(text=f"🔮 PROPHET H4 VISION: {symbol}", font=dict(family="Orbitron", size=15, color="#00b4ff")),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=500,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", y=1, x=0),
        hovermode="x unified",
        xaxis=dict(type="date")
    )
    fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)', side="right")

    return fig
