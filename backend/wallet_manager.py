import json
import os

# Đường dẫn file lưu trữ (Nó sẽ tự tạo file này nếu chưa có)
DB_FILE = "backend/shark_book.json"

# Danh sách mặc định (Để Ngài không bỡ ngỡ khi mở lần đầu)
DEFAULT_SHARKS = [
    {"name": "Justin Sun (Tron Founder)", "address": "0x3DdfA8eC3052539b6C9549F12cEA2C295cfF5296"},
    {"name": "Binance Hot Wallet 6", "address": "0x8894e0a0c962cb723c1976a4421c95949be2d4e3"},
    {"name": "Vitalik Buterin (ETH Founder)", "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"},
    {"name": "Wintermute (Market Maker)", "address": "0xdbF5E9c5206d0dB70a90108bf936DA60221dC080"}
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
