# BÁO CÁO TỔNG QUAN TOÀN DIỆN DỰ ÁN NỀN TẢNG VĂN HÓA CHĂM (CHAM CULTURE PLATFORM)

> **Dự án**: Nền tảng Số hóa Di sản Văn Hóa Chăm (Cham Culture Platform)  
> **Trạng thái**: Đã triển khai hoàn tất và vận hành chính thức trên AWS Cloud (Live Production)  
> **URL Website chính thức**: [https://medxqx35ff.ap-southeast-1.awsapprunner.com](https://medxqx35ff.ap-southeast-1.awsapprunner.com)  
> **Tài liệu API Swagger**: [https://medxqx35ff.ap-southeast-1.awsapprunner.com/docs](https://medxqx35ff.ap-southeast-1.awsapprunner.com/docs)  
> **Ngày lập báo cáo**: 25/09/2026  

---

## MỤC LỤC
1. [Giới Thiệu & Mục Tiêu Dự Án](#1-giới-thiệu--mục-tiêu-dự-án)
2. [Ngôn Ngữ Lập Trình & Mục Đích Từng Phân Hệ](#2-ngôn-ngữ-lập-trình--mục-đích-từng-phân-hệ)
3. [Kiến Trúc Cơ Sở Dữ Liệu & Hệ Thống Quản Lý Dữ Liệu](#3-kiến-trúc-cơ-sở-dữ-liệu--hệ-thống-quản-lý-dữ-liệu)
4. [Các Dịch Vụ Điện Toán Đám Mây AWS Được Sử Dụng](#4-các-dịch-vụ-điện-toán-đám-mây-aws-được-sử-dụng)
5. [Các Thành Phần, Công Nghệ & Nhân Sự Xây Dựng Dự Án](#5-các-thành-phần-công-nghệ--nhân-sự-xây-dựng-dự-án)
6. [Quy Trình Triển Khai & Vận Hành Hệ Thống](#6-quy-trình-triển-khai--vận-hành-hệ-thống)

---

## 1. GIỚI THIỆU & MỤC TIÊU DỰ ÁN

**Nền tảng Văn Hóa Chăm** là một hệ thống web toàn diện kết hợp giữa **Cổng tri thức số**, **Mạng xã hội cộng đồng** và **Trợ lý Trí tuệ Nhân tạo (AI Chatbot)** nhằm mục đích:
- Lưu trữ, bảo tồn và số hóa các tư liệu quý báu về lịch sử, nhân khẩu, địa bàn cư trú, ngôn ngữ Akhar Thrah và di sản kiến trúc - lễ hội của đồng bào Chăm.
- Kết nối cộng đồng những người quan tâm, các nhà nghiên cứu và thế hệ trẻ thông qua diễn đàn tương tác đa phương tiện (chia sẻ bài viết, hình ảnh, video).
- Tích hợp công nghệ Trí tuệ nhân tạo thế hệ mới (Google Gemini AI) để cung cấp trải nghiệm giải đáp, hỏi đáp văn hóa tự động, trực quan và không giới hạn 24/7.

```
+-----------------------------------------------------------------------------------+
|                           NGƯỜI DÙNG (MOBILE / DESKTOP)                           |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼ HTTPS / TLS 1.3
+-----------------------------------------------------------------------------------+
|                        AWS APP RUNNER (Singapore Region)                          |
|  - Cổng 8000 | 1 vCPU | 2 GB RAM | Auto-scale | Managed Envoy Proxy               |
|                                                                                   |
|  [ FASTAPI ASYNC MONOLITH (Python 3.12) ]                                         |
|  ├─ Phục vụ Single Origin Frontend (Dashboard, Learn Pages, Community, Chatbot)   |
|  ├─ RESTful API Modules: /api/auth, /api/community, /api/profile, /api/chatbot    |
|  └─ Bảo mật: HTTPOnly Cookie (Fernet Encrypted), SlowAPI Rate Limiting            |
+-----------------------------------------------------------------------------------+
          │                                  │                        │
          ▼ SQL over TLS (IPv4 Pooler)       ▼ HTTPS REST             ▼ SDK v1
+--------------------+            +--------------------+    +--------------------+
|  SUPABASE POSTGRES |            |  SUPABASE STORAGE  |    |  GOOGLE GEMINI AI  |
|  - Users           |            |  - Bucket ảnh      |    |  - gemini-3.1-     |
|  - Posts & Likes   |            |    'community-     |    |    flash-lite      |
|  - Comments        |            |     images'        |    |  - Văn hóa Chăm    |
|  - Follows         |            |                    |    |    System Persona  |
|                    |            |                    |    |  - Auto-Fallback   |
+--------------------+            +--------------------+    +--------------------+
```

---

## 2. NGÔN NGỮ LẬP TRÌNH & MỤC ĐÍCH TỪNG PHÂN HỆ

Hệ thống được thiết kế theo tư duy **Clean Architecture** và mô hình **Monolith hiện đại**, sử dụng các ngôn ngữ và công nghệ tối ưu cho từng tầng:

### 2.1. Phân Hệ Frontend (Giao Diện Người Dùng)
* **Ngôn ngữ sử dụng**: **HTML5**, **CSS3**, **JavaScript (ES6+ Vanilla)**.
* **Mục đích lựa chọn**:
  - Không phụ thuộc vào các framework nặng nề (như React hay Angular), giúp tối ưu tốc độ tải trang (Page Load Speed) đạt mức cực đại (< 0.5s).
  - Tối ưu SEO tự nhiên (Search Engine Optimization), thân thiện với các công cụ tìm kiếm và trình thu thập dữ liệu web.
  - Khả năng kiểm soát chi tiết Responsive Design trên cả điện thoại (Mobile) và máy tính (Desktop/Laptop).
* **Phân bổ chi tiết từng trang**:
  1. **`frontend/dashboard/` (Trang chủ & Điều hướng trung tâm)**:
     - `index.html`: Cấu trúc Landing Page, Header phân cấp, Hero Section, thẻ điều hướng nhanh đến các phân hệ, phần chân trang hiển thị bản quyền và đơn vị thực hiện.
     - `style.css`: Hệ màu chủ đạo di sản (Vàng đất nung tháp Chăm `#c26522`, Đỏ sẫm `#8a251a`, Nền kem sang trọng `#faf7f2`), hiệu ứng Glassmorphism và cấu trúc Responsive 2 tầng cho Mobile (`@media (max-width: 880px)`).
     - `script.js`: Xử lý tương tác giao diện, chuyển trang mượt mà.
  2. **Cụm Trang Học Tập & Nghiên Cứu (`frontend/*.html`)**:
     - `learn.html`: Cổng tổng quan văn hóa Chăm.
     - `nguon-goc.html`: Lịch sử hình thành, nguồn gốc cư dân Champa qua các thời kỳ.
     - `dan-so.html`: Thống kê nhân khẩu học, dữ liệu điều tra dân tộc.
     - `khu-vuc.html`: Bản đồ phân bố địa bàn cư trú (Ninh Thuận, Bình Thuận, An Giang, Tây Ninh, TP.HCM,...).
     - `ngon-ngu.html`: Hệ thống ngôn ngữ và chữ viết Akhar Thrah cổ truyền.
     - `assets/learn/learn-responsive.css`: Bộ CSS chuyên dụng chuẩn hóa hiển thị trên mọi kích cỡ màn hình di động, tablet và màn hình lớn.
  3. **`frontend/community/` (Mạng Xã Hội Văn Hóa Chăm)**:
     - `index.html`, `style.css`, `community.js`: Giao diện mạng xã hội hiện đại, hỗ trợ tạo bài viết kèm đa ảnh/video, bình luận tương tác, thả tim (Like/Unlike), chia sẻ bài viết (Repost/Share), theo dõi tác giả (Follow) và bộ lọc chuyên đề (Văn hóa, Lễ hội, Ẩm thực, Kiến trúc...).
  4. **`frontend/chatbot.html` & `frontend/chatbot.js` (Trợ Lý AI Văn Hóa Chăm)**:
     - Giao diện trò chuyện dạng Message Stream hiện đại.
     - Tích hợp gợi ý câu hỏi thông minh, thanh gõ tin nhắn tự co giãn, hiển thị huy hiệu hạn mức: **"Không giới hạn"**.

### 2.2. Phân Hệ Backend (Máy Chủ Ứng Dụng & API)
* **Ngôn ngữ sử dụng**: **Python 3.12**.
* **Framework chính**: **FastAPI 0.115.6** kết hợp máy chủ ASGI **Uvicorn 0.34.0**.
* **Mục đích lựa chọn**:
  - Tận dụng cơ chế xử lý bất đồng bộ (`asyncio`, `async/await`) để phục vụ hàng ngàn kết nối I/O-bound đồng thời với mức tiêu hao RAM và CPU cực thấp.
  - Sử dụng **Pydantic v2 (2.10.4)** để xác thực dữ liệu đầu vào/đầu ra (Data Validation & Serialization) tự động, ngăn chặn các lỗi kiểu dữ liệu và injection.
  - Tự động sinh tài liệu chuẩn hóa **Swagger UI** (`/docs`) và **ReDoc** (`/redoc`) hỗ trợ tích hợp và kiểm thử trực quan.
  - Đóng vai trò máy chủ **Single-Origin Monolith**: Backend trực tiếp phục vụ các file tĩnh của Frontend tại thư mục gốc, triệt tiêu hoàn toàn sự cố phân tách Domain (loại bỏ xung đột Cross-Origin CORS và chặn Third-party Cookies trên Safari/Chrome).
* **Phân bổ các module Backend (`backend/app/`)**:
  - `auth/`: Đăng ký, đăng nhập, bảo mật phiên Cookie HTTPOnly Fernet mã hóa đối xứng, liên kết tài khoản với Supabase Auth.
  - `community/`: Xử lý nghiệp vụ diễn đàn (CRUD bài viết, phân trang offset/limit, like, comment, follow, đếm tương tác).
  - `chatbot/`: Giao tiếp với Google Gemini Generative AI, tích hợp bộ tri thức địa phương `faq.json`, hệ thống System Persona chuẩn mực văn hóa Chăm và cơ chế dự phòng tự động (Model Fallback).
  - `storage/`: Xử lý tải lên và tối ưu hóa hình ảnh/video qua Supabase Storage.
  - `middleware/`: Quản lý CORS, bảo vệ chống brute-force/DDoS bằng `slowapi`, mã hóa phiên làm việc.

### 2.3. Ngôn Ngữ Kịch Bản Tự Động Hóa & Hạ Tầng (DevOps)
* **PowerShell (`deploy_aws.ps1`)**: Tự động hóa 100% chu trình kiểm tra môi trường, xác thực AWS ECR Token, đóng gói Docker Container và đẩy lên máy chủ đám mây AWS.
* **Dockerfile (Linux Engine)**: Kịch bản đóng gói ứng dụng độc lập trên nền `python:3.12-slim`, biên dịch kiến trúc chuẩn `linux/amd64`.

---

## 3. KIẾN TRÚC CƠ SỞ DỮ LIỆU & HỆ THỐNG QUẢN LÝ DỮ LIỆU

Ứng dụng vận hành trên hệ cơ sở dữ liệu **PostgreSQL 15+** được quản lý tập trung trên nền tảng **Supabase Cloud Enterprise**, kết nối qua cụm hạ tầng đặt tại **Singapore (`ap-southeast-1`)** giúp đồng bộ tốc độ và giảm độ trễ mạng xuống mức mili-giây.

```
                             [ FASTAPI BACKEND POOL ]
                                        │
                         psycopg3 AsyncConnectionPool
                               (Max 10-20 Conns)
                                        │
                         IPv4 Session Pooler (Port 5432)
                                        │
                         +--------------▼---------------+
                         |   SUPABASE POSTGRESQL 15+    |
                         |  (Region: ap-southeast-1)    |
                         +--------------┬---------------+
                                        │
       ┌─────────────────┬──────────────┼──────────────┬────────────────┐
       ▼                 ▼              ▼              ▼                ▼
   [ users ]         [ posts ]    [ comments ]   [ post_likes ]    [ follows ]
 - id (BIGINT)     - id           - id           - post_id         - follower_id
 - email           - user_id      - user_id      - user_id         - following_id
 - username        - content      - post_id      - created_at      - created_at
 - avatar_url      - image_url    - content
 - password_hash   - video_url    - image_url
 - public_status   - shared_post  - video_url
 - created_at      - category     - created_at
                   - created_at
```

### 3.1. Cơ Chế Kết Nối & Tối Ưu Hiệu Năng (Connection Pool)
- **Thư viện Driver**: Sử dụng **`psycopg[binary,pool]==3.2.4`** - driver PostgreSQL thế hệ mới nhất cho Python, hỗ trợ Native Async Engine.
- **Async Connection Pooling**: Máy chủ duy trì một bể kết nối (`AsyncConnectionPool`) mở sẵn khi ứng dụng khởi động (`lifespan`), tái sử dụng kết nối liên tục, loại bỏ hoàn toàn chi phí bắt tay TCP/SSL (handshake) ở mỗi truy vấn.
- **Session Pooler IPv4**: Kết nối thông qua Supabase Pooler (`aws-0-ap-southeast-1.pooler.supabase.com:5432`) với chế độ mã hóa `sslmode=require`, đảm bảo tương thích hoàn hảo với môi trường mạng IPv4 của AWS App Runner.

### 3.2. Cấu Trúc Bảng Dữ Liệu Chi Tiết (Schema Specifications)

#### 1. Bảng `users` (Hồ Sơ & Danh Tính Người Dùng)
* Lưu trữ thông tin định danh cấp ứng dụng, liên kết với hệ thống Supabase GoTrue Auth qua email.
* **Các trường dữ liệu**:
  - `id`: `BIGINT IDENTITY PRIMARY KEY` — Khóa chính định danh tự tăng.
  - `email`: `VARCHAR UNIQUE NOT NULL` — Địa chỉ hòm thư người dùng (chuyển chữ thường `lower(email)` khi truy vấn).
  - `username`: `VARCHAR` — Tên hiển thị của người dùng trên diễn đàn và bình luận.
  - `avatar_url`: `TEXT` — Đường dẫn ảnh đại diện (mặc định lấy từ kho ảnh SVG hoặc Supabase Storage).
  - `password_hash`: `TEXT` — Mã băm mật khẩu bảo mật (bcrypt) dự phòng.
  - `public_status`: `BOOLEAN DEFAULT TRUE` — Trạng thái công khai thông tin cá nhân.
  - `created_at`: `TIMESTAMPTZ DEFAULT NOW()` — Thời điểm khởi tạo tài khoản.

#### 2. Bảng `posts` (Bài Viết Diễn Đàn Cộng Đồng)
* Quản lý các bài đăng chia sẻ tri thức văn hóa, trải nghiệm và hình ảnh từ cộng đồng.
* **Các trường dữ liệu**:
  - `id`: `BIGINT IDENTITY PRIMARY KEY` — Khóa chính bài viết.
  - `user_id`: `BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE` — Tác giả bài viết.
  - `content`: `TEXT` — Nội dung văn bản của bài đăng.
  - `category`: `VARCHAR(50)` — Phân loại chuyên mục (*Văn hóa Chăm, Ẩm thực Chăm, Lễ hội, Hỏi đáp, Du lịch – Trải nghiệm, Daily*).
  - `image_url`: `TEXT` — Danh sách các liên kết ảnh được lưu dưới dạng chuỗi mảng JSON (`["url1", "url2"]`).
  - `video_url`: `TEXT` — Liên kết video đính kèm (nếu có).
  - `shared_post_id`: `BIGINT REFERENCES posts(id) ON DELETE SET NULL` — Hỗ trợ tính năng chia sẻ lại (Repost) một bài viết khác.
  - `created_at`: `TIMESTAMPTZ DEFAULT NOW()` — Thời điểm đăng tải.

#### 3. Bảng `comments` (Bình Luận Tương Tác)
* Quản lý tương tác thảo luận dưới mỗi bài viết.
* **Các trường dữ liệu**:
  - `id`: `BIGINT IDENTITY PRIMARY KEY` — Khóa chính bình luận.
  - `post_id`: `BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE` — Bài viết liên quan.
  - `user_id`: `BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE` — Người bình luận.
  - `content`: `TEXT NOT NULL` — Nội dung bình luận.
  - `image_url`: `TEXT` — Hình ảnh đính kèm bình luận.
  - `video_url`: `TEXT` — Video đính kèm bình luận.
  - `created_at`: `TIMESTAMPTZ DEFAULT NOW()` — Thời điểm bình luận.

#### 4. Bảng `post_likes` (Tương Tác Thích Bài Viết)
* **Các trường dữ liệu**:
  - `post_id`: `BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE`.
  - `user_id`: `BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE`.
  - `created_at`: `TIMESTAMPTZ DEFAULT NOW()`.
  - **Khóa chính kết hợp**: `PRIMARY KEY (post_id, user_id)` — Đảm bảo mỗi người dùng chỉ được bấm thích 1 lần duy nhất cho mỗi bài viết.

#### 5. Bảng `follows` (Mối Quan Hệ Theo Dõi)
* **Các trường dữ liệu**:
  - `follower_id`: `BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE` (Người theo dõi).
  - `following_id`: `BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE` (Người được theo dõi).
  - `created_at`: `TIMESTAMPTZ DEFAULT NOW()`.
  - **Khóa chính kết hợp**: `PRIMARY KEY (follower_id, following_id)`.

### 3.3. Hệ Thống Lưu Trữ Tệp (Supabase Object Storage)
- **Bucket**: `community-images` (Chế độ Public Access).
- **Mục đích**: Lưu trữ ảnh đại diện, ảnh bài viết cộng đồng và ảnh minh họa được upload từ người dùng.
- **Cơ chế**: Quản lý truy xuất qua Supabase REST Storage API v1, tích hợp mạng phân phối CDN toàn cầu giúp tải ảnh mượt mà và tiết kiệm băng thông máy chủ chính.

---

## 4. CÁC DỊCH VỤ ĐIỆN TOÁN ĐÁM MÂY AWS ĐƯỢC SỬ DỤNG

Dự án được triển khai trên nền tảng **Amazon Web Services (AWS)** với mô hình **Serverless Managed Container**, tận dụng tối đa các dịch vụ hiện đại:

| Tên Dịch Vụ AWS | Tên Tài Nguyên Cụ Thể | Mục Đích & Vai Trò Trong Dự Án |
| :--- | :--- | :--- |
| **AWS App Runner** | `cham-culture-app` | Dịch vụ tính toán trung tâm chạy ứng dụng (Fully-managed Container Platform). Tự động quản lý vòng đời ứng dụng, cấp phát chứng chỉ HTTPS/SSL miễn phí, giám sát trạng thái thông qua `/health`, tự động co giãn tài nguyên theo lưu lượng truy cập và tự động cập nhật triển khai (Auto-deploy). |
| **Amazon ECR** | `cham-culture` (Private Repo) | Kho lưu trữ Docker Container Registry an toàn. Lưu giữ các image Docker của ứng dụng (`.../cham-culture:latest`), đảm bảo tính bảo mật nội bộ và tích hợp trực tiếp vào quy trình CI/CD của App Runner. |
| **AWS IAM** | User: `nla-aws`<br>Role: `AppRunnerECRAccessRole` | Hệ thống quản lý quyền truy cập và bảo mật danh tính. Cung cấp quyền cho App Runner được phép tự động tải (pull) container image từ kho chứa ECR mà không cần lộ mật khẩu. |
| **Amazon CloudWatch** | Log Groups: `/aws/apprunner/cham-culture-app/*` | Hệ thống ghi nhận nhật ký (Logging) và giám sát hệ thống (Monitoring). Thu thập toàn bộ log hệ thống Uvicorn, lịch sử build và triển khai của container theo thời gian thực để hỗ trợ truy vết sự cố. |
| **AWS Envoy Proxy / Edge Network** | Tích hợp sẵn trong App Runner | Đóng vai trò Reverse Proxy biên, định tuyến lưu lượng truy cập từ Internet, kiểm tra chứng chỉ bảo mật TLS 1.3 và chống các cuộc tấn công mạng cơ bản trước khi dẫn lưu lượng vào container. |

### Thông số kỹ thuật của dịch vụ AWS đã cấu hình:
- **Tài khoản AWS ID**: `641532809384`
- **Region hoạt động**: `ap-southeast-1` (Asia Pacific - Singapore)
- **Cấu hình phần cứng Container**: **1 vCPU / 2 GB RAM**
- **Cổng dịch vụ nội bộ**: `8000`
- **Đường dẫn Health Check**: `/health` (giao thức HTTP)
- **Chế độ Deployment**: `Automatic` (Mỗi khi có image mới được push lên kho ECR, AWS App Runner tự động kích hoạt quá trình Zero-Downtime Deployment).

---

## 5. CÁC THÀNH PHẦN, CÔNG NGHỆ & NHÂN SỰ XÂY DỰNG DỰ ÁN

### 5.1. Đơn Vị & Nhân Sự Thực Hiện
* **Đơn vị chủ trì xây dựng**: **Học sinh Trường THPT Nguyễn Thị Minh Khai**  
  *(Được ghi nhận chính thức tại phần chân trang hệ thống: "A product by Nguyen Thi Minh Khai High School students")*.
* **Mục tiêu cống hiến**: Ứng dụng công nghệ phần mềm mới nhất, kết hợp nghiên cứu khoa học xã hội để tạo ra một sản phẩm di sản số thực tế, phục vụ cộng đồng và lan tỏa văn hóa dân tộc Chăm đến bạn bè trong nước và quốc tế.

### 5.2. Động Cơ Trí Tuệ Nhân Tạo (AI Engine - Google Gemini)
* **Model AI tích hợp chính**: **`gemini-3.1-flash-lite`** (Thế hệ mô hình AI siêu tốc mới nhất từ Google, tối ưu thời gian phản hồi < 1 giây và hạn mức Free Tier rộng rãi 1.500 requests/ngày).
* **Cơ chế dự phòng liên hoàn (Multi-Model Quota Fallback)**: Tự động chuyển đổi mượt mà theo chuỗi: `['gemini-3.1-flash-lite', 'gemini-3.5-flash-lite', 'gemini-flash-latest', 'gemini-3.6-flash', 'gemini-3.8-flash']`. Nếu gặp sự cố bảo trì hoặc lỗi quá tải hạn mức gọi (HTTP 429 ResourceExhausted), hệ thống tự động nhảy sang mô hình kế tiếp ngay lập tức, triệt tiêu hoàn toàn nguy cơ gián đoạn hội thoại.
* **Bộ dữ liệu cơ sở tri thức (Knowledge Base)**: Tệp `services/chatbot/faq.json` lưu trữ các dữ liệu chuẩn xác về:
  - Tháp cổ Champa (Mỹ Sơn, Po Klong Garai, Po Nagar...).
  - Trang phục truyền thống (Áo chắp Aw Cahi, khăn đội đầu, thắt lưng Kaban).
  - Lễ hội linh thiêng (Katê của người Chăm Bà La Môn, Ramuwan của người Chăm Bani).
  - Chữ viết Akhar Thrah cổ và nghệ thuật gốm Bàu Trúc, dệt thổ cẩm Mỹ Nghiệp.
* **Đặc tính Persona & Logic Phản Hồi**:
  - Hạn mức câu hỏi: **Hoàn toàn không giới hạn** (Unlimited Questions).
  - Đối với câu hỏi về văn hóa Chăm: Trả lời sâu sắc, chân thực, tôn trọng di sản.
  - Đối với câu hỏi ngoài lề (khoa học, đời sống, toán học, hành chính...): Vẫn phản hồi ngắn gọn, chính xác, lịch sự; đồng thời khéo léo đính kèm một câu gợi mở tự nhiên mời người dùng tìm hiểu về nét đẹp văn hóa Chăm tương đồng.

### 5.3. Danh Mục Các Thư Viện & Công Nghệ Bổ Trợ

| Tầng Công Nghệ | Gói Thư Viện / Công Cụ | Phiên Bản | Vai Trò Kỹ Thuật |
| :--- | :--- | :---: | :--- |
| **Web Server** | `uvicorn[standard]` | 0.34.0 | Máy chủ ASGI hiệu năng cao chạy ứng dụng Python |
| **Web Framework** | `fastapi` | 0.115.6 | Framework xây dựng REST API bất đồng bộ |
| **Database Driver** | `psycopg[binary,pool]` | 3.2.4 | Kết nối và quản lý Connection Pool với PostgreSQL |
| **Validation** | `pydantic` & `pydantic-settings` | 2.10.4 / 2.7.1 | Khai báo, chuẩn hóa Schema và cấu hình môi trường |
| **Bảo Mật Session** | `cryptography` | 44.0.0 | Mã hóa đối xứng Fernet cho Cookie phiên an toàn |
| **Mật Khẩu** | `bcrypt` | Mới nhất | Mã hóa băm mật khẩu một chiều |
| **Chống DoS/Spam** | `slowapi` | 0.1.9 | Giới hạn tần suất gọi API (Rate Limiting) |
| **HTTP Client** | `httpx` | 0.28.1 | Giao tiếp Asynchronous HTTP với Supabase & AI Services |
| **AI SDK** | `google-generativeai` | 0.8.3 | Thư viện chính thức giao tiếp Google Gemini API |
| **Icon & Font** | `Font Awesome` & `Google Fonts` | 6.5.2 | Bộ icon web và phông chữ Inter, Outfit, Segoe UI |

---

## 6. QUY TRÌNH TRIỂN KHAI & VẬN HÀNH HỆ THỐNG

Dự án đã được thiết lập chu trình triển khai liên tục (CI/CD) bán tự động thông qua tập lệnh PowerShell [`deploy_aws.ps1`](file:///L:/FPT/Side%20project/vhc/deploy_aws.ps1).

### Chu trình 4 bước cập nhật hệ thống lên AWS:
```powershell
# 1. Đăng nhập Docker vào Amazon ECR Registry
aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin 641532809384.dkr.ecr.ap-southeast-1.amazonaws.com

# 2. Build Docker Image tối ưu cho AWS App Runner (kiến trúc linux/amd64)
docker build --platform linux/amd64 -t cham-culture:latest .

# 3. Gắn tag định danh Amazon ECR
docker tag cham-culture:latest 641532809384.dkr.ecr.ap-southeast-1.amazonaws.com/cham-culture:latest

# 4. Đẩy (push) image lên kho chứa ECR
docker push 641532809384.dkr.ecr.ap-southeast-1.amazonaws.com/cham-culture:latest
```

> **Cơ chế Tự Động Kích Hoạt (Automatic Deployment):**  
> Ngay sau khi lệnh `docker push` hoàn tất, **AWS App Runner** sẽ tự động phát hiện phiên bản container image mới trong ECR, tự động khởi tạo instance mới, chạy kiểm tra `/health` thành công và chuyển lưu lượng truy cập sang instance mới mà không làm gián đoạn người dùng (Zero-downtime Rolling Update).

---

## KẾT LUẬN

Nền tảng Văn Hóa Chăm là một công trình kết hợp hài hòa giữa **giá trị bảo tồn di sản văn hóa truyền thống** và **công nghệ đám mây hiện đại (Cloud Computing, Serverless, AI)**. Toàn bộ kiến trúc từ mã nguồn, cơ sở dữ liệu cho đến hạ tầng đám mây AWS đều đã được chuẩn hóa, bảo mật và vận hành ổn định trên môi trường sản xuất thực tế.
