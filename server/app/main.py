import hashlib
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import config, models
from app.database import SessionLocal
from app.routers import admin as admin_router
from app.routers import ads as ads_router
from app.routers import auth as auth_router
from app.routers import listings as listings_router
from app.routers import my as my_router

app = FastAPI(title="find_good_room API")


@app.middleware("http")
async def track_visit(request: Request, call_next):
    """租客找房行为埋点：列表/详情 GET 且响应 200 时记一条 visit_logs。

    visitor_key = sha256(ip + ua) 前 16 位，统计侧 DISTINCT 去重得 UV。
    ponytail: 同步写库（约 1ms），量级上来再换队列/异步
    """
    path = request.url.path
    is_list = path == "/api/listings"
    is_detail = path.startswith("/api/listings/") and path.rsplit("/", 1)[1].isdigit()
    if request.method == "GET" and (is_list or is_detail):
        response = await call_next(request)
        if response.status_code == 200:
            ip = request.headers.get("x-real-ip") or (request.client.host if request.client else "")
            ua = request.headers.get("user-agent", "")
            key = hashlib.sha256(f"{ip}{ua}".encode()).hexdigest()[:16]
            now = datetime.now()
            db = SessionLocal()
            try:
                db.add(
                    models.VisitLog(
                        vdate=now.date(),
                        hour=now.hour,
                        visitor_key=key,
                        listing_id=int(path.rsplit("/", 1)[1]) if is_detail else None,
                    )
                )
                db.commit()
            finally:
                db.close()
        return response
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(config.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")
# demo 演示图片（随仓库走，scripts/seed_demo.py 生成）；check_dir=False：目录未生成时不阻塞启动
app.mount("/static", StaticFiles(directory="static", check_dir=False), name="static")

app.include_router(auth_router.router)
app.include_router(listings_router.router)
app.include_router(my_router.router)
app.include_router(ads_router.router)
app.include_router(admin_router.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
