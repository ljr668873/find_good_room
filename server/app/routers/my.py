"""房东接口：发布/编辑/状态/我的房源/照片上传。"""
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.photos import process_photos

router = APIRouter(prefix="/api/my", tags=["my"])


def _own_listing(db: Session, listing_id: int, user: models.User) -> models.Listing:
    listing = db.get(models.Listing, listing_id)
    # 404 而非 403：不泄露他人房源存在性
    if listing is None or listing.landlord_id != user.id:
        raise HTTPException(404, "房源不存在")
    return listing


def _auto_title(data: schemas.ListingCreate) -> str:
    return (data.title or "").strip() or f"{data.village}·{data.layout}·{data.rent}元"


@router.post("/listings", response_model=schemas.ListingOut, status_code=201)
def create_listing(
    data: schemas.ListingCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not db.scalar(select(models.City).where(models.City.name == data.city)):
        raise HTTPException(400, f"暂不支持城市: {data.city}")
    listing = models.Listing(
        landlord_id=user.id,
        title=_auto_title(data),
        **data.model_dump(exclude={"title"}),
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


@router.put("/listings/{listing_id}", response_model=schemas.ListingOut)
def update_listing(
    listing_id: int,
    data: schemas.ListingCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = _own_listing(db, listing_id, user)
    if not db.scalar(select(models.City).where(models.City.name == data.city)):
        raise HTTPException(400, f"暂不支持城市: {data.city}")
    for key, value in data.model_dump(exclude={"title"}).items():
        setattr(listing, key, value)
    listing.title = _auto_title(data)
    db.commit()
    db.refresh(listing)
    return listing


@router.patch("/listings/{listing_id}/status")
def set_status(
    listing_id: int,
    data: schemas.StatusAction,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = _own_listing(db, listing_id, user)
    if listing.status == "rented":
        raise HTTPException(400, "已租房源请复制重新发布")
    if data.action == "rented" and listing.status != "active":
        raise HTTPException(400, "下架房源不能直接标记已租")
    listing.status = data.action
    db.commit()
    return {"ok": True}


@router.get("/listings/{listing_id}", response_model=schemas.ListingOut)
def get_my_listing(
    listing_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """编辑/复制回读：返回自己名下任意状态的房源（公开详情接口只暴露 active）。"""
    return _own_listing(db, listing_id, user)


@router.get("/listings", response_model=schemas.ListingPage)
def my_listings(
    status: str | None = Query(None, pattern="^(active|rented|offline)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = select(models.Listing).where(models.Listing.landlord_id == user.id)
    if status:
        stmt = stmt.where(models.Listing.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(
        stmt.order_by(models.Listing.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return schemas.ListingPage(items=items, total=total, page=page, page_size=page_size)


@router.post("/upload/photos")
def upload_photos(
    files: list[UploadFile] = File(...),
    user: models.User = Depends(get_current_user),
):
    return {"photos": process_photos(files)}
