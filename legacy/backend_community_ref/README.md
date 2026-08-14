# Chăm Culture Community Backend

FastAPI backend cho Community, đứng giữa browser và Supabase/PostgreSQL.

## 1. Kiến trúc

Browser → FastAPI → PostgreSQL / Supabase Storage / Supabase Auth

- `psycopg` + PostgreSQL: query, transaction, pagination và aggregation.
- `supabase-py`: upload/delete ảnh trong Storage bằng service-role client chỉ tồn tại ở server.
- Supabase Auth REST: xác thực email/password tại server trong route login.
- Session: Fernet-encrypted + HTTPOnly cookie, không dùng `localStorage` làm nguồn xác thực.

## 2. Chạy

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Frontend có thể gọi `/api/...` cùng origin. Đặt `community_optimized.html`, `.css`, `.js` trong thư mục frontend mà web server đang phục vụ; không đưa `SUPABASE_SERVICE_ROLE_KEY` vào frontend.

## 3. Authentication

`community_optimized.js` hiện chỉ gọi `GET /api/auth/me` và chuyển khách về `/login/index.html`; file JS không chứa login request. Backend cung cấp thêm `POST /api/auth/login` và `POST /api/auth/logout` để login page hiện tại có thể cấp/xóa session mà không thay đổi kiến trúc Community.

`users.id` được kỳ vọng khớp `auth.users.id` của Supabase Auth. Nếu website hiện tại đã có hệ thống login riêng, chỉ cần sau khi login thành công cấp cùng session cookie cho backend hoặc chuyển login page sang `POST /api/auth/login`.

## 4. Image serialization

Giữ nguyên schema `posts.image_url`: backend lưu một JSON array string, ví dụ `["url1","url2"]`. API luôn trả `image_urls: []` để frontend không phải hiểu cách lưu DB.

Bucket mặc định là `community-images`. Backend tạo path UUID như `posts/<uuid>.jpg`, không dùng tên file người dùng làm path.

## 5. Production notes

- `SESSION_SECURE=true` khi chạy HTTPS.
- `FRONTEND_ORIGINS` phải chứa origin thật.
- `ALLOW_MISSING_ORIGIN_FOR_UNSAFE_METHODS=false` khi production nếu browser-only API là mục tiêu.
- Đổi `RATE_LIMIT_STORAGE_URI` sang Redis khi chạy nhiều worker/instance.
- Có thể dùng pooled Supabase Postgres connection string trong `DATABASE_URL`.
- Public bucket đơn giản cho frontend `<img src=...>`. Với bucket private, đổi sang signed URLs và cơ chế refresh.

## Profile API integration

The Community profile feature is implemented by `app/profile.py` and registered in `app/__init__.py`.

Endpoint:

`GET /api/community/profiles/{user_id}?page=1&limit=50`

The endpoint is protected by the existing `get_current_user` dependency. It returns the requested user's public profile and their posts. The `email` field is returned only when `{user_id}` belongs to the authenticated user.

The frontend automatically follows `pagination.has_next` until all profile posts are loaded.
