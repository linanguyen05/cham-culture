# Triển khai công khai (Option B) — Render + Docker

Đưa backend (kèm frontend, cùng origin) lên một URL công khai, luôn online. Dữ
liệu vẫn dùng Supabase đang có, không cần dựng thêm DB.

Đã có sẵn trong repo:
- `Dockerfile` — đóng gói backend + frontend.
- `.dockerignore` — loại `node_modules`, `.venv`, `.env`, `legacy/`, `services/`…
- `render.yaml` — cấu hình sẵn dịch vụ web Docker cho Render.

---

## Bước 1 — Đưa code lên GitHub
Render deploy từ một repo Git. Tạo repo (private nên tốt hơn vì có cấu hình nhạy cảm)
và push nhánh `main`.

```powershell
cd "l:\FPT\Side project\vhc"
git add Dockerfile .dockerignore render.yaml backend/ frontend/ README.md HANDOVER.md DEPLOY.md .gitignore
git commit -m "Deploy: Docker + Render blueprint cho backend hợp nhất"
git push -u origin main
```
> Kiểm tra `git status` chắc chắn KHÔNG có `backend/.env` và `Van_hoa_Cham_Database.docx`
> trong danh sách (đã được `.gitignore`). Tuyệt đối không đẩy secret lên repo.

## Bước 2 — Tạo dịch vụ trên Render
1. Đăng nhập <https://render.com> → **New +** → **Blueprint**.
2. Kết nối GitHub và chọn repo vừa push. Render tự đọc `render.yaml`.
3. Render hỏi giá trị cho các biến `sync:false` → nhập đúng giá trị lấy từ
   `backend/.env` (xem bảng dưới).
4. Bấm **Apply** → Render build Docker image và deploy. Xong sẽ có URL dạng
   `https://cham-culture.onrender.com`.

## Bước 3 — Biến môi trường cần nhập trên Render
(Các biến không nhạy cảm đã set sẵn trong `render.yaml`; `SECRET_KEY` được Render
tự sinh. Chỉ cần nhập các biến bí mật sau — copy từ `backend/.env`.)

| Biến | Giá trị (lấy trong backend/.env) |
| --- | --- |
| `SUPABASE_URL` | `https://<ref>.supabase.co` |
| `SUPABASE_PROJECT_REF` | `<ref>` |
| `SUPABASE_SERVICE_ROLE_KEY` | `sb_secret_...` |
| `SUPABASE_DB_PASSWORD` | mật khẩu DB |
| `DATABASE_URL` | chuỗi Session Pooler (xem bên dưới) |

`DATABASE_URL` nên dùng **Session Pooler (IPv4)** cho ổn định:
```
host=aws-0-ap-southeast-1.pooler.supabase.com port=5432 dbname=postgres user=postgres.<ref> password=<db-password> sslmode=require
```
(Đây chính là giá trị đang có trong `backend/.env`.)

## Bước 4 — Kiểm tra sau khi deploy
- `https://<app>.onrender.com/health` → `{"status":"ok"}`
- Mở `https://<app>.onrender.com/` → đăng nhập `minhanh@gmail.com` / `123Aa`
- Vào **Cộng đồng** → xem feed, đăng bài, thích, bình luận.
- Tài liệu API: `https://<app>.onrender.com/docs`

## Ghi chú
- **Cùng origin:** frontend và API dùng chung tên miền Render nên KHÔNG cần
  `FRONTEND_ORIGINS`. Chỉ set biến này nếu sau đó bạn tách frontend sang domain khác,
  hoặc có bên thứ ba gọi API từ web khác.
- **HTTPS + cookie:** Render cấp HTTPS sẵn; đã đặt `SESSION_SECURE=true` nên cookie
  phiên an toàn.
- **Supabase:** không cần cấu hình redirect/OAuth vì đăng nhập xử lý phía server
  (admin create + password grant). Bucket `community-images` sẽ tự tạo nếu chưa có.
- **Gói Free của Render** sẽ "ngủ" sau ~15 phút không truy cập (lần gọi kế tiếp bị
  chờ khởi động lại vài giây). Muốn luôn sẵn sàng thì nâng lên gói trả phí.
- **Scale nhiều tiến trình:** đổi `RATE_LIMIT_STORAGE_URI` sang Redis (vd Upstash)
  để đếm rate-limit dùng chung; phần còn lại đã sẵn sàng scale ngang.

## Nền tảng khác (tương đương)
- **Railway:** New Project → Deploy from Repo → nó nhận `Dockerfile`; thêm cùng bộ
  biến môi trường; Railway tự cấp `PORT` và domain.
- **Fly.io:** `fly launch` (dùng `Dockerfile`), `fly secrets set KEY=...` cho các biến,
  `fly deploy`.

## ⚠️ Bảo mật
`SUPABASE_SERVICE_ROLE_KEY` toàn quyền bỏ qua RLS. Vì key này đã từng lộ (trong
`Van_hoa_Cham_Database.docx`), **nên rotate lại** trong Supabase rồi mới cập nhật
biến môi trường trên Render.
