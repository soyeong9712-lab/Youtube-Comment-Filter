# ==============================
# DB 연결 테스트 스크립트
# ==============================
import pymysql
import sys
import socket

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

DB_CONFIG = {
    "host": "1.220.247.75",
    "port": 3306,
    "user": "root",
    "password": "1234",
    "database": "root",
    "charset": "utf8mb4",
    "connect_timeout": 10,
    "read_timeout": 10,
    "write_timeout": 10
}

print("=" * 50)
print("MariaDB 연결 테스트")
print("=" * 50)
print(f"서버: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
print(f"데이터베이스: {DB_CONFIG['database']}")
print(f"사용자: {DB_CONFIG['user']}")
print("-" * 50)

# 먼저 소켓 연결 테스트
print("1단계: 소켓 연결 테스트...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((DB_CONFIG['host'], DB_CONFIG['port']))
    sock.close()
    
    if result == 0:
        print("   [OK] 포트가 열려있습니다.")
    else:
        print(f"   [FAIL] 포트 연결 실패 (코드: {result})")
        print("   -> 방화벽 또는 MariaDB 서버 설정을 확인하세요.")
except Exception as e:
    print(f"   [FAIL] 소켓 테스트 실패: {e}")

print("\n2단계: MariaDB 연결 시도...")
try:
    connection = pymysql.connect(**DB_CONFIG)
    print("✅ 연결 성공!")
    
    # 간단한 쿼리 테스트
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"✅ MariaDB 버전: {version[0]}")
        
        # 데이터베이스 목록 확인
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        print(f"✅ 사용 가능한 데이터베이스: {[db[0] for db in databases]}")
        
        # 현재 데이터베이스의 테이블 확인
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        if tables:
            print(f"✅ 테이블 목록: {[table[0] for table in tables]}")
        else:
            print("ℹ️  테이블이 없습니다. (정상 - 아직 생성되지 않음)")
    
    connection.close()
    print("=" * 50)
    print("✅ 모든 테스트 통과!")
    sys.exit(0)
    
except pymysql.err.OperationalError as e:
    error_code, error_msg = e.args
    print(f"❌ 연결 실패 (오류 코드: {error_code})")
    print(f"   메시지: {error_msg}")
    
    if error_code == 2003:
        print("\n💡 해결 방법:")
        print("   1. MariaDB 서버가 실행 중인지 확인")
        print("   2. bind-address 설정 확인 (0.0.0.0 또는 서버 IP)")
        print("   3. 방화벽에서 3306 포트가 열려있는지 확인")
    elif error_code == 1045:
        print("\n💡 해결 방법:")
        print("   1. 사용자명과 비밀번호 확인")
        print("   2. 사용자 권한 확인")
    elif error_code == 1049:
        print("\n💡 해결 방법:")
        print("   1. 데이터베이스 이름 확인")
        print("   2. 데이터베이스가 존재하는지 확인")
    
    sys.exit(1)
    
except Exception as e:
    print(f"❌ 예상치 못한 오류: {e}")
    sys.exit(1)

