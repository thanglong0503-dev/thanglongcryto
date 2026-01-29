def get_cyberpunk_css():
    return """
    <style>
        /* =================================================================================
           1. IMPORT FONTS & VARIABLES (BỘ MÀU NEON CHUẨN)
        ================================================================================= */
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;700&family=Share+Tech+Mono&display=swap');
        
        :root {
            --bg-dark: #050505;
            --glass: rgba(10, 10, 10, 0.9); /* Kính tối màu hơn */
            --neon-cyan: #00f3ff;
            --neon-pink: #ff0055;
            --neon-green: #00ff9f;
            --neon-yellow: #fcee0a;
            --text-main: #e0e0e0;
            --grid-color: rgba(0, 243, 255, 0.07);
        }

        /* =================================================================================
           2. GLOBAL BACKGROUND (LẤY LẠI HIỆU ỨNG LƯỚI 3D CỦA V17)
        ================================================================================= */
        .stApp {
            background-color: var(--bg-dark);
            /* Vẽ lưới Grid background */
            background-image: 
                linear-gradient(var(--grid-color) 1px, transparent 1px),
                linear-gradient(90deg, var(--grid-color) 1px, transparent 1px);
            background-size: 40px 40px;
            font-family: 'Rajdhani', sans-serif;
            color: var(--text-main);
        }

        /* =================================================================================
           3. GLITCH HEADER (LẤY LẠI HIỆU ỨNG GIẬT GIẬT CỦA V17)
        ================================================================================= */
        .glitch-header {
            font-family: 'Orbitron', sans-serif;
            font-size: 48px;
            font-weight: 900;
            color: #fff;
            text-transform: uppercase;
            text-shadow: 2px 2px 0px var(--neon-pink), -2px -2px 0px var(--neon-cyan);
            animation: glitch 1s infinite alternate; /* Kích hoạt Animation */
        }
        
        @keyframes glitch {
            0% { text-shadow: 2px 2px 0px var(--neon-pink), -2px -2px 0px var(--neon-cyan); }
            20% { text-shadow: -2px 2px 0px var(--neon-pink), 2px -2px 0px var(--neon-cyan); }
            40% { text-shadow: 2px -2px 0px var(--neon-pink), -2px 2px 0px var(--neon-cyan); }
            100% { text-shadow: 1px 1px 0px var(--neon-pink), -1px -1px 0px var(--neon-cyan); }
        }

        /* =================================================================================
           4. SIDEBAR FIX (CHỮ TRONG MENU PHẢI SÁNG MÀU)
        ================================================================================= */
        section[data-testid="stSidebar"] {
            background-color: #000000 !important;
            border-right: 1px solid #333;
            box-shadow: 5px 0 15px rgba(0,0,0,0.5);
        }
        /* Ép tất cả chữ trong Sidebar thành màu trắng/xám sáng */
        section[data-testid="stSidebar"] * {
            color: #e0e0e0 !important;
            font-family: 'Rajdhani', sans-serif;
        }
        /* Hiệu ứng khi rê chuột vào nút chọn */
        section[data-testid="stSidebar"] .stRadio label:hover {
            color: var(--neon-cyan) !important;
            text-shadow: 0 0 8px var(--neon-cyan);
            cursor: pointer;
        }

        /* =================================================================================
           5. GLASS CARDS (THẺ KÍNH TRONG SUỐT SIÊU NGẦU)
        ================================================================================= */
        .glass-card {
            background: rgba(15, 20, 25, 0.7); /* Màu nền kính tối */
            border: 1px solid rgba(0, 243, 255, 0.3); /* Viền Cyan mờ */
            border-radius: 0px; /* Góc vuông nam tính */
            padding: 20px;
            backdrop-filter: blur(10px); /* Làm mờ hậu cảnh */
            box-shadow: 0 0 20px rgba(0,0,0,0.8); /* Đổ bóng sâu */
            transition: 0.3s;
            position: relative;
        }
        .glass-card:hover {
            border-color: var(--neon-cyan);
            box-shadow: 0 0 25px rgba(0, 243, 255, 0.2);
            transform: translateY(-2px);
        }
        /* Trang trí 4 góc thẻ (Corner Decorations) */
        .glass-card::before {
            content: ''; position: absolute; top: -1px; left: -1px; width: 10px; height: 10px;
            border-top: 2px solid var(--neon-cyan); border-left: 2px solid var(--neon-cyan);
        }
        .glass-card::after {
            content: ''; position: absolute; bottom: -1px; right: -1px; width: 10px; height: 10px;
            border-bottom: 2px solid var(--neon-cyan); border-right: 2px solid var(--neon-cyan);
        }

        /* =================================================================================
           6. CUSTOM TRADING TABLE (BẢNG ĐIỆN TỬ ĐEN TUYỀN)
        ================================================================================= */
        .trade-row {
            display: flex;
            align-items: center;
            background: rgba(10, 10, 10, 0.8);
            border-bottom: 1px solid #222;
            padding: 12px;
            transition: all 0.2s;
        }
        .trade-row:hover {
            background: rgba(0, 243, 255, 0.08); /* Highlight khi rê chuột */
            border-left: 3px solid var(--neon-cyan);
        }
        
        /* Font chữ số trong bảng */
        .mono-font { font-family: 'Share Tech Mono', monospace; }
        
        /* Nút bấm (Button) phong cách Cyber */
        button {
            border: 1px solid var(--neon-cyan) !important;
            color: var(--neon-cyan) !important;
            background: transparent !important;
            font-family: 'Orbitron' !important;
            border-radius: 0px !important;
            transition: 0.3s !important;
        }
        button:hover {
            background: var(--neon-cyan) !important;
            color: #000 !important;
            box-shadow: 0 0 15px var(--neon-cyan) !important;
        }

        /* =================================================================================
           7. METRICS & TEXT STYLES
        ================================================================================= */
        .metric-label {
            font-family: 'Share Tech Mono';
            color: var(--neon-cyan);
            font-size: 14px;
            letter-spacing: 2px;
            margin-bottom: 5px;
            opacity: 0.8;
        }
        .metric-value {
            font-family: 'Orbitron';
            font-size: 32px;
            font-weight: 700;
            color: #fff;
            text-shadow: 0 0 10px rgba(255,255,255,0.2);
        }
        
        /* Input Field (Ô nhập liệu) */
        div[data-baseweb="input"] {
            background-color: rgba(0,0,0,0.6) !important;
            border: 1px solid #444 !important;
            border-radius: 0px !important;
        }
        input {
            color: var(--neon-green) !important;
            font-family: 'Share Tech Mono' !important;
        }
        
        /* Dialog/Modal (Cửa sổ bật lên) */
        div[data-testid="stDialog"] {
            background-color: rgba(5, 5, 5, 0.95) !important;
            border: 1px solid var(--neon-cyan);
            box-shadow: 0 0 50px rgba(0, 243, 255, 0.2);
        }
    </style>
    """
