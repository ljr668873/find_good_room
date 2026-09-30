"""公开广告接口：详情页广告位拉取 + 点击计数。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/api/ads", tags=["ads"])


@router.get("", response_model=list[schemas.AdOut])
def list_ads(db: Session = Depends(get_db)):
    return db.scalars(
        select(models.Ad).where(models.Ad.enabled).order_by(models.Ad.sort, models.Ad.id)
    ).all()


@router.post("/{ad_id}/click")
def ad_click(ad_id: int, db: Session = Depends(get_db)):
    ad = db.get(models.Ad, ad_id)
    if ad is None:
        raise HTTPException(404, "广告不存在")
    ad.click_count += 1
    db.commit()
    return {"ok": True}
