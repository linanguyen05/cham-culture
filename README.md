# Chăm Culture (vhc)

Nền tảng cộng đồng tìm hiểu và kết nối văn hóa dân tộc Chăm: trang chủ giới
thiệu, khu **Cộng đồng** (đăng bài, ảnh, thích, bình luận, chia sẻ, hồ sơ), cùng
các dịch vụ phụ trợ (Tìm hiểu, Chatbot).

Dự án gồm **một backend FastAPI hợp nhất** chạy trên **Supabase** (PostgreSQL +
Auth + Storage) theo đúng thiết kế database đã thống nhất, phục vụ luôn
**frontend SPA** cùng origin.

---

## Cấu trúc thư mục

```
vhc/
├─ backend/        Backend hợp nhất — FastAPI + Supabase/PostgreSQL (xem backend/README.md)
├─ frontend/       Giao diện SPA (HTML/CSS/JS tĩnh) — được backend phục vụ
├─ services/
│  ├─ chatbot/     App chatbot Gemini (Flask, độc lập)
│  └─ learn/       Nội dung "Tìm hiểu" (Flask, độc lập)
├─ legacy/         Lưu trữ code cũ/trùng lặp (không dùng, không xóa)
├─ HANDOVER.md     Tài liệu bàn giao (hiện trạng, demo, mức sẵn sàng)
└─ README.md       File này
```

## Công nghệ

- **Backend:** Python 3.12, FastAPI, Uvicorn, psycopg (Supabase PostgreSQL),
  Supabase Auth + Storage (qua httpx), Pydantic, slowapi (rate limit),
  cryptography (phiên đăng nhập mã hóa).
- **Frontend:** HTML/CSS/JavaScript thuần (SPA), gọi API cùng origin.
- **Dịch vụ phụ:** Flask (chatbot Gemini, trang Tìm hiểu).

## Bắt đầu nhanh

```powershell
cd "l:\FPT\Side project\vhc\backend"
python -m venv .venv
.\.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env               # rồi điền thông tin Supabase (URL, service key, DB password, DATABASE_URL)
python seed.py                       # tạo user + bài viết demo (chạy 1 lần)
python run.py                        # http://127.0.0.1:8000
```

- Mở: <http://127.0.0.1:8000/>
- Tài khoản demo: **`minhanh@gmail.com` / `123Aa`**
- Tài liệu API (OpenAPI): <http://127.0.0.1:8000/docs>

Chi tiết cấu hình, kiến trúc phân lớp và biến môi trường: xem
[`backend/README.md`](backend/README.md).

## Tình trạng tính năng

| Tính năng | Trạng thái |
| --- | --- |
| Đăng ký / Đăng nhập / Hồ sơ | ✅ Hoạt động |
| Trang chủ (dashboard) | ✅ Hoạt động |
| Cộng đồng (feed, đăng bài + ảnh, thích, bình luận, chia sẻ, thống kê, hồ sơ) | ✅ Hoạt động đầy đủ |
| Tìm hiểu | ⛔ Chưa nối vào SPA (link nav đang `#`); nội dung ở `services/learn` |
| Chatbot | ⛔ Chưa nối vào SPA (link nav đang `#`); app ở `services/chatbot` (cần `GEMINI_API_KEY`) |

## Tổng quan API

Backend phục vụ frontend tĩnh và các nhóm endpoint (cùng origin):

| Nhóm | Endpoint tiêu biểu | Mô tả |
| --- | --- | --- |
| Auth (SPA cũ) | `POST /register`, `POST /login`, `POST /update_profile` | Đúng hợp đồng của `frontend/index.html` & `profile.js` |
| Auth (API) | `GET /api/auth/me`, `POST /api/auth/login`, `POST /api/auth/logout` | Phiên đăng nhập cho `community.js` |
| Community | `GET/POST /api/community/posts`, `.../{id}/like`, `.../{id}/comments`, `.../{id}/share` | Feed & tương tác bài viết |
| Thống kê | `GET /api/community/stats/topics`, `.../active-members` | Chủ đề & thành viên tích cực |
| Hồ sơ | `GET /api/community/profiles/{id}` | Hồ sơ + bài viết (ẩn email nếu không phải chính chủ) |
| Khác | `GET /health`, `/docs`, `/uploads/*` | Health check, tài liệu, ảnh đã tải lên |

## Kiểm thử

```powershell
cd backend
python run.py            # terminal 1
python verify.py         # terminal 2 — 42 kiểm thử đầu-cuối
```

## Triển khai cho người dùng cuối

`http://127.0.0.1:8000/` chỉ chạy trên **máy cục bộ**. Để người ngoài dùng được
cần đưa lên máy chủ công khai + tên miền + HTTPS (đặt `SESSION_SECURE=true`).
Dữ liệu đã nằm trên Supabase (cloud) nên có thể scale ngang; chỉ cần đổi
rate-limit sang Redis khi chạy nhiều tiến trình. Demo nhanh có thể dùng tunnel
(`cloudflared tunnel --url http://127.0.0.1:8000`) và thêm URL tunnel vào
`FRONTEND_ORIGINS`. Chi tiết xem [`HANDOVER.md`](HANDOVER.md) mục 3.

## Ghi chú

- `legacy/` chỉ để tham khảo lịch sử, không tham gia vào hệ thống đang chạy.
- `frontend/` được giữ nguyên theo yêu cầu; chỉ bổ sung 2 file trước đây bị thiếu
  là `frontend/community/community.js` và `community.css`.
