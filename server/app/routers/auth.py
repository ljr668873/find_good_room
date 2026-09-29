import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import create_token, get_current_user, hash_password, verify_password
from app.database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 登录限流：内存计数，同 IP 每分钟 10 次。ponytail: 单实例内存版，多实例部署换 Redis
_login_attempts: dict[str, list[float]] = defaultdict(list)
LOGIN_LIMIT = 10
LOGIN_WINDOW = 60


def _rate_limited(ip: str) -> bool:
    now = time.time()
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < LOGIN_WINDOW]
    return len(_login_attempts[ip]) >= LOGIN_LIMIT


@router.post("/register", response_model=schemas.UserOut)
def register(data: schemas.RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(models.User).where(models.User.username == data.username)):
        raise HTTPException(400, "用户名已存在")
    user = models.User(username=data.username, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.TokenOut)
def login(data: schemas.LoginIn, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "?"
    if _rate_limited(ip):
        raise HTTPException(429, "尝试过于频繁，请稍后再试")
    _login_attempts[ip].append(time.time())

    user = db.scalar(select(models.User).where(models.User.username == data.username))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(400, "用户名或密码错误")
    return schemas.TokenOut(token=create_token(user.id))


@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user
