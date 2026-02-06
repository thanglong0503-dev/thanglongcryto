import json
import os

# Đường dẫn file lưu trữ (Nó sẽ tự tạo file này nếu chưa có)
DB_FILE = "backend/shark_book_v2.json"

# backend/wallet_manager.py

DEFAULT_SHARKS = [
    {"name": "Justin Sun (Tron Founder)", "address": "0x3DdfA8eC3052539b6C9549F12cEA2C295cfF5296"},
    {"name": "Vitalik Buterin (ETH King)", "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"},
    {"name": "Wintermute (Market Maker)", "address": "0xdbF5E9c5206d0dB70a90108bf936DA60221dC080"},
    {"name": "Donald Trump (Public)", "address": "0x94845333028B1204Fbe14E1278Fd4Adde4660273"},
    {"name": "Shiba Inu Deployer", "address": "0xb8f226dDb7bC672E27dffB67e4ad2ddeC968768e"},
    {"name": "Uniswap Founder (Hayden)", "address": "0x50EC05ADe8280758E2077fcBC08D878D4aef79C3"},
    {"name": "Jump Trading (Quỹ lớn)", "address": "0xf584F8728B874a6a5c7A8d4d387C9aae9172D621"},
    {"name": "a16z (Quỹ đầu tư Mỹ)", "address": "0x05Ff2B0db69458A0750badebc4f9e13aDd608C7F"},
    {"name": "Mach Big Brother (Cá Voi NFT)", "address": "0x020cA66C30beC2c4Fe3861a94E4DB4A498A35872"},
    {"name": "Binance Hot Wallet 6", "address": "0x8894e0a0c962cb723c1976a4421c95949be2d4e3"}
]

def load_book():
    """Đọc danh sách từ file"""
    if not os.path.exists(DB_FILE):
        # Nếu chưa có file thì tạo mới với danh sách mặc định
        save_book(DEFAULT_SHARKS)
        return DEFAULT_SHARKS
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return DEFAULT_SHARKS

def save_book(data):
    """Lưu danh sách vào file"""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_shark(name, address):
    """Thêm cá mập mới"""
    sharks = load_book()
    # Kiểm tra trùng lặp
    for s in sharks:
        if s['address'] == address:
            return False, "⚠️ Ví này đã có trong danh sách rồi!"
    
    sharks.append({"name": name, "address": address})
    save_book(sharks)
    return True, f"✅ Đã thêm '{name}' vào danh sách!"

def delete_shark(address):
    """Xóa cá mập"""
    sharks = load_book()
    new_list = [s for s in sharks if s['address'] != address]
    
    if len(new_list) < len(sharks):
        save_book(new_list)
        return True, "🗑️ Đã xóa thành công!"
    return False, "❌ Không tìm thấy ví để xóa."
