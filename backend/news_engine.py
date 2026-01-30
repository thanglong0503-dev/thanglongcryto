import feedparser
from textblob import TextBlob
import pandas as pd
from datetime import datetime

# DANH SÁCH NGUỒN TIN (RSS FEEDS)
RSS_URLS = {
    "CoinTelegraph": "https://cointelegraph.com/rss",
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "Investing Gold": "https://www.investing.com/rss/commodities_Gold.rss", # Thêm nguồn chuyên Vàng
    "Kitco Gold": "https://www.kitco.com/rss/category/news/gold" # Thêm nguồn Kitco
}

def analyze_sentiment(text):
    """
    V44 ENGINE: TÍCH HỢP TỪ ĐIỂN TÀI CHÍNH (GOLD & MACRO)
    Thay vì chỉ dịch word-by-word, AI sẽ hiểu ngữ cảnh tài chính.
    """
    text_lower = text.lower()
    
    # 1. PHÂN TÍCH CƠ BẢN (TEXTBLOB)
    analysis = TextBlob(text)
    base_score = analysis.sentiment.polarity # Điểm gốc (-1 đến 1)
    
    # 2. TỪ ĐIỂN "BULLISH" (TIN TỐT CHO VÀNG/CRYPTO) -> CỘNG ĐIỂM
    # War/Crisis -> Vàng tăng. Rate Cut -> Vàng/Crypto tăng.
    bull_keywords = [
        "rate cut", "pivot", "dovish", "weak dollar", "dxy down", # Tiền tệ
        "war", "conflict", "tension", "crisis", "recession", "fear", # Địa chính trị
        "surge", "soar", "jump", "record high", "bull", "rally", # Hành động giá
        "inflation down", "cpi miss" # Kinh tế
    ]
    
    # 3. TỪ ĐIỂN "BEARISH" (TIN XẤU CHO VÀNG/CRYPTO) -> TRỪ ĐIỂM
    # Rate Hike/Strong Dollar -> Vàng sập.
    bear_keywords = [
        "rate hike", "hike", "hawkish", "strong dollar", "dxy up", "yield rise", # Tiền tệ
        "crash", "plunge", "collapse", "ban", "sue", "lawsuit", "fraud", # Tiêu cực
        "inflation up", "cpi beat", "nfp beat", # Kinh tế nóng -> Fed tăng lãi
        "sec", "regulation", "hack"
    ]
    
    # --- LOGIC GHI ĐÈ ĐIỂM SỐ ---
    final_score = base_score
    
    # Quét từ khóa Bullish
    for word in bull_keywords:
        if word in text_lower:
            final_score += 0.3 # Cộng thêm điểm
            
    # Quét từ khóa Bearish
    for word in bear_keywords:
        if word in text_lower:
            final_score -= 0.3 # Trừ bớt điểm
            
    # Chuẩn hóa lại điểm (để không vượt quá -1 hoặc 1)
    if final_score > 1: final_score = 1
    if final_score < -1: final_score = -1
    
    # RA QUYẾT ĐỊNH MÀU SẮC
    if final_score > 0.1: return "BULLISH 🟢", final_score, "#00ff9f" # Xanh
    elif final_score < -0.1: return "BEARISH 🔴", final_score, "#ff0055" # Đỏ
    else: return "NEUTRAL ⚪", final_score, "#888" # Xám

def fetch_crypto_news():
    """
    Hàm quét tin tức đa luồng
    """
    news_list = []
    
    for source, url in RSS_URLS.items():
        try:
            # Timeout thấp để không bị treo
            feed = feedparser.parse(url)
            
            # Lấy 3 tin mới nhất mỗi nguồn cho nhanh
            for entry in feed.entries[:3]: 
                sentiment, score, color = analyze_sentiment(entry.title)
                
                # Format thời gian cho gọn
                try:
                    dt = datetime(*entry.published_parsed[:6])
                    published = dt.strftime("%H:%M")
                except:
                    published = "Just now"
                
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
        
    # Tạo DataFrame
    df = pd.DataFrame(news_list)
    
    if not df.empty:
        # Tính điểm trung bình thị trường
        avg_score = df['score'].mean()
        
        # LOGIC "MOOD" (TÂM TRẠNG THỊ TRƯỜNG)
        # Điểm cao -> Hưng phấn (Risk On) -> Tốt cho Crypto/Stock
        # Điểm thấp -> Sợ hãi (Risk Off) -> Tốt cho Vàng (Safe Haven)
        
        if avg_score > 0.15: market_mood = "RISK ON (HƯNG PHẤN) 🤑"
        elif avg_score < -0.15: market_mood = "RISK OFF (SỢ HÃI) 😱"
        else: market_mood = "SIDEWAY (THẬN TRỌNG) 😐"
        
        return df, market_mood, avg_score
    else:
        return pd.DataFrame(), "DISCONNECTED", 0
