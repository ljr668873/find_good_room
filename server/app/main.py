from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import config
from app.routers import admin as admin_router
from app.routers import auth as auth_router
from app.routers import listings as listings_router
from app.routers import my as my_router

app = FastAPI(title="find_good_room API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(config.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")

app.include_router(auth_router.router)
app.include_router(listings_router.router)
app.include_router(my_router.router)
app.include_router(admin_router.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
