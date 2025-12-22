import os
import json
import re
import requests
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ==============================
# ✅ 카테고리 정의 (DB와 일치시킴)
# ==============================
# DB 통계 기준: 1.정상, 2.위험(욕설/혐오), 3.스팸(광고)
ALLOWED_CATEGORIES = ["정상", "위험", "스팸"]

# ==============================
# 1️⃣ 로컬 욕설 필터
# ==============================
BAD_WORD_PATTERNS = [
    r"씨\s*발", r"ㅅ\s*ㅂ", r"병\s*신", r"ㅂ\s*ㅅ",
    r"좆", r"미\s*친", r"지\s*랄", r"개\s*새끼", r"염병",
    r"꺼\s*져", r"죽\s*어"
]

def local_badword_filter(text: str):
    for pattern in BAD_WORD_PATTERNS:
        if re.search(pattern, text):
            # '욕설'은 DB에서 '위험' 카테고리(ID: 2)로 분류되도록 설정
            return {"category": "위험", "reason": "욕설 패턴 감지"}
    return None

# ==============================
# 2️⃣ 로컬 광고 필터
# ==============================
def local_ad_filter(text: str):
    AD_PATTERNS = [
        r"http[s]?://[^\s]+", r"www\.[^\s]+",
        r"\d{2,4}-\d{3,4}-\d{4}", r"010-?\d{4}-?\d{4}",
        r"카톡\s*문의", r"텔레그램", r"인스타\s*@"
    ]
    for pattern in AD_PATTERNS:
        if re.search(pattern, text):
            # '광고'는 DB에서 '스팸' 카테고리(ID: 3)로 분류
            return {"category": "스팸", "reason": "광고/홍보 의심"}
    return None

# ==============================
# 3️⃣ 로컬 정상 필터 (빠른 통과)
# ==============================
def local_fast_filter(text: str):
    stripped = text.strip()
    if len(stripped) <= 3 and not any(char.isalnum() for char in stripped):
        return {"category": "정상", "reason": "이모티콘 반응"}
    
    POSITIVE_WORDS = ["ㅋㅋㅋ", "ㅎㅎㅎ", "좋아", "귀여워", "최고", "감사", "응원", "👍", "❤️"]
    NEGATIVE_WORDS = ["죽", "꺼져", "싫어", "최악", "쓰레기", "혐오", "무식"]
    
    if any(word in stripped for word in NEGATIVE_WORDS):
        return None
    
    if any(word in stripped for word in POSITIVE_WORDS) and len(stripped) >= 5:
        return {"category": "정상", "reason": "긍정적 반응"}
    return None

# ==============================
# 4️⃣ GPT 배치 분석 (프롬프트 카테고리 고정)
# ==============================
def analyze_comments_batch(texts: list[str]):
    joined = "\n".join([f"{i+1}. {text}" for i, text in enumerate(texts)])
    payload = {
        "model": "gpt-4o-mini",
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": f"""너는 유튜브 댓글 필터링 AI다. 다음 3가지 카테고리로만 분류해라: {ALLOWED_CATEGORIES}

1. **정상**: 일반적인 의견, 질문, 긍정적 반응, 단순 농담.
2. **위험**: 욕설, 비속어, 특정인에 대한 혐오 표현, 인신공격, 폭력적 발언.
3. **스팸**: 상품 홍보, 외부 링크 유도, 연락처 남기기, 도배성 광고.

반드시 JSON 배열만 반환해라."""
            },
            {
                "role": "user",
                "content": f"댓글 분석:\n{joined}\n\n반환 형식: [{{'index': 1, 'category': '정상|위험|스팸', 'reason': '이유'}}]"
            }
        ]
    }
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
        json=payload, timeout=15
    )
    # JSON 파싱 로직 (간소화)
    content = response.json()["choices"][0]["message"].get("content", "[]")
    match = re.search(r"\[.*\]", content, re.S)
    return json.loads(match.group()) if match else []

# ==============================
# 5️⃣ 통합 분석 함수 (DB 구조에 맞게 리턴)
# ==============================
def analyze_comments_bulk(comments: list[dict]):
    """
    최종 결과 구조를 DB 저장 함수인 save_video_with_comments가 
    정확히 읽을 수 있도록 구성합니다.
    """
    final_results = []
    gpt_targets = []

    for c in comments:
        text = c.get("text", "")
        # 로컬 필터 우선 적용
        res = local_badword_filter(text) or local_ad_filter(text) or local_fast_filter(text)
        
        if res:
            # DB가 기대하는 중첩 구조 생성
            final_results.append({
                "user": {"author": c.get("author"), "profile_image": c.get("profile_image")},
                "comment": {"text": text, "like_count": c.get("like_count"), "published_at": c.get("published_at")},
                "analysis": res
            })
        else:
            gpt_targets.append(c)

    # GPT 처리
    if gpt_targets:
        texts = [c["text"] for c in gpt_targets]
        try:
            gpt_res_list = analyze_comments_batch(texts)
            for c, g in zip(gpt_targets, gpt_res_list):
                final_results.append({
                    "user": {"author": c.get("author"), "profile_image": c.get("profile_image")},
                    "comment": {"text": c.get("text"), "like_count": c.get("like_count"), "published_at": c.get("published_at")},
                    "analysis": {
                        "category": g.get("category") if g.get("category") in ALLOWED_CATEGORIES else "위험",
                        "reason": g.get("reason", "AI 분석")
                    }
                })
        except Exception as e:
            print(f"GPT 분석 실패: {e}")
            for c in gpt_targets:
                final_results.append({
                    "user": c, "comment": c, 
                    "analysis": {"category": "위험", "reason": "분석 오류"}
                })

    return final_results

def analyze_comment(text: str):
    """
    단일 댓글 분석을 위한 래퍼 함수
    youtube_api.py에서 이 이름을 찾고 있으므로 반드시 필요합니다.
    """
    # 임시로 단일 리스트를 만들어 bulk 함수를 호출하거나 직접 분석
    results = analyze_comments_bulk([{"text": text, "author": "unknown"}])
    if results:
        # 결과 구조에서 analysis 부분만 반환
        return results[0]["analysis"]
    return {"category": "위험", "reason": "분석 실패"}