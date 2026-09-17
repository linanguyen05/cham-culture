import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
import google.generativeai as genai
from google.api_core import exceptions

from app.config import get_settings, Settings
from app.rate_limit import limiter
from fastapi import Request

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])

# Load FAQ data
FAQ_PATH = Path(__file__).parent / "faq.json"
if FAQ_PATH.exists():
    with open(FAQ_PATH, "r", encoding="utf-8") as f:
        faq_data = json.load(f)
else:
    faq_data = {}

# Simple global memory store for quota (reset when server restarts)
question_count = 0
DAILY_LIMIT = 20

# We'll configure genai lazily when the first request comes in or when settings are available.
_genai_configured = False


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
@limiter.limit("20/minute")
async def chat(request: Request, payload: ChatRequest, settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    global question_count
    global _genai_configured

    user_msg = payload.message.strip()
    if not user_msg:
        return {"reply": "Vui lòng nhập câu hỏi.", "count": question_count, "limit": DAILY_LIMIT}

    # 1. Check internal FAQ first
    user_msg_upper = user_msg.upper()
    for key, value in faq_data.items():
        if key in user_msg_upper:
            if isinstance(value, dict):
                reply = "\n".join([f"{k}: {v}" for k, v in value.items()])
            else:
                reply = value
            return {
                "reply": reply,
                "count": question_count,
                "limit": DAILY_LIMIT
            }

    # 2. Check quota
    if question_count >= DAILY_LIMIT:
        return {
            "reply": "Bạn đã vượt quá hạn mức miễn phí trong ngày (20 câu hỏi). Vui lòng thử lại ngày mai hoặc bật billing để tăng quota.",
            "count": question_count,
            "limit": DAILY_LIMIT
        }

    # 3. Call Gemini API
    if not settings.gemini_api_key:
        return {
            "reply": "Hệ thống chưa được cấu hình GEMINI_API_KEY. Tính năng Chatbot tạm thời không khả dụng.",
            "count": question_count,
            "limit": DAILY_LIMIT
        }

    try:
        if not _genai_configured:
            genai.configure(api_key=settings.gemini_api_key)
            _genai_configured = True
            
        model = genai.GenerativeModel("gemini-2.5-flash")
        # In an async context, ideally we'd use async API, but we'll use synchronous model.generate_content for now
        # or we could use generate_content_async if available.
        # Let's use async generate_content_async since it's available in the library.
        response = await model.generate_content_async(user_msg)
        reply = response.text if hasattr(response, "text") else ""

        question_count += 1
        return {
            "reply": reply.strip(),
            "count": question_count,
            "limit": DAILY_LIMIT
        }

    except exceptions.ResourceExhausted:
        question_count = 0  # reset fallback
        return {
            "reply": "Quota của Gemini đã hết, vui lòng thử lại sau hoặc bật billing để tăng hạn mức.",
            "count": question_count,
            "limit": DAILY_LIMIT
        }
    except Exception as e:
        return {
            "reply": f"Đã xảy ra lỗi hệ thống: {str(e)}",
            "count": question_count,
            "limit": DAILY_LIMIT
        }
