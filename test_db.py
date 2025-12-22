import requests
from backend.database import save_video_with_comments

def debug_youtube_to_db():
    # 1. API 호출
    target_youtube_url = "https://www.youtube.com/watch?v=L7JSaIBnqZs"
    api_url = f"http://localhost:5000/api/comments?url={target_youtube_url}"
    
    print(f"📡 API 서버 요청: {api_url}")
    response = requests.get(api_url)
    
    if response.status_code == 200:
        data = response.json()
        
        # [중요] 응답 데이터에서 댓글 목록 가져오기
        comments = data.get('comments', [])
        
        # [원인 발견] video_info가 없으므로 임시 데이터를 만듭니다.
        video_info = data.get('video_info')
        if not video_info:
            print("⚠️ 'video_info'가 응답에 없어서 임시 데이터를 생성합니다.")
            video_info = {
                "video_id": "L7JSaIBnqZs",
                "title": "에픽하이 x 조정석 유튜브 영상",
                "channel_name": "OfficialEpikHigh",
                "channel_id": "UC...",
                "view_count": 0,
                "published_at": "2025-01-01 00:00:00",
                "description": "임시 설명",
                "thumbnail_url": ""
            }

        # 2. 데이터 형식 변환 (API 응답 -> DB 함수용)
        # API 응답의 'author'를 DB의 'user_id'와 'username'으로 매핑해야 함
        formatted_comments = []
        for c in comments:
            formatted_comments.append({
                "user": {
                    "user_id": c.get('author', 'unknown_user'),
                    "username": c.get('author', '알 수 없음'),
                    "profile_image_url": ""
                },
                "comment": {
                    "comment_id": f"id_{c.get('publishedAt')}_{c.get('author')}", # 임시 ID 생성
                    "text": c.get('text', ''),
                    "like_count": c.get('likeCount', 0),
                    "published_at": c.get('publishedAt').replace('T', ' ').replace('Z', '')
                },
                "analysis": {
                    "category": c.get('category', 'normal'),
                    "reason": c.get('reason', ''),
                    "confidence_score": 0.8
                }
            })

        # 3. DB 적재
        print(f"💾 {len(formatted_comments)}개의 댓글을 DB에 저장을 시도합니다...")
        stats = save_video_with_comments(video_info, formatted_comments)
        print(f"📊 결과: {stats}")
        
    else:
        print(f"❌ 서버 응답 실패: {response.status_code}")

if __name__ == "__main__":
    debug_youtube_to_db()