import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def create_chart(df, symbol):
    """
    V45 ENGINE: WHALE SONAR (VOLUME PROFILE)
    Tích hợp Volume Ngang để nhìn xuyên thấu các vùng cản.
    """
    if df is None: return go.Figure()

    # TẠO LAYOUT CHÍNH (2 Cột Y: Giá bên trái, Volume Profile bên phải)
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05, 
        row_heights=[0.7, 0.3],
        specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
    )

    # 1. BIỂU ĐỒ NẾN
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name="Price",
        increasing_line_color='#00ff9f', 
        decreasing_line_color='#ff0055'
    ), row=1, col=1)

    # 2. CHỈ BÁO EMA & BOLLINGER
    fig.add_trace(go.Scatter(x=df.index, y=df['ema_34'], line=dict(color='#ffff00', width=1), name="EMA 34"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['ema_89'], line=dict(color='#ff00ff', width=1), name="EMA 89"), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df.index, y=df['bb_upper'], line=dict(color='rgba(0, 255, 255, 0.3)', width=1), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['bb_lower'], line=dict(color='rgba(0, 255, 255, 0.3)', width=1), fill='tonexty', fillcolor='rgba(0, 255, 255, 0.05)', showlegend=False), row=1, col=1)

    # 🔥 VOLUME PROFILE (WHALE SONAR)
    price_min = df['low'].min()
    price_max = df['high'].max()
    price_bins = np.linspace(price_min, price_max, 50)
    
    vol_profile = []
    for i in range(len(price_bins)-1):
        mask = (df['close'] >= price_bins[i]) & (df['close'] < price_bins[i+1])
        vol_sum = df.loc[mask, 'volume'].sum()
        vol_profile.append(vol_sum)
    
    fig.add_trace(go.Bar(
        y=price_bins[:-1],
        x=vol_profile,
        orientation='h',
        name="Volume Profile",
        marker=dict(color=vol_profile, colorscale='Jet', opacity=0.3),
        hoverinfo='skip'
    ), row=1, col=1, secondary_y=True)

    # 3. VOLUME DƯỚI ĐÁY
    colors = ['#00ff9f' if c >= o else '#ff0055' for c, o in zip(df['close'], df['open'])]
    fig.add_trace(go.Bar(x=df.index, y=df['volume'], marker_color=colors, name="Volume"), row=2, col=1)

    # 4. TRANG TRÍ
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        height=600,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        xaxis2=dict(showticklabels=False, overlaying='x', side='top') 
    )
    fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(showgrid=False, secondary_y=True, showticklabels=False)
    
    return fig
