import asyncio
import logging

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.celery_worker import celery_app
from app.crud.million_mile import upsert_encar_listings
from app.parsers.encar import iter_listing_pages
from app.settings import settings

log = logging.getLogger(__name__)


async def _sync_encar_listings_async() -> dict[str, int]:
    engine = create_async_engine(settings.get_db_url(), echo=True, pool_size=1)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False)

    total_fetched = 0
    total_upserted = 0

    try:
        for page_num, page_items in enumerate(iter_listing_pages(), start=1):
            total_fetched += len(page_items)
            async with session_factory() as session:
                n = await upsert_encar_listings(session, page_items)
                total_upserted += n
            log.info("encar: страница %s — сохранено %s записей", page_num, n)
    finally:
        await engine.dispose()

    log.info("encar: итого получено=%s сохранено=%s",
             total_fetched, total_upserted)
    return {"fetched": total_fetched, "upserted": total_upserted}


@celery_app.task(name="app.tasks.sync_encar_listings")
def sync_encar_listings() -> dict[str, int]:
    try:
        return asyncio.run(_sync_encar_listings_async())
    except Exception as e:
        log.exception("sync_encar_listings упал: %s", e)
        raise
