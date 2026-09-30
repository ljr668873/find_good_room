"""演示数据：清空旧数据，造 5 个房东、广深两城约 30 套均衡房源。

用法：cd server && .venv/bin/python -m scripts.seed_demo
- 图片取项目 data/*.png，走与线上一致的压缩管线（photos._save_webp），落 uploads/demo/
- random.seed 固定，重复执行结果一致
- 会删除全部房源/举报/非管理员用户，仅用于演示环境
"""
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

from PIL import Image
from sqlalchemy import delete

from app import models
from app.auth import hash_password
from app.database import SessionLocal
from app.photos import LONG_EDGE, TARGET_SIZE, THUMB_EDGE, _save_webp

random.seed(42)

DATA_DIR = Path("../data")
# 生成到 static/demo（随仓库/镜像走，线上导入无需 data/ 源图）；真实上传仍走 uploads
OUT_DIR = Path("static/demo")

# 房东：(用户名, 村名列表, 房源数)
LANDLORDS = [
    ("demo_石牌阿强", ["石牌村"], 6),
    ("demo_客村林姨", ["客村", "鹭江"], 5),
    ("demo_员村小陈", ["员村", "棠下", "上社"], 5),
    ("demo_深圳老周", ["白石洲", "大冲"], 6),
    ("demo_岗厦阿珍", ["岗厦", "新洲"], 4),
]

# 村 → (城市, 地铁线路, 站名, 步行分钟)；None = 无地铁（无地铁房源也要有，测试筛选均衡）
VILLAGES = {
    "石牌村": ("广州", "3号线", "石牌桥站", 10),
    "客村": ("广州", "8号线", "客村站", 6),
    "鹭江": ("广州", "8号线", "鹭江站", 8),
    "员村": ("广州", "5号线", "员村站", 7),
    "棠下": ("广州", None, None, None),
    "上社": ("广州", None, None, None),
    "白石洲": ("深圳", "1号线", "白石洲站", 9),
    "大冲": ("深圳", "1号线", "高新园站", 8),
    "岗厦": ("深圳", "1号线", "岗厦站", 5),
    "新洲": ("深圳", "7号线", "沙尾站", 11),
}

# 户型 → (面积下限, 上限, 租金下限, 上限)
LAYOUTS = {
    "单间": (12, 25, 800, 1400),
    "一房一厅": (30, 45, 1500, 2300),
    "两房": (50, 70, 2300, 3300),
    "隔断间": (8, 15, 550, 950),
}
LAYOUT_WEIGHTS = [("单间", 45), ("一房一厅", 25), ("隔断间", 15), ("两房", 15)]

DEPOSITS = ["押一付一", "押一付一", "押一付一", "押二付一", "押一付三"]  # 押一付一为主
FACINGS = ["南", "南向采光好", "东南", "北", "西", "南北通透", "朝南带阳台"]
SURROUNDINGS = [
    "楼下有超市和菜市场，生活方便",
    "巷口有便利店，晚上有宵夜街",
    "近公交站，出门即地铁",
    "附近有小学和社区医院",
    "一楼有快递柜，收发方便",
    None, None,
]


def prepare_images():
    """data/*.png → static/demo/ 下原图+缩略图 webp。只处理一次，重复执行跳过。"""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pairs = []
    for p in sorted(DATA_DIR.glob("*.png")):
        orig = OUT_DIR / f"{uuid.uuid5(uuid.NAMESPACE_URL, p.name)}.webp"
        thumb = orig.with_name(orig.stem + "_thumb.webp")
        if not orig.exists():
            img = Image.open(p)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            _save_webp(img, orig, LONG_EDGE, TARGET_SIZE)
            _save_webp(Image.open(orig), thumb, THUMB_EDGE)
        pairs.append(("/static/demo/" + thumb.name, "/static/demo/" + orig.name))
    if not pairs:
        raise SystemExit(f"{DATA_DIR.resolve()} 下没有图片")
    return pairs


def rand_layout():
    name = random.choices([n for n, _ in LAYOUT_WEIGHTS], weights=[w for _, w in LAYOUT_WEIGHTS])[0]
    return name


def make_listing(landlord_id, village, photos_pairs, status):
    city, line, station, walk = VILLAGES[village]
    layout = rand_layout()
    a_min, a_max, r_min, r_max = LAYOUTS[layout]
    area = round(random.uniform(a_min, a_max), 1)
    rent = int(random.uniform(r_min, r_max) // 50 * 50)
    if city == "深圳":
        rent = int(rent * 1.15 // 50 * 50)

    chosen = random.sample(photos_pairs, k=min(random.randint(2, 4), len(photos_pairs)))
    photos = [chosen[0][0]] + [p[1] for p in chosen]  # photos[0]=封面缩略图, [1:]=原图

    floor_total = random.randint(4, 9)
    return models.Listing(
        landlord_id=landlord_id,
        title=f"{village}·{layout}·{rent}元",
        city=city,
        village=village,
        address=f"{random.choice('甲乙丙丁戊')}巷{random.randint(1, 30)}号{random.randint(1, floor_total)}楼",
        rent=rent,
        deposit_type=random.choice(DEPOSITS),
        layout=layout,
        area=area,
        floor=random.randint(1, floor_total),
        floor_total=floor_total,
        has_elevator=random.random() < 0.4,
        facing=random.choice(FACINGS),
        private_bathroom=random.random() < 0.7,
        water_price=round(random.uniform(3, 6), 1),
        electric_price=round(random.uniform(1.0, 1.8), 2),  # 商水商电区间，详情页可见
        available_date=date.today() + timedelta(days=random.randint(0, 30)),
        metro_line=line,
        metro_station=station,
        walk_minutes=walk,
        surroundings=random.choice(SURROUNDINGS),
        photos=photos,
        phone=f"138{random.randint(10000000, 99999999)}",
        wechat=random.choice(["wx_" + village, None, None]),
        status=status,
    )


def main():
    photos_pairs = prepare_images()
    db = SessionLocal()
    try:
        db.execute(delete(models.Report))
        db.execute(delete(models.Listing))
        db.execute(delete(models.User).where(models.User.is_admin.is_(False)))
        db.commit()

        stats = {"active": 0, "rented": 0, "offline": 0}
        for username, villages, count in LANDLORDS:
            landlord = models.User(
                username=username,
                password_hash=hash_password("demo123456"),
            )
            db.add(landlord)
            db.flush()
            for i in range(count):
                village = villages[i % len(villages)]
                # 每个房东最后一套 rented、倒数第二套 20% 概率 offline，其余 active
                status = "rented" if i == count - 1 else ("offline" if i == count - 2 and random.random() < 0.5 else "active")
                db.add(make_listing(landlord.id, village, photos_pairs, status))
                stats[status] += 1
        db.commit()
        print(f"demo done: 房东 {len(LANDLORDS)} 个（密码均 demo123456），房源 {sum(stats.values())} 套 {stats}")
        print(f"图片 {len(photos_pairs)} 张 → {OUT_DIR}/")
    finally:
        db.close()


if __name__ == "__main__":
    main()
