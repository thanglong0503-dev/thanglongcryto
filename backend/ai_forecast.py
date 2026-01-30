import pandas as pd
from prophet import Prophet
import plotly.graph_objects as go
from datetime import datetime, timedelta

def prophet_forecast(df, days_ahead):
    """
    V46 AI ENGINE: DỰ BÁO TƯƠNG LAI BẰNG PROPHET
    Hàm này tên là 'prophet_forecast' để khớp với app.py
    """
    if df is None or len(df) < 50:
        return go.Figure(), "⚠️ NOT ENOUGH DATA FOR AI PREDICTION"

    # 1. CHUẨN BỊ DỮ LIỆU CHO PROPHET (Cần cột 'ds' và 'y')
    # Resample về H4 (4 giờ) để giảm nhiễu và dự báo mượt hơn
    data = df.resample('4h').agg({'open':'first', 'high':'max', 'low':'min', 'close':'last'}).dropna()
    
    # Reset index để lấy cột thời gian
    prophet_df = data.reset_index()[['t', 'close']]
    prophet_df.columns = ['ds', 'y'] # Prophet bắt buộc phải đặt tên cột là 'ds' và 'y'
    
    # Xóa múi giờ (timezone) nếu có để tránh lỗi Prophet
    prophet_df['ds'] = prophet_df['ds'].dt.tz_localize(None)

    # 2. TRAINING MODEL
    # Changepoint prior scale: Độ nhạy với biến động (0.05 - 0.5)
    m = Prophet(daily_seasonality=True, yearly_seasonality=False, changepoint_prior_scale=0.1)
    m.fit(prophet_df)

    # 3. DỰ BÁO (FUTURE)
    # days_ahead là số ngày (vd: 1, 3, 7). Đổi ra số nến H4 (1 ngày = 6 nến H4)
    periods = days_ahead * 6 
    future = m.make_future_dataframe(periods=periods, freq='4h')
    forecast = m.predict(future)

    # 4. TÍNH TOÁN KẾT QUẢ
    current_price = df['close'].iloc[-1]
    predicted_price = forecast['yhat'].iloc[-1]
    diff = predicted_price - current_price
    diff_pct = (diff / current_price) * 100
    
    if diff_pct > 0:
        trend = "BULLISH 🚀"
        color = "#00ff9f"
    else:
        trend = "BEARISH 🩸"
        color = "#ff0055"

    text_result = f"""
    ### 🔮 AI PREDICTION ({days_ahead} DAYS)
    - **Current Price:** ${current_price:,.2f}
    - **Target Price:** ${predicted_price:,.2f}
    - **Trend:** {trend} ({diff_pct:+.2f}%)
    """

    # 5. VẼ BIỂU ĐỒ (VISUALIZATION)
    fig = go.Figure()

    # A. Dữ liệu thực tế (Đường màu xám)
    fig.add_trace(go.Scatter(
        x=prophet_df['ds'], y=prophet_df['y'],
        mode='lines', name='Actual Price',
        line=dict(color='rgba(255, 255, 255, 0.3)', width=1)
    ))

    # B. Dữ liệu dự báo (Đường màu Cyan sáng)
    # Chỉ lấy phần dự báo tương lai
    future_forecast = forecast.tail(periods)
    
    fig.add_trace(go.Scatter(
        x=future_forecast['ds'], y=future_forecast['yhat'],
        mode='lines+markers', name='AI Prediction',
        line=dict(color='#00b4ff', width=2),
        marker=dict(size=3, color='#00b4ff')
    ))

    # C. Dải tin cậy (Confidence Interval - Vùng mờ bao quanh)
    fig.add_trace(go.Scatter(
        x=pd.concat([future_forecast['ds'], future_forecast['ds'][::-1]]),
        y=pd.concat([future_forecast['yhat_upper'], future_forecast['yhat_lower'][::-1]]),
        fill='toself',
        fillcolor='rgba(0, 180, 255, 0.1)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        showlegend=False
    ))

    # D. Trang trí
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
        height=400,
        margin=dict(l=10, r=10, t=30, b=10),
        title=dict(text=f"PROPHET VISION: {trend}", font=dict(color=color)),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    )

    return fig, text_result
