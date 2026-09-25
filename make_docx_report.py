import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_report():
    doc = docx.Document()
    
    # Page setup - 1 inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    # Styles
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    # Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("BÁO CÁO TỔNG QUAN TOÀN DIỆN DỰ ÁN\nNỀN TẢNG VĂN HÓA CHĂM (CHAM CULTURE)")
    run_title.font.name = 'Calibri'
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x8A, 0x25, 0x1A) # Heritage Red
    
    # Subtitle box
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("Trạng thái: Live Production trên AWS Cloud | Ngày báo cáo: 25/09/2026\nURL: https://medxqx35ff.ap-southeast-1.awsapprunner.com")
    run_sub.font.size = Pt(10.5)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Function to add heading 1
    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(6)
        r = p.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(15)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x8A, 0x25, 0x1A)
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(12.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xC2, 0x65, 0x22)
        return p

    # 1. TỔNG QUAN
    add_h1("1. GIỚI THIỆU & MỤC TIÊU DỰ ÁN")
    p = doc.add_paragraph(
        "Nền tảng Văn Hóa Chăm (Cham Culture Platform) là hệ sinh thái web tích hợp hiện đại, kết hợp giữa Cổng tri thức di sản số, "
        "Mạng xã hội cộng đồng và Trợ lý ảo Trí tuệ Nhân tạo (AI Chatbot). Dự án hướng đến các mục tiêu chiến lược:\n"
        "• Lưu trữ, số hóa và tôn vinh các giá trị di sản văn hóa, lịch sử vương quốc Champa cổ, kiến trúc đền tháp, lễ hội và ngôn ngữ Akhar Thrah.\n"
        "• Xây dựng diễn đàn mở cho cộng đồng Chăm và công chúng giao lưu, chia sẻ bài viết, hình ảnh, trải nghiệm thực tế.\n"
        "• Tích hợp trợ lý AI thông minh giải đáp tri thức văn hóa 24/7 không giới hạn, thân thiện và chính xác."
    )
    p.paragraph_format.line_spacing = 1.15

    # 2. NGÔN NGỮ LẬP TRÌNH
    add_h1("2. NGÔN NGỮ LẬP TRÌNH & MỤC ĐÍCH TỪNG PHÂN HỆ")
    
    add_h2("2.1. Phân Hệ Frontend (Giao Diện Người Dùng)")
    doc.add_paragraph(
        "• Ngôn ngữ: HTML5, CSS3, JavaScript (ES6+ Vanilla), Font Awesome 6.5.2, Google Fonts.\n"
        "• Mục đích kỹ thuật: Tối đa hóa tốc độ tải trang (Page Load Speed < 0.5s), thân thiện chuẩn SEO, kiểm soát Responsive Design 100% không phụ thuộc framework nặng.\n"
        "• Phân bổ trang:\n"
        "   - frontend/dashboard/: Trang chủ điều hướng, Hero Banner động, phần chân trang ghi nhận nhóm tác giả học sinh THPT Nguyễn Thị Minh Khai.\n"
        "   - frontend/learn.html & Cụm chuyên đề (dan-so.html, khu-vuc.html, ngon-ngu.html, nguon-goc.html): Cổng tra cứu dữ liệu nhân khẩu, địa bàn cư trú, lịch sử và chữ viết Akhar Thrah, tối ưu hiển thị Mobile qua file assets/learn/learn-responsive.css.\n"
        "   - frontend/community/: Diễn đàn mạng xã hội tương tác (đăng bài, ảnh/video, like, comment, repost, follow, lọc chủ đề).\n"
        "   - frontend/chatbot.html: Giao diện trợ lý ảo AI thông minh, hỗ trợ hỏi đáp không giới hạn."
    )

    add_h2("2.2. Phân Hệ Backend (Máy Chủ Ứng Dụng & API)")
    doc.add_paragraph(
        "• Ngôn ngữ: Python 3.12.\n"
        "• Framework chính: FastAPI 0.115.6 kết hợp máy chủ ASGI Uvicorn 0.34.0.\n"
        "• Mục đích kỹ thuật: Xử lý I/O bất đồng bộ (asyncio) chịu tải cao; chuẩn hóa và bảo vệ dữ liệu với Pydantic v2; tự động sinh tài liệu Swagger UI (/docs); đóng vai trò Single-Origin Monolith phục vụ Frontend và Backend trên cùng một domain nhằm triệt tiêu hoàn toàn lỗi CORS và chặn Cookie bên thứ ba.\n"
        "• Các module trọng tâm: backend/app/auth (xác thực phiên Fernet mã hóa), backend/app/community (nghiệp vụ mạng xã hội), backend/app/chatbot (xử lý hội thoại AI, fallback đa mô hình), backend/app/storage (upload Supabase Storage)."
    )

    add_h2("2.3. Ngôn Ngữ Tự Động Hóa & Đóng Gói (DevOps)")
    doc.add_paragraph(
        "• PowerShell (deploy_aws.ps1): Tự động hóa đăng nhập AWS ECR, đóng gói Docker và đẩy image lên AWS Cloud.\n"
        "• Dockerfile: Kịch bản đóng gói container chuẩn hóa môi trường linux/amd64 trên nền python:3.12-slim."
    )

    # 3. CƠ SỞ DỮ LIỆU
    add_h1("3. MÔ TẢ DATABASE & HỆ THỐNG QUẢN LÝ DỮ LIỆU")
    doc.add_paragraph(
        "• Hệ quản trị CSDL chính: PostgreSQL 15+ trên nền tảng Supabase Cloud Enterprise, đặt tại Singapore (ap-southeast-1) cùng Region với AWS App Runner để tối thiểu hóa độ trễ truy vấn (< 5ms).\n"
        "• Driver & Connection Pooling: Thư viện psycopg[binary,pool] 3.2.4 duy trì AsyncConnectionPool mở sẵn kết nối bất đồng bộ; kết nối qua Supabase IPv4 Session Pooler (port 5432) với chế độ bảo mật SSL bắt buộc (sslmode=require)."
    )
    
    # Table Schema
    p_tbl = doc.add_paragraph()
    p_tbl.add_run("Bảng thông số các thực thể CSDL (Database Schema):").bold = True
    
    table = doc.add_table(rows=6, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Tên Bảng", "Các Trường Dữ Liệu Chính", "Mô Tả Nghiệp Vụ"]
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        set_cell_background(cell, "8A251A")
        cell.paragraphs[0].runs[0].font.bold = True
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        set_cell_margins(cell, 120, 120, 150, 150)
        
    data = [
        ("users", "id (BIGINT PK), email (UNIQUE), username, avatar_url, password_hash, public_status, created_at", "Hồ sơ người dùng ứng dụng, liên kết Supabase Auth qua email"),
        ("posts", "id (BIGINT PK), user_id (FK), content, category, image_url (JSON text), video_url, shared_post_id (FK), created_at", "Bài viết cộng đồng kèm đa ảnh, video, chuyên mục và chia sẻ"),
        ("comments", "id (BIGINT PK), post_id (FK), user_id (FK), content, image_url, video_url, created_at", "Bình luận trao đổi thảo luận dưới bài viết"),
        ("post_likes", "post_id (FK), user_id (FK), created_at (PK: post_id + user_id)", "Tương tác thích bài viết, ràng buộc chống like trùng lặp"),
        ("follows", "follower_id (FK), following_id (FK), created_at (PK: follower_id + following_id)", "Mối quan hệ kết nối và theo dõi giữa các thành viên")
    ]
    for row_idx, (col1, col2, col3) in enumerate(data, start=1):
        bg = "F9F5F0" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate([col1, col2, col3]):
            cell = table.cell(row_idx, col_idx)
            cell.text = text
            set_cell_background(cell, bg)
            set_cell_margins(cell, 100, 100, 150, 150)
            
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    doc.add_paragraph("• Lưu trữ tệp media: Supabase Storage Bucket 'community-images' phục vụ lưu trữ và phân phối ảnh đại diện, ảnh bài viết qua CDN toàn cầu.")

    # 4. DỊCH VỤ AWS
    add_h1("4. CÁC DỊCH VỤ ĐIỆN TOÁN ĐÁM MÂY AWS ĐƯỢC SỬ DỤNG")
    
    aws_table = doc.add_table(rows=6, cols=3)
    aws_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    aws_headers = ["Dịch Vụ AWS", "Tài Nguyên Cụ Thể", "Mục Đích & Vai Trò Trong Dự Án"]
    for i, h in enumerate(aws_headers):
        cell = aws_table.cell(0, i)
        cell.text = h
        set_cell_background(cell, "C26522")
        cell.paragraphs[0].runs[0].font.bold = True
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        set_cell_margins(cell, 120, 120, 150, 150)
        
    aws_data = [
        ("AWS App Runner", "cham-culture-app (1 vCPU, 2 GB RAM, Singapore)", "Dịch vụ tính toán Serverless Container trung tâm, tự động cấp HTTPS, quản lý Health Check (/health) và tự động triển khai bản mới"),
        ("Amazon ECR", "cham-culture (Private Container Registry)", "Kho chứa Docker Image bảo mật cao, mã hóa lưu trữ container linux/amd64"),
        ("AWS IAM", "User: nla-aws | Role: AppRunnerECRAccessRole", "Quản lý danh tính và phân quyền cho phép App Runner pull image từ ECR an toàn"),
        ("Amazon CloudWatch", "Log Groups: /aws/apprunner/cham-culture-app/*", "Ghi nhận Application Logs và Deployment Logs theo thời gian thực để giám sát hệ thống"),
        ("AWS Envoy Edge", "Tích hợp sẵn trong App Runner", "Cân bằng tải, mã hóa đường truyền TLS 1.3 và bảo vệ chống tấn công mạng cơ bản")
    ]
    for row_idx, (col1, col2, col3) in enumerate(aws_data, start=1):
        bg = "F9F5F0" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate([col1, col2, col3]):
            cell = aws_table.cell(row_idx, col_idx)
            cell.text = text
            set_cell_background(cell, bg)
            set_cell_margins(cell, 100, 100, 150, 150)
            
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # 5. THÀNH PHẦN THAM GIA XÂY DỰNG
    add_h1("5. NHỮNG THÀNH PHẦN THAM GIA XÂY DỰNG NÊN WEB")
    
    add_h2("5.1. Đơn Vị & Nhân Sự Khởi Xướng")
    doc.add_paragraph(
        "• Tác giả & Ý tưởng: Nhóm học sinh Trường THPT Nguyễn Thị Minh Khai (TP. Hồ Chí Minh).\n"
        "• Tôn chỉ sản phẩm: 'A product by Nguyen Thi Minh Khai High School students' - mang di sản văn hóa Chăm tiếp cận thế hệ trẻ thông qua nền tảng công nghệ số."
    )

    add_h2("5.2. Động Cơ Trí Tuệ Nhân Tạo (AI Engine - Google Gemini)")
    doc.add_paragraph(
        "• Mô hình tích hợp chính: gemini-3.1-flash-lite (Tốc độ phản hồi cực nhanh < 1 giây, hạn mức gọi cao 1.500 requests/ngày).\n"
        "• Chuỗi dự phòng liên hoàn (Multi-Model Fallback): Tự động chuyển đổi mượt mà qua các model ['gemini-3.1-flash-lite', 'gemini-3.5-flash-lite', 'gemini-flash-latest', 'gemini-3.6-flash', 'gemini-3.8-flash']. Bắt lỗi 429 ResourceExhausted để tự động chuyển model, không làm gián đoạn người dùng.\n"
        "• Cơ sở tri thức: Tệp services/chatbot/faq.json kết hợp System Persona nhà nghiên cứu văn hóa Chăm.\n"
        "• Đặc tính: Hạn mức không giới hạn câu hỏi; trả lời câu hỏi ngoài lề ngắn gọn, chính xác và khéo léo chuyển ý về nét đẹp văn hóa Chăm."
    )

    add_h2("5.3. Các Thư Viện Công Nghệ & Khung Phát Triển")
    doc.add_paragraph(
        "• Web Framework: FastAPI 0.115.6, Starlette, Uvicorn 0.34.0.\n"
        "• Driver & Data: psycopg 3.2.4 (Async Connection Pool), Pydantic 2.10.4, pydantic-settings 2.7.1.\n"
        "• An ninh & Bảo mật: cryptography 44.0.0 (Fernet symmetric encryption cho Cookie session), bcrypt (mã hóa mật khẩu), slowapi 0.1.9 (giới hạn tần suất gọi chống spam/DDoS).\n"
        "• Giao tiếp API & Mạng: httpx 0.28.1 (Async HTTP Client cho Supabase & Gemini), python-dotenv 1.0.1.\n"
        "• Trí tuệ nhân tạo SDK: google-generativeai 0.8.3."
    )

    # Save document
    output_path = r"L:\FPT\Side project\vhc\BAO_CAO_DU_AN_TOAN_DIEN.docx"
    doc.save(output_path)
    print(f"Report generated successfully: {output_path}")

if __name__ == "__main__":
    create_report()
