# frontend/styles.py

def get_cyberpunk_css():
    return """
    <style>
        /* 1. IMPORT FONTS TƯƠNG LAI */
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;700&family=Share+Tech+Mono&display=swap');

        /* 2. KHAI BÁO BIẾN MÀU (DỄ SỬA) */
        :root {
            --bg-dark: #050505;
            --glass: rgba(10, 10, 10, 0.8);
            --neon-cyan: #00f3ff;
            --neon-pink: #ff00ff;
            --neon-green: #00ff9f;
            --neon-yellow: #fcee0a;
            --border-color: #333;
        }

        /* 3. THIẾT LẬP CƠ BẢN */
        .stApp {
            background-color: var(--bg-dark);
            background-image: 
                linear-gradient(rgba(0, 243, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 243, 255, 0.03) 1px, transparent 1px);
            background-size: 30px 30px; /* Hiệu ứng lưới Grid nền */
            font-family: 'Rajdhani', sans-serif;
            color: #e0e0e0;
        }

        /* 4. HIỆU ỨNG GLITCH CHO HEADER */
        .glitch-header {
            font-family: 'Orbitron', sans-serif;
            font-size: 48px;
            font-weight: 900;
            text-transform: uppercase;
            position: relative;
            text-shadow: 0.05em 0 0 var(--neon-pink), -0.03em -0.04em 0 var(--neon-cyan);
            animation: glitch 725ms infinite;
        }

        @keyframes glitch {
            0% { text-shadow: 0.05em 0 0 var(--neon-pink), -0.03em -0.04em 0 var(--neon-cyan); }
            15% { text-shadow: 0.05em 0 0 var(--neon-pink), -0.03em -0.04em 0 var(--neon-cyan); }
            16% { text-shadow: -0.05em -0.025em 0 var(--neon-pink), 0.025em 0.035em 0 var(--neon-cyan); }
            49% { text-shadow: -0.05em -0.025em 0 var(--neon-pink), 0.025em 0.035em 0 var(--neon-cyan); }
            50% { text-shadow: 0.05em 0.035em 0 var(--neon-pink), 0.03em 0 0 var(--neon-cyan); }
            99% { text-shadow: 0.05em 0.035em 0 var(--neon-pink), 0.03em 0 0 var(--neon-cyan); }
            100% { text-shadow: -0.05em 0 0 var(--neon-pink), -0.025em -0.04em 0 var(--neon-cyan); }
        }

        /* 5. THẺ KÍNH (GLASS CARD) SIÊU CẤP */
        .glass-card {
            background: rgba(15, 20, 25, 0.6);
            border: 1px solid rgba(0, 243, 255, 0.2);
            border-radius: 0px; /* Góc vuông cho nam tính */
            padding: 20px;
            backdrop-filter: blur(12px);
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.8);
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        /* Hiệu ứng viền phát sáng khi rê chuột */
        .glass-card:hover {
            border-color: var(--neon-cyan);
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.2);
            transform: translateY(-2px);
        }

        /* Trang trí góc thẻ (Corner Decorations) */
        .glass-card::before {
            content: ''; position: absolute; top: 0; left: 0;
            width: 10px; height: 10px;
            border-top: 2px solid var(--neon-cyan); border-left: 2px solid var(--neon-cyan);
        }
        .glass-card::after {
            content: ''; position: absolute; bottom: 0; right: 0;
            width: 10px; height: 10px;
            border-bottom: 2px solid var(--neon-cyan); border-right: 2px solid var(--neon-cyan);
        }

        /* 6. METRICS STYLE */
        .metric-label {
            font-family: 'Share Tech Mono', monospace;
            color: var(--neon-cyan);
            font-size: 14px;
            letter-spacing: 2px;
            margin-bottom: 5px;
            opacity: 0.8;
        }
        .metric-value {
            font-family: 'Orbitron', sans-serif;
            font-size: 32px;
            font-weight: 700;
            color: #fff;
            text-shadow: 0 0 10px rgba(255,255,255,0.3);
        }

        /* 7. CUSTOM INPUT (HACKER STYLE) */
        /* Ẩn giao diện mặc định của Streamlit */
        div[data-baseweb="input"] {
            background-color: rgba(0,0,0,0.5) !important;
            border: 1px solid var(--neon-cyan) !important;
            border-radius: 0px !important;
        }
        input[type="text"] {
            color: var(--neon-cyan) !important;
            font-family: 'Share Tech Mono', monospace !important;
            font-size: 18px !important;
        }
        /* Hiệu ứng focus */
        div[data-baseweb="input"]:focus-within {
            box-shadow: 0 0 15px var(--neon-cyan) !important;
            border-color: #fff !important;
        }

        /* 8. THANH TRẠNG THÁI (SYSTEM LOG) */
        .system-log {
            font-family: 'Share Tech Mono', monospace;
            font-size: 12px;
            color: #666;
            border-top: 1px solid #333;
            padding-top: 10px;
            margin-top: 20px;
        }
        .blinking-cursor {
            display: inline-block;
            width: 8px; height: 15px;
            background: var(--neon-green);
            animation: blink 1s infinite;
        }
        @keyframes blink { 50% { opacity: 0; } }
        
        /* 9. SCROLLBAR */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #000; }
        ::-webkit-scrollbar-thumb { background: #333; border: 1px solid #000; }
        ::-webkit-scrollbar-thumb:hover { background: var(--neon-cyan); }
        /* ... (Giữ nguyên các CSS cũ) ... */

        /* CSS CHO SIDEBAR (THANH MENU TRÁI) */
        section[data-testid="stSidebar"] {
            background-color: #000 !important;
            border-right: 1px solid #333;
        }
        
        /* Chỉnh màu chữ trong Sidebar */
        section[data-testid="stSidebar"] .stMarkdown {
            color: #fff !important;
        }
        
        /* Hiệu ứng cho nút Radio (Menu chọn) */
        div[role="radiogroup"] label {
            background: rgba(255,255,255,0.05);
            border: 1px solid #333;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 5px;
            transition: 0.3s;
        }
        div[role="radiogroup"] label:hover {
            border-color: var(--neon-cyan);
            color: var(--neon-cyan) !important;
        }
        div[role="radiogroup"] [data-checked="true"] {
            background: linear-gradient(90deg, rgba(0, 229, 255, 0.2), transparent) !important;
            border-left: 3px solid var(--neon-cyan) !important;
            font-weight: bold;
        }
    </style>
    """
