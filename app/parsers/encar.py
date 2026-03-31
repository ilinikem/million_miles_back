"""Парсинг листингов Encar (HTTP + маппинг в поля модели Listing)."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Generator

import httpx

from app.settings import settings

log = logging.getLogger(__name__)

ENCAR_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.encar.com/",
    "Accept": "application/json",
}


def _parse_year(raw: Any, form_year: Any) -> int:
    if form_year is not None:
        try:
            y = int(str(form_year).strip()[:4])
            if 1980 <= y <= 2035:
                return y
        except (ValueError, TypeError):
            pass
    if raw is None:
        return 0
    try:
        v = float(raw)
        return int(v // 10000) if v > 10000 else int(v)
    except (ValueError, TypeError):
        return 0


def _photo_urls(item: dict[str, Any]) -> list[str]:
    base = settings.encar_image_base.rstrip("/")
    out: list[str] = []
    seen: set[str] = set()
    for p in item.get("Photos") or []:
        loc = p.get("location")
        if not loc:
            continue
        path = loc if str(loc).startswith("/") else f"/{loc}"
        url = f"{base}{path}"
        if url not in seen:
            seen.add(url)
            out.append(url)
    if not out and item.get("Photo"):
        prefix = str(item["Photo"])
        path = prefix if prefix.startswith("/") else f"/{prefix}"
        if path.endswith(".jpg"):
            out = [f"{base}{path}"]
        else:
            out = [f"{base}{path}001.jpg"]
    return out


def map_encar_item(item: dict[str, Any]) -> dict[str, Any] | None:
    sid = str(item.get("Id") or "").strip()
    if not sid:
        return None
    make = str(item.get("Manufacturer") or "").strip() or "Unknown"
    model = str(item.get("Model") or "").strip() or "Unknown"
    badge = str(item.get("Badge") or "").strip()
    year = _parse_year(item.get("Year"), item.get("FormYear"))
    try:
        mileage = int(float(item.get("Mileage") or 0))
    except (ValueError, TypeError):
        mileage = 0
    try:
        price_man = int(float(item.get("Price") or 0))
    except (ValueError, TypeError):
        price_man = 0
    photos = _photo_urls(item)
    if not photos:
        log.debug("skip listing %s: no photo URLs", sid)
        return None
    title = f"{make} {model}".strip()
    if badge:
        title = f"{title} {badge}"
    q = f"carid={sid}"
    source_url = f"{settings.encar_detail_base}?{q}"
    return {
        "source_listing_id": sid,
        "make": make,
        "model": model,
        "year": year,
        "mileage_km": mileage,
        "price_man_won": price_man,
        "currency": "KRW",
        "photos_json": json.dumps(photos, ensure_ascii=False),
        "source_url": source_url,
        "title": title[:1023],
    }


def fetch_page(
    client: httpx.Client, offset: int, page_size: int
) -> list[dict[str, Any]]:
    sr = f"|ModifiedDate|{offset}|{page_size}"
    params = {"q": settings.encar_query, "sr": sr}
    url = f"{settings.encar_api_base.rstrip('/')}{settings.encar_list_path}"
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            r = client.get(url, params=params,
                           headers=ENCAR_HEADERS, timeout=30.0)
            r.raise_for_status()
            data = r.json()
            return list(data.get("SearchResults") or [])
        except (httpx.HTTPError, ValueError) as e:
            last_err = e
            log.warning(
                "encar fetch offset=%s attempt %s: %s", offset, attempt + 1, e
            )
            time.sleep(1.0 * (attempt + 1))
    log.error("encar fetch failed offset=%s: %s", offset, last_err)
    return []


def _fetch_total_count(client: httpx.Client) -> int:
    """Получаем общее количество объявлений из первого запроса."""
    params = {
        "count": "true",
        "q": settings.encar_query,
        "sr": "|ModifiedDate|0|1",
    }
    url = f"{settings.encar_api_base.rstrip('/')}{settings.encar_list_path}"
    try:
        r = client.get(url, params=params, headers=ENCAR_HEADERS, timeout=30.0)
        r.raise_for_status()
        return int(r.json().get("Count") or 0)
    except Exception as e:
        log.warning("не удалось получить Count: %s", e)
        return 0


def iter_listing_pages() -> Generator[list[dict[str, Any]], None, None]:
    if not settings.encar_query.strip():
        log.warning("ENCAR_QUERY пуст — пропуск загрузки")
        return

    size = max(1, min(settings.encar_page_size, 60))

    with httpx.Client() as client:
        total = _fetch_total_count(client)
        if total == 0:
            log.warning("Count=0 или не удалось получить — прерываем")
            return

        total_pages = (total + size - 1) // size  # ceil division
        log.info("encar: всего %s объявлений, %s страниц по %s",
                 total, total_pages, size)

        for page in range(total_pages):
            offset = page * size
            rows = fetch_page(client, offset, size)
            if not rows:
                log.info("encar: пустая страница на offset=%s — стоп", offset)
                break

            items = [m for row in rows if (m := map_encar_item(row))]
            if items:
                yield items

            log.info("encar: страница %s/%s (offset=%s)",
                     page + 1, total_pages, offset)
            time.sleep(settings.encar_request_delay_sec)

            if len(rows) < size:
                break
