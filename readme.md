# 找好房 — 城中村租房信息平台

干净简易的城中村租房网站：房东直发房源，租客免注册浏览、电话直联。无广告、无中介、无交易环节。

- 需求：[docs/需求文档-v1.0.md](docs/需求文档-v1.0.md)
- 技术方案：[docs/技术方案-v1.0.md](docs/技术方案-v1.0.md)
- 部署：[docs/部署文档.md](docs/部署文档.md)（Docker Compose / 裸机）

## 技术栈

- 后端：FastAPI + SQLAlchemy 2.0 + MySQL 8 + Alembic
- 前端：Vue 3 + Vite + Vant 4 + Pinia
- 部署：Docker Compose（nginx + api + mysql）或裸机 systemd + nginx

## 本地开发

一键启动（MySQL 容器 + 依赖检查 + 迁移种子 + 前后端同起，Ctrl+C 一起停）：

```bash
./start.sh
# 后端 http://127.0.0.1:8000  前端 http://localhost:5173
```

MySQL 连接可用环境变量覆盖：`DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME`（默认本机 mysql-local 容器）。

分步启动（等效）：

```bash
# 后端
cd server
python3 -m venv .venv && .venv/bin/pip install -e .
.venv/bin/alembic upgrade head
.venv/bin/python -m scripts.seed
.venv/bin/uvicorn app.main:app --port 8000

# 前端（另开终端，代理 /api 与 /uploads 到 8000）
cd web
npm install && npm run dev

# 冒烟测试（服务运行中执行）
bash server/scripts/smoke.sh       # M1 认证链路
bash server/scripts/smoke2.sh      # M2 房源全链路
```

## 目录

```
docs/      需求、技术方案、部署文档
server/    FastAPI 后端（app/ 应用，scripts/ 种子与冒烟脚本，alembic/ 迁移）
web/       Vue3 前端
deploy/    Docker Compose、Dockerfile、nginx 配置、.env 模板
```
