# Chăm Culture — Backend hợp nhất (Supabase / PostgreSQL)

Một dịch vụ FastAPI độc lập, chuyên nghiệp cho toàn bộ dự án. Nó phục vụ luôn
frontend SPA chuẩn (`../frontend`) và cung cấp mọi API mà frontend cần, chạy trên
**đúng nền tảng đã thống nhất**: **Supabase PostgreSQL** (dữ liệu, qua psycopg),
**Supabase Auth** (đăng nhập/đăng ký) và **Supabase Storage** (ảnh).

> Giữ nguyên kiến trúc phân lớp của nền tảng gốc (routes → service → repository,
> phiên đăng nhập bằng cookie mã hóa, kiểm tra dữ liệu, giới hạn tần suất, chống
> CSRF/origin) và hoàn thiện thành một dịch vụ duy nhất. Các bản cũ được lưu ở
> `../legacy/`.

## Kiến trúc

```
Trình duyệt ── cùng origin ──> FastAPI
                                ├── /                      frontend tĩnh (SPA)
                                ├── /login /register       auth tương thích (frontend/index.html)
                                ├── /update_profile        hồ sơ tương thích (frontend/profile.js)
                                ├── /api/auth/*            phiên đăng nhập (community.js)
                                ├── /api/community/*       bài viết, thích, bình luận, chia sẻ, thống kê
                                └── /api/community/profiles/{id}
                                        │
                                        ├── psycopg  ──> Supabase PostgreSQL
                                        └── httpx    ──> Supabase Auth (GoTrue) + Storage
```

- **Dữ liệu**: Supabase PostgreSQL, truy cập bằng psycopg (async pool). Bảng
  `users / posts / comments / post_likes` (khóa `bigint`), liên kết `users`↔auth
  bằng **email**.
- **Xác thực**: Supabase Auth giữ mật khẩu. Đăng ký tạo user đã xác nhận qua
  admin API; đăng nhập xác thực qua password grant. Backend phát hành cookie
  phiên HTTPOnly mã hóa (Fernet) — không tin `localStorage`.
- **Lưu ảnh**: Supabase Storage (bucket `community-images`), trả về URL công khai.
- **Ánh xạ category**: frontend dùng nhãn dài (vd "Văn hóa Chăm") trong khi ràng
  buộc CHECK của DB dùng nhãn ngắn (vd "Văn hóa"); backend tự dịch hai chiều.

## Cấu hình `.env`

Sao chép `.env.example` → `.env` và điền thông tin Supabase. **Không commit `.env`.**

| Biến | Ý nghĩa |
| --- | --- |
| `SECRET_KEY` | ≥32 ký tự; dẫn xuất khóa mã hóa phiên. |
| `SUPABASE_URL`, `SUPABASE_PROJECT_REF` | Project URL / ref. |
| `SUPABASE_SERVICE_ROLE_KEY` | Khóa service-role (chỉ dùng phía server, tối mật). |
| `SUPABASE_DB_PASSWORD` | Mật khẩu database. |
| `DATABASE_URL` | Chuỗi kết nối psycopg. Khuyến nghị **Session Pooler (IPv4)**: `host=aws-0-<region>.pooler.supabase.com port=5432 dbname=postgres user=postgres.<ref> password=... sslmode=require`. Nếu để trống sẽ tự suy ra kết nối trực tiếp `db.<ref>.supabase.co` (có thể chỉ có IPv6). |
| `SUPABASE_STORAGE_BUCKET` | Mặc định `community-images`. |
| `SESSION_SECURE` | `true` khi chạy HTTPS. |
| `FRONTEND_ORIGINS` | Origin công khai bổ sung (cùng origin luôn được chấp nhận). |

## Chạy dự án

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env               # rồi điền thông tin Supabase
python seed.py                        # tùy chọn: tạo user + bài viết demo
python run.py                         # http://127.0.0.1:8000
```

> Lưu ý Windows: psycopg (async) không chạy trên ProactorEventLoop, nên `run.py`
> và `seed.py` tự đặt `WindowsSelectorEventLoopPolicy`.

Mở <http://127.0.0.1:8000/>. Tài khoản demo (sau `seed.py`): `minhanh@gmail.com` / `123Aa`.

## Kiểm thử

```powershell
python run.py            # terminal 1
python verify.py         # terminal 2 — 39 kiểm thử đầu-cuối trên Supabase thật
```
`verify.py` tạo tài khoản + bài viết tạm để kiểm tra rồi **tự dọn sạch** dữ liệu
đó (xóa bài viết test và user auth tạm) để không làm bẩn project.

## Đưa API ra ngoài (tóm tắt)

Cùng origin nên frontend + API dùng chung URL. Để công khai:
1. Deploy lên máy chủ công khai (VPS / Render / Railway / Fly.io) có HTTPS, đặt
   `SESSION_SECURE=true`, `SECRET_KEY` mạnh, `FRONTEND_ORIGINS` nếu cần.
2. Hoặc demo nhanh: tunnel (`cloudflared tunnel --url http://127.0.0.1:8000`) và
   thêm URL tunnel vào `FRONTEND_ORIGINS`.
Vì dữ liệu đã ở Supabase (cloud) nên có thể chạy nhiều bản/scale ngang; chỉ cần
đổi rate-limit sang Redis khi chạy >1 tiến trình.

## ⚠️ Bảo mật

- `.env` và file `../Van_hoa_Cham_Database.docx` chứa **service-role key + mật
  khẩu DB thật** — tuyệt đối không commit lên git. Nên **rotate lại** service key
  trong Supabase vì nó đã từng lộ ra ngoài.
