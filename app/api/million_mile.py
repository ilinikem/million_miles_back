from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.million_mile import get_listing_by_id
from app.crud.million_mile import list_listings as crud_list_listings
from app.database import get_db
from app.schemas.million_mile import (ListingCard, ListingDetail,
                                      ListingListResponse, listing_to_card,
                                      listing_to_detail)

router = APIRouter(
    prefix="/api/v1/million_miles",
    tags=["million_miles"],
)

_SORT_CHOICES = (
    "price_asc",
    "price_desc",
    "year_desc",
    "year_asc",
    "mileage_asc",
    "mileage_desc",
    "updated_desc",
    "updated_asc",
)


@router.get(
    "/listings",
    summary="Список объявлений",
    response_model=ListingListResponse,
    status_code=200,
)
async def list_listings(
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(20, ge=1, le=100, description="Записей на странице"),
    sort: str = Query(
        "updated_desc",
        description=f"Сортировка: {', '.join(_SORT_CHOICES)}",
    ),
    year_min: int | None = Query(None, description="Мин. год"),
    year_max: int | None = Query(None, description="Макс. год"),
    price_min_krw: int | None = Query(None, ge=0,
                                      description="Мин. цена, KRW"),
    price_max_krw: int | None = Query(None, ge=0,
                                      description="Макс. цена, KRW"),
    db: AsyncSession = Depends(get_db),
) -> ListingListResponse:
    if sort not in _SORT_CHOICES:
        raise HTTPException(
            status_code=422,
            detail=f"sort должен быть одним из: {', '.join(_SORT_CHOICES)}",
        )
    rows, total = await crud_list_listings(
        db,
        page=page,
        limit=limit,
        sort=sort,
        year_min=year_min,
        year_max=year_max,
        price_min_krw=price_min_krw,
        price_max_krw=price_max_krw,
    )
    items = [ListingCard.model_validate(listing_to_card(r)) for r in rows]
    return ListingListResponse(
        items=items, total=total, page=page, limit=limit
    )


@router.get(
    "/listings/{listing_id}",
    summary="Одно объявление",
    response_model=ListingDetail,
    status_code=200,
)
async def get_listing(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
) -> ListingDetail:
    row = await get_listing_by_id(db, listing_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    return ListingDetail.model_validate(listing_to_detail(row))
