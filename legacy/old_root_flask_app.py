import sqlite3
import json
import os
import traceback
from flask import Flask, render_template, request, jsonify, session, redirect
from database import db
from models import User
from chatbot_engine import get_answer_from_db
from werkzeug.utils import secure_filename

# ==========================
# Khởi tạo Flask
# ==========================
app = Flask(__name__)

app.secret_key = "chamculture2026"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_PERMANENT"] = False
db.init_app(app)

with app.app_context():
    print("DB URL:", db.engine.url)
    print("DB FILE:", os.path.abspath(db.engine.url.database))
    db.create_all()

# ==========================
# TẠO DATABASE CỘNG ĐỒNG
# ==========================
def create_community_table():

    conn = sqlite3.connect(COMMUNITY_DB)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        author_name TEXT,
        author_avatar TEXT,
        category TEXT,
        content TEXT,
        images TEXT DEFAULT '[]',
        likes INTEGER DEFAULT 0,
        comments INTEGER DEFAULT 0,
        shares INTEGER DEFAULT 0,
        repost_by TEXT DEFAULT '',
        original_post_id INTEGER DEFAULT NULL,
        privacy TEXT DEFAULT 'public',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS likes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_id INTEGER,
        UNIQUE(post_id,user_id)
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_id INTEGER,
        username TEXT,
        avatar TEXT,
        content TEXT,
        image TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_id INTEGER,
        reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shares(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_id INTEGER,
        friend_name TEXT,
        caption TEXT DEFAULT '',
        privacy TEXT DEFAULT 'public',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(post_id,user_id)
    )
    """)


    conn.commit()
    conn.close()

    print("✅ COMMUNITY DATABASE READY")

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
            return render_template(
                "change_password.html",
                error="Mật khẩu cũ không đúng!"
            )

        if new_password != confirm_password:
            return render_template(
                "change_password.html",
                error="Mật khẩu xác nhận không khớp!"
            )

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
# Trang tìm hiểu
# ==========================
@app.route("/learn")
def learn():
    if "user_id" not in session:
        return redirect("/")
    return render_template("learn.html")

# ==========================
# Trang chatbot
# ==========================
@app.route("/chatbot")
def chatbot():
    if "user_id" not in session:
        return redirect("/")
    return render_template("chatbot.html")

# ==========================
# Trang cộng đồng
# ==========================
@app.route("/community")
def community():
    if "user_id" not in session:
        return redirect("/")
    return render_template("community.html")

# ==========================
# Đăng ký
# ==========================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        avatar = request.form.get("avatar", "")
        uploaded_file = request.files.get("avatarUpload")
        email = request.form["email"]
        
        old_user = User.query.filter_by(username=username).first()
        old_email = User.query.filter_by(email=email).first()

        if old_user:
            return render_template(
                "register.html",
                error="Tên đăng nhập đã tồn tại!"
            )

        if old_email:
            return render_template(
                "register.html",
                error="Email đã tồn tại!"
            )
        
        # Nếu có upload ảnh
        if uploaded_file and uploaded_file.filename != "":

            upload_folder = os.path.join(
                app.static_folder,
                "avatars",
                "uploads"
            )

            os.makedirs(upload_folder, exist_ok=True)

            filename = secure_filename(uploaded_file.filename)

            save_path = os.path.join(
                upload_folder,
                filename
            )

            uploaded_file.save(save_path)

            avatar = "uploads/" + filename

        # Nếu không chọn gì cả
        elif avatar == "":

            avatar = "ma.jpg"

        user = User(
            username=username,
            password=password,
            avatar=avatar,
            email=email, 
        )

        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        session["username"] = user.username
        session["avatar"] = user.avatar

        return redirect("/index")

    return render_template("register.html")
# ==========================


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if not user:
            return render_template(
                "login.html",
                error="Email không tồn tại!"
            )

        if user.password != password:
            return render_template(
                "login.html",
                error="Sai mật khẩu!"
            )

        session["user_id"] = user.id
        session["username"] = user.username
        session["avatar"] = user.avatar
        session.permanent = False
        return redirect("/index")

    return render_template("login.html")

    
@app.route("/update-avatar", methods=["POST"])
def update_avatar():

    if "user_id" not in session:
        return jsonify({"success": False})

    data = request.get_json()

    user = User.query.get(session["user_id"])

    user.avatar = data["avatar"]

    db.session.commit()

    # cập nhật luôn session
    session["avatar"] = user.avatar

    return jsonify({
        "success": True,
        "avatar": user.avatar
    })


@app.context_processor
def inject_user():

    return dict(
        current_user=session.get('username')
    )
# ==========================
# Hồ sơ cá nhân
# ==========================
@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    return render_template(
        "profile.html",
        user=user
    )

# ==========================
# Đăng xuất
# ==========================
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# ==========================
# Chatbot
# ==========================
@app.route("/get_bot_response", methods=["POST"])
def get_bot_response():

    data = request.json

    cau_hoi = data.get("question", "").strip()

    if not cau_hoi:
        return jsonify({
            "reply": "Bạn chưa nhập câu hỏi."
        })

    tra_loi = get_answer_from_db(cau_hoi)

    return jsonify({
        "reply": tra_loi
    })
@app.route("/settings")
def settings():

    if "user_id" not in session:
        return redirect("/login")

    user = User.query.get(session["user_id"])

    return render_template(
        "settings.html",
        user=user
    )
    
@app.route("/tongquan")
def tongquan():
    if "user_id" not in session:
        return redirect("/")
    return render_template("learn.html")

@app.route("/nguongoc")
def nguongoc():
    if "user_id" not in session:
        return redirect("/")
    return render_template("nguon-goc.html")

@app.route("/danso")
def danso():
    if "user_id" not in session:
        return redirect("/")
    return render_template("dan-so.html")

@app.route("/ngonngu")
def ngonngu():
    if "user_id" not in session:
        return redirect("/")
    return render_template("ngon-ngu.html")

@app.route("/khuvuc")
def khuvuc():
    if "user_id" not in session:
        return redirect("/")
    return render_template("khu-vuc.html")


# ==========================
# API COMMUNITY
# ==========================
# ==========================
# COMMUNITY API
# ==========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

COMMUNITY_DB = os.path.join(
    BASE_DIR,
    "cham_culture.db"
)
create_community_table()

def get_community_db():

    conn = sqlite3.connect(
        COMMUNITY_DB,
        timeout=10
    )

    conn.row_factory = sqlite3.Row

    return conn



@app.route("/api/current-user")
def current_user_api():

    if "user_id" not in session:
        return jsonify({
            "success":False
        })

    user = User.query.get(session["user_id"])

    avatar = user.avatar

    # nếu database chỉ lưu tên file
    if not avatar.startswith("/static"):
        avatar = "/static/avatars/" + avatar


    return jsonify({
        "success":True,
        "data":{
            "name": user.username,
            "avatar": avatar
        }
    })



@app.route("/api/posts")
def get_posts():
    from datetime import datetime, timedelta
    try:
        tab = request.args.get("tab","Tổng quan")
        
        username = ""

        if "user_id" in session:
            user = User.query.get(session["user_id"])
            username = user.username

        conn = get_community_db()
        cursor = conn.cursor()

        if tab == "Tổng quan":
            cursor.execute("""
                SELECT *
                FROM posts
                WHERE privacy='public'
                   OR author_name=?
                ORDER BY id DESC
            """, (username,))

        else:
            cursor.execute("""
                SELECT *
                FROM posts
                WHERE category=?
                  AND (
                        privacy='public'
                        OR author_name=?
                  )
                ORDER BY id DESC
            """, (tab, username))
            
        rows = cursor.fetchall()

        posts=[]

        for row in rows:
            
            reposted = False

            if "user_id" in session:
                cursor.execute("""
                    SELECT id
                    FROM shares
                   WHERE post_id=? AND user_id=?
                """, (
                    row["id"],
                    session["user_id"]
                ))

                reposted = cursor.fetchone() is not None
                    
            cursor.execute("""
            SELECT COUNT(*)
            FROM shares
            WHERE post_id=?
            """, (row["id"],))

            share_count = row["shares"]

            avatar = row["author_avatar"]
            # kiểm tra user hiện tại đã tim bài này chưa
            liked = False

            if "user_id" in session:

                cursor.execute("""
                    SELECT id
                    FROM likes
                    WHERE post_id=? AND user_id=?
                """,
                (
                    row["id"],
                    session["user_id"]
                ))

                if cursor.fetchone():
                    liked = True
            avatar = row["author_avatar"]

            if not avatar:
                avatar = "default.jpg"

            if not avatar.startswith("/static"):
                avatar = "/static/avatars/" + avatar 


            created = datetime.strptime(
                row["created_at"],
                "%Y-%m-%d %H:%M:%S"
            )
            created = created + timedelta(hours=7)
            
            delta = datetime.now() - created

            if delta.days > 0:
                time_text = f"{delta.days} ngày trước"
            elif delta.seconds >= 3600:
                time_text = f"{delta.seconds//3600} giờ trước"
            elif delta.seconds >= 60:
                time_text = f"{delta.seconds//60} phút trước"
            else:
                time_text = "Vừa xong"
            
            print("===== POST =====")
            print("ID:", row["id"])
            print("original_post_id:", row["original_post_id"])

            original_data = None

            if row["original_post_id"]:

                cursor.execute(
                    "SELECT * FROM posts WHERE id=?",
                    (row["original_post_id"],)
                )

                old = cursor.fetchone()

                if old:

                    old_avatar = old["author_avatar"]

                    if not old_avatar:
                        old_avatar = "default.jpg"

                    if not old_avatar.startswith("/static"):
                        old_avatar = "/static/avatars/" + old_avatar

                    from datetime import datetime, timedelta

                    old_created = datetime.strptime(
                        old["created_at"],
                        "%Y-%m-%d %H:%M:%S"
                    )
                    old_created += timedelta(hours=7)

                    old_delta = datetime.now() - old_created

                    if old_delta.days > 0:
                        old_time = f"{old_delta.days} ngày trước"
                    elif old_delta.seconds >= 3600:
                        old_time = f"{old_delta.seconds//3600} giờ trước"
                    elif old_delta.seconds >= 60:
                        old_time = f"{old_delta.seconds//60} phút trước"
                    else:
                        old_time = "Vừa xong"

                    original_data = {
                        "name": old["author_name"],
                        "avatar": old_avatar,
                        "content": old["content"],
                        "images": json.loads(old["images"]) if old["images"] else [],
                        "timeText": old_time
                    }
        
            posts.append({
                "id":row["id"],
                
                "timeText": time_text,
                
                "createdAt":row["created_at"],
                
                "authorName": row["author_name"],

                "authorAvatar": avatar,

                "category": row["category"],

                "text": row["content"],

                "images": json.loads(row["images"]) if row["images"] else [],

                "likes": row["likes"],

                "comments": row["comments"],
                
                "shares": share_count,
                
                "liked": liked,
                
                "isReposted": reposted,
                
                "original": original_data,
                
                "repostBy": row["repost_by"] if "repost_by" in row.keys() else None,     
            })
        conn.close()

        return jsonify({
            "success":True,
            "data":posts
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "success":False,
            "error":str(e)
        }),500


@app.route("/api/posts", methods=["POST"])
def create_post():

    if "user_id" not in session:
        return jsonify({"success": False}), 401

    data = request.get_json()

    if not data:
        return jsonify({
            "success":False,
            "error":"Không có dữ liệu gửi lên"
        }),400

    user = User.query.get(session["user_id"])

    conn = get_community_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO posts
        (
            author_name,
            author_avatar,
            category,
            content,
            images,
            likes,
            comments
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
    (
        user.username,
        user.avatar,
        data["category"],
        data["text"],
        json.dumps(data.get("images", [])),
        0,
        0
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True
    })

# ==========================
# TOPICS COUNT
# ==========================

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

    conn.close()

    data = []

    for row in rows:
        data.append({
            "name": row["category"],
            "count": row["count"]
        })


    return jsonify({
        "success":True,
        "data":data
    })



# ==========================
# ACTIVE MEMBER
# ==========================

@app.route("/api/active-member")
def active_member():

    conn = get_community_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
        author_name,
        author_avatar,
        COUNT(*) as post_count

        FROM posts

        GROUP BY author_name, author_avatar

        ORDER BY post_count DESC

        LIMIT 1
    """)


    row = cursor.fetchone()

    conn.close()


    if row:

        avatar = row["author_avatar"]

        if not avatar:
            avatar = "default.png"

        if not avatar.startswith("/static"):
            avatar = "/static/avatars/" + avatar

        data = {
            "name": row["author_name"],
            "avatar": avatar,
            "postCount": row["post_count"]
        }

    else:

        data = {
            "name":"Chưa có dữ liệu",
            "avatar":"https://i.pravatar.cc/150",
            "postCount":0
        }


    return jsonify({
        "success":True,
        "data":data
    })

