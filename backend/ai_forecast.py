import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import plotly.graph_objects as go

def run_ai_forecast(df, periods=12):
    """
    CYBER AI ENGINE V38: Hỗ trợ dự báo dài hạn (Long-term)
    """
    try:
        # 1. CHUẨN BỊ DỮ LIỆU
        data = df.copy()
        data = data.reset_index()
        
        # Fix tên cột thời gian (như bản V37)
        time_col = data.columns[0]
        if time_col != 't':
            data.rename(columns={time_col: 't'}, inplace=True)

        # Feature Engineering
        data['lag_1'] = data['close'].shift(1)
        data['lag_2'] = data['close'].shift(2)
        data['lag_3'] = data['close'].shift(3)
        data['ma_5'] = data['close'].rolling(window=5).mean()
        data['ma_20'] = data['close'].rolling(window=20).mean() # Thêm MA20 cho dài hạn
        
        data = data.dropna()
        if len(data) < 30: return None

        # 2. TRAIN MODEL
        features = ['lag_1', 'lag_2', 'lag_3', 'ma_5', 'ma_20', 'volume']
        X = data[features]
        y = data['close']
        
        # Tăng số cây (estimators) lên 200 để học kỹ hơn cho đường dài
        model = RandomForestRegressor(n_estimators=200, random_state=42)
        model.fit(X, y)
        
        # 3. DỰ BÁO TƯƠNG LAI (Vòng lặp)
        future_preds = []
        last_row = data.iloc[-1].copy()
        
        # Nếu forecast quá dài (>100), ta giảm độ phức tạp tính toán MA
        for _ in range(periods):
            input_data = pd.DataFrame([{
                'lag_1': last_row['close'],
                'lag_2': last_row['lag_1'],
                'lag_3': last_row['lag_2'],
                'ma_5': (last_row['close'] + last_row['ma_5']*4)/5,
                'ma_20': (last_row['close'] + last_row['ma_20']*19)/20,
                'volume': last_row['volume']
            }])
            
            pred = model.predict(input_data)[0]
            future_preds.append(pred)
            
            # Cập nhật biến trễ
            last_row['lag_3'] = last_row['lag_2']
            last_row['lag_2'] = last_row['lag_1']
            last_row['lag_1'] = pred
            last_row['close'] = pred
            
        # 4. KẾT QUẢ
        last_date = data['t'].iloc[-1]
        future_dates = [last_date + pd.Timedelta(hours=i+1) for i in range(periods)]
        
        forecast_df = pd.DataFrame({
            'ds': future_dates,
            'yhat': future_preds
        })
        
        current_price = data.iloc[-1]['close']
        predicted_price = future_preds[-1]
        diff_pct = ((predicted_price - current_price) / current_price) * 100
        
        return {
            "forecast_df": forecast_df,
            "predicted_price": predicted_price,
            "trend": "BULLISH 🚀" if diff_pct > 0 else "BEARISH 🩸",
            "diff_pct": diff_pct,
            "history": data[['t', 'close']]
        }

    except Exception as e:
        print(f"AI Error: {e}")
        return None

def plot_ai_chart(symbol, ai_result):
    """
    V38: INTERACTIVE CHART (ZOOMABLE)
    """
    if not ai_result: return None
    
    # Lấy nhiều dữ liệu quá khứ hơn để nhìn cho cân đối với tương lai 30 ngày
    history = ai_result['history'].tail(200) 
    forecast = ai_result['forecast_df']
    
    fig = go.Figure()

    # 1. Quá khứ
    fig.add_trace(go.Scatter(
        x=history['t'], y=history['close'],
        mode='lines', name='History',
        line=dict(color='#00f3ff', width=2)
    ))

    # 2. Tương lai
    fig.add_trace(go.Scatter(
        x=forecast['ds'], y=forecast['yhat'],
        mode='lines', name='AI Forecast',
        line=dict(color='#bc13fe', width=2, dash='dot')
    ))

    # Nối dây
    fig.add_trace(go.Scatter(
        x=[history['t'].iloc[-1], forecast['ds'].iloc[0]],
        y=[history['close'].iloc[-1], forecast['yhat'].iloc[0]],
        mode='lines', showlegend=False,
        line=dict(color='#bc13fe', width=2, dash='dot')
    ))

    # --- CẤU HÌNH TƯƠNG TÁC (QUAN TRỌNG) ---
    fig.update_layout(
        title=dict(text=f"🧠 AI VISION: {symbol}", font=dict(family="Orbitron", size=15, color="#bc13fe")),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=500, # Cao hơn chút để dễ nhìn
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", y=1, x=0),
        hovermode="x unified",
        
        # Bật tính năng Zoom/Pan bằng chuột
        dragmode='pan', 
        
        # Thanh trượt thời gian bên dưới
        xaxis=dict(
            rangeslider=dict(visible=True, thickness=0.1),
            type="date"
        )
    )
    
    # Ẩn lưới thừa nhưng giữ trục giá
    fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)', side="right") # Giá bên phải cho giống TradingView
    
    return fig
