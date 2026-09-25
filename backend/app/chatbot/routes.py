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

# Question count for analytics/monitoring (no limit restriction)
question_count = 0

# We'll configure genai lazily when the first request comes in or when settings are available.
_genai_configured = False


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
@limiter.limit("60/minute")
async def chat(request: Request, payload: ChatRequest, settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    global question_count
    global _genai_configured

    user_msg = payload.message.strip()
    if not user_msg:
        return {"reply": "Vui lòng nhập câu hỏi.", "count": question_count, "limit": "unlimited"}

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
                "limit": "unlimited"
            }

    # 2. Unlimited access - no daily cap check
    # 3. Call Gemini API
    if not settings.gemini_api_key:
        return {
            "reply": "Hệ thống chưa được cấu hình GEMINI_API_KEY. Tính năng Chatbot tạm thời không khả dụng.",
            "count": question_count,
            "limit": "unlimited"
        }

    try:
        if not _genai_configured:
            genai.configure(api_key=settings.gemini_api_key)
            _genai_configured = True

        system_instruction = (
            "Bạn là Chăm Culture AI - trợ lý ảo thông thái, thân thiện và tận tâm của nền tảng Văn Hóa Chăm (Cham Culture). "
            "Sứ mệnh cốt lõi của bạn là giới thiệu, giải đáp và lan tỏa vẻ đẹp về lịch sử Champa, phong tục tập quán, "
            "lễ hội truyền thống (Katê, Ramuwan, Rija Nưgar...), kiến trúc đền tháp (Mỹ Sơn, Po Klong Garai, Po Nagar...), "
            "làng nghề thủ công (gốm Bàu Trúc, dệt Mỹ Nghiệp), ngôn ngữ và đời sống của đồng bào dân tộc Chăm tại Việt Nam.\n\n"
            "NGUYÊN TẮC PHẢN HỒI:\n"
            "1. Với câu hỏi về văn hóa Chăm: Trả lời thật chi tiết, sâu sắc, chuẩn xác và trân trọng giá trị truyền thống.\n"
            "2. Với các câu hỏi ngoài lề (khoa học, đời sống, lập trình, toán học, địa lý thế giới...): Hãy trả lời "
            "ngắn gọn, chuẩn xác và hữu ích cho người dùng; đồng thời ở cuối phản hồi, hãy luôn khéo léo và tự nhiên "
            "đính kèm một câu gợi mở hoặc lời mời tìm hiểu về Văn hóa Chăm (ví dụ: 'Bên cạnh đó, nếu bạn muốn khám phá thêm "
            "về các nét đẹp văn hóa, lễ hội Katê hay kiến trúc tháp Chăm cổ kính, đừng ngần ngại hỏi mình nhé!').\n"
            "3. Luôn dùng tiếng Việt lịch sự, thân thiện, văn phong ấm áp."
        )

        # Fallback sequence in case a model is deprecated, quota-limited, or temporarily unavailable
        candidate_models = [
            "gemini-3.1-flash-lite",
            settings.gemini_model,
            "gemini-3.5-flash-lite",
            "gemini-flash-latest",
            "gemini-3.6-flash",
            "gemini-3.8-flash",
        ]
        seen = set()
        models_to_try = [m for m in candidate_models if m and not (m in seen or seen.add(m))]

        reply = ""
        last_error = None

        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
                response = await model.generate_content_async(user_msg)
                if response and hasattr(response, "text") and response.text:
                    reply = response.text
                    break
            except (exceptions.NotFound, exceptions.InvalidArgument, exceptions.ResourceExhausted, exceptions.GoogleAPICallError) as model_err:
                last_error = model_err
                continue
            except Exception as model_err:
                last_error = model_err
                continue

        if not reply and last_error:
            raise last_error

        question_count += 1
        return {
            "reply": reply.strip(),
            "count": question_count,
            "limit": "unlimited"
        }

    except exceptions.ResourceExhausted:
        return {
            "reply": "Hệ thống AI đang quá tải lượt gọi trong giây lát, vui lòng thử lại sau ít giây.",
            "count": question_count,
            "limit": "unlimited"
        }
    except Exception as e:
        return {
            "reply": f"Đã xảy ra lỗi hệ thống: {str(e)}",
            "count": question_count,
            "limit": "unlimited"
        }
