def get_cyberpunk_css():
    return """
    <style>
        /* 1. FONTS & RESET */
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;700&family=Share+Tech+Mono&display=swap');
        
        :root {
            --bg-dark: #050505;
            --neon-cyan: #00f3ff;
            --neon-pink: #ff0055;
            --neon-green: #00ff9f;
            --text-main: #e0e0e0;
            --grid-color: rgba(0, 243, 255, 0.05);
        }

        .stApp {
            background-color: var(--bg-dark);
            background-image: 
                linear-gradient(var(--grid-color) 1px, transparent 1px),
                linear-gradient(90deg, var(--grid-color) 1px, transparent 1px);
            background-size: 40px 40px;
            font-family: 'Rajdhani', sans-serif;
            color: var(--text-main);
        }

        /* 2. SIDEBAR FULL BLACK */
        section[data-testid="stSidebar"] {
            background-color: #000000 !important;
            border-right: 1px solid #222;
        }
        section[data-testid="stSidebar"] * {
            color: #e0e0e0 !important;
        }
        
        /* 3. GLITCH HEADER */
        .glitch-header {
            font-family: 'Orbitron', sans-serif;
            font-size: 40px;
            font-weight: 900;
            color: #fff;
            text-transform: uppercase;
            text-shadow: 2px 2px 0px var(--neon-pink), -2px -2px 0px var(--neon-cyan);
        }

        /* 4. GLASS CARDS (KHÔI PHỤC THẺ KÍNH) */
        .glass-card {
            background: rgba(10, 10, 10, 0.85);
            border: 1px solid rgba(0, 243, 255, 0.2);
            padding: 15px;
            margin-bottom: 10px;
            position: relative;
            backdrop-filter: blur(5px);
        }
        .glass-card::before {
            content: ''; position: absolute; top: -1px; left: -1px; width: 8px; height: 8px;
            border-top: 2px solid var(--neon-cyan); border-left: 2px solid var(--neon-cyan);
        }
        
        /* 5. TRADING ROW (BẢNG ĐIỆN TỬ) */
        .trade-row {
            display: flex; align-items: center;
            background: rgba(5, 5, 5, 0.9);
            border-bottom: 1px solid #222;
            padding: 12px; transition: 0.2s;
        }
        .trade-row:hover {
            background: rgba(0, 243, 255, 0.05);
            border-left: 4px solid var(--neon-cyan);
        }
        
        /* 6. POPUP DIALOG FIX */
        div[data-testid="stDialog"] {
            background-color: #050505 !important;
            border: 1px solid var(--neon-cyan);
            box-shadow: 0 0 50px rgba(0,0,0,0.8);
        }
        
        /* Button Style */
        button {
            border: 1px solid #333 !important;
            color: var(--neon-cyan) !important;
            background: #000 !important;
            font-family: 'Orbitron' !important;
            transition: 0.3s !important;
        }
        button:hover {
            border-color: var(--neon-cyan) !important;
            box-shadow: 0 0 10px var(--neon-cyan) !important;
        }
        
        /* Text Styles */
        .metric-label { font-family: 'Share Tech Mono'; color: #888; font-size: 12px; }
        .metric-val { font-family: 'Orbitron'; color: #fff; font-size: 24px; font-weight: bold; }
    </style>
    """
