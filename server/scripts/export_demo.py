"""导出演示数据为 JSON：scripts/demo_data.json。

导出范围：demo_% 房东及其名下全部房源（含已租/下架）。
密码不导出（导入侧统一重置为 demo123456）；照片只存相对 URL，
图片文件由导入脚本从项目 data/ 目录现场压缩生成。
"""
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from app import models
from app.database import SessionLocal

OUT_FILE = Path(__file__).parent / "demo_data.json"


def _jsonable(v):
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    return v

FIELDS = [
    "title", "city", "village", "address", "rent", "deposit_type", "layout",
    "area", "floor", "floor_total", "has_elevator", "facing", "private_bathroom",
    "water_price", "electric_price", "available_date", "metro_line", "metro_station",
    "walk_minutes", "surroundings", "photos", "phone", "wechat", "status",
]


def main():
    db = SessionLocal()
    try:
        landlords = {
            u.id: u.username
            for u in db.scalars(select(models.User).where(models.User.username.like("demo_%")))
        }
        if not landlords:
            raise SystemExit("没有 demo_% 房东，请先运行 scripts/seed_demo.py")

        listings = db.scalars(
            select(models.Listing).where(models.Listing.landlord_id.in_(landlords)).order_by(models.Listing.id)
        ).all()

        data = {
            "landlords": sorted(set(landlords.values())),
            "listings": [
                {"username": landlords[l.landlord_id], **{f: _jsonable(getattr(l, f)) for f in FIELDS}}
                for l in listings
            ],
        }
        OUT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"导出 {len(data['landlords'])} 房东 / {len(listings)} 房源 → {OUT_FILE}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
