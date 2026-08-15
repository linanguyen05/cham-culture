# BÀN GIAO — Chăm Culture (vhc)

Tài liệu bàn giao ngắn gọn: hiện trạng, cách demo, và mức độ sẵn sàng cho người
dùng cuối.

---

## 1. Tình trạng source code

### Cấu trúc thư mục (đã dọn lại)
```
vhc/
├─ backend/        ← MỘT backend hợp nhất (FastAPI + Supabase/PostgreSQL), CHẠY ĐƯỢC
├─ frontend/       ← Giao diện SPA chuẩn (KHÔNG chỉnh sửa; chỉ bổ sung 2 file còn thiếu)
├─ services/
│  ├─ chatbot/     ← App chatbot Gemini (Flask, độc lập) — trước là Chatbox/
│  └─ learn/       ← Nội dung "Tìm hiểu" (Flask, độc lập) — trước là Timhieudantoccham/
├─ legacy/         ← Lưu trữ code cũ/trùng lặp, KHÔNG xóa (6 backend cũ, trang Jinja cũ...)
├─ README.md / HANDOVER.md
└─ Van_hoa_Cham_Database.docx  ← chứa SECRET Supabase — KHÔNG commit, nên rotate key
```

### Backend
- Gộp 6 backend rải rác thành **một** dịch vụ FastAPI, kiến trúc phân lớp
  `routes → service → repository`.
- Chạy trên **Supabase** đúng thiết kế đã thống nhất:
  - **PostgreSQL** (bảng `users/posts/comments/post_likes`, khóa `bigint`) qua psycopg.
  - **Supabase Auth** (đăng ký/đăng nhập; mật khẩu do Supabase quản lý; `users` liên kết auth qua email).
  - **Supabase Storage** (ảnh bài viết + avatar, bucket `community-images`).
- Có sẵn: phiên đăng nhập cookie mã hóa (Fernet), kiểm tra dữ liệu, giới hạn tần
  suất, chống CSRF/origin, tài liệu API `/docs`, và **lớp ánh xạ category** để
  khớp nhãn frontend với ràng buộc CHECK của DB.
- Backend phục vụ luôn frontend cùng origin.

### Tình trạng tính năng
| Tính năng | Trạng thái |
| --- | --- |
| Đăng ký / Đăng nhập / Hồ sơ | ✅ Hoạt động (Supabase Auth) |
| Trang chủ (dashboard) | ✅ |
| Cộng đồng (feed, đăng bài + ảnh, thích, bình luận, chia sẻ, thống kê, hồ sơ) | ✅ đầy đủ |
| **Tìm hiểu** | ⛔ Chưa nối — link nav frontend đang `href="#"`; nội dung ở `services/learn` |
| **Chatbot** | ⛔ Chưa nối — link nav đang `href="#"`; app ở `services/chatbot` (cần `GEMINI_API_KEY`) |

### Kiểm thử
- `backend/verify.py`: **39/39 PASS trên Supabase thật**, và tự dọn dữ liệu test.

---

## 2. Hướng dẫn chạy khi cần demo

```powershell
cd "l:\FPT\Side project\vhc\backend"
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env        # điền: SUPABASE_URL, SERVICE_ROLE_KEY, DB_PASSWORD, DATABASE_URL
python seed.py                # tạo user + bài viết demo (chạy 1 lần)
python run.py                 # http://127.0.0.1:8000
```
- Mở <http://127.0.0.1:8000/> — **tài khoản demo:** `minhanh@gmail.com` / `123Aa`
- Luồng: Đăng nhập → Trang chủ → **Cộng đồng** → đăng bài (kèm ảnh), thích, bình
  luận, chia sẻ, mở hồ sơ.
- Tài liệu API: <http://127.0.0.1:8000/docs> · Kiểm thử: `python verify.py`

> `.env` đã có sẵn (đang git-ignore) với thông tin Supabase từ file `.docx`.
> `DATABASE_URL` đang dùng **Session Pooler (IPv4, region ap-southeast-1)** vì kết
> nối trực tiếp `db.<ref>.supabase.co` chỉ có IPv6 nên async không resolve được.

---

## 3. Người dùng cuối đã dùng được chưa?

**Chưa — mới chạy được trên máy bạn.** Làm rõ hiểu lầm: `http://127.0.0.1:8000/`
là địa chỉ **loopback**, dán cho người khác sẽ không mở được.

Để người ngoài dùng thật cần:
1. **Đưa lên máy chủ công khai** (VPS / Render / Railway / Fly.io) + **tên miền** + **HTTPS**.
2. Đặt `SESSION_SECURE=true`, `SECRET_KEY` mạnh, `FRONTEND_ORIGINS` nếu frontend khác domain.
3. Nếu bên thứ ba gọi API bằng chương trình: bổ sung **token/API key** (hiện dùng cookie-phiên cho trình duyệt).

Demo nhanh không cần deploy: `cloudflared tunnel --url http://127.0.0.1:8000`
rồi thêm URL tunnel vào `FRONTEND_ORIGINS`.

### Về tải cao / scale
Dữ liệu đã nằm trên **Supabase (PostgreSQL cloud)** nên đã sẵn sàng cho nhiều lượt
truy cập và **scale ngang** (phiên là cookie mã hóa, không giữ state server; ảnh
trên Supabase Storage). Điểm duy nhất cần đổi khi chạy **nhiều tiến trình**:
`RATE_LIMIT_STORAGE_URI` từ `memory://` sang **Redis**.

---

## ⚠️ Bảo mật (quan trọng)
File `Van_hoa_Cham_Database.docx` và `backend/.env` chứa **service-role key + mật
khẩu DB thật**. Đừng commit lên git (đã có `.gitignore` cho `.env`). Vì key đã
từng lộ ra ngoài, nên **rotate lại** service-role key trong Supabase.
