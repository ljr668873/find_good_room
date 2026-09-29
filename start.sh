#!/bin/bash
# 一键启动本地开发环境：MySQL 容器 + 后端(API) + 前端(Vite)
# 用法：./start.sh    停止：Ctrl+C（前后端一起停）
set -e
cd "$(dirname "$0")"

# ---- 可通过环境变量覆盖本地 MySQL 连接 ----
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-Root@123}"
DB_NAME="${DB_NAME:-find_good_room}"
export DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME

# ---- 服务端口与监听地址（vite.config.js 读取同一环境变量做代理）----
# 注意：5000 被 macOS AirPlay 接收器（ControlCenter）占用，别用作 API_PORT
API_PORT="${API_PORT:-5002}"
WEB_PORT="${WEB_PORT:-5001}"
HOST="${HOST:-0.0.0.0}"   # 0.0.0.0 = 局域网可访问（手机联调用）；只想本机访问设 HOST=127.0.0.1
export API_PORT WEB_PORT HOST

# ---- 1. MySQL：本地容器 mysql-local，没跑就拉起 ----
if ! docker exec mysql-local mysql -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1" &>/dev/null; then
  echo "[1/5] MySQL 未运行，尝试启动容器 mysql-local ..."
  docker start mysql-local >/dev/null 2>&1 || {
    echo "MySQL 不可用。请先启动 mysql-local 容器，或用 DB_HOST/DB_PORT/DB_USER/DB_PASSWORD 指向其它 MySQL。"
    exit 1
  }
  sleep 3
else
  echo "[1/5] MySQL 已运行"
fi

docker exec mysql-local mysql -u"$DB_USER" -p"$DB_PASSWORD" \
  -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci" 2>/dev/null \
  || echo "（跳过建库：非 mysql-local 容器时请自行建库 $DB_NAME）"

# ---- 2. 后端依赖 ----
if [ ! -x server/.venv/bin/python ]; then
  echo "[2/5] 创建后端 venv 并安装依赖 ..."
  python3 -m venv server/.venv
  server/.venv/bin/pip install -q -e server
else
  echo "[2/5] 后端依赖就绪"
fi

# ---- 3. 数据库迁移 + 种子（幂等）----
echo "[3/5] 迁移数据库 ..."
(cd server && .venv/bin/alembic upgrade head -q 2>/dev/null || .venv/bin/alembic upgrade head)
echo "[3/5] 种子数据 ..."
(cd server && .venv/bin/python -m scripts.seed)

# ---- 4. 前端依赖 ----
if [ ! -d web/node_modules ]; then
  echo "[4/5] 安装前端依赖 ..."
  (cd web && npm install --silent)
else
  echo "[4/5] 前端依赖就绪"
fi

# ---- 4.5 端口预检：按端口找占用 PID，本项目旧实例才清理，其它程序报错退出 ----
port_busy() { lsof -nP -iTCP:"$1" -sTCP:LISTEN 2>/dev/null | grep -q LISTEN; }

# 清理指定端口：占用者全是本项目服务（uvicorn/vite）则杀掉返回 0，遇到外来进程返回 1
clean_port() {
  local pid
  for pid in $(lsof -nP -iTCP:"$1" -sTCP:LISTEN -t 2>/dev/null); do
    if ps -p "$pid" -o command= 2>/dev/null | grep -qE "uvicorn app\.main:app|find_good_room/web/node_modules/\.bin/vite"; then
      kill "$pid" 2>/dev/null
    else
      return 1
    fi
  done
  return 0
}

for PORT_TO_CHECK in "$API_PORT" "$WEB_PORT"; do
  if port_busy "$PORT_TO_CHECK"; then
    if clean_port "$PORT_TO_CHECK"; then
      echo "      端口 $PORT_TO_CHECK 被旧实例占用，已清理"
    else
      echo "端口 $PORT_TO_CHECK 被其它程序占用（不会强杀）："
      lsof -nP -iTCP:"$PORT_TO_CHECK" -sTCP:LISTEN 2>/dev/null | grep LISTEN
      echo "换端口：API_PORT=5003 WEB_PORT=5004 ./start.sh"
      exit 1
    fi
  fi
done
sleep 1
if port_busy "$API_PORT" || port_busy "$WEB_PORT"; then
  echo "旧实例清理后端口仍被占（可能刚释放中，稍等重试）"
  exit 1
fi

# ---- 5. 启动前后端 ----
# exec 替换子 shell：保证 $PID 就是服务进程本身，Ctrl+C 能直接杀掉
echo "[5/5] 启动服务 ..."
(cd server && exec .venv/bin/uvicorn app.main:app --host "$HOST" --port "$API_PORT") &
API_PID=$!
(cd web && exec ./node_modules/.bin/vite) &
WEB_PID=$!

trap 'kill $API_PID $WEB_PID 2>/dev/null; echo; echo "已停止"' INT TERM EXIT

sleep 3
LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "")
echo
echo "============================================"
echo "  后端 API : http://127.0.0.1:$API_PORT/api/health"
echo "  前端页面 : http://localhost:$WEB_PORT"
if [ -n "$LAN_IP" ] && [ "$HOST" = "0.0.0.0" ]; then
  echo "  手机访问 : http://$LAN_IP:$WEB_PORT   （同一 WiFi）"
fi
echo "  （Ctrl+C 一起停止）"
echo "============================================"
wait
