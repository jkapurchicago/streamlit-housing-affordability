#!/usr/bin/env bash
set -euo pipefail

ORACLE_SOCK="/tmp/mysql.sock"
ORACLE_PW="279i271j"
OUT1="$HOME/oracle_tables.txt"
OUT2="$HOME/brew_tables.txt"

echo "== Oracle -> $OUT1 =="
mysql -uroot -p"$ORACLE_PW" -S "$ORACLE_SOCK" -N -e "
SELECT CONCAT(table_schema,'.',table_name)
FROM information_schema.tables
WHERE table_schema NOT IN ('mysql','performance_schema','information_schema','sys')
ORDER BY 1;" | tee "$OUT1"

echo
echo "== Brew (trying TCP :3306; will fall back to skip-grant if needed) =="

if mysql -uroot -h127.0.0.1 -P3306 -N -e "SELECT 1" >/dev/null 2>&1; then
  mysql -uroot -h127.0.0.1 -P3306 -N -e "
  SELECT CONCAT(table_schema,'.',table_name)
  FROM information_schema.tables
  WHERE table_schema NOT IN ('mysql','performance_schema','information_schema','sys')
  ORDER BY 1;" | tee "$OUT2"
else
  echo "TCP failed; trying temporary skip-grant on custom socket..."
  BREW_MYSQLD="$(brew --prefix mysql)/bin/mysqld"
  sudo pkill -f "$BREW_MYSQLD" 2>/dev/null || true
  sudo rm -f /tmp/mysql-reset.sock /tmp/mysqlx-reset.sock /tmp/mysql*.lock 2>/dev/null || true
  sudo -u _mysql "$BREW_MYSQLD" \
    --skip-grant-tables --skip-networking \
    --socket=/tmp/mysql-reset.sock \
    --mysqlx_socket=/tmp/mysqlx-reset.sock \
    --pid-file=/opt/homebrew/var/mysql/mysqld.reset.pid \
    --datadir=/opt/homebrew/var/mysql >/tmp/brew-skip.log 2>&1 &
  sleep 2
  mysql -uroot -S /tmp/mysql-reset.sock -N -e "
  SELECT CONCAT(table_schema,'.',table_name)
  FROM information_schema.tables
  WHERE table_schema NOT IN ('mysql','performance_schema','information_schema','sys')
  ORDER BY 1;" | tee "$OUT2"
  sudo pkill -f "$BREW_MYSQLD" || true
fi

echo
echo "== Diff =="
echo "In Oracle but not in Brew:"
comm -23 <(sort "$OUT1") <(sort "$OUT2") || true
echo
echo "In Brew but not in Oracle:"
comm -13 <(sort "$OUT1") <(sort "$OUT2") || true
