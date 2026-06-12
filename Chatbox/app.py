#genai.configure(api_key="AIzaSyAPhK0Hnhq8fjXjr7zfbtEpf_ezSWa3xXw")
from flask import Flask, render_template, request, jsonify
from waitress import serve
import google.generativeai as genai
from google.api_core import exceptions
import json, os

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

genai.configure(api_key="AIzaSyAPhK0Hnhq8fjXjr7zfbtEpf_ezSWa3xXw")
model = genai.GenerativeModel("gemini-2.5-flash")

question_count = load_count()
daily_limit = 20   # hạn mức free tier

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
                "limit": daily_limit
            })

    try:
        # ====== Kiểm tra hạn mức ======
        if question_count >= daily_limit:
            return jsonify({
                "reply": "Bạn đã vượt quá hạn mức miễn phí trong ngày (20 câu hỏi). Vui lòng thử lại ngày mai hoặc bật billing để tăng quota.",
                "count": question_count,
                "limit": daily_limit
            })

        # ====== Gọi Gemini ======
        response = model.generate_content(user_msg)
        reply = response.text if hasattr(response, "text") else ""

        # ====== Tăng biến đếm ======
        question_count += 1
        save_count(question_count)

        return jsonify({
            "reply": reply.strip(),
            "count": question_count,
            "limit": daily_limit
        })

    except exceptions.ResourceExhausted:
        # ====== Khi API báo lỗi quota vượt quá ======
        question_count = 0  # reset lại biến đếm
        save_count(question_count)
        return jsonify({
            "reply": "Quota của Gemini đã hết, vui lòng thử lại sau hoặc bật billing để tăng hạn mức.",
            "count": question_count,
            "limit": daily_limit
        })

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=81)