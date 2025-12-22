# MariaDB 서버 설정 확인 체크리스트

## 현재 상태
- ❌ 포트 연결 실패 (오류 코드: 10035)
- ❌ MariaDB 연결 타임아웃

## 서버(1.220.247.75)에서 확인해야 할 사항

### 1. MariaDB 서비스 실행 확인
```bash
sudo systemctl status mariadb
# 또는
sudo service mariadb status
```

서비스가 실행 중이 아니라면:
```bash
sudo systemctl start mariadb
sudo systemctl enable mariadb
```

### 2. MariaDB bind-address 설정 확인 및 수정

#### 설정 파일 위치 확인:
```bash
# Ubuntu/Debian
sudo nano /etc/mysql/mariadb.conf.d/50-server.cnf

# CentOS/RHEL
sudo nano /etc/my.cnf.d/server.cnf
```

#### 설정 확인:
```ini
[mysqld]
bind-address = 0.0.0.0    # ✅ 이렇게 설정되어 있어야 함
# 또는
# bind-address = 1.220.247.75
```

**주의**: `bind-address = 127.0.0.1` 또는 `bind-address = localhost`로 되어 있으면 외부 접속 불가!

#### MariaDB 재시작:
```bash
sudo systemctl restart mariadb
```

### 3. 방화벽 설정 확인

#### Ubuntu/Debian (ufw):
```bash
# 포트 확인
sudo ufw status | grep 3306

# 포트 열기 (아직 안 열려있다면)
sudo ufw allow 3306/tcp
sudo ufw reload

# 상태 확인
sudo ufw status verbose
```

#### CentOS/RHEL (firewalld):
```bash
# 포트 확인
sudo firewall-cmd --list-ports | grep 3306

# 포트 열기
sudo firewall-cmd --permanent --add-port=3306/tcp
sudo firewall-cmd --reload

# 상태 확인
sudo firewall-cmd --list-all
```

#### iptables 직접 사용하는 경우:
```bash
# 규칙 확인
sudo iptables -L -n | grep 3306

# 규칙 추가
sudo iptables -A INPUT -p tcp --dport 3306 -j ACCEPT
sudo iptables-save
```

### 4. MariaDB 사용자 권한 확인

MariaDB에 접속해서:
```bash
mysql -u root -p
```

다음 명령 실행:
```sql
-- 현재 사용자 권한 확인
SELECT user, host FROM mysql.user WHERE user='root';

-- 외부 접속 허용 (모든 IP)
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY '1234' WITH GRANT OPTION;
FLUSH PRIVILEGES;

-- 또는 특정 IP만 허용
GRANT ALL PRIVILEGES ON *.* TO 'root'@'192.168.0.25' IDENTIFIED BY '1234' WITH GRANT OPTION;
FLUSH PRIVILEGES;
```

### 5. 네트워크 확인

서버에서 자신의 IP 확인:
```bash
ip addr show
# 또는
ifconfig
```

로컬에서 MariaDB 포트 리스닝 확인:
```bash
sudo netstat -tlnp | grep 3306
# 또는
sudo ss -tlnp | grep 3306
```

다음과 같이 표시되어야 함:
```
tcp  0  0  0.0.0.0:3306  0.0.0.0:*  LISTEN  ...
```

**주의**: `127.0.0.1:3306`으로만 표시되면 외부 접속 불가!

### 6. 테스트

서버에서 로컬 연결 테스트:
```bash
mysql -h 127.0.0.1 -P 3306 -u root -p
```

외부에서 연결 테스트 (다른 컴퓨터에서):
```bash
mysql -h 1.220.247.75 -P 3306 -u root -p
```

## 빠른 진단 스크립트

서버에서 다음 명령들을 실행해서 결과를 확인하세요:

```bash
# 1. MariaDB 실행 확인
sudo systemctl status mariadb | grep Active

# 2. 포트 리스닝 확인
sudo netstat -tlnp | grep 3306

# 3. bind-address 확인
sudo grep -r "bind-address" /etc/mysql/ /etc/my.cnf 2>/dev/null

# 4. 방화벽 확인
sudo ufw status 2>/dev/null || sudo firewall-cmd --list-all 2>/dev/null
```

## 설정 완료 후

모든 설정을 완료한 후:
1. MariaDB 재시작: `sudo systemctl restart mariadb`
2. 방화벽 재로드: `sudo ufw reload` 또는 `sudo firewall-cmd --reload`
3. 로컬에서 다시 연결 테스트: `python test_db_connection.py`

