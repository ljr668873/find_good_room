#!/bin/bash
# 裸机一键部署/更新（Linux 服务器：systemd + nginx，非 Docker）
#
# 用法：
#   1. 项目放到服务器（git clone 或 rsync 上来）
#   2. cd deploy && cp .env.example .env && 修改其中值
#   3. sudo bash deploy-bare.sh          # 首次部署；之后重跑 = 更新发布
#
# 前置：python3(3.12+)、nginx、MySQL（本机或可达）；node 仅在需要现场构建前端时要求，
#       没有 node 就提前在本地 npm run build 带上 web/dist 一起上传。
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT=$(pwd)

# ---- 配置 ----
ENV_FILE="deploy/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "缺少 $ENV_FILE：先 cp deploy/.env.example deploy/.env 并修改"
  exit 1
fi
set -a; source "$ENV_FILE"; set +a

INSTALL_DIR="${INSTALL_DIR:-/opt/find_good_room}"
SERVER_NAME="${SERVER_NAME:-_}"          # nginx server_name，填域名或公网 IP
API_PORT="${API_PORT:-8000}"             # 后端监听（仅本机）
HTTP_PORT="${HTTP_PORT:-80}"             # nginx 对外端口
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-root}"
DB_NAME="${DB_NAME:-find_good_room}"
DB_PASSWORD="${DB_PASSWORD:?请在 deploy/.env 设置 DB_PASSWORD}"
JWT_SECRET="${JWT_SECRET:?请在 deploy/.env 设置 JWT_SECRET}"
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:?请在 deploy/.env 设置 ADMIN_PASSWORD}"

# ---- 前置检查 ----
[ "$(id -u)" = 0 ] || { echo "请用 sudo 运行"; exit 1; }
for cmd in python3 nginx systemctl curl; do
  command -v "$cmd" >/dev/null || { echo "缺少 $cmd，请先安装"; exit 1; }
done
if [ ! -d web/dist ]; then
  if command -v node >/dev/null; then
    echo "[前端] 检测到 node，现场构建 ..."
    (cd web && npm install --silent && npm run build)
  else
    echo "web/dist 不存在且服务器无 node：请在本地 npm run build 后把 dist 一起上传，或安装 node"
    exit 1
  fi
fi

# ---- 同步文件（.venv 与 uploads 不覆盖不删除）----
echo "[1/6] 同步文件到 $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
rsync -a --exclude '.venv' --exclude 'uploads' --exclude '__pycache__' "$ROOT/server/" "$INSTALL_DIR/server/"
rsync -a "$ROOT/web/dist/" "$INSTALL_DIR/web-dist/"

# ---- 后端依赖 ----
if [ ! -x "$INSTALL_DIR/server/.venv/bin/python" ]; then
  echo "[2/6] 创建 venv 并安装依赖 ..."
  python3 -m venv "$INSTALL_DIR/server/.venv"
fi
"$INSTALL_DIR/server/.venv/bin/pip" install -q "$INSTALL_DIR/server"

# ---- 运行时环境文件（systemd EnvironmentFile，含密码，权限收紧）----
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

# ---- 数据库（幂等）----
echo "[4/6] 数据库迁移 + 种子 ..."
set -a; source "$INSTALL_DIR/app.env"; set +a
(cd "$INSTALL_DIR/server" && .venv/bin/alembic upgrade head)
(cd "$INSTALL_DIR/server" && ADMIN_USERNAME="$ADMIN_USERNAME" ADMIN_PASSWORD="$ADMIN_PASSWORD" .venv/bin/python -m scripts.seed)

# ---- systemd ----
echo "[5/6] 配置 systemd 服务 ..."
cat > /etc/systemd/system/find-good-room.service <<EOF
[Unit]
Description=find_good_room API
After=network.target mysql.service

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

# ---- nginx ----
echo "[6/6] 配置 nginx ..."
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
    location / {
        root $INSTALL_DIR/web-dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
nginx -t
systemctl reload nginx

# ---- 健康检查 ----
sleep 2
if curl -fs "http://127.0.0.1:$API_PORT/api/health" >/dev/null; then
  echo
  echo "部署完成 ✓"
  echo "  站点   : http://$(curl -s ifconfig.me 2>/dev/null || echo 服务器IP):$HTTP_PORT"
  echo "  服务   : systemctl status find-good-room"
  echo "  日志   : journalctl -u find-good-room -f"
  echo "  更新   : 重跑 sudo bash deploy/deploy-bare.sh"
else
  echo "健康检查失败，查看日志：journalctl -u find-good-room -n 50"
  exit 1
fi
