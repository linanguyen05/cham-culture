# Chăm Culture — Backend hợp nhất

Một dịch vụ FastAPI độc lập, chuyên nghiệp cho toàn bộ dự án. Nó phục vụ luôn
frontend SPA chuẩn (`../frontend`) và cung cấp mọi API mà frontend cần, chạy
hoàn toàn bằng **SQLite cục bộ + lưu file trên ổ đĩa cục bộ** — không cần bất kỳ
thông tin đăng nhập cloud nào, nên chạy được và kiểm thử được ngay lập tức.

> Backend này giữ nguyên kiến trúc phân lớp của nền tảng gốc
> `backend` / `backend_community` (routes → service → repository, phiên đăng nhập
> bằng cookie mã hóa, kiểm tra dữ liệu đầu vào, giới hạn tần suất, chống CSRF /
> origin guard) và hoàn thiện thành một dịch vụ duy nhất chạy được. Bản gốc dùng
> Postgres/Supabase được lưu trữ tại `../legacy/` để tham khảo.

## Kiến trúc

```
Trình duyệt ── cùng origin ──> FastAPI
                                ├── /                      frontend tĩnh (SPA)
                                ├── /uploads/*             ảnh đã tải lên (ổ đĩa cục bộ)
                                ├── /login /register       auth tương thích (frontend/index.html)
                                ├── /update_profile        hồ sơ tương thích (frontend/profile.js)
                                ├── /api/auth/*            API phiên đăng nhập (community.js)
                                ├── /api/community/*       bài viết, thích, bình luận, chia sẻ, thống kê
                                └── /api/community/profiles/{id}
```

Mỗi tính năng chia làm các lớp: `routes.py` (HTTP) → `service.py` (nghiệp vụ /
kiểm tra) → `repository.py` (SQLite). Các thành phần dùng chung: `config.py`,
`db.py`, `extensions.py` (vòng đời ứng dụng), `middleware/auth.py` (cookie phiên
Fernet + `get_current_user`), `middleware/security.py` (chống CSRF / origin
guard), `rate_limit.py`, `storage/` (lưu media cục bộ), `web.py` (gắn file tĩnh).

- **Dữ liệu**: SQLite tại `data/cham_culture.db` (schema trong `app/schema.sql`).
- **Xác thực**: email/mật khẩu băm bằng PBKDF2-HMAC-SHA256; cookie phiên HTTPOnly
  được mã hóa (khóa dẫn xuất từ `SECRET_KEY`). Không bao giờ tin `localStorage`
  làm nguồn xác thực.
- **Lưu trữ**: ảnh tải lên được ghi vào `uploads/` và phục vụ tại `/uploads/...`.

## Chạy dự án

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate            # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env               # tùy chọn; nếu không có vẫn dùng giá trị mặc định hợp lý
python seed.py                        # tùy chọn: tạo dữ liệu demo
python run.py                         # http://127.0.0.1:8000
```

Sau đó mở <http://127.0.0.1:8000/> — trang đăng nhập/đăng ký. Sau khi đăng nhập
bạn vào trang chủ (dashboard); trang Cộng đồng nằm ở `/community/index.html`.

Tài khoản demo (sau khi chạy `seed.py`): `minhanh@gmail.com` / `123Aa`.

## Kiểm thử / xác minh

```powershell
python run.py                 # ở một cửa sổ terminal
python verify.py              # ở terminal khác — 42 kiểm thử đầu-cuối
```

`verify.py` chạy qua toàn bộ hợp đồng API: chặn khách chưa đăng nhập, đăng ký →
cập nhật hồ sơ → phiên đăng nhập, đăng nhập/đăng xuất, tải feed + lọc + sắp xếp,
tạo bài (kèm tải ảnh lên), bật/tắt thích, bình luận, chia sẻ (kèm bài gốc nhúng),
thống kê, quyền riêng tư hồ sơ, chống CSRF, và phục vụ trang tĩnh.

## Cấu hình

Mọi thiết lập đều có giá trị mặc định cho môi trường cục bộ; xem `.env.example`.
Một số biến quan trọng:

| Biến | Mục đích |
| --- | --- |
| `SECRET_KEY` | ≥32 ký tự; dùng để dẫn xuất khóa mã hóa phiên. **Bắt buộc đổi khi lên production.** |
| `DATABASE_PATH` | File SQLite (tương đối so với thư mục `backend/`). |
| `UPLOAD_DIR` | Thư mục media cục bộ, phục vụ tại `/uploads`. |
| `FRONTEND_DIR` | Thư mục frontend cần phục vụ (mặc định `../frontend`). |
| `SESSION_SECURE` | Đặt `true` khi chạy qua HTTPS. |
| `FRONTEND_ORIGINS` | Các origin bổ sung được phép; cùng origin luôn được chấp nhận. |
| `RATE_LIMIT_*` | Giới hạn tần suất theo từng endpoint. |

## Về các dịch vụ khác

`../services/chatbot` (chatbot Gemini) và `../services/learn` (nội dung tìm hiểu)
là các ứng dụng Flask độc lập, được giữ nguyên; chúng không nằm trong tiến trình
của backend này và có thể chạy riêng khi cần.
