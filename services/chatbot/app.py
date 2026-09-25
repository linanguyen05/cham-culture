from flask import Flask, render_template, request, jsonify
from waitress import serve
import google.generativeai as genai
from google.api_core import exceptions
import json, os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ====== Quản lý biến đếm ======
def load_count():
    if os.path.exists("usage.json"):
        with open("usage.json", "r") as f:
            return json.load(f).get("count", 0)
    return 0

def save_count(count):
    with open("usage.json", "w") as f:
        json.dump({"count": count}, f)

# ====== Load dữ liệu tình huống từ file JSON ======
with open("faq.json", "r", encoding="utf-8") as f:
    faq_data = json.load(f)

# ====== Flask App ======
app = Flask(__name__)

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set. Please configure it in a .env file.")
genai.configure(api_key=api_key)
model_name = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
system_instruction = (
    "Bạn là Chăm Culture AI - trợ lý ảo thông thái, thân thiện và tận tâm của nền tảng Văn Hóa Chăm (Cham Culture). "
    "Sứ mệnh cốt lõi của bạn là giới thiệu, giải đáp và lan tỏa vẻ đẹp về lịch sử Champa, phong tục tập quán, "
    "lễ hội truyền thống (Katê, Ramuwan, Rija Nưgar...), kiến trúc đền tháp, làng nghề thủ công và đời sống người Chăm.\n\n"
    "NGUYÊN TẮC PHẢN HỒI:\n"
    "1. Với câu hỏi về văn hóa Chăm: Trả lời sâu sắc, chuẩn xác và trân trọng giá trị truyền thống.\n"
    "2. Với các câu hỏi ngoài lề: Trả lời ngắn gọn, chuẩn xác; đồng thời ở cuối phản hồi, luôn khéo léo đính kèm câu gợi mở tìm hiểu Văn hóa Chăm.\n"
    "3. Luôn dùng tiếng Việt lịch sự, thân thiện."
)
model = genai.GenerativeModel(model_name, system_instruction=system_instruction)

question_count = load_count()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global question_count
    data = request.get_json()
    user_msg = data.get("message", "")

    # ====== Ưu tiên dữ liệu nội bộ ======
    for key, value in faq_data.items():
        if key in user_msg.upper():
            if isinstance(value, dict):
                reply = "\n".join([f"{k}: {v}" for k, v in value.items()])
            else:
                reply = value
            return jsonify({
                "reply": reply,
                "count": question_count,
                "limit": "unlimited"
            })

    try:
        # ====== Gọi Gemini (Không giới hạn câu hỏi) ======
        response = model.generate_content(user_msg)
        reply = response.text if hasattr(response, "text") else ""

        # ====== Tăng biến đếm thống kê ======
        question_count += 1
        save_count(question_count)

        return jsonify({
            "reply": reply.strip(),
            "count": question_count,
            "limit": "unlimited"
        })

    except exceptions.ResourceExhausted:
        # ====== Khi API báo lỗi quota vượt quá ======
        question_count = 0  # reset lại biến đếm
        save_count(question_count)
        return jsonify({
            "reply": "Quota của Gemini đã hết, vui lòng thử lại sau hoặc bật billing để tăng hạn mức.",
            "count": question_count,
            "limit": "unlimited"
        })

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=81)