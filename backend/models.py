from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.db import Base


class StockHistory(Base):
    __tablename__ = "stock_history"

    stock_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    trade_date: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    open_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    close_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    high_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    low_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    turnover: Mapped[float | None] = mapped_column(Float, nullable=True)
    amplitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    pct_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    turnover_rate: Mapped[float | None] = mapped_column(Float, nullable=True)


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), primary_key=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)


class UserHistory(Base):
    __tablename__ = "user_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.username", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stock_name: Mapped[str] = mapped_column(String(100), nullable=False)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False)
    visit_time_str: Mapped[str] = mapped_column(String(32), nullable=False)
    timestamp: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.now)


class AIReport(Base):
    __tablename__ = "ai_reports"
    __table_args__ = (UniqueConstraint("stock_code", "date_range", name="uq_ai_reports_stock_date_range"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    date_range: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    report_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.now, index=True)
