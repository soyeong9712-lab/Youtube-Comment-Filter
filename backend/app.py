# ==============================
# Flask 기본 모듈
# ==============================
from flask import Flask, request, jsonify

# ==============================
# 프론트엔드(React)와 통신하기 위한 CORS 설정
# ==============================
from flask_cors import CORS

# ==============================
# 정규식 사용 (유튜브 URL에서 video_id 추출)
# ==============================
import re

# ==============================
# youtube_api.py에 작성한 함수 가져오기
# ==============================
from youtube_api import get_comments


# ==============================
# Flask 앱 생성
# ==============================
app = Flask(__name__)

# ==============================
# CORS 허용 (React → Flask API 호출 가능)
# ==============================
CORS(app)


# ==============================
# 유튜브 URL에서 video_id 추출하는 함수
# ==============================
def extract_video_id(youtube_url):
    """
    다양한 형태의 유튜브 URL에서 video_id를 추출한다.
    지원 예시:
    - https://www.youtube.com/watch?v=xxxx
    - https://youtu.be/xxxx
    - https://www.youtube.com/shorts/xxxx
    """

    patterns = [
        r"v=([^&]+)",          # watch?v=xxxx
        r"youtu\.be/([^?]+)",  # youtu.be/xxxx
        r"shorts/([^?]+)"      # shorts/xxxx
    ]

    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)

    return None


# ==============================
# 유튜브 댓글 API 엔드포인트
# ==============================
@app.route("/api/comments", methods=["GET"])
def comments():
    """
    유튜브 댓글을 반환하는 API
    사용 예:
    /api/comments?url=https://www.youtube.com/watch?v=xxxx
    """

    # URL 파라미터에서 유튜브 주소 가져오기
    youtube_url = request.args.get("url")

    # url이 없으면 에러 반환
    if not youtube_url:
        return jsonify({"error": "url is required"}), 400

    # 유튜브 URL에서 video_id 추출
    video_id = extract_video_id(youtube_url)

    # video_id 추출 실패 시 에러 반환
    if not video_id:
        return jsonify({"error": "invalid youtube url"}), 400

    try:
        # youtube_api.py의 함수로 댓글 가져오기
        comments = get_comments(video_id)

        # JSON 형태로 프론트엔드에 반환
        return jsonify(comments)

    except Exception as e:
        # 서버 내부 에러 처리
        return jsonify({"error": str(e)}), 500


# ==============================
# 이 파일을 직접 실행했을 때만 Flask 서버 실행
# ==============================
if __name__ == "__main__":
    app.run(debug=True)
