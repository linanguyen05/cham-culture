import sqlite3
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Cấp quyền CORS toàn diện giúp Frontend gọi API mượt mà không lo bị chặn sync
CORS(app) 

DB_NAME = "cham_culture.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    return conn

# =========================================================================
# API 1: LẤY THÔNG TIN NGƯỜI DÙNG VỪA ĐĂNG NHẬP / ĐĂNG KÝ
# =========================================================================
@app.route('/api/current-user', methods=['GET'])
def get_current_user():
    try:
        # Tối ưu logic: Nếu hệ thống của m đã có bảng users (người dùng đăng ký),
        # Backend sẽ tự động bốc tài khoản mới nhất vừa được tạo hoặc vừa đăng nhập lên.
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Thử kiểm tra xem bảng dữ liệu người dùng (users) của m đã tồn tại chưa
        cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='table' AND tbl_name='users'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # Nếu có bảng users, bốc ngay người dùng vừa mới tương tác/đăng ký gần nhất
            cursor.execute('SELECT username, avatar FROM users ORDER BY id DESC LIMIT 1')
            user_row = cursor.fetchone()
            if user_row:
                conn.close()
                return jsonify({
                    "success": True,
                    "data": {
                        "name": user_row["username"],
                        "avatar": user_row["avatar"] if user_row["avatar"] else "https://i.pravatar.cc/150?img=47"
                    }
                }), 200

        conn.close()
        # Phương án dự phòng (Fallback): Nếu chưa chạy đăng ký/đăng nhập, trả về tài khoản mặc định định danh để tránh trống UI
        return jsonify({
            "success": True,
            "data": {
                "name": "Lan Nhi",
                "avatar": "https://i.pravatar.cc/150?img=47"
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": "Lỗi xử lý định danh tài khoản!", "error": str(e)}), 500


# =========================================================================
# API 2: LẤY DANH SÁCH BÀI VIẾT FEED (TỐI ƯU TỐC ĐỘ TRUY VẤN)
# =========================================================================
@app.route('/api/posts', methods=['GET'])
def get_posts():
    try:
        tab_name = request.args.get('tab', 'Tổng quan')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if not tab_name or tab_name == 'Tổng quan':
            cursor.execute('SELECT * FROM posts ORDER BY id DESC')
        elif tab_name == 'Được quan tâm':
            cursor.execute('SELECT * FROM posts ORDER BY likes DESC')
        else:
            cursor.execute('SELECT * FROM posts WHERE category = ? COLLATE NOCASE ORDER BY id DESC', (tab_name,))
            
        rows = cursor.fetchall()
        conn.close()
        
        posts_list = []
        for row in rows:
            posts_list.append({
                "id": row["id"],
                "authorName": row["author_name"],
                "authorAvatar": row["author_avatar"],
                "timeText": row["time_text"],
                "category": row["category"],
                "text": row["content"],
                "images": json.loads(row["images"]) if row["images"] else [],
                "likes": row["likes"],
                "comments": row["comments"]
            })
            
        return jsonify({"success": True, "count": len(posts_list), "data": posts_list}), 200
    except Exception as e:
        return jsonify({"success": False, "message": "Lỗi lấy dữ liệu bài viết!", "error": str(e)}), 500


# =========================================================================
# API 3: LƯU BÀI VIẾT MỚI (NHẬN THÔNG TIN ĐỘNG HOÀN TOÀN TỪ USER MỚI)
# =========================================================================
@app.route('/api/posts', methods=['POST'])
def create_post():
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "Dữ liệu trống!"}), 400
            
        author_name = data.get("authorName")
        author_avatar = data.get("authorAvatar")
        category = data.get("category", "Văn hóa Chăm")
        content = data.get("text", "").strip()
        images = json.dumps(data.get("images", [])) 
        
        if not content and not data.get("images"):
            return jsonify({"success": False, "message": "Nội dung bài viết rỗng!"}), 400
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO posts (author_name, author_avatar, time_text, category, content, images, likes, comments)
            VALUES (?, ?, 'Vừa xong', ?, ?, ?, 0, 0)
        ''', (author_name, author_avatar, category, content, images))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Đăng bài thành công!"}), 201
    except Exception as e:
        return jsonify({"success": False, "message": "Lỗi ghi nhận bài viết!", "error": str(e)}), 500


# =========================================================================
# API 4: BẢNG XẾP HẠNG CHỦ ĐỀ SIDEBAR ĐỘNG
# =========================================================================
@app.route('/api/topics-count', methods=['GET'])
def get_topics_count():
    try:
        default_topics = {
            "Hỏi đáp": 42, "Lễ hội Katê": 36, "Văn hóa Chăm": 28,
            "Du lịch – Trải nghiệm": 18, "Ẩm thực Chăm": 15, "Kinh nghiệm": 0
        }
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT category, COUNT(*) as count FROM posts GROUP BY category')
        rows = cursor.fetchall()
        conn.close()
        
        db_counts = {row["category"]: row["count"] for row in rows}
        response_data = []
        for name, base_count in default_topics.items():
            response_data.append({
                "name": name,
                "count": base_count + db_counts.get(name, 0)
            })
            
        response_data.sort(key=lambda x: x["count"], reverse=True)
        return jsonify({"success": True, "data": response_data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# =========================================================================
# API 5: THÀNH VIÊN TÍCH CỰC TOP 1
# =========================================================================
@app.route('/api/active-member', methods=['GET'])
def get_active_member():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT author_name, author_avatar, COUNT(*) as post_count 
            FROM posts 
            GROUP BY author_name, author_avatar
            ORDER BY post_count DESC LIMIT 1
        ''')
        row = cursor.fetchone()
        conn.close()
        
        if row:
            member_data = {"name": row["author_name"], "avatar": row["author_avatar"], "postCount": row["post_count"]}
        else:
            member_data = {"name": "Chưa có dữ liệu", "avatar": "https://i.pravatar.cc/150?img=47", "postCount": 0}
        return jsonify({"success": True, "data": member_data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)