import streamlit.components.v1 as components

def render_chart(symbol, height=900): # <--- Thêm tham số height
    # LOGIC CHỌN NGUỒN BIỂU ĐỒ
    if symbol == 'GC=F': tv_symbol = "TVC:GOLD"
    elif symbol == 'CL=F': tv_symbol = "TVC:USOIL"
    elif symbol == '^GSPC': tv_symbol = "TVC:SPX"
    elif symbol == 'EURUSD=X': tv_symbol = "FX:EURUSD"
    else:
        clean_sym = symbol.replace('/', '').replace('-', '').replace('USD', '')
        tv_symbol = f"BINANCE:{clean_sym}USDT"
    
    html_code = f"""
    <div class="tradingview-widget-container" style="height:100%;width:100%">
      <div id="tv_chart_{symbol}" style="height:{height}px;width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
      "autosize": true,
      "symbol": "{tv_symbol}",
      "interval": "60",
      "timezone": "Asia/Ho_Chi_Minh",
      "theme": "dark",
      "style": "1",
      "locale": "en",
      "toolbar_bg": "#f1f3f6",
      "enable_publishing": false,
      "backgroundColor": "#050505",
      "gridColor": "rgba(0, 243, 255, 0.05)",
      "hide_top_toolbar": { 'true' if height < 500 else 'false' }, /* Ẩn toolbar nếu chart nhỏ */
      "container_id": "tv_chart_{symbol}",
      "studies": [
        "BB@tv-basicstudies",
        "RSI@tv-basicstudies"
      ]
      }});
      </script>
    </div>
    """
    components.html(html_code, height=height + 10)
