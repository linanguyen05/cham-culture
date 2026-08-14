# Chăm Culture (vhc)

## 1. Tình trạng source code

### Cấu trúc thư mục (đã dọn lại)
```
vhc/
├─ backend/        ← MỘT backend hợp nhất, chuyên nghiệp, CHẠY ĐƯỢC (FastAPI + SQLite)
├─ frontend/       ← Giao diện SPA chuẩn (KHÔNG chỉnh sửa; chỉ bổ sung 2 file còn thiếu)
├─ services/
│  ├─ chatbot/     ← App chatbot Gemini (Flask, độc lập) — trước là Chatbox/
│  └─ learn/       ← Nội dung "Tìm hiểu" (Flask, độc lập) — trước là Timhieudantoccham/
├─ legacy/         ← Lưu trữ code cũ/trùng lặp, KHÔNG xóa (6 backend cũ, trang Jinja cũ...)
└─ HANDOVER.md
```

### Backend 
- Gộp 6 backend rải rác thành **một** dịch vụ FastAPI duy nhất, kiến trúc phân
  lớp: `routes → service → repository`.
- Chạy hoàn toàn cục bộ: **SQLite** (dữ liệu) + **ổ đĩa cục bộ** (ảnh), không cần
  cloud/Supabase.
- Có sẵn: xác thực bằng phiên (cookie mã hóa), băm mật khẩu PBKDF2, kiểm tra dữ
  liệu, giới hạn tần suất, chống CSRF/origin, tài liệu API tự sinh tại `/docs`.
- Backend phục vụ luôn frontend cùng origin nên khớp sẵn với code frontend.

### Tình trạng tính năng
| Tính năng | Trạng thái |
| --- | --- |
| Đăng ký / Đăng nhập / Hồ sơ | ✅ Hoạt động (API + phiên đăng nhập) |
| Trang chủ (dashboard) | ✅ Hoạt động |
| Cộng đồng (feed, đăng bài, ảnh, thích, bình luận, chia sẻ, thống kê, hồ sơ) | ✅ Hoạt động đầy đủ |
| **Tìm hiểu** | ⛔ Chưa nối — link nav đang để `href="#"`; nội dung nằm ở `services/learn` (app Flask riêng) |
| **Chatbot** | ⛔ Chưa nối — link nav đang để `href="#"`; app nằm ở `services/chatbot` (Flask riêng, cần `GEMINI_API_KEY`) |

> Lý do "Tìm hiểu"/"Chatbot" chưa chạy: yêu cầu là **không sửa frontend**, mà
> frontend đang để link `#`. Chúng là 2 app Flask độc lập; muốn tích hợp cần
> quyết định: cho phép sửa nav frontend, và hợp nhất/định tuyến 2 dịch vụ này vào
> backend chính (hoặc chạy song song sau reverse proxy).

### Kiểm thử
- `backend/verify.py`: **42/42 PASS** (đăng ký → hồ sơ → phiên, đăng nhập/xuất,
  feed + lọc + sắp xếp, đăng bài kèm ảnh, thích, bình luận, chia sẻ, thống kê,
  quyền riêng tư hồ sơ, chống CSRF, phục vụ trang tĩnh).

---

## 2. Hướng dẫn chạy khi cần demo

```powershell
cd "l:\FPT\Side project\vhc\backend"
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python seed.py        # tạo dữ liệu demo (chạy 1 lần)
python run.py         # mở http://127.0.0.1:8000
```

- Mở trình duyệt: <http://127.0.0.1:8000/>
- **Tài khoản demo:** `minhanh@gmail.com` / `123Aa`
- Luồng demo: Đăng nhập → Trang chủ → bấm **Cộng đồng** → xem feed, đăng bài
  (kèm ảnh), thích, bình luận, chia sẻ, mở hồ sơ.
- Tài liệu API (thử endpoint trực tiếp): <http://127.0.0.1:8000/docs>
- Kiểm thử tự động: mở terminal thứ hai, chạy `python verify.py`.

> Lưu ý: `123Aa` chỉ tạo được qua `seed.py` (đăng ký qua web yêu cầu mật khẩu
> ≥ 8 ký tự). Đăng nhập bằng tài khoản này vẫn bình thường.

---

## 3. Người dùng cuối đã dùng được chưa?

**Chưa — mới chạy được trên local.** Cần làm rõ hiểu lầm quan trọng:

> `http://127.0.0.1:8000/` là địa chỉ **loopback** — chỉ chính máy đang chạy
> server mới truy cập được. Dán link này cho người khác sẽ **không mở được**,
> vì `127.0.0.1` trên máy họ trỏ về chính máy họ, không phải máy bạn.

API đã "xuất" (đã có endpoint + tài liệu `/docs`), nhưng để người ngoài dùng thật
còn cần:

1. **Đưa lên một máy chủ có địa chỉ công khai** (VPS/hosting) và một **tên miền**.
2. **HTTPS** (chứng chỉ TLS, thường qua reverse proxy nginx/Caddy), rồi đặt
   `SESSION_SECURE=true`, `SECRET_KEY` mạnh, cấu hình `FRONTEND_ORIGINS` nếu
   frontend ở domain khác.
3. Nếu bên thứ ba gọi API bằng chương trình (không qua trình duyệt): bổ sung
   **xác thực bằng token/API key** (hiện đang dùng cookie-phiên cho trình duyệt).
4. Chạy production đúng cách: nhiều worker (uvicorn/gunicorn) sau reverse proxy.

### Khi có NHIỀU lượt truy cập đồng thời → hướng cloud
Bản chạy-local hiện tại có 3 giới hạn cần nâng cấp khi tải cao:
- **SQLite → PostgreSQL/Supabase** (nhiều người ghi đồng thời / chạy nhiều bản).
  Tầng `repository.py` đã tách riêng SQL nên đổi khá gọn.
- **Lưu ảnh cục bộ → object storage (S3/Supabase Storage) + CDN**.
- **Rate limit `memory://` → Redis** khi chạy hơn 1 bản.
- Phiên đăng nhập đã ở dạng cookie mã hóa (không giữ state server) nên **sẵn sàng
  scale ngang**.

Lộ trình theo quy mô: nhỏ → 1 VPS; vừa → Render/Railway/Fly.io (Docker);
lớn → AWS/GCP (Cloud Run/ECS + Postgres quản lý + S3 + Redis + load balancer,
autoscale).
