#!/bin/bash
# MariaDB 포트 설정 빠른 확인 스크립트
# 서버(1.220.247.75)에서 실행하세요

echo "=========================================="
echo "MariaDB 포트 설정 확인"
echo "=========================================="

# 1. MariaDB 실행 상태
echo -e "\n[1] MariaDB 서비스 상태:"
sudo systemctl status mariadb --no-pager | grep -E "Active|Loaded" || echo "서비스 확인 실패"

# 2. 포트 리스닝 확인
echo -e "\n[2] 3306 포트 리스닝 상태:"
PORT_CHECK=$(sudo netstat -tlnp 2>/dev/null | grep 3306 || sudo ss -tlnp 2>/dev/null | grep 3306)
if [ -z "$PORT_CHECK" ]; then
    echo "   ❌ 3306 포트가 리스닝되지 않습니다!"
else
    echo "   ✅ 포트 리스닝 중:"
    echo "$PORT_CHECK" | sed 's/^/      /'
    
    # 0.0.0.0인지 확인
    if echo "$PORT_CHECK" | grep -q "0.0.0.0:3306"; then
        echo "   ✅ 외부 접속 허용됨 (0.0.0.0)"
    elif echo "$PORT_CHECK" | grep -q "127.0.0.1:3306"; then
        echo "   ❌ 로컬만 허용됨 (127.0.0.1) - bind-address 설정 필요!"
    fi
fi

# 3. bind-address 설정 확인
echo -e "\n[3] bind-address 설정:"
BIND_CHECK=$(sudo grep -r "bind-address" /etc/mysql/ /etc/my.cnf /etc/my.cnf.d/ 2>/dev/null | grep -v "^#" | grep -v "^;" | head -1)
if [ -z "$BIND_CHECK" ]; then
    echo "   ⚠️  bind-address 설정을 찾을 수 없습니다 (기본값 사용 중일 수 있음)"
else
    echo "   현재 설정:"
    echo "$BIND_CHECK" | sed 's/^/      /'
    if echo "$BIND_CHECK" | grep -q "127.0.0.1"; then
        echo "   ❌ 외부 접속 불가! 0.0.0.0으로 변경 필요"
    elif echo "$BIND_CHECK" | grep -q "0.0.0.0"; then
        echo "   ✅ 외부 접속 허용됨"
    fi
fi

# 4. 방화벽 확인
echo -e "\n[4] 방화벽 상태:"
if command -v ufw &> /dev/null; then
    echo "   UFW 사용 중:"
    sudo ufw status | grep 3306 || echo "      ❌ 3306 포트 규칙 없음"
elif command -v firewall-cmd &> /dev/null; then
    echo "   firewalld 사용 중:"
    sudo firewall-cmd --list-ports | grep 3306 || echo "      ❌ 3306 포트 규칙 없음"
else
    echo "   iptables 사용 중 (수동 확인 필요)"
fi

# 5. 사용자 권한 확인
echo -e "\n[5] 사용자 권한 (root):"
mysql -u root -p1234 -e "SELECT user, host FROM mysql.user WHERE user='root';" 2>/dev/null || echo "   ⚠️  MySQL 접속 실패 (비밀번호 확인 필요)"

echo -e "\n=========================================="
echo "확인 완료"
echo "=========================================="

