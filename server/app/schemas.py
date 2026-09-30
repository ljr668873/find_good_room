from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

LayoutType = Literal["单间", "一房一厅", "两房", "隔断间"]
DepositType = Literal["押一付一", "押一付三", "押二付一"]
ReportReason = Literal["fake", "rented", "wrong", "other"]


# ---- auth ----

class RegisterIn(BaseModel):
    username: str = Field(min_length=2, max_length=32, pattern=r"^[\w一-龥]+$")
    password: str = Field(min_length=6, max_length=64)


class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    is_admin: bool


class UserBrief(BaseModel):
    id: int
    username: str


class TokenOut(BaseModel):
    token: str


# ---- listing ----

class ListingCreate(BaseModel):
    city: str = Field(min_length=1, max_length=32)
    village: str = Field(min_length=1, max_length=32)
    address: str = Field(min_length=1, max_length=100)
    rent: int = Field(ge=1)
    deposit_type: DepositType
    layout: LayoutType
    area: float = Field(gt=0)
    floor: int = Field(ge=-2, le=200)
    floor_total: int = Field(ge=1, le=200)
    has_elevator: bool
    facing: str | None = Field(default=None, max_length=50)
    private_bathroom: bool
    water_price: float = Field(ge=0, le=100)
    electric_price: float = Field(ge=0, le=10)
    available_date: date
    metro_line: str | None = Field(default=None, max_length=16)
    metro_station: str | None = Field(default=None, max_length=32)
    walk_minutes: int | None = Field(default=None, ge=1, le=120)
    surroundings: str | None = Field(default=None, max_length=200)
    photos: list[str] = Field(min_length=1, max_length=9)
    phone: str = Field(pattern=r"^\d{6,20}$")
    wechat: str | None = Field(default=None, max_length=32)
    title: str | None = Field(default=None, max_length=50)

    @model_validator(mode="after")
    def metro_pair(self):
        if bool(self.metro_line) != bool(self.metro_station):
            raise ValueError("metro_line 与 metro_station 必须成对填写")
        return self


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    landlord_id: int
    title: str
    city: str
    village: str
    address: str
    rent: int
    deposit_type: str
    layout: str
    area: float
    floor: int
    floor_total: int
    has_elevator: bool
    facing: str | None
    private_bathroom: bool
    water_price: float
    electric_price: float
    available_date: date
    metro_line: str | None
    metro_station: str | None
    walk_minutes: int | None
    surroundings: str | None
    photos: list[str]
    phone: str
    wechat: str | None
    status: str
    created_at: datetime


class ListingPage(BaseModel):
    items: list[ListingOut]
    total: int
    page: int
    page_size: int


class LandlordPage(BaseModel):
    landlord: UserBrief
    items: list[ListingOut]
    total: int
    page: int
    page_size: int


class FilterOption(BaseModel):
    name: str
    count: int


class FilterOptionsOut(BaseModel):
    villages: list[FilterOption]
    metro: list[FilterOption]


# ---- my ----

class StatusAction(BaseModel):
    action: Literal["offline", "active", "rented"]


# ---- report / admin ----

class ReportIn(BaseModel):
    listing_id: int
    reason: ReportReason


class ReportAdminOut(BaseModel):
    id: int
    listing_id: int
    reason: str
    status: str
    created_at: datetime
    listing_title: str
    listing_city: str
    listing_village: str
    listing_status: str
    landlord_username: str


class ReportAdminPage(BaseModel):
    items: list[ReportAdminOut]
    total: int
    page: int
    page_size: int


class ReportPatch(BaseModel):
    status: Literal["done"]


class AdminListingAction(BaseModel):
    action: Literal["offline", "active"]


# ---- 管理员：房东 CRUD ----

class LandlordAdminCreate(BaseModel):
    username: str = Field(min_length=2, max_length=32, pattern=r"^[\w一-龥]+$")
    password: str = Field(min_length=6, max_length=64)
    is_admin: bool = False


class LandlordAdminUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=2, max_length=32, pattern=r"^[\w一-龥]+$")
    password: str | None = Field(default=None, min_length=6, max_length=64)


class LandlordAdminOut(BaseModel):
    id: int
    username: str
    is_admin: bool
    listing_count: int
    created_at: datetime


class LandlordAdminPage(BaseModel):
    items: list[LandlordAdminOut]
    total: int
    page: int
    page_size: int


# ---- 管理员：访问统计 ----

class StatsSummary(BaseModel):
    uv: int
    pv: int
    listing_pv: int


class HourlyStat(BaseModel):
    hour: int
    uv: int
    pv: int


class TopListing(BaseModel):
    listing_id: int
    title: str
    village: str
    count: int


# ---- 广告 ----

class AdBase(BaseModel):
    title: str = Field(min_length=1, max_length=50)
    desc: str = Field(default="", max_length=100)
    image: str | None = Field(default=None, max_length=255)
    link: str = Field(default="#", max_length=200)
    color: str = Field(default="#5a6a8a", max_length=16)
    sort: int = Field(default=0, ge=0, le=9999)
    enabled: bool = True


class AdCreate(AdBase):
    pass


class AdUpdate(AdBase):
    pass


class AdOut(AdBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    click_count: int
    created_at: datetime