@app.route("/api/posts/<int:post_id>/like", methods=["POST"])
def like_post(post_id):
    if "user_id" not in session:
        return jsonify({"success":False}),401

    conn=get_community_db()
    cursor=conn.cursor()

    post_id=int(post_id)
    user_id=session["user_id"]

    cursor.execute("""
    SELECT *
    FROM likes
    WHERE post_id=? AND user_id=?
    """,(post_id,user_id))

    liked=cursor.fetchone()

    if liked:

        cursor.execute("""
        DELETE FROM likes
        WHERE post_id=? AND user_id=?
        """,(post_id,user_id))

        cursor.execute("""
        UPDATE posts
        SET likes=likes-1
        WHERE id=?
        """,(post_id,))

        isLiked=False

    else:

        cursor.execute("""
        INSERT INTO likes(post_id,user_id)
        VALUES(?,?)
        """,(post_id,user_id))

        cursor.execute("""
        UPDATE posts
        SET likes=likes+1
        WHERE id=?
        """,(post_id,))

        isLiked=True

    conn.commit()

    cursor.execute("SELECT likes FROM posts WHERE id=?",(post_id,))
    count=cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "success":True,
        "liked":isLiked,
        "likes":count
    })

@app.route("/api/posts/<int:post_id>/comment",
methods=["POST"])
def add_comment(post_id):

    if "user_id" not in session:
        return jsonify({"success":False})


    data=request.json

    user=User.query.get(
        session["user_id"]
    )


    conn=get_community_db()
    cursor=conn.cursor()


    cursor.execute("""
    INSERT INTO comments
    (
    post_id,
    user_id,
    username,
    avatar,
    content
    )

    VALUES(?,?,?,?,?)
    """,
    (
    post_id,
    user.id,
    user.username,
    user.avatar,
    data["content"]
    ))


    cursor.execute("""
    UPDATE posts
    SET comments=comments+1
    WHERE id=?
    """,
    (post_id,))


    conn.commit()
    conn.close()


    return jsonify({
    "success":True
    })

