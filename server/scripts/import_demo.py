"""导入演示数据：读取 scripts/demo_data.json + 项目 data/ 图片。

用法：cd server && .venv/bin/python -m scripts.import_demo
- 幂等：先清空房源/举报/非管理员用户，再按 JSON 精确导入
- 图片从 data/*.png 现场压缩到 uploads/demo/（复用 seed_demo 的 prepare_images，不依赖导出时的文件）
- 房东密码统一 demo123456
"""
import json
from datetime import date
from pathlib import Path

from sqlalchemy import delete

from app import models
from app.auth import hash_password
from app.database import SessionLocal
from scripts.seed_demo import prepare_images

DATA_FILE = Path(__file__).parent / "demo_data.json"


def main():
    if not DATA_FILE.exists():
        raise SystemExit(f"缺少 {DATA_FILE}，请先在开发机运行 scripts/export_demo.py 并提交该文件")

    # 图片先就位（URL 需与 JSON 里的一致：prepare_images 按文件名确定性生成，可复现）
    prepare_images()

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    db = SessionLocal()
    try:
        db.execute(delete(models.Report))
        db.execute(delete(models.Listing))
        db.execute(delete(models.User).where(models.User.is_admin.is_(False)))
        db.commit()

        name_to_user = {}
        for entry in data["landlords"]:
            # 兼容旧格式（纯用户名列表）；新格式带 share_slug 保持链接稳定
            if isinstance(entry, str):
                entry = {"username": entry}
            user = models.User(
                username=entry["username"],
                password_hash=hash_password("demo123456"),
                share_slug=entry.get("share_slug") or None,
            )
            db.add(user)
            name_to_user[entry["username"]] = user
        db.flush()

        for item in data["listings"]:
            username = item.pop("username")
            if isinstance(item.get("available_date"), str):
                item["available_date"] = date.fromisoformat(item["available_date"])
            db.add(models.Listing(landlord_id=name_to_user[username].id, **item))
        db.commit()
        print(f"导入 {len(data['landlords'])} 房东 / {len(data['listings'])} 房源（密码均 demo123456）")
    finally:
        db.close()


if __name__ == "__main__":
    main()
