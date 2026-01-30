import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go

def run_ai_forecast(df, periods=12):
    """
    CYBER AI ENGINE: Dùng Random Forest để dự báo giá.
    """
    try:
        # 1. CHUẨN BỊ DỮ LIỆU (FEATURE ENGINEERING)
        data = df.copy()
        data = data.reset_index()
        
        # Tạo biến để AI học (Lag features)
        # Học giá của 3 giờ trước đó
        data['lag_1'] = data['close'].shift(1)
        data['lag_2'] = data['close'].shift(2)
        data['lag_3'] = data['close'].shift(3)
        
        # Thêm chỉ báo kỹ thuật vào để AI thông minh hơn
        # (Nếu df đã có RSI/SMA từ logic.py thì dùng, ko thì tính tạm)
        data['ma_5'] = data['close'].rolling(window=5).mean()
        
        # Xóa dòng thiếu dữ liệu (do shift)
        data = data.dropna()
        
        if len(data) < 30: return None

        # 2. TẠO MODEL
        # X = Dữ liệu đầu vào (Quá khứ), y = Kết quả (Hiện tại)
        features = ['lag_1', 'lag_2', 'lag_3', 'ma_5', 'volume']
        X = data[features]
        y = data['close']
        
        # Dùng Random Forest (Rừng ngẫu nhiên) - Nhẹ và mạnh
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # 3. DỰ BÁO TƯƠNG LAI (RECURSIVE FORECAST)
        # Vì ta cần dự báo 12h tới, ta phải dự báo từng bước một
        future_preds = []
        last_row = data.iloc[-1].copy()
        
        for _ in range(periods):
            # Tạo input cho bước tiếp theo từ kết quả vừa dự đoán
            input_data = pd.DataFrame([{
                'lag_1': last_row['close'],
                'lag_2': last_row['lag_1'],
                'lag_3': last_row['lag_2'],
                'ma_5': (last_row['close'] + last_row['ma_5']*4)/5, # Ước lượng MA
                'volume': last_row['volume'] # Giả định vol giữ nguyên
            }])
            
            pred = model.predict(input_data)[0]
            future_preds.append(pred)
            
            # Cập nhật last_row để dự báo bước kế tiếp
            last_row['lag_3'] = last_row['lag_2']
            last_row['lag_2'] = last_row['lag_1']
            last_row['lag_1'] = pred
            last_row['close'] = pred
            
        # 4. ĐÓNG GÓI KẾT QUẢ
        last_date = data['t'].iloc[-1]
        future_dates = [last_date + pd.Timedelta(hours=i+1) for i in range(periods)]
        
        forecast_df = pd.DataFrame({
            'ds': future_dates,
            'yhat': future_preds
        })
        
        current_price = data.iloc[-1]['close']
        predicted_price = future_preds[-1]
        
        diff_pct = ((predicted_price - current_price) / current_price) * 100
        trend = "BULLISH 🚀" if diff_pct > 0 else "BEARISH 🩸"
        
        return {
            "forecast_df": forecast_df,
            "predicted_price": predicted_price,
            "trend": trend,
            "diff_pct": diff_pct,
            "history": data[['t', 'close']] # Để vẽ biểu đồ
        }

    except Exception as e:
        print(f"AI Error: {e}")
        return None

def plot_ai_chart(symbol, ai_result):
    """Vẽ biểu đồ AI (Cyberpunk Style)"""
    if not ai_result: return None
    
    history = ai_result['history'].tail(48) # Lấy 48h quá khứ
    forecast = ai_result['forecast_df']
    
    fig = go.Figure()

    # 1. Quá khứ (Xanh Neon)
    fig.add_trace(go.Scatter(
        x=history['t'], y=history['close'],
        mode='lines+markers', name='History',
        line=dict(color='#00f3ff', width=2),
        marker=dict(size=4)
    ))

    # 2. Tương lai (Tím Neon - Nét đứt)
    fig.add_trace(go.Scatter(
        x=forecast['ds'], y=forecast['yhat'],
        mode='lines+markers', name='AI Forecast',
        line=dict(color='#bc13fe', width=3, dash='dot'),
        marker=dict(size=5, symbol='star')
    ))

    # Nối điểm cuối quá khứ với điểm đầu tương lai cho liền mạch
    fig.add_trace(go.Scatter(
        x=[history['t'].iloc[-1], forecast['ds'].iloc[0]],
        y=[history['close'].iloc[-1], forecast['yhat'].iloc[0]],
        mode='lines', showlegend=False,
        line=dict(color='#bc13fe', width=3, dash='dot')
    ))

    fig.update_layout(
        title=dict(
            text=f"🧠 NEURAL AI: {symbol} NEXT 12H",
            font=dict(family="Orbitron", size=15, color="#bc13fe")
        ),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", y=1, x=0),
        hovermode="x unified"
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)')
    
    return fig
