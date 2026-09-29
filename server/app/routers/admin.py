"""管理员接口：举报队列、强制下架。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import require_admin
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
