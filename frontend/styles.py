def get_css():
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500;700&display=swap');

        :root {
            --bg-color: #050505; 
            --card-bg: rgba(20, 20, 20, 0.7);
            --accent: #00e5ff; 
            --bull: #00ffa3;   
            --bear: #ff0055;   
            --text: #e0e0e0;
            --border: #333;
        }

        .stApp { background-color: var(--bg-color) !important; color: var(--text) !important; font-family: 'Rajdhani', sans-serif !important; }
        
        .cyber-header {
            font-family: 'Orbitron', sans-serif;
            font-size: 36px;
            background: -webkit-linear-gradient(45deg, var(--accent), #bd00ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
            text-shadow: 0 0 20px rgba(0, 229, 255, 0.6);
            letter-spacing: 2px;
        }

        .glass-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 15px;
            backdrop-filter: blur(10px);
            margin-bottom: 15px;
            transition: 0.3s;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        }
        
        .metric-label { font-size: 12px; color: #888; letter-spacing: 2px; text-transform: uppercase; font-family: 'Orbitron'; }
        .metric-val { font-size: 28px; font-weight: bold; font-family: 'Orbitron'; color: #fff; }
        
        div[data-baseweb="input"] { background-color: #111 !important; border: 1px solid #333 !important; }
        input[type="text"] { color: var(--accent) !important; font-family: 'Orbitron' !important; text-transform: uppercase; }
    </style>
    """