@app.route("/api/users")
def get_users():

    users=User.query.all()


    return jsonify({

    "success":True,

    "data":[

    {
    "id":u.id,
    "name":u.username,
    "avatar":u.avatar
    }

    for u in users

    ]

    })
    
    
@app.route("/api/posts/<int:post_id>/share", methods=["POST"])
def share_post(post_id):

    if "user_id" not in session:
        return jsonify({
            "success":False,
            "message":"Chưa đăng nhập"
        })


    user = User.query.get(session["user_id"])

    data = request.json or {}

    caption = data.get("caption","")
    
    privacy = data.get("privacy", "public")
    
    print("Privacy:", privacy)

    conn = get_community_db()
    cursor = conn.cursor()


    # lấy bài gốc
    cursor.execute(
        "SELECT * FROM posts WHERE id=?",
        (post_id,)
    )

    original = cursor.fetchone()


    if not original:
        return jsonify({
            "success":False,
            "message":"Không tìm thấy bài viết"
        })


    # tạo bài đăng mới
    cursor.execute("""
    INSERT INTO posts
    (
        author_name,
        author_avatar,
        category,
        content,
        images,
        likes,
        comments,
        shares,
        repost_by,
        original_post_id,
        privacy
    )

    VALUES(?,?,?,?,?,?,?,?,?,?,?)
    """,
    (
        user.username,
        user.avatar,
        original["category"],
        caption,
        json.dumps([]),
        0,
        0,
        0,
        original["author_name"],
        post_id,
        privacy
    ))



    # tăng số share bài gốc
    cursor.execute("""
    UPDATE posts
    SET shares = shares + 1
    WHERE id=?
    """,
    (post_id,))
    
    print("Rows updated:", cursor.rowcount)

    cursor.execute(
        "SELECT shares FROM posts WHERE id=?",
        (post_id,)
    )

    print("Current shares:", cursor.fetchone()["shares"])

    conn.commit()
    cursor.execute("""
    SELECT privacy
    FROM posts
    ORDER BY id DESC
    LIMIT 1
    """)

    print(cursor.fetchone()["privacy"])
    conn.close()


    return jsonify({
        "success":True
    })
