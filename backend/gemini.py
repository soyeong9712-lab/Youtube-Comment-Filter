from google import genai
import os
from dotenv import load_dotenv
import json

# ==============================
# .env 파일 로드
# ==============================
load_dotenv()

# ==============================
# Gemini API 키
# ==============================
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
    
)

def analyze_comment(text):
    """
    댓글 하나를 Gemini로 분석
    분류: 욕설 / 광고·스팸 / 정상
    """

    prompt = f"""
다음 유튜브 댓글을 분석해서 분류해줘.

분류 기준:
- 욕설
- 광고/스팸
- 정상

댓글:
"{text}"

JSON 형식으로만 출력:
{{
  "category": "욕설 | 광고/스팸 | 정상",
  "reason": "판단 이유 한 줄"
}}
"""

    response = client.models.generate_content(
        model="gemini-1.5-flash",   # ✅ 여기만 수정
        contents=[
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    )

    return json.loads(response.text)
