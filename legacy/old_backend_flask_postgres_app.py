import psycopg2
import psycopg2.extras
import json
import os
import traceback
from flask import Flask, render_template, request, jsonify, session, redirect
from database import db
from models import User
from chatbot_engine import get_answer_from_db
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

# ==========================
# Khởi tạo Flask
# ==========================
app = Flask(__name__)

app.secret_key = "chamculture2026"

# Cấu hình SQLAlchemy kết nối tới Supabase (PostgreSQL) thay vì SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SUPABASE_DB_URL", "postgresql://user:password@db.supabase.co:5432/postgres")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_PERMANENT"] = False
db.init_app(app)

with app.app_context():
    print("DB URL:", db.engine.url)
    db.create_all()

# ==========================
# TẠO DATABASE CỘNG ĐỒNG (SUPABASE)
# ==========================
# Các table đã được thiết kế sẵn trên Supabase theo cấu trúc mới:
# users, posts, comments, post_likes
# Do đó, hàm create_community_table có thể được cấu hình để kiểm tra hoặc tạo table nếu chưa có, 
# nhưng thực tế Supabase đã quản lý, hàm này sẽ đảm bảo cấu trúc.
def create_community_table():
    conn = get_community_db()
    cursor = conn.cursor()

    # Table users (được SQLAlchemy quản lý nhưng khai báo ở đây để đồng bộ nếu cần)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        username VARCHAR(255) UNIQUE,
        email VARCHAR(255) UNIQUE,
        password VARCHAR(255),
        avatar_url TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts(
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        content TEXT,
        image_url TEXT,
        user_id INTEGER REFERENCES users(id),
        category VARCHAR(255),
        shared_post_id INTEGER REFERENCES posts(id) NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments(
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        content TEXT,
        user_id INTEGER REFERENCES users(id),
        post_id INTEGER REFERENCES posts(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS post_likes(
        post_id INTEGER REFERENCES posts(id),
        user_id INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (post_id, user_id)
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ SUPABASE (POSTGRESQL) COMMUNITY DATABASE READY")

# Hàm kết nối Supabase Postgres cho các raw queries
def get_community_db():
    DATABASE_URL = os.environ.get("SUPABASE_DB_URL", "postgresql://user:password@db.supabase.co:5432/postgres")
    conn = psycopg2.connect(DATABASE_URL)
    # Trả về DictCursor để truy xuất qua tên cột tương tự sqlite3.Row
    conn.cursor_factory = psycopg2.extras.DictCursor 
    return conn

@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "user_id" not in session:
        return redirect("/login")
    user = User.query.get(session["user_id"])
    if request.method == "POST":
        old_password = request.form["old_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if old_password != user.password:
            return render_template("change_password.html", error="Mật khẩu cũ không đúng!")
        if new_password != confirm_password:
            return render_template("change_password.html", error="Mật khẩu xác nhận không khớp!")

        user.password = new_password
        db.session.commit()
        return redirect("/profile")
    return render_template("change_password.html")

# ==========================
# Đăng nhập đăng ký
# ==========================
@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/index")
    return render_template("login.html")

# ==========================
# Trang chủ
# ==========================
@app.route("/index")
def index():
    if "user_id" not in session:
        return redirect("/")
    return render_template("index.html")

# ==========================
# Các trang tĩnh
# ==========================
@app.route("/learn")
def learn():
    if "user_id" not in session: return redirect("/")
    return render_template("learn.html")

@app.route("/chatbot")
def chatbot():
    if "user_id" not in session: return redirect("/")
    return render_template("chatbot.html")

@app.route("/community")
def community():
    if "user_id" not in session: return redirect("/")
    return render_template("community.html")

# ==========================
# Đăng ký
# ==========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        avatar_url = request.form.get("avatar", "")
        uploaded_file = request.files.get("avatarUpload")
        email = request.form["email"]
        
        old_user = User.query.filter_by(username=username).first()
        old_email = User.query.filter_by(email=email).first()

        if old_user: return render_template("register.html", error="Tên đăng nhập đã tồn tại!")
        if old_email: return render_template("register.html", error="Email đã tồn tại!")
        
        if uploaded_file and uploaded_file.filename != "":
            upload_folder = os.path.join(app.static_folder, "avatars", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            filename = secure_filename(uploaded_file.filename)
            save_path = os.path.join(upload_folder, filename)
            uploaded_file.save(save_path)
            avatar_url = "uploads/" + filename
        elif avatar_url == "":
            avatar_url = "ma.jpg"

        # Sử dụng avatar_url thay cho avatar theo thiết kế của Supabase
        user = User(
            username=username,
            password=password,
            avatar_url=avatar_url,
            email=email, 
        )

        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        session["username"] = user.username
        session["avatar"] = user.avatar_url
        return redirect("/index")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if not user:
            return render_template("login.html", error="Email không tồn tại!")
        if user.password != password:
            return render_template("login.html", error="Sai mật khẩu!")

        session["user_id"] = user.id
        session["username"] = user.username
        session["avatar"] = user.avatar_url
        session.permanent = False
        return redirect("/index")
    return render_template("login.html")
    
@app.route("/update-avatar", methods=["POST"])
def update_avatar():
    if "user_id" not in session: return jsonify({"success": False})
    data = request.get_json()
    user = User.query.get(session["user_id"])
    user.avatar_url = data["avatar"]
    db.session.commit()
    session["avatar"] = user.avatar_url
    return jsonify({"success": True, "avatar": user.avatar_url})

@app.context_processor
def inject_user():
    return dict(current_user=session.get('username'))

@app.route("/profile")
def profile():
    if "user_id" not in session: return redirect("/login")
    user = User.query.get(session["user_id"])
    return render_template("profile.html", user=user)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/get_bot_response", methods=["POST"])
def get_bot_response():
    data = request.json
    cau_hoi = data.get("question", "").strip()
    if not cau_hoi:
        return jsonify({"reply": "Bạn chưa nhập câu hỏi."})
    tra_loi = get_answer_from_db(cau_hoi)
    return jsonify({"reply": tra_loi})

@app.route("/settings")
def settings():
    if "user_id" not in session: return redirect("/login")
    user = User.query.get(session["user_id"])
    return render_template("settings.html", user=user)

@app.route("/tongquan")
def tongquan():
    if "user_id" not in session: return redirect("/")
    return render_template("learn.html")

@app.route("/nguongoc")
def nguongoc():
    if "user_id" not in session: return redirect("/")
    return render_template("nguon-goc.html")

@app.route("/danso")
def danso():
    if "user_id" not in session: return redirect("/")
    return render_template("dan-so.html")

@app.route("/ngonngu")
def ngonngu():
    if "user_id" not in session: return redirect("/")
    return render_template("ngon-ngu.html")

@app.route("/khuvuc")
def khuvuc():
    if "user_id" not in session: return redirect("/")
    return render_template("khu-vuc.html")


# ==========================
# API COMMUNITY
# ==========================

@app.route("/api/current-user")
def current_user_api():
    if "user_id" not in session: return jsonify({"success":False})
    user = User.query.get(session["user_id"])
    avatar = user.avatar_url

    if not avatar.startswith("/static"):
        avatar = "/static/avatars/" + avatar

    return jsonify({"success":True, "data":{"name": user.username, "avatar": avatar}})

@app.route("/api/posts")
def get_posts():
    try:
        tab = request.args.get("tab","Tổng quan")
        username = ""
        user_id_current = None
        if "user_id" in session:
            user = User.query.get(session["user_id"])
            username = user.username
            user_id_current = user.id

        conn = get_community_db()
        cursor = conn.cursor()

        # Update SQL to use Postgres JOIN vì author_name và avatar nằm ở table users
        base_query = """
            SELECT p.id, p.created_at, p.content, p.image_url, p.category, p.shared_post_id,
                   u.username as author_name, u.avatar_url as author_avatar,
                   (SELECT COUNT(*) FROM post_likes pl WHERE pl.post_id = p.id) as likes,
                   (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) as comments,
                   (SELECT COUNT(*) FROM posts p2 WHERE p2.shared_post_id = p.id) as shares
            FROM posts p
            JOIN users u ON p.user_id = u.id
        """
        
        if tab == "Tổng quan":
            cursor.execute(base_query + " ORDER BY p.id DESC")
        else:
            cursor.execute(base_query + " WHERE p.category=%s ORDER BY p.id DESC", (tab,))
            
        rows = cursor.fetchall()
        posts = []

        for row in rows:
            reposted = False
            if user_id_current:
                cursor.execute("SELECT id FROM posts WHERE shared_post_id=%s AND user_id=%s", (row["id"], user_id_current))
                reposted = cursor.fetchone() is not None
                    
            liked = False
            if user_id_current:
                cursor.execute("SELECT post_id FROM post_likes WHERE post_id=%s AND user_id=%s", (row["id"], user_id_current))
                if cursor.fetchone(): liked = True
                
            avatar = row["author_avatar"]
            if not avatar: avatar = "default.jpg"
            if not avatar.startswith("/static"): avatar = "/static/avatars/" + avatar 

            created = row["created_at"]
            created = created + timedelta(hours=7)
            delta = datetime.now() - created

            if delta.days > 0: time_text = f"{delta.days} ngày trước"
            elif delta.seconds >= 3600: time_text = f"{delta.seconds//3600} giờ trước"
            elif delta.seconds >= 60: time_text = f"{delta.seconds//60} phút trước"
            else: time_text = "Vừa xong"

            original_data = None
            if row["shared_post_id"]:
                cursor.execute("""
                    SELECT p.content, p.image_url, p.created_at, u.username, u.avatar_url
                    FROM posts p
                    JOIN users u ON p.user_id = u.id
                    WHERE p.id=%s
                """, (row["shared_post_id"],))
                old = cursor.fetchone()
                if old:
                    old_avatar = old["avatar_url"]
                    if not old_avatar: old_avatar = "default.jpg"
                    if not old_avatar.startswith("/static"): old_avatar = "/static/avatars/" + old_avatar

                    old_created = old["created_at"] + timedelta(hours=7)
                    old_delta = datetime.now() - old_created

                    if old_delta.days > 0: old_time = f"{old_delta.days} ngày trước"
                    elif old_delta.seconds >= 3600: old_time = f"{old_delta.seconds//3600} giờ trước"
                    elif old_delta.seconds >= 60: old_time = f"{old_delta.seconds//60} phút trước"
                    else: old_time = "Vừa xong"

                    original_data = {
                        "name": old["username"],
                        "avatar": old_avatar,
                        "content": old["content"],
                        "images": json.loads(old["image_url"]) if old["image_url"] else [],
                        "timeText": old_time
                    }
        
            posts.append({
                "id":row["id"],
                "timeText": time_text,
                "createdAt": str(row["created_at"]),
                "authorName": row["author_name"],
                "authorAvatar": avatar,
                "category": row["category"],
                "text": row["content"],
                "images": json.loads(row["image_url"]) if row["image_url"] else [],
                "likes": row["likes"],
                "comments": row["comments"],
                "shares": row["shares"],
                "liked": liked,
                "isReposted": reposted,
                "original": original_data,
                "repostBy": row["author_name"] if row["shared_post_id"] else None,     
            })
        
        cursor.close()
        conn.close()
        return jsonify({"success":True, "data":posts})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success":False, "error":str(e)}),500


@app.route("/api/posts", methods=["POST"])
def create_post():
    if "user_id" not in session: return jsonify({"success": False}), 401
    data = request.get_json()
    if not data: return jsonify({"success":False, "error":"Không có dữ liệu gửi lên"}),400

    conn = get_community_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO posts (user_id, category, content, image_url)
        VALUES (%s, %s, %s, %s)
    """, (
        session["user_id"],
        data["category"],
        data["text"],
        json.dumps(data.get("images", []))
    ))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/topics-count")
def topics_count():
    conn = get_community_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM posts
        GROUP BY category
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    data = [{"name": row["category"], "count": row["count"]} for row in rows]
    return jsonify({"success":True, "data":data})

@app.route("/api/active-member")
def active_member():
    conn = get_community_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.username, u.avatar_url, COUNT(p.id) as post_count
        FROM users u
        JOIN posts p ON u.id = p.user_id
        GROUP BY u.id
        ORDER BY post_count DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        avatar = row["avatar_url"]
        if not avatar: avatar = "default.png"
        if not avatar.startswith("/static"): avatar = "/static/avatars/" + avatar
        data = {"name": row["username"], "avatar": avatar, "postCount": row["post_count"]}
    else:
        data = {"name":"Chưa có dữ liệu", "avatar":"https://i.pravatar.cc/150", "postCount":0}

    return jsonify({"success":True, "data":data})

@app.route("/api/posts/<int:post_id>/like", methods=["POST"])
def like_post(post_id):
    if "user_id" not in session: return jsonify({"success":False}),401
    conn=get_community_db()
    cursor=conn.cursor()
    user_id=session["user_id"]

    cursor.execute("SELECT * FROM post_likes WHERE post_id=%s AND user_id=%s", (post_id, user_id))
    liked=cursor.fetchone()

    if liked:
        cursor.execute("DELETE FROM post_likes WHERE post_id=%s AND user_id=%s", (post_id, user_id))
        isLiked=False
    else:
        cursor.execute("INSERT INTO post_likes (post_id, user_id) VALUES (%s, %s)", (post_id, user_id))
        isLiked=True

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM post_likes WHERE post_id=%s", (post_id,))
    count=cursor.fetchone()[0]
    cursor.close()
    conn.close()

    return jsonify({"success":True, "liked":isLiked, "likes":count})

@app.route("/api/posts/<int:post_id>/comment", methods=["POST"])
def add_comment(post_id):
    if "user_id" not in session: return jsonify({"success":False})
    data=request.json
    conn=get_community_db()
    cursor=conn.cursor()

    cursor.execute("""
        INSERT INTO comments (post_id, user_id, content)
        VALUES(%s, %s, %s)
    """, (post_id, session["user_id"], data["content"]))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success":True})

@app.route("/api/users")
def get_users():
    users=User.query.all()
    return jsonify({
        "success":True,
        "data":[{"id":u.id, "name":u.username, "avatar":u.avatar_url} for u in users]
    })
    
@app.route("/api/posts/<int:post_id>/share", methods=["POST"])
def share_post(post_id):
    if "user_id" not in session: return jsonify({"success":False, "message":"Chưa đăng nhập"})
    data = request.json or {}
    caption = data.get("caption","")
    
    conn = get_community_db()
    cursor = conn.cursor()

    cursor.execute("SELECT category FROM posts WHERE id=%s", (post_id,))
    original = cursor.fetchone()

    if not original:
        return jsonify({"success":False, "message":"Không tìm thấy bài viết"})

    cursor.execute("""
        INSERT INTO posts (user_id, category, content, image_url, shared_post_id)
        VALUES(%s, %s, %s, %s, %s)
    """, (session["user_id"], original["category"], caption, json.dumps([]), post_id))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success":True})

@app.route("/api/posts/<int:post_id>/comments")
def get_comments(post_id):
    conn=get_community_db()
    cursor=conn.cursor()

    cursor.execute("""
        SELECT c.content, u.username, u.avatar_url
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id=%s
        ORDER BY c.id DESC
    """, (post_id,))

    rows=cursor.fetchall()
    cursor.close()
    conn.close()

    data=[]
    for row in rows:
        avatar=row["avatar_url"]
        if not avatar.startswith("/static"): avatar="/static/avatars/"+avatar
        data.append({"username":row["username"], "avatar":avatar, "content":row["content"]})

    return jsonify({"success":True, "data":data})

@app.route("/upload-avatar", methods=["POST"])
def upload_avatar():
    if "user_id" not in session: return jsonify({"success": False}), 401
    file = request.files.get("avatar")
    if not file or file.filename == "": return jsonify({"success": False})

    filename = secure_filename(file.filename)
    upload_folder = os.path.join(app.static_folder, "avatars", "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    save_path = os.path.join(upload_folder, filename)
    file.save(save_path)

    user = User.query.get(session["user_id"])
    user.avatar_url = "uploads/" + filename
    db.session.commit()
    session["avatar"] = user.avatar_url

    return jsonify({"success": True, "avatar": "/static/avatars/uploads/" + filename})
    
# ==========================
# Chạy chương trình
# ==========================
if __name__ == "__main__":
    # Đã thực hiện create_community_table() từ trong context nếu dùng logic quản lý table ban đầu
    app.run(
        host="0.0.0.0",
        port=10000,
        debug=True,
        use_reloader=False
    )