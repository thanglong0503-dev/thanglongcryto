import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import plotly.graph_objects as go

def run_ai_forecast(df, periods=12):
    """
    CYBER AI ENGINE V37: Tự động sửa lỗi tên cột thời gian (Fix Yahoo/Binance mismatch)
    """
    try:
        # 1. CHUẨN BỊ DỮ LIỆU
        data = df.copy()
        data = data.reset_index()
        
        # === 🚑 FIX QUAN TRỌNG: TỰ ĐỘNG ĐỔI TÊN CỘT THỜI GIAN ===
        # Dù là 'Date', 'Datetime', 'index' hay gì thì cũng ép về 't' cho thống nhất
        time_col = data.columns[0] # Cột đầu tiên luôn là thời gian sau khi reset_index
        if time_col != 't':
            data.rename(columns={time_col: 't'}, inplace=True)
        # ========================================================

        # Tạo biến trễ (Lag features)
        data['lag_1'] = data['close'].shift(1)
        data['lag_2'] = data['close'].shift(2)
        data['lag_3'] = data['close'].shift(3)
        data['ma_5'] = data['close'].rolling(window=5).mean()
        
        data = data.dropna()
        if len(data) < 30: return None

        # 2. TẠO MODEL
        features = ['lag_1', 'lag_2', 'lag_3', 'ma_5', 'volume']
        X = data[features]
        y = data['close']
        
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # 3. DỰ BÁO TƯƠNG LAI
        future_preds = []
        last_row = data.iloc[-1].copy()
        
        for _ in range(periods):
            input_data = pd.DataFrame([{
                'lag_1': last_row['close'],
                'lag_2': last_row['lag_1'],
                'lag_3': last_row['lag_2'],
                'ma_5': (last_row['close'] + last_row['ma_5']*4)/5,
                'volume': last_row['volume']
            }])
            
            pred = model.predict(input_data)[0]
            future_preds.append(pred)
            
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
        
        return {
            "forecast_df": forecast_df,
            "predicted_price": predicted_price,
            "trend": "BULLISH 🚀" if diff_pct > 0 else "BEARISH 🩸",
            "diff_pct": diff_pct,
            "history": data[['t', 'close']] # Giờ chắc chắn có cột 't'
        }

    except Exception as e:
        print(f"AI Error: {e}")
        return None

def plot_ai_chart(symbol, ai_result):
    """Vẽ biểu đồ AI"""
    if not ai_result: return None
    
    history = ai_result['history'].tail(48)
    forecast = ai_result['forecast_df']
    
    fig = go.Figure()

    # Quá khứ
    fig.add_trace(go.Scatter(
        x=history['t'], y=history['close'],
        mode='lines+markers', name='History',
        line=dict(color='#00f3ff', width=2),
        marker=dict(size=4)
    ))

    # Tương lai
    fig.add_trace(go.Scatter(
        x=forecast['ds'], y=forecast['yhat'],
        mode='lines+markers', name='AI Forecast',
        line=dict(color='#bc13fe', width=3, dash='dot'),
        marker=dict(size=5, symbol='star')
    ))

    # Nối dây
    fig.add_trace(go.Scatter(
        x=[history['t'].iloc[-1], forecast['ds'].iloc[0]],
        y=[history['close'].iloc[-1], forecast['yhat'].iloc[0]],
        mode='lines', showlegend=False,
        line=dict(color='#bc13fe', width=3, dash='dot')
    ))

    fig.update_layout(
        title=dict(text=f"🧠 NEURAL AI: {symbol} NEXT 12H", font=dict(family="Orbitron", size=15, color="#bc13fe")),
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=400, margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", y=1, x=0), hovermode="x unified"
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)')
    
    return fig
