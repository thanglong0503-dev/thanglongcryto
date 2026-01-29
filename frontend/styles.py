def get_cyberpunk_css():
    return """
    <style>
        /* 1. FONTS & COLORS */
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;700&family=Share+Tech+Mono&display=swap');
        
        :root {
            --bg-dark: #050505;
            --neon-cyan: #00f3ff;
            --neon-pink: #ff0055;
            --neon-green: #00ff9f;
            --text-main: #e0e0e0;
        }

        /* 2. GLOBAL RESET (ÉP MÀU ĐEN TOÀN TẬP) */
        .stApp {
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: 'Rajdhani', sans-serif;
        }
        
        /* 3. SIDEBAR FIX (CHỮ BỊ ĐEN -> THÀNH TRẮNG) */
        section[data-testid="stSidebar"] {
            background-color: #000000 !important;
            border-right: 1px solid #333;
        }
        /* Ép màu chữ cho tất cả thành phần trong Sidebar */
        section[data-testid="stSidebar"] * {
            color: #e0e0e0 !important;
        }
        section[data-testid="stSidebar"] .stRadio label:hover {
            color: var(--neon-cyan) !important;
            cursor: pointer;
        }

        /* 4. CUSTOM TRADING ROW (BẢNG ĐIỆN TỬ MỚI) */
        .trade-row {
            display: flex;
            align-items: center;
            background: rgba(20, 20, 20, 0.8);
            border: 1px solid #333;
            margin-bottom: 8px;
            padding: 10px;
            border-radius: 4px;
            transition: all 0.2s;
        }
        .trade-row:hover {
            border-color: var(--neon-cyan);
            background: rgba(0, 243, 255, 0.05);
            transform: translateX(5px);
        }
        .col-asset { font-family: 'Orbitron'; font-weight: bold; font-size: 16px; width: 15%; }
        .col-price { font-family: 'Share Tech Mono'; font-size: 16px; width: 25%; text-align: right; }
        .col-change { font-family: 'Share Tech Mono'; font-size: 16px; width: 25%; text-align: right; }
        .col-trend { font-size: 20px; width: 10%; text-align: center; }
        .col-action { width: 25%; text-align: right; }

        /* 5. GLITCH HEADER & GLASS CARDS (GIỮ NGUYÊN) */
        .glitch-header {
            font-family: 'Orbitron', sans-serif;
            font-size: 40px;
            font-weight: 900;
            color: #fff;
            text-shadow: 2px 2px 0px var(--neon-pink), -2px -2px 0px var(--neon-cyan);
        }
        .glass-card {
            background: rgba(15, 20, 25, 0.6);
            border: 1px solid rgba(0, 243, 255, 0.2);
            padding: 20px;
            box-shadow: 0 0 15px rgba(0,0,0,0.8);
        }
        
        /* 6. MODAL/DIALOG STYLE */
        div[data-testid="stDialog"] {
            background-color: #000 !important;
            border: 1px solid var(--neon-cyan);
        }
    </style>
    """
