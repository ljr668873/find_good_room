"""初始化数据：支持城市 + 管理员账号。幂等，可重复执行。"""
import os

from sqlalchemy import select

from app import models
from app.auth import hash_password
from app.database import SessionLocal

# 首批支持城市，按实际落地调整
CITIES = ["广州", "深圳"]


def main():
    db = SessionLocal()
    try:
        for name in CITIES:
            if not db.scalar(select(models.City).where(models.City.name == name)):
                db.add(models.City(name=name))

        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123456")
        if not db.scalar(select(models.User).where(models.User.username == admin_username)):
            db.add(
                models.User(
                    username=admin_username,
                    password_hash=hash_password(admin_password),
                    is_admin=True,
                )
            )
        db.commit()
        print(f"seed done: cities={CITIES}, admin={admin_username}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
