import pandas as pd
from prophet import Prophet
import plotly.graph_objects as go

def run_prophet_forecast(df, periods=12):
    """
    Chạy model Meta Prophet để dự báo `periods` giờ tiếp theo.
    """
    try:
        # 1. Chuẩn bị dữ liệu cho Prophet (Yêu cầu cột 'ds' và 'y')
        # df đang có index là datetime, ta reset index
        data = df.reset_index()[['t', 'close']].rename(columns={'t': 'ds', 'close': 'y'})
        
        # 2. Cấu hình Model (Tối ưu cho Crypto H1)
        # Crypto chạy 24/7 nên không có 'weekly' nghỉ cuối tuần, nhưng ta vẫn bật để xem xu hướng tuần
        m = Prophet(
            daily_seasonality=True,  # Tìm quy luật trong ngày (ví dụ: phiên Á/Âu/Mỹ)
            yearly_seasonality=False, 
            weekly_seasonality=True,
            changepoint_prior_scale=0.05 # Độ nhạy với sự thay đổi xu hướng
        )
        
        # 3. Train Model (Học từ quá khứ)
        m.fit(data)
        
        # 4. Dự báo tương lai
        future = m.make_future_dataframe(periods=periods, freq='H') # Dự báo thêm `periods` giờ
        forecast = m.predict(future)
        
        # 5. Lấy kết quả
        # Lấy phần dự báo tương lai
        future_forecast = forecast.tail(periods)
        
        # Giá dự báo cuối cùng
        predicted_price = future_forecast.iloc[-1]['yhat']
        current_price = data.iloc[-1]['y']
        
        # Xu hướng dự báo
        trend = "BULLISH 🚀" if predicted_price > current_price else "BEARISH 🩸"
        diff_pct = ((predicted_price - current_price) / current_price) * 100
        
        return {
            "forecast_df": forecast,
            "predicted_price": predicted_price,
            "trend": trend,
            "diff_pct": diff_pct,
            "model": m
        }
    except Exception as e:
        print(f"Prophet Error: {e}")
        return None

def plot_prophet_chart(symbol, prophet_result):
    """Vẽ biểu đồ dự báo đẹp kiểu Cyberpunk"""
    if not prophet_result: return None
    
    fc = prophet_result['forecast_df']
    
    # Chia làm 2 phần: Quá khứ (Actual) và Tương lai (Forecast)
    # Cắt bớt quá khứ cho đỡ dài, chỉ lấy 48h gần nhất + tương lai
    display_len = 48 + 12 
    fc_cut = fc.tail(display_len)
    
    fig = go.Figure()

    # 1. Đường dự báo (Màu Tím Neon - Đặc trưng AI)
    fig.add_trace(go.Scatter(
        x=fc_cut['ds'], y=fc_cut['yhat'],
        mode='lines',
        name='AI Prediction',
        line=dict(color='#bc13fe', width=3, dash='dot') # Tím, nét đứt
    ))

    # 2. Vùng mây dao động (Uncertainty Interval) - Vùng bóng mờ
    fig.add_trace(go.Scatter(
        x=fc_cut['ds'], y=fc_cut['yhat_upper'],
        mode='lines', marker=dict(color="#444"),
        line=dict(width=0), showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=fc_cut['ds'], y=fc_cut['yhat_lower'],
        mode='lines', marker=dict(color="#444"),
        line=dict(width=0), fill='tonexty',
        fillcolor='rgba(188, 19, 254, 0.1)', # Màu tím nhạt
        showlegend=False
    ))

    # 3. Giá thực tế (Dữ liệu thật) - Chỉ vẽ đến hiện tại
    # Lấy dữ liệu thật từ prophet_result (trong model history)
    history = prophet_result['model'].history
    history_cut = history.tail(48)
    
    fig.add_trace(go.Scatter(
        x=history_cut['ds'], y=history_cut['y'],
        mode='lines+markers',
        name='Actual Price',
        line=dict(color='#00f3ff', width=2),
        marker=dict(size=4)
    ))

    # Trang trí
    fig.update_layout(
        title=dict(
            text=f"🔮 META PROPHET: {symbol} NEXT 12H FORECAST",
            font=dict(family="Orbitron", size=15, color="#bc13fe")
        ),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", y=1, x=0, bgcolor='rgba(0,0,0,0)')
    )
    
    return fig
