from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.dialects.mysql import BIGINT, INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), unique=True)
    password_hash: Mapped[str] = mapped_column(String(127))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    landlord_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(32))
    village: Mapped[str] = mapped_column(String(32))
    address: Mapped[str] = mapped_column(String(100))
    rent: Mapped[int] = mapped_column(INTEGER(unsigned=True))
    deposit_type: Mapped[str] = mapped_column(String(16))
    layout: Mapped[str] = mapped_column(String(16))
    area: Mapped[float] = mapped_column(Numeric(5, 1))
    floor: Mapped[int] = mapped_column(Integer)
    floor_total: Mapped[int] = mapped_column(Integer)
    has_elevator: Mapped[bool] = mapped_column(Boolean)
    facing: Mapped[str | None] = mapped_column(String(50))
    private_bathroom: Mapped[bool] = mapped_column(Boolean)
    water_price: Mapped[float] = mapped_column(Numeric(5, 2))
    electric_price: Mapped[float] = mapped_column(Numeric(5, 2))
    available_date: Mapped[date] = mapped_column(Date)
    metro_line: Mapped[str | None] = mapped_column(String(16))
    metro_station: Mapped[str | None] = mapped_column(String(32))
    walk_minutes: Mapped[int | None] = mapped_column(Integer)
    surroundings: Mapped[str | None] = mapped_column(String(200))
    photos: Mapped[list] = mapped_column(JSON)
    phone: Mapped[str] = mapped_column(String(20))
    wechat: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(8), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_city_status_rent", "city", "status", "rent"),
        Index("idx_city_village", "city", "status", "village"),
        Index("idx_city_metro", "city", "status", "metro_station"),
        Index("idx_landlord", "landlord_id", "status"),
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"))
    reason: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(8), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (Index("idx_status", "status"),)
