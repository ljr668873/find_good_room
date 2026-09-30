"""管理员接口：举报队列、房东账号 CRUD、房源管理、访问统计、广告。"""
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import hash_password, require_admin
from app.database import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/reports", response_model=schemas.ReportAdminPage)
def report_list(
    status: str = Query("pending", pattern="^(pending|done|all)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    cond = [] if status == "all" else [models.Report.status == status]
    total = db.scalar(select(func.count(models.Report.id)).where(*cond))
    rows = db.execute(
        select(models.Report, models.Listing, models.User)
        .join(models.Listing, models.Report.listing_id == models.Listing.id)
        .join(models.User, models.Listing.landlord_id == models.User.id)
        .where(*cond)
        .order_by(models.Report.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    items = [
        schemas.ReportAdminOut(
            id=report.id,
            listing_id=report.listing_id,
            reason=report.reason,
            status=report.status,
            created_at=report.created_at,
            listing_title=listing.title,
            listing_city=listing.city,
            listing_village=listing.village,
            listing_status=listing.status,
            landlord_username=user.username,
        )
        for report, listing, user in rows
    ]
    return schemas.ReportAdminPage(items=items, total=total, page=page, page_size=page_size)


@router.patch("/reports/{report_id}")
def report_done(report_id: int, data: schemas.ReportPatch, db: Session = Depends(get_db)):
    report = db.get(models.Report, report_id)
    if report is None:
        raise HTTPException(404, "举报不存在")
    report.status = data.status
    db.commit()
    return {"ok": True}


@router.patch("/listings/{listing_id}/status")
def force_status(listing_id: int, data: schemas.AdminListingAction, db: Session = Depends(get_db)):
    listing = db.get(models.Listing, listing_id)
    if listing is None:
        raise HTTPException(404, "房源不存在")
    listing.status = data.action
    db.commit()
    return {"ok": True}


# ---- 房东账号 CRUD ----

def _parse_date(s: str | None) -> date:
    if not s:
        return datetime.now().date()
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "日期格式应为 YYYY-MM-DD")


@router.get("/landlords", response_model=schemas.LandlordAdminPage)
def landlord_list(
    keyword: str | None = Query(None, max_length=32),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    cond = []
    if keyword:
        cond.append(models.User.username.contains(keyword))
    total = db.scalar(select(func.count(models.User.id)).where(*cond))
    rows = db.execute(
        select(models.User, func.count(models.Listing.id))
        .outerjoin(models.Listing, models.Listing.landlord_id == models.User.id)
        .where(*cond)
        .group_by(models.User.id)
        .order_by(models.User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    items = [
        schemas.LandlordAdminOut(
            id=u.id, username=u.username, is_admin=u.is_admin,
            listing_count=n or 0, created_at=u.created_at,
        )
        for u, n in rows
    ]
    return schemas.LandlordAdminPage(items=items, total=total, page=page, page_size=page_size)


@router.post("/landlords", response_model=schemas.UserOut, status_code=201)
def landlord_create(data: schemas.LandlordAdminCreate, db: Session = Depends(get_db)):
    if db.scalar(select(models.User).where(models.User.username == data.username)):
        raise HTTPException(400, "用户名已存在")
    user = models.User(
        username=data.username,
        password_hash=hash_password(data.password),
        is_admin=data.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/landlords/{user_id}", response_model=schemas.UserOut)
def landlord_update(user_id: int, data: schemas.LandlordAdminUpdate, db: Session = Depends(get_db)):
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(404, "账号不存在")
    if not data.username and not data.password:
        raise HTTPException(400, "至少修改用户名或密码之一")
    if data.username and data.username != user.username:
        if db.scalar(select(models.User).where(models.User.username == data.username)):
            raise HTTPException(400, "用户名已存在")
        user.username = data.username
    if data.password:
        user.password_hash = hash_password(data.password)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/landlords/{user_id}")
def landlord_delete(user_id: int, db: Session = Depends(get_db)):
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(404, "账号不存在")
    if user.is_admin:
        raise HTTPException(400, "不能删除管理员账号")
    n = db.scalar(
        select(func.count(models.Listing.id)).where(models.Listing.landlord_id == user_id)
    )
    if n:
        raise HTTPException(400, f"名下还有 {n} 套房源，请先处理房源再删除账号")
    db.delete(user)
    db.commit()
    return {"ok": True}


# ---- 访问统计 ----

@router.get("/stats/summary", response_model=schemas.StatsSummary)
def stats_summary(date_: str | None = Query(None, alias="date"), db: Session = Depends(get_db)):
    d = _parse_date(date_)
    cond = models.VisitLog.vdate == d
    uv = db.scalar(select(func.count(func.distinct(models.VisitLog.visitor_key))).where(cond)) or 0
    pv = db.scalar(select(func.count()).select_from(models.VisitLog).where(cond)) or 0
    lpv = db.scalar(
        select(func.count()).select_from(models.VisitLog).where(cond, models.VisitLog.listing_id.is_not(None))
    ) or 0
    return schemas.StatsSummary(uv=uv, pv=pv, listing_pv=lpv)


@router.get("/stats/hourly", response_model=list[schemas.HourlyStat])
def stats_hourly(date_: str | None = Query(None, alias="date"), db: Session = Depends(get_db)):
    d = _parse_date(date_)
    rows = db.execute(
        select(
            models.VisitLog.hour,
            func.count(func.distinct(models.VisitLog.visitor_key)),
            func.count(),
        )
        .where(models.VisitLog.vdate == d)
        .group_by(models.VisitLog.hour)
    ).all()
    by_hour = {h: (uv, pv) for h, uv, pv in rows}
    # 24 小时补零，前端直接画柱
    return [
        schemas.HourlyStat(hour=h, uv=by_hour.get(h, (0, 0))[0], pv=by_hour.get(h, (0, 0))[1])
        for h in range(24)
    ]


@router.get("/stats/top-listings", response_model=list[schemas.TopListing])
def stats_top_listings(
    date_: str | None = Query(None, alias="date"),
    hour: int | None = Query(None, ge=0, le=23),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    d = _parse_date(date_)
    cond = [models.VisitLog.vdate == d, models.VisitLog.listing_id.is_not(None)]
    if hour is not None:
        cond.append(models.VisitLog.hour == hour)
    rows = db.execute(
        select(models.VisitLog.listing_id, func.count().label("c"))
        .where(*cond)
        .group_by(models.VisitLog.listing_id)
        .order_by(func.count().desc())
        .limit(limit)
    ).all()
    out = []
    for listing_id, count in rows:
        listing = db.get(models.Listing, listing_id)
        if listing:
            out.append(schemas.TopListing(
                listing_id=listing_id, title=listing.title, village=listing.village, count=count,
            ))
    return out


# ---- 房源管理 ----

@router.get("/listings", response_model=schemas.AdminListingPage)
def admin_listing_list(
    keyword: str | None = Query(None, max_length=32),
    status: str | None = Query(None, pattern="^(active|rented|offline)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """管理端房源列表：全状态可见，带房东用户名。"""
    cond = []
    if status:
        cond.append(models.Listing.status == status)
    if keyword:
        kw = f"%{keyword}%"
        cond.append(
            models.Listing.title.like(kw)
            | models.Listing.village.like(kw)
            | models.Listing.city.like(kw)
            | models.User.username.like(kw)
        )
    stmt = (
        select(models.Listing, models.User)
        .join(models.User, models.Listing.landlord_id == models.User.id)
        .where(*cond)
    )
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    rows = db.execute(
        stmt.order_by(models.Listing.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    items = []
    for listing, user in rows:
        item = schemas.AdminListingItem.model_validate(listing)
        item.landlord_username = user.username
        items.append(item)
    return schemas.AdminListingPage(items=items, total=total, page=page, page_size=page_size)


def _delete_listings(db: Session, listing_ids: list[int]) -> int:
    """删房源连带相关举报（reports 有 FK）。返回删除条数。"""
    if not listing_ids:
        return 0
    db.execute(delete(models.Report).where(models.Report.listing_id.in_(listing_ids)))
    db.execute(delete(models.Listing).where(models.Listing.id.in_(listing_ids)))
    db.commit()
    return len(listing_ids)


@router.delete("/listings")
def admin_listings_delete(data: schemas.IdsIn, db: Session = Depends(get_db)):
    n = _delete_listings(db, data.ids)
    return {"ok": True, "deleted": n}


@router.delete("/landlords/{user_id}/listings")
def admin_delete_landlord_listings(user_id: int, db: Session = Depends(get_db)):
    """按房东删除名下全部房源。"""
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(404, "账号不存在")
    ids = db.scalars(select(models.Listing.id).where(models.Listing.landlord_id == user_id)).all()
    n = _delete_listings(db, ids)
    return {"ok": True, "deleted": n}


# ---- 广告管理 ----

@router.get("/ads", response_model=list[schemas.AdOut])
def ad_list(db: Session = Depends(get_db)):
    return db.scalars(select(models.Ad).order_by(models.Ad.sort, models.Ad.id)).all()


@router.post("/ads", response_model=schemas.AdOut, status_code=201)
def ad_create(data: schemas.AdCreate, db: Session = Depends(get_db)):
    ad = models.Ad(**data.model_dump())
    db.add(ad)
    db.commit()
    db.refresh(ad)
    return ad


@router.put("/ads/{ad_id}", response_model=schemas.AdOut)
def ad_update(ad_id: int, data: schemas.AdUpdate, db: Session = Depends(get_db)):
    ad = db.get(models.Ad, ad_id)
    if ad is None:
        raise HTTPException(404, "广告不存在")
    for key, value in data.model_dump().items():
        setattr(ad, key, value)
    db.commit()
    db.refresh(ad)
    return ad


@router.delete("/ads/{ad_id}")
def ad_delete(ad_id: int, db: Session = Depends(get_db)):
    ad = db.get(models.Ad, ad_id)
    if ad is None:
        raise HTTPException(404, "广告不存在")
    db.delete(ad)
    db.commit()
    return {"ok": True}
