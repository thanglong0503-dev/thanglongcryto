import pandas as pd
from prophet import Prophet
import plotly.graph_objects as go
import logging

# Tắt log rác của Prophet
logging.getLogger('prophet').setLevel(logging.WARNING)
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)

def run_prophet_forecast(df, periods=12):
    """
    Chạy model Meta Prophet (Bản tối ưu cho dữ liệu ngắn hạn)
    """
    try:
        # 1. CHUẨN BỊ DỮ LIỆU
        # Prophet yêu cầu 2 cột: 'ds' (thời gian) và 'y' (giá trị)
        data = df.reset_index()[['t', 'close']].rename(columns={'t': 'ds', 'close': 'y'})
        
        # --- FIX QUAN TRỌNG 1: XÓA TIMEZONE ---
        # Prophet rất hay lỗi nếu cột thời gian có múi giờ (UTC+7...)
        if data['ds'].dt.tz is not None:
            data['ds'] = data['ds'].dt.tz_localize(None)
            
        # Đảm bảo dữ liệu sạch
        data = data.dropna()
        if len(data) < 30: return None # Không đủ dữ liệu thì thôi

        # 2. CẤU HÌNH MODEL (BẢN LITE)
        # Vì ta chỉ load 200 nến (~8 ngày), nên KHÔNG ĐƯỢC bật weekly_seasonality
        m = Prophet(
            daily_seasonality=True,  # Tìm quy luật trong ngày (ví dụ: sáng tăng chiều giảm)
            weekly_seasonality=False, # <--- TẮT CÁI NÀY ĐỂ TRÁNH LỖI CONVERGE
            yearly_seasonality=False,
            changepoint_prior_scale=0.05, # Độ nhạy
            growth='linear'
        )
        
        # 3. TRAIN (HỌC)
        m.fit(data)
        
        # 4. DỰ BÁO
        future = m.make_future_dataframe(periods=periods, freq='H')
        forecast = m.predict(future)
        
        # 5. KẾT QUẢ
        future_forecast = forecast.tail(periods)
        predicted_price = future_forecast.iloc[-1]['yhat']
        current_price = data.iloc[-1]['y']
        
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
        # In lỗi ra Terminal để debug nếu cần
        print(f"Prophet Error Details: {e}")
        return None

def plot_prophet_chart(symbol, prophet_result):
    """Vẽ biểu đồ Tiên tri (Giữ nguyên giao diện đẹp)"""
    if not prophet_result: return None
    
    fc = prophet_result['forecast_df']
    
    # Chỉ hiển thị 48h quá khứ + 12h tương lai cho gọn
    display_len = 48 + 12 
    fc_cut = fc.tail(display_len)
    
    fig = go.Figure()

    # 1. Đường Dự báo (Tím Neon)
    fig.add_trace(go.Scatter(
        x=fc_cut['ds'], y=fc_cut['yhat'],
        mode='lines',
        name='AI Prediction',
        line=dict(color='#bc13fe', width=3, dash='dot')
    ))

    # 2. Vùng Mây (Khoảng tin cậy)
    fig.add_trace(go.Scatter(
        x=fc_cut['ds'], y=fc_cut['yhat_upper'],
        mode='lines', marker=dict(color="#444"),
        line=dict(width=0), showlegend=False, hoverinfo='skip'
    ))
    fig.add_trace(go.Scatter(
        x=fc_cut['ds'], y=fc_cut['yhat_lower'],
        mode='lines', marker=dict(color="#444"),
        line=dict(width=0), fill='tonexty',
        fillcolor='rgba(188, 19, 254, 0.1)',
        showlegend=False, hoverinfo='skip'
    ))

    # 3. Giá Thực tế (Xanh Cyan)
    # Lấy data thật từ lịch sử model
    history = prophet_result['model'].history
    # Lọc lấy phần trùng với fc_cut để vẽ đè lên chuẩn xác
    mask = history['ds'] >= fc_cut['ds'].min()
    history_cut = history.loc[mask]
    
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
        legend=dict(orientation="h", y=1, x=0, bgcolor='rgba(0,0,0,0)'),
        hovermode="x unified"
    )
    
    # Ẩn lưới thừa
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)')
    
    return fig
