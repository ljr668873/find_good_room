"""公开接口：城市、筛选项聚合、房源列表/详情、房东主页、举报。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import ListingFilters

router = APIRouter(prefix="/api", tags=["listings"])


def _ensure_city(db: Session, city: str) -> None:
    if not db.scalar(select(models.City).where(models.City.name == city)):
        raise HTTPException(400, f"暂不支持城市: {city}")


def _apply_filters(stmt, q: ListingFilters, city: str | None, landlord_id: int | None):
    stmt = stmt.where(models.Listing.status == "active")
    if city is not None:
        stmt = stmt.where(models.Listing.city == city)
    if landlord_id is not None:
        stmt = stmt.where(models.Listing.landlord_id == landlord_id)
    if q.village:
        stmt = stmt.where(models.Listing.village == q.village)
    if q.metro_station:
        stmt = stmt.where(models.Listing.metro_station == q.metro_station)
    if q.rent_min is not None:
        stmt = stmt.where(models.Listing.rent >= q.rent_min)
    if q.rent_max is not None:
        stmt = stmt.where(models.Listing.rent <= q.rent_max)
    if q.layout:
        stmt = stmt.where(models.Listing.layout == q.layout)
    if q.private_bathroom is not None:
        stmt = stmt.where(models.Listing.private_bathroom == q.private_bathroom)
    if q.deposit_type:
        stmt = stmt.where(models.Listing.deposit_type == q.deposit_type)
    if q.has_elevator is not None:
        stmt = stmt.where(models.Listing.has_elevator == q.has_elevator)
    return stmt


def _keyword_stmt(stmt, q: ListingFilters):
    if q.keyword:
        kw = f"%{q.keyword}%"
        cond = (
            models.Listing.title.like(kw)
            | models.Listing.village.like(kw)
            | models.Listing.address.like(kw)
            | models.Listing.metro_station.like(kw)
        )
        stmt = stmt.where(cond)
    return stmt


@router.get("/cities")
def list_cities(db: Session = Depends(get_db)):
    return [
        {"id": c.id, "name": c.name}
        for c in db.scalars(select(models.City).order_by(models.City.id))
    ]


@router.get("/filter-options", response_model=schemas.FilterOptionsOut)
def filter_options(city: str, db: Session = Depends(get_db)):
    _ensure_city(db, city)
    base = [models.Listing.city == city, models.Listing.status == "active"]

    def group(col):
        rows = db.execute(
            select(col, func.count()).where(*base, col.is_not(None)).group_by(col).order_by(func.count().desc())
        ).all()
        return [schemas.FilterOption(name=n, count=c) for n, c in rows]

    return schemas.FilterOptionsOut(villages=group(models.Listing.village), metro=group(models.Listing.metro_station))


@router.get("/listings", response_model=schemas.ListingPage)
def list_listings(city: str, q: ListingFilters = Depends(), db: Session = Depends(get_db)):
    _ensure_city(db, city)
    stmt = _apply_filters(select(models.Listing), q, city, None)
    stmt = _keyword_stmt(stmt, q)
    return _page(db, stmt, q)


@router.get("/listings/{listing_id}", response_model=schemas.ListingOut)
def listing_detail(listing_id: int, db: Session = Depends(get_db)):
    listing = db.get(models.Listing, listing_id)
    if listing is None or listing.status != "active":
        raise HTTPException(404, "房源不存在或已下架")
    return listing


@router.get("/landlords/{landlord_id}/listings", response_model=schemas.LandlordPage)
def landlord_listings(
    landlord_id: int,
    q: ListingFilters = Depends(),
    city: str | None = None,
    db: Session = Depends(get_db),
):
    landlord = db.get(models.User, landlord_id)
    if landlord is None:
        raise HTTPException(404, "房东不存在")
    stmt = _apply_filters(select(models.Listing), q, city, landlord_id)
    stmt = _keyword_stmt(stmt, q)
    result = _page(db, stmt, q)
    return schemas.LandlordPage(
        landlord=schemas.UserBrief(id=landlord.id, username=landlord.username),
        items=result.items,
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.post("/reports", status_code=201)
def create_report(data: schemas.ReportIn, db: Session = Depends(get_db)):
    listing = db.get(models.Listing, data.listing_id)
    if listing is None or listing.status != "active":
        raise HTTPException(404, "房源不存在或已下架")
    db.add(models.Report(listing_id=data.listing_id, reason=data.reason))
    db.commit()
    return {"ok": True}


def _page(db: Session, stmt, q: ListingFilters) -> schemas.ListingPage:
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    items = db.scalars(
        stmt.order_by(models.Listing.id.desc()).offset((q.page - 1) * q.page_size).limit(q.page_size)
    ).all()
    return schemas.ListingPage(items=items, total=total, page=q.page, page_size=q.page_size)
