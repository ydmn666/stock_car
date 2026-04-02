from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
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


class StockInstrument(Base):
    __tablename__ = "stock_instruments"

    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    market: Mapped[str] = mapped_column(String(8), nullable=False, default="CN", index=True)
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False, default="stock")
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_symbol: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    exchange: Mapped[str | None] = mapped_column(String(32), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CNY")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.now, onupdate=dt.datetime.now)


class PriceCache(Base):
    __tablename__ = "price_cache"
    __table_args__ = (UniqueConstraint("symbol", "trade_date", "adjusted", name="uq_price_cache_symbol_trade_date_adjusted"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), ForeignKey("stock_instruments.symbol", ondelete="CASCADE"), nullable=False, index=True)
    trade_date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    adjusted: Mapped[str] = mapped_column(String(12), nullable=False, default="qfq")
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
    source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fetched_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.now, index=True)


class NewsCache(Base):
    __tablename__ = "news_cache"
    __table_args__ = (UniqueConstraint("symbol", "title", "published_at", name="uq_news_cache_symbol_title_published_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), ForeignKey("stock_instruments.symbol", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(64), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    matched_by: Mapped[str | None] = mapped_column(String(32), nullable=True)
    published_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, index=True)
    fetched_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.now, index=True)


class UserPortfolio(Base):
    __tablename__ = "user_portfolios"
    __table_args__ = (UniqueConstraint("username", "name", name="uq_user_portfolios_username_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), ForeignKey("users.username", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="默认组合")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    base_currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CNY")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.now, onupdate=dt.datetime.now)


class InvestmentTransaction(Base):
    __tablename__ = "investment_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), ForeignKey("users.username", ondelete="CASCADE"), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), ForeignKey("stock_instruments.symbol", ondelete="CASCADE"), nullable=False, index=True)
    stock_name: Mapped[str] = mapped_column(String(100), nullable=False)
    trade_type: Mapped[str] = mapped_column(String(16), nullable=False)
    trade_date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    fee: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    tax: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.now)


class PositionSnapshot(Base):
    __tablename__ = "position_snapshots"
    __table_args__ = (UniqueConstraint("portfolio_id", "symbol", "snapshot_date", name="uq_position_snapshots_portfolio_symbol_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), ForeignKey("users.username", ondelete="CASCADE"), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), ForeignKey("stock_instruments.symbol", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    avg_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    invested_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    market_value: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    unrealized_pnl: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    unrealized_pnl_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.now)
