import feedparser
from textblob import TextBlob
import pandas as pd
from datetime import datetime

# DANH SÁCH NGUỒN TIN (RSS FEEDS)
RSS_URLS = {
    "CoinTelegraph": "https://cointelegraph.com/rss",
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "Investing.com": "https://www.investing.com/rss/news_25.rss" # Tin Crypto
}

def analyze_sentiment(text):
    """
    Dùng AI (TextBlob) để chấm điểm cảm xúc:
    > 0: Tích cực (Tin tốt)
    < 0: Tiêu cực (Tin xấu)
    = 0: Trung lập
    """
    analysis = TextBlob(text)
    score = analysis.sentiment.polarity
    
    if score > 0.1: return "BULLISH 🟢", score, "#00ff9f"
    elif score < -0.1: return "BEARISH 🔴", score, "#ff0055"
    else: return "NEUTRAL ⚪", score, "#888"

def fetch_crypto_news():
    """
    Hàm quét tin tức Real-time
    """
    news_list = []
    
    for source, url in RSS_URLS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]: # Lấy 5 tin mới nhất mỗi nguồn
                # Phân tích tiêu đề
                sentiment, score, color = analyze_sentiment(entry.title)
                
                # Làm sạch thời gian
                published = entry.get("published", datetime.now().strftime("%Y-%m-%d %H:%M"))
                
                news_list.append({
                    "source": source,
                    "title": entry.title,
                    "link": entry.link,
                    "published": published,
                    "sentiment": sentiment,
                    "score": score,
                    "color": color
                })
        except: pass
        
    # Sắp xếp tin mới nhất lên đầu
    df = pd.DataFrame(news_list)
    # Tính điểm tâm lý chung
    if not df.empty:
        avg_score = df['score'].mean()
        if avg_score > 0.05: market_mood = "GREED (THAM LAM) 🤑"
        elif avg_score < -0.05: market_mood = "FEAR (SỢ HÃI) 😱"
        else: market_mood = "NEUTRAL (LƯỠNG LỰ) 😐"
        return df, market_mood, avg_score
    else:
        return pd.DataFrame(), "UNKNOWN", 0
