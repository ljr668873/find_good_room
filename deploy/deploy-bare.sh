#!/bin/bash
# 裸机一键部署/更新（Linux 服务器：systemd + nginx，非 Docker）
#
# 用法（唯一命令，可重复执行 = 更新发布）：
#   sudo bash deploy/deploy-bare.sh
#
# 零人工设计：
#   - deploy/.env 不存在时自动探测生成（继承旧 dev 进程环境变量 / 旧项目 .env / MySQL 常见密码），仅全部失败才询问
#   - 自动停掉旧的 vite dev / uvicorn dev 进程
#   - nginx 缺失自动安装；MySQL 先试连再部署，早失败早报
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT=$(pwd)

# ---- 0. 环境自检 ----
[ "$(id -u)" = 0 ] || { echo "请用 sudo 运行"; exit 1; }

PYV=$(python3 -c 'import sys; print(f"{sys.version_info[0]}{sys.version_info[1]}")')
if [ "$PYV" -lt 310 ]; then
  echo "python3 版本过低（$(python3 -V)，需 3.10+）。安装："
  echo "  Ubuntu/Debian: apt-get install -y python3.11 python3.11-venv"
  echo "  CentOS/RHEL  : dnf install -y python3.11 或使用 SCL"
  exit 1
fi

command -v rsync >/dev/null || { apt-get install -y rsync 2>/dev/null || dnf install -y rsync || { echo "缺少 rsync 且自动安装失败"; exit 1; }; }
if ! command -v nginx >/dev/null; then
  echo "安装 nginx ..."
  apt-get install -y nginx 2>/dev/null || dnf install -y nginx || { echo "nginx 自动安装失败，请手动安装后重跑"; exit 1; }
fi
command -v systemctl >/dev/null || { echo "缺少 systemd，本脚本仅支持 systemd 主机"; exit 1; }
command -v curl >/dev/null || { apt-get install -y curl 2>/dev/null || dnf install -y curl; }

# ---- 1. 配置：.env 自动生成（核心零人工点）----
ENV_FILE="deploy/.env"

gen_db_password() { echo "Root@123"; }   # 常见本地默认，兜底候选

detect_db_password() {
  # 依次：旧项目 .env → 运行中的 uvicorn 进程环境 → mysql-local 容器 → 常见默认
  for f in "$ROOT/server/.env" "/data/src/find_good_room/server/.env"; do
    [ -f "$f" ] && grep -E '^DB_PASSWORD=' "$f" 2>/dev/null | head -1 | cut -d= -f2- && return 0
  done
  for pid in $(pgrep -f "uvicorn app.main" 2>/dev/null || true); do
    tr '\0' '\n' < "/proc/$pid/environ" 2>/dev/null | grep -E '^DB_PASSWORD=' | head -1 | cut -d= -f2- && return 0
  done
  docker exec mysql-local printenv MYSQL_ROOT_PASSWORD 2>/dev/null && return 0
  return 1
}

if [ ! -f "$ENV_FILE" ]; then
  echo "[配置] $ENV_FILE 不存在，自动探测生成 ..."
  DETECTED_PWD=$(detect_db_password || true)
  DB_PASSWORD_VALUE="${DETECTED_PWD:-Root@123}"
  cat > "$ENV_FILE" <<EOF
# 由 deploy-bare.sh 自动生成（$(date '+%F %T')），可手动修改后重跑
DB_PASSWORD=$DB_PASSWORD_VALUE
DB_NAME=find_good_room
HTTP_PORT=80
INSTALL_DIR=/opt/find_good_room
SERVER_NAME=$(curl -s -m 5 ifconfig.me 2>/dev/null || echo _)
API_PORT=8000
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
JWT_SECRET=$(head -c 32 /dev/urandom | base64 | tr -d '=+/')
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123456
LOAD_DEMO=0
EOF
  chmod 600 "$ENV_FILE"
  echo "[配置] 已生成 $ENV_FILE（数据库密码来源：$([ -n "$DETECTED_PWD" ] && echo "自动探测" || echo "默认值 Root@123")）"
fi

set -a; source "$ENV_FILE"; set +a

INSTALL_DIR="${INSTALL_DIR:-/opt/find_good_room}"
SERVER_NAME="${SERVER_NAME:-_}"
API_PORT="${API_PORT:-8000}"
HTTP_PORT="${HTTP_PORT:-80}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-root}"
DB_NAME="${DB_NAME:-find_good_room}"
DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD 为空，请检查 $ENV_FILE}"
JWT_SECRET="${JWT_SECRET:?JWT_SECRET 为空}"
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:?ADMIN_PASSWORD 为空}"

# ---- 2. 停旧 dev 进程（vite dev / 旧 uvicorn dev）----
pgrep -f "node_modules/.bin/vite" >/dev/null 2>&1 && {
  echo "[清理] 停止旧的 vite dev 进程 ..."
  pkill -f "node_modules/.bin/vite" 2>/dev/null || true
  sleep 1
}
if pgrep -f "uvicorn app.main" >/dev/null 2>&1 && ss -ltn 2>/dev/null | grep -q ":$API_PORT "; then
  echo "[清理] 停止占用 $API_PORT 的旧后端进程 ..."
  pkill -f "uvicorn app.main" 2>/dev/null || true
  sleep 1
fi

# ---- 3. 前端产物 ----
if [ ! -d web/dist ]; then
  if command -v node >/dev/null; then
    echo "[前端] 检测到 node，现场构建 ..."
    (cd web && npm install --silent && npm run build)
  else
    echo "web/dist 不存在且服务器无 node：请在本地 npm run build 后把 dist 一起上传，或安装 node"
    exit 1
  fi
