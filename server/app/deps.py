from fastapi import Query


class ListingFilters:
    """房源列表公共查询参数，/api/listings 与 /api/landlords/{id}/listings 复用。"""

    def __init__(
        self,
        village: str | None = Query(None, max_length=32),
        metro_station: str | None = Query(None, max_length=32),
        rent_min: int | None = Query(None, ge=0),
        rent_max: int | None = Query(None, ge=0),
        layout: str | None = Query(None, max_length=16),
        private_bathroom: bool | None = Query(None),
        deposit_type: str | None = Query(None, max_length=16),
        has_elevator: bool | None = Query(None),
        keyword: str | None = Query(None, max_length=32),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=50),
    ):
        self.village = village
        self.metro_station = metro_station
        self.rent_min = rent_min
        self.rent_max = rent_max
        self.layout = layout
        self.private_bathroom = private_bathroom
        self.deposit_type = deposit_type
        self.has_elevator = has_elevator
        self.keyword = keyword
        self.page = page
        self.page_size = page_size
