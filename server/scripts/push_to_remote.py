"""本地数据推送到线上环境（走 HTTP API，无需连线上数据库）。

用法：
  .venv/bin/python -m scripts.push_to_remote http://113.45.231.18:5003
  REMOTE_BASE=http://113.45.231.18:5003 .venv/bin/python -m scripts.push_to_remote   # 等效

行为：
  - 导出本地全部非管理员房东及其房源（含已租/下架状态）
  - 房东线上不存在则注册，已存在则登录（密码统一 DEMO_PWD，线上密码不同则该房东跳过并提示）
  - 图片经线上 /api/my/upload/photos 重传，photos URL 自动重写（不依赖线上代码里的 static 资源）
  - 默认 --clean：先用管理员账号清空各房东线上房源再导（保证线上=本地，幂等可重跑）；
    不想清空用 --append（重跑会产生重复房源）

环境变量：
  ADMIN_USERNAME / ADMIN_PASSWORD   线上管理员账号（clean 用），默认 admin/admin123456
"""
import os
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import requests
from sqlalchemy import select

from app import models
from app.database import SessionLocal


def _jsonable(v):
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, date):
        return v.isoformat()
    return v

DEMO_PWD = "demo123456"
UPLOADABLE = {"active", "rented", "offline"}

FIELDS = [
    "title", "city", "village", "address", "rent", "deposit_type", "layout",
    "area", "floor", "floor_total", "has_elevator", "facing", "private_bathroom",
    "water_price", "electric_price", "available_date", "metro_line", "metro_station",
    "walk_minutes", "surroundings", "photos", "phone", "wechat", "status",
]


def url_to_local_path(url: str) -> Path | None:
    """线上可访问的 /uploads、/static 图片 URL → 本地文件路径。"""
    if not url or not url.startswith("/"):
        return None
    local = Path(url.lstrip("/"))  # uploads/... 或 static/...（相对 server/ 运行目录）
    return local if local.exists() else None


class Remote:
    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "push_to_remote/1.0"

    def api(self, method, path, token=None, ok_codes=(200, 201), **kw):
        headers = kw.pop("headers", {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        r = self.s.request(method, self.base + path, headers=headers, timeout=60, **kw)
        if r.status_code not in ok_codes:
            raise RuntimeError(f"{method} {path} -> {r.status_code}: {r.text[:200]}")
        return r.json() if r.content else {}

    def login(self, username, password, retry_on_limit=True):
        r = self.s.post(self.base + "/api/auth/login", json={"username": username, "password": password}, timeout=60)
        if r.status_code == 429 and retry_on_limit:
            print("    …线上登录限流，等 65 秒重试")
            import time
            time.sleep(65)
            return self.login(username, password, retry_on_limit=False)
        return r.json().get("token") if r.ok else None

    def register_and_login(self, username):
        token = self.login(username, DEMO_PWD)
        if token:
            return token
        r = self.s.post(self.base + "/api/auth/register", json={"username": username, "password": DEMO_PWD}, timeout=60)
        if r.ok:
            return self.login(username, DEMO_PWD)
        return None

    def upload_photo(self, token, path: Path):
        """上传单张，返回线上 [thumbUrl, origUrl]。"""
        with open(path, "rb") as f:
            res = self.api(
                "POST", "/api/my/upload/photos", token=token,
                files={"files": (path.name, f, "image/webp")},
            )
        return res["photos"][0], res["photos"][1]

    def remote_user_id(self, admin_token, username):
        res = self.api("GET", "/api/admin/landlords", token=admin_token, params={"keyword": username, "page_size": 50})
        for item in res["items"]:
            if item["username"] == username:
                return item["id"]
        return None

    def clean_landlord(self, admin_token, username):
        uid = self.remote_user_id(admin_token, username)
        if uid:
            self.api("DELETE", f"/api/admin/landlords/{uid}/listings", token=admin_token)


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else os.getenv("REMOTE_BASE")
    clean = "--append" not in sys.argv
    if not base:
        raise SystemExit("用法: python -m scripts.push_to_remote <base_url>   例: http://113.45.231.18:5003")

    admin_token = Remote(base).login(os.getenv("ADMIN_USERNAME", "admin"), os.getenv("ADMIN_PASSWORD", "admin123456"))
    if clean and not admin_token:
        raise SystemExit("默认 --clean 需要线上管理员账号（ADMIN_USERNAME/ADMIN_PASSWORD），或改用 --append")

    remote = Remote(base)
    remote.api("GET", "/api/health")  # 连通性检查
    print(f"目标: {base}（{'先清空再导' if clean else '追加模式'}）")

    db = SessionLocal()
    try:
        landlords = {u.id: u.username for u in db.scalars(select(models.User).where(models.User.is_admin.is_(False)))}
        listings = db.scalars(select(models.Listing).where(models.Listing.landlord_id.in_(landlords))).all()
    finally:
        db.close()

    # 图片 URL 上传缓存：同一张图（demo 图复用）只传一次
    photo_cache: dict[str, tuple[str, str]] = {}
    stat = {"landlords": 0, "listings": 0, "skipped": 0}

    for uid, username in landlords.items():
        mine = [l for l in listings if l.landlord_id == uid]
        token = remote.register_and_login(username)
        if not token:
            print(f"  ✗ {username}: 线上已存在但密码不是 {DEMO_PWD}，跳过（{len(mine)} 套）")
            stat["skipped"] += len(mine)
            continue
        if clean:
            remote.clean_landlord(admin_token, username)
        stat["landlords"] += 1

        for l in mine:
            payload = {f: _jsonable(getattr(l, f)) for f in FIELDS}
            status = payload.pop("status")
            # 重传图片并重写 URL：photos = [封面thumb, ...原图]，原图逐张传，新封面 thumb 取第一张的
            origs = payload["photos"][1:]
            new_urls = []
            missing = []
            for url in origs:
                if url not in photo_cache:
                    p = url_to_local_path(url)
                    if not p:
                        missing.append(url)
                        continue
                    photo_cache[url] = remote.upload_photo(token, p)
                new_urls.append(photo_cache[url])
            if missing:
                print(f"  ✗ {payload['title']}: 本地缺图 {missing}，跳过")
                stat["skipped"] += 1
                continue
            payload["photos"] = [new_urls[0][0]] + [u[1] for u in new_urls]

            created = remote.api("POST", "/api/my/listings", token=token, json=payload)
            if status in UPLOADABLE and status != "active":
                remote.api("PATCH", f"/api/my/listings/{created['id']}/status", token=token, json={"action": status})
            stat["listings"] += 1
            print(f"  ✓ {username}: {payload['title']}（{status}）")

    print(f"完成: 房东 {stat['landlords']} / 房源 {stat['listings']} / 跳过 {stat['skipped']}")


if __name__ == "__main__":
    main()
