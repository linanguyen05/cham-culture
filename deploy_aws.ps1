# Cham Culture — AWS ECR Build & Push Automation Script
# Usage: .\deploy_aws.ps1

$ErrorActionPreference = "Continue"

Write-Host "=== BƯỚC 1: KIỂM TRA AWS CREDENTIALS ===" -ForegroundColor Cyan
try {
    $callerJson = aws sts get-caller-identity
    $caller = $callerJson | ConvertFrom-Json
    $ACCOUNT_ID = $caller.Account
    $REGION = "ap-southeast-1"
    Write-Host "Tài khoản AWS: $ACCOUNT_ID (Region: $REGION)" -ForegroundColor Green
} catch {
    Write-Host "LỖI: Chưa cấu hình AWS CLI hoặc Token không hợp lệ. Vui lòng chạy 'aws configure' trước!" -ForegroundColor Red
    exit 1
}

$REPO_NAME = "cham-culture"
$ECR_URI = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
$IMAGE_TAG = "$ECR_URI/$REPO_NAME`:latest"

Write-Host "`n=== BƯỚC 2: TẠO HOẶC KIỂM TRA ECR REPOSITORY ===" -ForegroundColor Cyan
$null = aws ecr describe-repositories --repository-names $REPO_NAME --region $REGION 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Đang tạo mới ECR repository: $REPO_NAME..." -ForegroundColor Yellow
    aws ecr create-repository --repository-name $REPO_NAME --region $REGION
} else {
    Write-Host "ECR repository '$REPO_NAME' đã sẵn sàng." -ForegroundColor Green
}

Write-Host "`n=== BƯỚC 3: ĐĂNG NHẬP DOCKER VÀO ECR ===" -ForegroundColor Cyan
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI
if ($LASTEXITCODE -ne 0) {
    Write-Host "LỖI: Đăng nhập Docker vào ECR thất bại!" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== BƯỚC 4: BUILD DOCKER IMAGE (linux/amd64) ===" -ForegroundColor Cyan
Set-Location -Path $PSScriptRoot
docker build --platform linux/amd64 -t "$REPO_NAME`:latest" .
if ($LASTEXITCODE -ne 0) {
    Write-Host "LỖI: Build Docker image thất bại!" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== BƯỚC 5: TAG VÀ PUSH IMAGE LÊN ECR ===" -ForegroundColor Cyan
docker tag "$REPO_NAME`:latest" $IMAGE_TAG
docker push $IMAGE_TAG
if ($LASTEXITCODE -ne 0) {
    Write-Host "LỖI: Push image lên ECR thất bại!" -ForegroundColor Red
    exit 1
}

Write-Host "`n🎉 HOÀN THÀNH PUSH DOCKER IMAGE LÊN ECR!" -ForegroundColor Green
Write-Host "Image URI của bạn: $IMAGE_TAG" -ForegroundColor Yellow
Write-Host "`nBây giờ bạn có thể vào AWS App Runner Console tạo Service và chọn image này:" -ForegroundColor Cyan
Write-Host "https://ap-southeast-1.console.aws.amazon.com/apprunner/home?region=$REGION" -ForegroundColor White
