# ==============================
# 환경변수 로드
# ==============================
import os
from dotenv import load_dotenv
load_dotenv()

# ==============================
# YouTube API 라이브러리
# ==============================
from googleapiclient.discovery import build

# ==============================
# OpenAI 댓글 분석 함수
# ==============================
# ❗ 1순위 개선 포인트:
# - analyze_comment 내부 GPT 프롬프트를
#   "확실할 때만 위험" 기준으로 완화해야 함
from backend.openai_service import analyze_comment


# ==============================
# DB 저장 모듈
# ==============================
from backend.database import (
    save_video_with_comments, 
    init_database,
    save_video,
    save_user,
    save_comment_and_analysis
)

# ==============================
# YouTube API Key
# ==============================
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# ❗ API 키 없을 때 바로 에러 확인용
if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY가 .env에 없습니다.")

# ==============================
# YouTube Data API 객체 생성
# ==============================
youtube = build(
    "youtube",
    "v3",
    developerKey=YOUTUBE_API_KEY
)

def get_video_info(video_id):
    """
    YouTube 비디오 정보 가져오기
    
    Returns:
        Dict: {
            'video_id': str,
            'title': str,
            'channel_name': str,
            'channel_id': str,
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'published_at': str,
            'description': str,
            'thumbnail_url': str
        }
    """
    try:
        request = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        )
        response = request.execute()
        
        if not response.get("items"):
            raise ValueError(f"비디오를 찾을 수 없습니다: {video_id}")
        
        item = response["items"][0]
        snippet = item["snippet"]
        statistics = item.get("statistics", {})
        
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = ""
        if thumbnails.get("high"):
            thumbnail_url = thumbnails["high"]["url"]
        elif thumbnails.get("medium"):
            thumbnail_url = thumbnails["medium"]["url"]
        elif thumbnails.get("default"):
            thumbnail_url = thumbnails["default"]["url"]
        
        return {
            "video_id": video_id,
            "title": snippet.get("title", ""),
            "channel_name": snippet.get("channelTitle", ""),
            "channel_id": snippet.get("channelId", ""),
            "view_count": int(statistics.get("viewCount", 0)),
            "like_count": int(statistics.get("likeCount", 0)),
            "comment_count": int(statistics.get("commentCount", 0)),
            "published_at": snippet.get("publishedAt", ""),
            "description": snippet.get("description", ""),
            "thumbnail_url": thumbnail_url
        }
    except Exception as e:
        print(f"⚠️ 비디오 정보 가져오기 실패: {e}")
        raise


def get_comments(video_id, max_results=50):
    """
    유튜브 댓글을 가져와서
    각 댓글을 OpenAI(GPT)로 분석한 뒤 반환

    ✔ max_results: 최대로 가져올 댓글 수 (50, 100, 200 등)

    ⚠️ 주의:
    - YouTube API는 한 번에 최대 50개만 반환
    - nextPageToken으로 반복 호출 필요
    """

    results = []        # 프론트엔드용 간단한 형식
    db_comments = []    # DB 저장용 상세 형식
    page_token = None   # 🔥 페이지네이션용 토큰

    danger_count = 0    # 🔥 위험 댓글 개수 (요약용)

    # ==============================
    # 🔁 nextPageToken이 있는 동안 반복 호출
    # ==============================
    while len(results) < max_results:

        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=50,            # ❗ YouTube API 최대값은 항상 50
            textFormat="plainText",
            pageToken=page_token      # 🔥 다음 페이지 요청
        )

        response = request.execute()

        # ==============================
        # 댓글 하나씩 처리
        # ==============================
        for item in response.get("items", []):
            top_comment = item["snippet"]["topLevelComment"]
            snippet = top_comment["snippet"]
            text = snippet["textDisplay"]
            youtube_comment_id = top_comment["id"]
            author_id = snippet.get("authorChannelId", {}).get("value", "")
            
            # authorChannelId가 없으면 authorDisplayName을 해시해서 사용
            if not author_id:
                import hashlib
                author_id = hashlib.md5(snippet["authorDisplayName"].encode()).hexdigest()

            # =====================================================
            # 🔥 OpenAI(GPT)로 댓글 분석
            # =====================================================
            analysis = analyze_comment(text)

            # ==============================
            # 🔥 category 정규화 (매우 중요)
            # ==============================
            raw_category = analysis.get("category", "정상")

            # GPT가 이상한 값 주면 무조건 정상 처리
            if raw_category not in ["정상", "위험", "욕설", "혐오", "광고"]:
                raw_category = "정상"

            if raw_category == "위험":
                danger_count += 1

            # 프론트엔드용 간단한 형식 (기존 호환성 유지)
            results.append({
                "author": snippet["authorDisplayName"],
                "text": text,
                "likeCount": snippet["likeCount"],
                "publishedAt": snippet["publishedAt"],
                "category": raw_category,
                "reason": analysis.get("reason", "분석 실패 또는 기본 처리")
            })
            
            # DB 저장용 상세 정보
            db_comments.append({
                "user": {
                    "user_id": author_id,
                    "username": snippet["authorDisplayName"],
                    "profile_image_url": snippet.get("authorProfileImageUrl", "")
                },
                "comment": {
                    "youtube_comment_id": youtube_comment_id,
                    "user_id": author_id,
                    "comment_text": text,
                    "like_count": snippet["likeCount"],
                    "reply_count": item["snippet"].get("totalReplyCount", 0),
                    "published_at": snippet["publishedAt"],
                    "parent_comment_id": None,
                    "is_reply": False
                },
                "analysis": {
                    "category": raw_category,
                    "reason": analysis.get("reason", ""),
                    "confidence_score": 0.8
                }
            })

            # ❗ max_results 초과 방지
            if len(results) >= max_results:
                break

        # ==============================
        # 다음 페이지 토큰 처리
        # ==============================
        page_token = response.get("nextPageToken")

        # ❗ 다음 페이지 없으면 종료
        if not page_token:
            break

    # ==============================
    # 🔥 비디오 정보 가져오기 및 DB 저장
    # ==============================
    try:
        video_info = get_video_info(video_id)
        
        # DB에 저장
        stats = save_video_with_comments(video_info, db_comments)
        print(f"✅ DB 저장 완료 - 비디오: {stats['videos']}, 사용자: {stats['users']}, 댓글: {stats['comments']}, 분석: {stats['analyses']}")
    except Exception as e:
        print(f"⚠️ DB 저장 중 오류 발생 (계속 진행): {e}")

    # ==============================
    # 🔥 요약 정보 포함해서 반환
    # ==============================
    return {
        "video_info": video_info,  # ⭐ 이 줄을 반드시 추가하세요!
        "summary": {
            "total": len(results),
            "danger": danger_count
        },
        "comments": results
    }
