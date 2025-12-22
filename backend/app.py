# app.py 전체 코드
from flask import (
    Blueprint, request, jsonify, render_template,
    session, redirect, url_for
)
from flask_cors import CORS
import re
import os
from functools import wraps
from backend.youtube_api import get_comments  # 👈 이 줄이 반드시 있어야 합니다!

# 커스텀 로직 임포트
from backend.youtube_api import get_comments
from backend.database import save_video_with_comments, get_dashboard_stats

api = Blueprint("api", __name__)
CORS(api)

# 🔑 [해결 1] 세션 에러 해결을 위한 비밀키 설정
# Blueprint 객체가 아닌 Flask 앱 설정에서 사용될 수 있도록 정의합니다.
# 만약 run.py에서 Flask(app)을 생성한다면 거기서 app.secret_key를 설정하는 것이 가장 정확합니다.
api.secret_key = os.urandom(24) 

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            # [해결 2] Blueprint 명칭 'api.' 포함
            return redirect(url_for("api.admin_login"))
        return func(*args, **kwargs)
    return wrapper

@api.route("/")
def public_monitor():
    return render_template("public_monitor.html")

@api.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html")

@api.route("/admin/blacklist")
@admin_required
def admin_blacklist():
    return render_template("admin_blacklist.html")

@api.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("admin_login.html")

    admin_id = request.form.get("admin_id")
    secret_code = request.form.get("secret_code")

    if admin_id == "admin123" and secret_code == "1234":
        session["is_admin"] = True
        return redirect(url_for("api.admin_dashboard"))

    return render_template("admin_login.html", error="관리자 정보가 올바르지 않습니다.")

def extract_video_id(youtube_url):
    patterns = [r"v=([^&]+)", r"youtu\.be/([^?]+)", r"shorts/([^?]+)"]
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match: return match.group(1)
    return None

# API 엔드포인트 유지
@api.route("/api/comments", methods=["GET"])
def comments():
    youtube_url = request.args.get("url")
    video_id = extract_video_id(youtube_url)

    if not video_id:
        return jsonify({"error": "유효한 YouTube URL이 아닙니다."}), 400

    try:
        # 1. 유튜브 API를 통해 댓글 및 영상 정보 가져오기
        result_data = get_comments(video_id) 
        
        # 2. DB 저장 시도 (데이터 구조 확인 필수)
        # result_data 안에 'video_info'와 'comments' 키가 정확히 있어야 합니다.
        if "video_info" in result_data and "comments" in result_data:
            try:
                # database.py의 저장 함수 호출
                db_res = save_video_with_comments(result_data['video_info'], result_data['comments'])
                print(f"✅ DB 저장 성공: {db_res}")
            except Exception as db_err:
                print(f"❌ DB 저장 중 상세 에러: {db_err}")
                # DB 저장이 실패해도 사용자에게 댓글은 보여주기 위해 pass 하거나 에러 기록
        
        return jsonify(result_data)

    except Exception as e:
        print(f"❌ API 호출 에러: {e}")
        return jsonify({"error": str(e)}), 500