fi

# ---- 4. MySQL 试连（早失败，避免迁移中途炸）----
mysql_probe() {
  python3 - "$DB_HOST" "$DB_PORT" "$DB_USER" "$DB_PASSWORD" <<'PYEOF'
import socket, sys
host, port, user, pwd = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
try:
    import pymysql
    pymysql.connect(host=host, port=port, user=user, password=pwd, connect_timeout=5)
    print("  MySQL 连接 OK")
except ImportError:
    s = socket.socket(); s.settimeout(5); s.connect((host, port)); s.close()
    print("  MySQL 端口可达（pymysql 未装，部署步骤中会安装后再验证）")
except Exception as e:
    print(f"  连接失败: {e}", file=sys.stderr); sys.exit(1)
PYEOF
}
echo "[检查] MySQL 连接 $DB_HOST:$DB_PORT ..."
if ! mysql_probe; then
  echo "✗ MySQL 连接失败。检查：1) 密码是否正确（当前来自 $ENV_FILE）2) MySQL 是否运行"
  exit 1
fi

# ---- 5. 同步文件（目标 .venv 与 uploads 不覆盖）----
echo "[1/6] 同步文件到 $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
rsync -a --exclude '.venv' --exclude 'uploads' --exclude '__pycache__' "$ROOT/server/" "$INSTALL_DIR/server/"
rsync -a "$ROOT/web/dist/" "$INSTALL_DIR/web-dist/"

# ---- 6. 后端依赖 ----
if [ ! -x "$INSTALL_DIR/server/.venv/bin/python" ]; then
  echo "[2/6] 创建 venv ..."
  python3 -m venv "$INSTALL_DIR/server/.venv"
fi
echo "[2/6] 依赖同步 ..."
"$INSTALL_DIR/server/.venv/bin/pip" install -q "$INSTALL_DIR/server"

# ---- 7. 运行时环境文件 ----
echo "[3/6] 生成运行时配置 ..."
cat > "$INSTALL_DIR/app.env" <<EOF
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME
JWT_SECRET=$JWT_SECRET
UPLOAD_DIR=$INSTALL_DIR/uploads
EOF
chmod 600 "$INSTALL_DIR/app.env"
mkdir -p "$INSTALL_DIR/uploads"

# ---- 8. 数据库（幂等，不动已有数据）----
echo "[4/6] 数据库迁移 + 种子 ..."
set -a; source "$INSTALL_DIR/app.env"; set +a
(cd "$INSTALL_DIR/server" && .venv/bin/alembic upgrade head)
(cd "$INSTALL_DIR/server" && ADMIN_USERNAME="$ADMIN_USERNAME" ADMIN_PASSWORD="$ADMIN_PASSWORD" .venv/bin/python -m scripts.seed)
if [ "${LOAD_DEMO:-0}" = "1" ]; then
  echo "      导入演示数据 ..."
  (cd "$INSTALL_DIR/server" && .venv/bin/python -m scripts.import_demo)
fi

# ---- 9. systemd ----
echo "[5/6] 配置 systemd 服务 ..."
cat > /etc/systemd/system/find-good-room.service <<EOF
[Unit]
Description=guanhaofang API
After=network.target mysqld.service mysql.service

[Service]
WorkingDirectory=$INSTALL_DIR/server
EnvironmentFile=$INSTALL_DIR/app.env
ExecStart=$INSTALL_DIR/server/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port $API_PORT
Restart=always

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable find-good-room >/dev/null
systemctl restart find-good-room

# ---- 10. nginx ----
echo "[6/6] 配置 nginx ..."
[ -f /etc/nginx/conf.d/default.conf ] && rm -f /etc/nginx/conf.d/default.conf && echo "      已移除 nginx 默认站点"
cat > /etc/nginx/conf.d/find-good-room.conf <<EOF
server {
    listen $HTTP_PORT;
    server_name $SERVER_NAME;
    client_max_body_size 100m;

    location /api/ {
        proxy_pass http://127.0.0.1:$API_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
    location /uploads/ {
        proxy_pass http://127.0.0.1:$API_PORT;
    }
    location /static/ {
        proxy_pass http://127.0.0.1:$API_PORT;
    }
    location / {
        root $INSTALL_DIR/web-dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
nginx -t
systemctl reload nginx 2>/dev/null || systemctl restart nginx

# SELinux 提示（CentOS/RHEL enforcing 下 nginx 读 /opt 静态文件会 403）
if command -v getenforce >/dev/null && [ "$(getenforce)" = "Enforcing" ]; then
  echo "⚠ SELinux 为 Enforcing：若站点静态文件 403，执行"
  echo "  sudo chcon -R -t httpd_sys_content_t $INSTALL_DIR/web-dist"
fi
echo "提示：云服务器安全组/防火墙需放行对外端口 $HTTP_PORT"

# ---- 健康检查 ----
sleep 3
if curl -fs "http://127.0.0.1:$API_PORT/api/health" >/dev/null; then
  IP=$(curl -s -m 5 ifconfig.me 2>/dev/null || echo 服务器IP)
  echo
  echo "=============================="
  echo " 部署完成 ✓"
  echo " 站点   : http://$IP:$HTTP_PORT"
  echo " 服务   : systemctl status find-good-room"
  echo " 日志   : journalctl -u find-good-room -f"
  echo " 更新   : git pull && sudo bash deploy/deploy-bare.sh"
  echo "=============================="
else
  echo "✗ 健康检查失败，查看日志：journalctl -u find-good-room -n 50"
  exit 1
fi
