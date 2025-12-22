import pymysql
from datetime import datetime
from dateutil import parser as date_parser
from pymysql.cursors import DictCursor

# ==============================
# 1. DB 연결 설정
# ==============================
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "1234",
    "database": "youtube",
    "charset": "utf8mb4",
    "cursorclass": DictCursor
}


def get_db_connection():
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")
        return None

# ==============================
# 2. 기초 저장 함수들
# ==============================


def save_video(video_data: dict) -> bool:
    conn = get_db_connection()
    if not conn:
        return False
    try:
        raw_date = video_data.get(
            'published_at') or video_data.get('publishedAt')
        formatted_date = date_parser.parse(
            raw_date).strftime('%Y-%m-%d %H:%M:%S')
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO videos (video_id, title, channel_name, channel_id, view_count, published_at, description, thumbnail_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE title=VALUES(title), view_count=VALUES(view_count)
            """
            cursor.execute(sql, (
                video_data.get('video_id'), video_data.get('title'),
                video_data.get('channel_name'), video_data.get('channel_id'),
                video_data.get('view_count', 0), formatted_date,
                video_data.get('description', ''), video_data.get(
                    'thumbnail_url', '')
            ))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ 비디오 저장 에러: {e}")
        return False
    finally:
        conn.close()


def save_user(user_data: dict) -> bool:
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO users (user_id, username, profile_image_url) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE username=VALUES(username)"
            cursor.execute(sql, (user_data.get('user_id'), user_data.get(
                'username'), user_data.get('profile_image_url', '')))
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ 유저 저장 에러: {e}")
        return False
    finally:
        conn.close()


def save_comment_and_analysis(video_id: str, comment_data: dict, analysis_data: dict):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        raw_date = comment_data.get('published_at') or comment_data.get(
            'publishedAt') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_date = date_parser.parse(
            str(raw_date)).strftime('%Y-%m-%d %H:%M:%S')

        user_id = comment_data.get('user_id') or comment_data.get('author')
        comment_id = comment_data.get('comment_id') or comment_data.get(
            'youtube_comment_id') or (str(formatted_date) + str(user_id))

        # [해결] comment_text null 에러 방지: 다양한 키값 대응
        comment_text = comment_data.get('text') or comment_data.get(
            'comment_text') or comment_data.get('content') or "내용 없음"

        with conn.cursor() as cursor:
            sql_comment = """
            INSERT INTO comments (youtube_comment_id, video_id, user_id, comment_text, like_count, published_at)
            VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE like_count=VALUES(like_count), comment_text=VALUES(comment_text)
            """
            cursor.execute(sql_comment, (comment_id, video_id, user_id,
                           comment_text, comment_data.get('like_count', 0), formatted_date))

            cursor.execute(
                "SELECT comment_id FROM comments WHERE youtube_comment_id = %s", (comment_id,))
            row = cursor.fetchone()
            if not row:
                return None

            cat_map = {'정상': 1, '위험': 2, '욕설': 2, '비하': 2, '스팸': 3, '광고': 3}
            cat_id = cat_map.get(analysis_data.get('category'), 1)

            sql_analysis = """
            INSERT INTO comment_analysis (comment_id, category_id, confidence_score, analysis_result) 
            VALUES (%s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE category_id=VALUES(category_id)
            """
            cursor.execute(sql_analysis, (row['comment_id'], cat_id, analysis_data.get(
                'confidence_score', 0.8), analysis_data.get('reason', '')))

            conn.commit()
            return row['comment_id']
    except Exception as e:
        print(f"❌ 댓글 저장 에러: {e}")
        return None
    finally:
        conn.close()

# ==============================
# 3. 통합 저장 및 통계 함수
# ==============================


def save_video_with_comments(video_data: dict, comments: list) -> dict:
    stats = {'videos': 0, 'users': 0, 'comments': 0, 'analyses': 0}
    if save_video(video_data):
        stats['videos'] = 1

    for item in comments:
        # 데이터 구조 유연하게 처리
        u_part = item.get('user', item)
        c_part = item.get('comment', item)
        a_part = item.get('analysis', item)

        user_info = {
            "user_id": u_part.get('author') or u_part.get('user_id'),
            "username": u_part.get('author') or u_part.get('username') or "Unknown",
            "profile_image_url": ""
        }

        if save_user(user_info):
            stats['users'] += 1

        if save_comment_and_analysis(video_data.get('video_id'), c_part, a_part):
            stats['comments'] += 1
            stats['analyses'] += 1

    print(f"📊 DB 저장 결과: {stats}")
    return stats


def get_dashboard_stats():
    conn = get_db_connection()
    if not conn:
        return {"total": 0, "normal": 0, "abuse": 0, "spam": 0}
    try:
        with conn.cursor() as cursor:
            sql = "SELECT COUNT(*) as total, SUM(CASE WHEN category_id = 1 THEN 1 ELSE 0 END) as normal, SUM(CASE WHEN category_id = 2 THEN 1 ELSE 0 END) as abuse, SUM(CASE WHEN category_id = 3 THEN 1 ELSE 0 END) as spam FROM comment_analysis"
            cursor.execute(sql)
            res = cursor.fetchone()
            return {"total": res['total'] or 0, "normal": int(res['normal'] or 0), "abuse": int(res['abuse'] or 0), "spam": int(res['spam'] or 0)}
    finally:
        conn.close()

# ==============================
# 4. DB 초기화 (컬럼명 오류 해결)
# ==============================


def init_database():
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cursor:
            # [해결] 컬럼명을 알 수 없을 때를 대비해 display_name 등으로 시도
            # 먼저 categories 테이블의 실제 컬럼명을 확인하는 것이 좋으나,
            # 가장 흔한 'category_name'과 'name' 두 가지를 모두 시도하도록 수정
            categories = [(1, '정상'), (2, '위험'), (3, '스팸')]

            try:
                cursor.executemany(
                    "INSERT IGNORE INTO categories (category_id, name) VALUES (%s, %s)", categories)
            except:
                try:
                    cursor.executemany(
                        "INSERT IGNORE INTO categories (category_id, display_name) VALUES (%s, %s)", categories)
                except:
                    cursor.executemany(
                        "INSERT IGNORE INTO categories (category_id, category_name) VALUES (%s, %s)", categories)

        conn.commit()
        print("✅ DB 카테고리 초기화 완료")
    except Exception as e:
        print(f"⚠️ 초기화 최종 실패: {e}")
    finally:
        conn.close()
