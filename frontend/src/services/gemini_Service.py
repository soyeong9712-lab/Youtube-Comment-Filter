# ==============================
# Google Gemini (google-genai SDK)
# ==============================

import os
import json
from google import genai

# ==============================
# Gemini Client 생성
# ==============================
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# ==============================
# 시스템 프롬프트
# ==============================
SYSTEM_PROMPT = """
당신은 글로벌 플랫폼의 지능형 필터링 시스템 'GuardAI'입니다.

분석 규칙:
1. 문맥 분석 분류: [정상, 스팸, 욕설, 비방] 중 하나로 분류하세요.
2. 글로벌 언어 자동 감지: ISO 639-1 코드(ko, en, ja, zh, es, ar, fr, vi 등)를 추출하세요.
3. 숏폼 문맥 이해: "ㅋㅋ", "lol", "🔥" 등은 정상으로 처리하세요.

JSON 형식으로만 응답하세요.
"""

# ==============================
# 댓글 하나 분류
# ==============================
def classify_comment(text: str):

    prompt = f"""
댓글 분석 요청:
"{text}"

JSON 형식:
{{
  "type": "정상 | 스팸 | 욕설 | 비방",
  "language": "언어명",
  "langCode": "en"
}}
"""

    response = client.models.generate_content(
        model="gemini-1.5-flash",   # ✅ 여기만 수정
        contents=[
            {
                "role": "user",
                "parts": [
                    {"text": SYSTEM_PROMPT + prompt}
                ]
            }
        ]
    )

    try:
        return json.loads(response.text)
    except:
        return {
            "type": "정상",
            "language": "Unknown",
            "langCode": "und"
        }
