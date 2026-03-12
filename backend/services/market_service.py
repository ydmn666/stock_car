from __future__ import annotations

import hashlib
from datetime import date, timedelta

import akshare as ak
import pandas as pd
from sqlalchemy import func, select

from backend.db import SessionLocal, engine
from backend.models import Base, StockHistory


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_stock_data(symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
    init_db()
    db_min, db_max = _get_db_range(symbol)

    if db_min is None or db_max is None:
        fetched = _fetch_from_akshare(symbol, start_date, end_date)
        _save_to_db(fetched, symbol)
        return _load_from_db(symbol, start_date, end_date)

    if start_date < db_min:
        fetched = _fetch_from_akshare(symbol, start_date, db_min - timedelta(days=1))
        _save_to_db(fetched, symbol)

    if end_date > db_max:
        fetched = _fetch_from_akshare(symbol, db_max + timedelta(days=1), end_date)
        _save_to_db(fetched, symbol)

    return _load_from_db(symbol, start_date, end_date)


def get_stock_name(symbol: str) -> str:
    try:
        info = ak.stock_individual_info_em(symbol=symbol)
        name_row = info[info["item"] == "股票简称"]
        if not name_row.empty:
            return str(name_row["value"].values[0])
    except Exception:
        pass
    return symbol


def get_sector_news_fallback(limit: int):
    try:
        df = ak.stock_news_em(symbol="399976")
        if df is not None and not df.empty:
            if "发布时间" in df.columns:
                df["发布时间"] = pd.to_datetime(df["发布时间"])
                df = df.sort_values(by="发布时间", ascending=False)
            return df.head(limit), True
    except Exception:
        pass
    return pd.DataFrame(), False


def get_stock_news(symbol: str, stock_name: str | None = None, limit: int = 10):
    try:
        news_df = ak.stock_news_em(symbol=symbol)
        if news_df is None or news_df.empty:
            return get_sector_news_fallback(limit)
        if "发布时间" in news_df.columns:
            news_df["发布时间"] = pd.to_datetime(news_df["发布时间"])
            news_df = news_df.sort_values(by="发布时间", ascending=False)
        return news_df.head(limit), False
    except Exception:
        return get_sector_news_fallback(limit)


def _get_db_range(symbol: str) -> tuple[date | None, date | None]:
    with SessionLocal() as session:
        stmt = select(func.min(StockHistory.trade_date), func.max(StockHistory.trade_date)).where(
            StockHistory.stock_code == symbol
        )
        result = session.execute(stmt).one()
        return result[0], result[1]


def _fetch_from_akshare(symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
    if start_date > end_date:
        return pd.DataFrame()

    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_date.strftime("%Y%m%d"),
        end_date=end_date.strftime("%Y%m%d"),
        adjust="qfq",
    )
    if df.empty:
        return df

    payload = df.copy()
    payload["日期"] = pd.to_datetime(payload["日期"])
    return payload


def _save_to_db(df: pd.DataFrame, symbol: str) -> None:
    if df.empty:
        return

    with SessionLocal() as session:
        for _, row in df.iterrows():
            session.merge(
                StockHistory(
                    stock_code=symbol,
                    trade_date=row["日期"].date(),
                    open_price=_safe_float(row.get("开盘")),
                    close_price=_safe_float(row.get("收盘")),
                    high_price=_safe_float(row.get("最高")),
                    low_price=_safe_float(row.get("最低")),
                    volume=_safe_float(row.get("成交量")),
                    turnover=_safe_float(row.get("成交额")),
                    amplitude=_safe_float(row.get("振幅")),
                    pct_change=_safe_float(row.get("涨跌幅")),
                    price_change=_safe_float(row.get("涨跌额")),
                    turnover_rate=_safe_float(row.get("换手率")),
                )
            )
        session.commit()


def _load_from_db(symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
    with SessionLocal() as session:
        stmt = (
            select(StockHistory)
            .where(
                StockHistory.stock_code == symbol,
                StockHistory.trade_date >= start_date,
                StockHistory.trade_date <= end_date,
            )
            .order_by(StockHistory.trade_date.asc())
        )
        rows = session.execute(stmt).scalars().all()

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(
        [
            {
                "日期": pd.to_datetime(row.trade_date),
                "开盘": row.open_price,
                "收盘": row.close_price,
                "最高": row.high_price,
                "最低": row.low_price,
                "成交量": row.volume,
                "成交额": row.turnover,
                "振幅": row.amplitude,
                "涨跌幅": row.pct_change,
                "涨跌额": row.price_change,
                "换手率": row.turnover_rate,
                "股票代码": row.stock_code,
            }
            for row in rows
        ]
    )


def _safe_float(value):
    if pd.isna(value):
        return None
    return float(value)
