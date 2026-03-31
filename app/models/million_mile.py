from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    source_listing_id: Mapped[str] = mapped_column(
        String(32), unique=True, index=True,
        comment="Идентификатор объявления")
    make: Mapped[str] = mapped_column(
        String(255), comment="Производитель")
    model: Mapped[str] = mapped_column(
        String(512), comment="Модель авто")
    year: Mapped[int] = mapped_column(
        Integer, index=True, comment="Год выпуска")
    mileage_km: Mapped[int] = mapped_column(
        Integer, index=True, comment="Пробег авто")
    price_man_won: Mapped[int] = mapped_column(
        Integer, index=True, comment="Цена на сайте")
    currency: Mapped[str] = mapped_column(
        String(8), default="KRW", comment="Валюта")
    photos_json: Mapped[str] = mapped_column(
        Text, comment="URL картинок")
    source_url: Mapped[str] = mapped_column(
        String(1024), comment="Ссылка на страницу объявления")
    title: Mapped[str] = mapped_column(
        String(1024), comment="Заголовок для карточки")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, index=True, comment="Активность")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc),
        comment="Дата создания в БД")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc), comment="Дата обновления в БД")
