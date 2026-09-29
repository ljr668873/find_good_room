import os

from sqlalchemy.engine import URL

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Root@123")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "find_good_room")

# URL.create 自动处理密码等特殊字符转义
DATABASE_URL = URL.create(
    "mysql+pymysql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
TOKEN_EXPIRE_DAYS = 30
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