@app.route("/api/posts/<int:post_id>/comments")
def get_comments(post_id):

    conn=get_community_db()
    cursor=conn.cursor()


    cursor.execute("""
    SELECT *
    FROM comments
    WHERE post_id=?
    ORDER BY id DESC
    """,(post_id,))


    rows=cursor.fetchall()

    conn.close()


    data=[]

    for row in rows:

        avatar=row["avatar"]

        if not avatar.startswith("/static"):
            avatar="/static/avatars/"+avatar


        data.append({

            "username":row["username"],

            "avatar":avatar,

            "content":row["content"]

        })


    return jsonify({

        "success":True,

        "data":data

    })

@app.route("/upload-avatar", methods=["POST"])
def upload_avatar():

    if "user_id" not in session:
        return jsonify({"success": False}), 401

    file = request.files.get("avatar")

    if not file or file.filename == "":
        return jsonify({"success": False})

    filename = secure_filename(file.filename)

    upload_folder = os.path.join(
        app.static_folder,
        "avatars",
        "uploads"
    )

    os.makedirs(upload_folder, exist_ok=True)

    save_path = os.path.join(upload_folder, filename)

    file.save(save_path)

    user = User.query.get(session["user_id"])

    user.avatar = "uploads/" + filename

    db.session.commit()

    session["avatar"] = user.avatar

    return jsonify({
        "success": True,
        "avatar": "/static/avatars/uploads/" + filename
    })
    
# ==========================
# Chạy chương trình
# ==========================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000,
        debug=True,
        use_reloader=False
    )
