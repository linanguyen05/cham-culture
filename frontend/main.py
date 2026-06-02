import bcrypt
import json
import os
from datetime import datetime, timezone

def hash_password(plain_password: str) -> str:
    """Trả về bcrypt hash dạng string"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def save_user_to_json(email, password, filename='data.json'):
    # 1. Đảm bảo file tồn tại với cấu trúc hợp lệ
    if not os.path.exists(filename):
        initial_data = {"users": []}
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=4)
    
    # 2. Đọc dữ liệu hiện tại
    with open(filename, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {"users": []}
    
    # 3. Kiểm tra email đã tồn tại chưa
    if any(user['email'] == email for user in data['users']):
        print(f"Email {email} đã tồn tại, bỏ qua.")
        return
    
    # 4. Tạo ID mới
    next_id = max((user['id'] for user in data['users']), default=0) + 1
    
    # 5. Hash mật khẩu trước khi lưu
    hashed_pw = hash_password(password)
    
    # 6. Tạo user mới
    new_user = {
        "id": next_id,
        "email": email,
        "password": hashed_pw,
        "createdAt": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }
    
    # 7. Ghi vào file
    data['users'].append(new_user)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    print(f"Đã lưu user {email} thành công với ID: {next_id} (password đã hash)")

if __name__ == "__main__":
    email_input = input("Nhập email: ").strip()
    pass_input = input("Nhập password: ").strip()
    save_user_to_json(email_input, pass_input)