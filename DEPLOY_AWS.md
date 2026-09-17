# Hướng Dẫn Triển Khai AWS App Runner (Serverless Tối Giản)

Tài liệu này hướng dẫn chi tiết từng bước (Step-by-Step) đưa ứng dụng **Văn Hóa Chăm (FastAPI Monolith)** lên dịch vụ **AWS App Runner** kết hợp với **Amazon ECR**.

---

## 📌 Chuẩn Bị Trước Khi Thực Hiện

1. Đảm bảo **Docker Desktop** đang chạy trên máy tính.
2. Tài khoản AWS có quyền Administrator hoặc quyền với ECR & App Runner.
3. Thông tin cấu hình từ file `backend/.env`.

---

## BƯỚC 1: Cấu hình AWS CLI

Mở **PowerShell** trên máy tính và chạy lệnh:

```powershell
aws configure
```

Nhập các thông tin sau khi được hỏi:
* **AWS Access Key ID**: Nhập Access Key của bạn
* **AWS Secret Access Key**: Nhập Secret Access Key của bạn
* **Default region name**: `ap-southeast-1`
* **Default output format**: `json`

Kiểm tra kết nối thành công:
```powershell
aws sts get-caller-identity
```
*(Nếu hiển thị UserId và Account ID của bạn là đã kết nối thành công).*

---

## BƯỚC 2: Tạo Private Repository trên Amazon ECR

Chạy lệnh sau để tạo kho chứa Docker image:

```powershell
aws ecr create-repository --repository-name cham-culture --region ap-southeast-1
```

---

## BƯỚC 3: Đăng nhập Docker vào Amazon ECR

Lấy Account ID của bạn và thực hiện đăng nhập:

```powershell
$ACCOUNT_ID = (aws sts get-caller-identity --query "Account" --output text)
$REGION = "ap-southeast-1"
$ECR_URI = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI
```
*(Thông báo: `Login Succeeded`)*

---

## BƯỚC 4: Build và Push Docker Image lên ECR

Đứng tại thư mục gốc của dự án (`L:\FPT\Side project\vhc`):

```powershell
cd "L:\FPT\Side project\vhc"

# Build image cho kiến trúc linux/amd64 (tương thích AWS App Runner)
docker build --platform linux/amd64 -t cham-culture:latest .

# Gắn tag ECR
docker tag cham-culture:latest "$ECR_URI/cham-culture:latest"

# Đẩy image lên Amazon ECR
docker push "$ECR_URI/cham-culture:latest"
```

---

## BƯỚC 5: Tạo Dịch Vụ AWS App Runner

Bạn có thể tạo nhanh qua **Giao diện AWS Console** (Khuyên dùng vì rất trực quan) hoặc qua **AWS CLI**.

### Cách 1: Tạo trên AWS Management Console (Khuyên dùng)

1. Truy cập [AWS App Runner Console](https://ap-southeast-1.console.aws.amazon.com/apprunner/home?region=ap-southeast-1).
2. Nhấn nút **Create service**.
3. **Step 1: Source and deployment**:
   * **Source**: Chọn **Container registry**.
   * **Provider**: Chọn **Amazon ECR**.
   * **Container image URI**: Nhấn nút **Browse** và chọn repository `cham-culture:latest`.
   * **Deployment settings**:
     * Chọn **Automatic** (mỗi khi push image mới lên ECR, App Runner sẽ tự động deploy lại) hoặc **Manual**.
   * **ECR access role**:
     * Nếu chưa có role, chọn **Create new service role** (App Runner sẽ tự động tạo role tên `AppRunnerECRAccessRole`).
   * Nhấn **Next**.

4. **Step 2: Configure service**:
   * **Service name**: `cham-culture-app`
   * **Virtual CPU & Memory**: Chọn `1 vCPU` và `2 GB` (hoặc `0.25 vCPU` / `0.5 GB` nếu muốn tiết kiệm tối đa).
   * **Port**: Điền **`8000`** *(Rất quan trọng, ứng dụng Uvicorn chạy cổng 8000)*.
   * **Environment variables** (Nhấn *Add environment variable* và điền các cặp Key - Value lấy từ `backend/.env`):
     * `ENVIRONMENT` = `production`
     * `PORT` = `8000`
     * `SECRET_KEY` = `cham-culture-supabase-dev-secret-key-please-rotate-1234`
     * `SUPABASE_URL` = `https://tlifaxyjdtgsbxmlmonh.supabase.co`
     * `SUPABASE_PROJECT_REF` = `tlifaxyjdtgsbxmlmonh`
     * `SUPABASE_SERVICE_ROLE_KEY` = `<Copy từ backend/.env>`
     * `SUPABASE_DB_PASSWORD` = `<Copy từ backend/.env>`
     * `DATABASE_URL` = `host=aws-0-ap-southeast-1.pooler.supabase.com port=5432 dbname=postgres user=postgres.tlifaxyjdtgsbxmlmonh password=<mật_khẩu> sslmode=require`
     * `GEMINI_API_KEY` = `<Copy từ backend/.env>`
     * `SESSION_SECURE` = `true`
     * `SESSION_SAMESITE` = `lax`
   * **Health check**:
     * **Protocol**: `HTTP`
     * **Path**: `/health`
     * **Interval**: `10`
     * **Timeout**: `5`
     * **Healthy threshold**: `1`
     * **Unhealthy threshold**: `5`
   * Nhấn **Next**.

5. **Step 3: Review and create**:
   * Kiểm tra lại thông tin và nhấn **Create & deploy**.
   * App Runner sẽ tiến hành khởi tạo container trong khoảng 2 - 3 phút.

---

## BƯỚC 6: Kiểm Tra Sau Khi Triển Khai

Khi trạng thái dịch vụ chuyển sang màu xanh **Running**, App Runner sẽ cấp một đường link công khai dạng:
`https://<mã_ngẫu_nhiên>.ap-southeast-1.awsapprunner.com`

Kiểm tra các tính năng chính:
1. **Health Check**: Truy cập `https://<url>/health` → Kết quả trả về `{"status":"ok"}`.
2. **Giao diện Web**: Truy cập `https://<url>/` → Trang chủ Văn Hóa Chăm xuất hiện mượt mà.
3. **Đăng nhập**: Đăng nhập tài khoản test `minhanh@gmail.com` / `123Aa`.
4. **Cộng đồng**: Đăng bài viết, tải ảnh lên Supabase Storage, bấm like, bình luận.
5. **Chatbot Văn Hóa Chăm**: Mở khung chat và đặt câu hỏi để kiểm tra kết nối Google Gemini API.
6. **Tài liệu API Swagger**: Truy cập `https://<url>/docs`.

---

## 💡 Cập Nhật Ứng Dụng Trong Tương Lai

Mỗi khi bạn có sửa đổi code, chỉ cần chạy 3 lệnh sau để cập nhật:

```powershell
cd "L:\FPT\Side project\vhc"
docker build --platform linux/amd64 -t cham-culture:latest .
docker tag cham-culture:latest "$ECR_URI/cham-culture:latest"
docker push "$ECR_URI/cham-culture:latest"
```
*(Nếu đã bật Automatic Deployment ở Bước 5, App Runner sẽ tự động cập nhật bản mới nhất không gián đoạn dịch vụ).*
