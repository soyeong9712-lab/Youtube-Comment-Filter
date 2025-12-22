# ==============================
# Flask 기본 설정
# ==============================
from flask import Flask
from flask_cors import CORS
import os  # 보안 키 생성을 위해 추가

# ==============================
# backend Blueprint 불러오기
# ==============================
from backend.app import api as backend_api

# ==============================
# DB 초기화
# ==============================
from backend.database import init_database


# ==============================
# 메인 Flask 앱 생성
# ==============================
app = Flask(
    __name__,
    template_folder="frontend/templates",
    static_folder="frontend/static"
)

# 🔑 [해결] 세션 에러 해결을 위한 비밀키 설정
# Blueprint(api)가 아닌 메인 app 객체에 설정해야 세션이 작동합니다.
app.secret_key = "super-secret-key-for-youtube-guard" 

# ==============================
# CORS 허용
# ==============================
CORS(app)


# ==============================
# 🔗 Blueprint 등록
# ==============================
app.register_blueprint(backend_api)


# ==============================
# 서버 실행
# ==============================
if __name__ == "__main__":
    # DB 테이블 초기화
    try:
        init_database()
        print("✅ DB 초기화 완료")
    except Exception as e:
        print(f"⚠️ DB 초기화 실패: {e}")
        print("서버는 계속 실행되지만 DB 저장 기능이 작동하지 않을 수 있습니다.")
    
    # 세션 테스트를 위해 debug=True 권장 (개발 단계)
    app.run(host='0.0.0.0',debug=True, port=5000)