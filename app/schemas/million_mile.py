import json
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from app.models.million_mile import Listing


def _parse_photo_urls(photos_json: str) -> list[str]:
    if not photos_json or not photos_json.strip():
        return []
    try:
        data = json.loads(photos_json)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [str(u) for u in data if u]


def listing_to_card(listing: "Listing") -> dict:
    photos = _parse_photo_urls(listing.photos_json)
    return {
        "id": listing.id,
        "title": listing.title,
        "make": listing.make,
        "model": listing.model,
        "year": listing.year,
        "mileage_km": listing.mileage_km,
        "mileage_unit": "km",
        "price_krw": listing.price_man_won * 10_000,
        "currency": listing.currency,
        "thumbnail_url": photos[0] if photos else "",
        "source_url": listing.source_url,
        "updated_at": listing.updated_at,
    }


def listing_to_detail(listing: "Listing") -> dict:
    base = listing_to_card(listing)
    base["photos"] = _parse_photo_urls(listing.photos_json)
    return base


class ListingCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    make: str
    model: str
    year: int
    mileage_km: int
    mileage_unit: str = "km"
    price_krw: int
    currency: str
    thumbnail_url: str
    source_url: str
    updated_at: datetime


class ListingDetail(ListingCard):
    photos: list[str]


class ListingListResponse(BaseModel):
    items: list[ListingCard]
    total: int
    page: int
    limit: int
