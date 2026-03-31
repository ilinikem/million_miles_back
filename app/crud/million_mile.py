from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.million_mile import Listing


def _listing_filters(
    *,
    year_min: int | None,
    year_max: int | None,
    price_min_krw: int | None,
    price_max_krw: int | None,
) -> list[Any]:
    cond: list[Any] = [Listing.is_active == True]  # noqa: E712
    if year_min is not None:
        cond.append(Listing.year >= year_min)
    if year_max is not None:
        cond.append(Listing.year <= year_max)
    if price_min_krw is not None:
        cond.append(Listing.price_man_won >= (price_min_krw + 9_999) // 10_000)
    if price_max_krw is not None:
        cond.append(Listing.price_man_won <= price_max_krw // 10_000)
    return cond


def _order_clause(sort: str) -> Any:
    order_map: dict[str, Any] = {
        "price_asc": Listing.price_man_won.asc(),
        "price_desc": Listing.price_man_won.desc(),
        "year_desc": Listing.year.desc(),
        "year_asc": Listing.year.asc(),
        "mileage_asc": Listing.mileage_km.asc(),
        "mileage_desc": Listing.mileage_km.desc(),
        "updated_desc": Listing.updated_at.desc(),
        "updated_asc": Listing.updated_at.asc(),
    }
    return order_map.get(sort, Listing.updated_at.desc())


async def count_listings(
    db: AsyncSession,
    *,
    year_min: int | None = None,
    year_max: int | None = None,
    price_min_krw: int | None = None,
    price_max_krw: int | None = None,
) -> int:
    cond = _listing_filters(
        year_min=year_min,
        year_max=year_max,
        price_min_krw=price_min_krw,
        price_max_krw=price_max_krw,
    )
    result = await db.execute(
        select(func.count()).select_from(Listing).where(*cond)
    )
    return result.scalar_one()


async def list_listings(
    db: AsyncSession,
    *,
    page: int,
    limit: int,
    sort: str,
    year_min: int | None = None,
    year_max: int | None = None,
    price_min_krw: int | None = None,
    price_max_krw: int | None = None,
) -> tuple[list[Listing], int]:
    cond = _listing_filters(
        year_min=year_min,
        year_max=year_max,
        price_min_krw=price_min_krw,
        price_max_krw=price_max_krw,
    )
    count_result = await db.execute(
        select(func.count()).select_from(Listing).where(*cond)
    )
    total = count_result.scalar_one()
    order = _order_clause(sort)
    q = select(Listing).where(*cond).order_by(order)
    offset = (page - 1) * limit
    result = await db.execute(q.offset(offset).limit(limit))
    rows = list(result.scalars().all())
    return rows, total


async def get_listing_by_id(
    db: AsyncSession, listing_id: int
) -> Listing | None:
    result = await db.execute(
        select(Listing).where(
            Listing.id == listing_id, Listing.is_active == True  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def upsert_encar_listings(
    db: AsyncSession, items: list[dict[str, Any]]
) -> int:
    """Вставка или обновление по source_listing_id (PostgreSQL ON CONFLICT)."""
    if not items:
        return 0
    now = datetime.now(timezone.utc)
    for item in items:
        values = {
            **item,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        ins = pg_insert(Listing).values(**values)
        stmt = ins.on_conflict_do_update(
            index_elements=[Listing.source_listing_id],
            set_={
                "make": ins.excluded.make,
                "model": ins.excluded.model,
                "year": ins.excluded.year,
                "mileage_km": ins.excluded.mileage_km,
                "price_man_won": ins.excluded.price_man_won,
                "currency": ins.excluded.currency,
                "photos_json": ins.excluded.photos_json,
                "source_url": ins.excluded.source_url,
                "title": ins.excluded.title,
                "updated_at": now,
                "is_active": True,
            },
        )
        await db.execute(stmt)
    await db.commit()
    return len(items)
