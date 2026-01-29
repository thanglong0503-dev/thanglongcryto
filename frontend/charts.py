import streamlit.components.v1 as components

def render_chart(symbol):
    # Mapping Symbol cho TradingView
    # Lưu ý: Volume Profile Visible Range (VPVR) là tính năng cao cấp của TradingView
    # Nhưng ta có thể dùng phiên bản Basic là "VbP" (Volume by Price)
    
    tv_symbol = f"BINANCE:{symbol}USDT"
    
    html_code = f"""
    <div class="tradingview-widget-container" style="height:900px;width:100%">
      <div id="tv_chart" style="height:100%;width:100%"></div>
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
      "hide_top_toolbar": false,
      "container_id": "tv_chart",
      "studies": [
        "BB@tv-basicstudies",     // Bollinger Bands
        "RSI@tv-basicstudies",    // RSI
        "VbPFixed@tv-basicstudies" // <--- VOLUME PROFILE (Phiên bản miễn phí)
      ],
      "studies_overrides": {{
        "volume.volume.color.0": "#ff0055",
        "volume.volume.color.1": "#00ffa3"
      }}
      }});
      </script>
    </div>
    """
    components.html(html_code, height=910)
