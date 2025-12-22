# MariaDB 포트 열기 가이드

## 서버(1.220.247.75)에서 해야 할 작업

### 1단계: 방화벽에서 포트 열기

#### Ubuntu/Debian (ufw 사용하는 경우):
```bash
# 포트 열기
sudo ufw allow 3306/tcp

# 방화벽 재로드
sudo ufw reload

# 상태 확인
sudo ufw status
```

#### CentOS/RHEL (firewalld 사용하는 경우):
```bash
# 포트 열기
sudo firewall-cmd --permanent --add-port=3306/tcp

# 방화벽 재로드
sudo firewall-cmd --reload

# 상태 확인
sudo firewall-cmd --list-ports
```

#### iptables 직접 사용하는 경우:
```bash
# 규칙 추가
sudo iptables -A INPUT -p tcp --dport 3306 -j ACCEPT

# 규칙 저장 (Ubuntu/Debian)
sudo iptables-save | sudo tee /etc/iptables/rules.v4

# 규칙 저장 (CentOS/RHEL)
sudo service iptables save
```

---

### 2단계: MariaDB 외부 접속 허용 설정 (⚠️ 매우 중요!)

방화벽만 열어서는 안 되고, MariaDB 자체가 외부 접속을 허용해야 합니다.

#### 설정 파일 찾기:
```bash
# Ubuntu/Debian
sudo nano /etc/mysql/mariadb.conf.d/50-server.cnf

# 또는
sudo nano /etc/mysql/my.cnf

# CentOS/RHEL
sudo nano /etc/my.cnf.d/server.cnf
```

#### 설정 수정:
`[mysqld]` 섹션에서 다음을 확인/수정:

```ini
[mysqld]
# ❌ 이렇게 되어 있으면 외부 접속 불가
# bind-address = 127.0.0.1

# ✅ 이렇게 변경해야 함
bind-address = 0.0.0.0
```

또는 주석 처리:
```ini
[mysqld]
# bind-address = 127.0.0.1
```

#### MariaDB 재시작:
```bash
sudo systemctl restart mariadb
# 또는
sudo service mariadb restart
```

#### 포트 리스닝 확인:
```bash
sudo netstat -tlnp | grep 3306
```

다음과 같이 표시되어야 함:
```
tcp  0  0  0.0.0.0:3306  0.0.0.0:*  LISTEN  ...
```

**주의**: `127.0.0.1:3306`으로만 표시되면 아직 외부 접속 불가!

---

### 3단계: 사용자 권한 설정

MariaDB에 접속:
```bash
mysql -u root -p
```

다음 명령 실행:
```sql
-- 외부 접속 허용 (모든 IP)
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY '1234' WITH GRANT OPTION;
FLUSH PRIVILEGES;

-- 또는 특정 IP만 허용 (더 안전)
GRANT ALL PRIVILEGES ON *.* TO 'root'@'192.168.0.25' IDENTIFIED BY '1234' WITH GRANT OPTION;
FLUSH PRIVILEGES;

-- 권한 확인
SELECT user, host FROM mysql.user WHERE user='root';
```

---

## 빠른 확인 스크립트

서버에서 다음 명령들을 실행해서 확인:

```bash
# 1. MariaDB 실행 상태
echo "=== MariaDB 상태 ==="
sudo systemctl status mariadb | grep Active

# 2. 포트 리스닝 확인
echo -e "\n=== 포트 리스닝 ==="
sudo netstat -tlnp | grep 3306

# 3. bind-address 확인
echo -e "\n=== bind-address 설정 ==="
sudo grep -r "bind-address" /etc/mysql/ /etc/my.cnf 2>/dev/null | grep -v "^#"

# 4. 방화벽 확인
echo -e "\n=== 방화벽 상태 ==="
sudo ufw status 2>/dev/null || sudo firewall-cmd --list-all 2>/dev/null || echo "iptables 사용 중"
```

---

## 완료 후 테스트

로컬 컴퓨터에서:
```bash
python test_db_connection.py
```

또는 직접 MySQL 클라이언트로:
```bash
mysql -h 1.220.247.75 -P 3306 -u root -p
```

---

## 중요 사항

1. **방화벽만 열면 안 됩니다!** MariaDB의 `bind-address` 설정도 변경해야 합니다.
2. **보안**: 가능하면 특정 IP만 허용하는 것이 좋습니다.
3. **재시작**: 설정 변경 후 반드시 MariaDB를 재시작해야 합니다.

