# MariaDB 연결 문제 해결 가이드

## 현재 상황
- 서버 IP: `1.220.247.75`
- 포트: `3306`
- Ping은 성공하지만 3306 포트 연결 실패

## 해결 방법

### 1. MariaDB 서버에서 외부 접속 허용 설정

MariaDB 서버(1.220.247.75)에서 다음 설정을 확인하세요:

#### `/etc/mysql/mariadb.conf.d/50-server.cnf` 파일 수정:

```ini
[mysqld]
bind-address = 0.0.0.0  # 모든 IP에서 접속 허용 (또는 특정 IP 지정)
```

또는

```ini
[mysqld]
bind-address = 1.220.247.75  # 특정 IP만 허용
```

#### MariaDB 재시작:
```bash
sudo systemctl restart mariadb
# 또는
sudo service mariadb restart
```

### 2. 방화벽 설정 확인

#### MariaDB 서버에서 3306 포트 열기:

**Ubuntu/Debian:**
```bash
sudo ufw allow 3306/tcp
sudo ufw reload
```

**CentOS/RHEL:**
```bash
sudo firewall-cmd --permanent --add-port=3306/tcp
sudo firewall-cmd --reload
```

### 3. 사용자 권한 확인

MariaDB 서버에서 다음 명령 실행:

```sql
-- root 사용자로 로그인
mysql -u root -p

-- 외부 접속 허용 확인
SELECT user, host FROM mysql.user WHERE user='root';

-- 외부 접속 허용 (필요한 경우)
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY '1234' WITH GRANT OPTION;
FLUSH PRIVILEGES;
```

### 4. 연결 테스트

로컬에서 연결 테스트:

```bash
# Windows PowerShell
Test-NetConnection -ComputerName 1.220.247.75 -Port 3306

# 또는 MySQL 클라이언트로 직접 테스트
mysql -h 1.220.247.75 -P 3306 -u root -p
```

### 5. 보안 고려사항

⚠️ **주의**: 외부 접속을 허용할 때는 보안을 고려하세요:

1. **강력한 비밀번호 사용**
2. **특정 IP만 허용** (가능한 경우)
3. **SSH 터널링 사용** (더 안전한 방법)
4. **SSL 연결 사용**

## 현재 코드 동작

코드는 다음과 같이 동작합니다:

- ✅ DB 연결 실패 시에도 서버는 정상 실행됩니다
- ✅ 댓글 분석 기능은 정상 작동합니다
- ⚠️ DB 연결이 실패하면 댓글 저장만 안 됩니다 (분석은 계속 됨)
- ✅ 연결 성공 시 자동으로 테이블이 생성됩니다

## 테스트 방법

서버를 실행한 후:
```bash
python run.py
```

콘솔에서 다음 메시지를 확인하세요:
- `✅ DB 초기화 완료` → 연결 성공
- `⚠️ DB 초기화 실패` → 연결 실패 (위의 설정 확인 필요)

