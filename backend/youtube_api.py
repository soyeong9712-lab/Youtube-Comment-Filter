# ==============================
# 환경변수 로드 관련
# ==============================
import os
from dotenv import load_dotenv

# ==============================
# YouTube API
# ==============================
from googleapiclient.discovery import build

# ==============================
# Gemini 댓글 분석 함수
# ==============================
from gemini import analyze_comment

# ==============================
# .env 로드
# ==============================
load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# ==============================
# YouTube Data API 객체 생성
# ==============================
youtube = build(
    "youtube",
    "v3",
    developerKey=YOUTUBE_API_KEY
)

def get_comments(video_id, max_results=50):
    """
    유튜브 댓글을 가져오고
    각 댓글을 Gemini로 분류해서 반환
    """

    results = []

    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_results,
        textFormat="plainText"
    )

    response = request.execute()

    for item in response["items"]:
        snippet = item["snippet"]["topLevelComment"]["snippet"]
        text = snippet["textDisplay"]

        analysis = analyze_comment(text)

        results.append({
            "author": snippet["authorDisplayName"],
            "text": text,
            "likeCount": snippet["likeCount"],
            "publishedAt": snippet["publishedAt"],
            "category": analysis["category"],
            "reason": analysis["reason"]
        })

    return results
