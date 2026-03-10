from __future__ import annotations

import hashlib
import os
import sqlite3
from datetime import datetime
from pathlib import Path

import akshare as ak
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
DB_FILE = ROOT_DIR / "stock_data.db"


def init_db() -> None:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stock_history (
            日期 TEXT, 开盘 REAL, 收盘 REAL, 最高 REAL, 最低 REAL,
            成交量 INTEGER, 成交额 REAL, 振幅 REAL, 涨跌幅 REAL, 涨跌额 REAL, 换手率 REAL,
            股票代码 TEXT, PRIMARY KEY (日期, 股票代码)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            stock_name TEXT,
            stock_code TEXT,
            visit_time_str TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    try:
        cursor.execute("SELECT stock_code FROM user_history LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE user_history ADD COLUMN stock_code TEXT")

    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def get_db_range(symbol: str):
    if not DB_FILE.exists():
        return None, None

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MIN(日期), MAX(日期) FROM stock_history WHERE 股票代码 = ?", (symbol,))
        result = cursor.fetchone()
        if result and result[0] and result[1]:
            return datetime.strptime(result[0], "%Y-%m-%d").date(), datetime.strptime(result[1], "%Y-%m-%d").date()
    finally:
        conn.close()
    return None, None


def save_to_sqlite(df: pd.DataFrame, symbol: str) -> None:
    if df.empty:
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        records = []
        for _, row in df.iterrows():
            records.append(
                (
                    row["日期"].strftime("%Y-%m-%d"),
                    row["开盘"],
                    row["收盘"],
                    row["最高"],
                    row["最低"],
                    row["成交量"],
                    row["成交额"],
                    row["振幅"],
                    row["涨跌幅"],
                    row["涨跌额"],
                    row["换手率"],
                    symbol,
                )
            )
        cursor.executemany(
            """
            INSERT OR IGNORE INTO stock_history
            (日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率, 股票代码)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            records,
        )
        conn.commit()
    finally:
        conn.close()


def load_from_sqlite(symbol: str, start_date, end_date) -> pd.DataFrame:
    conn = sqlite3.connect(DB_FILE)
    try:
        query = """
        SELECT * FROM stock_history
        WHERE 股票代码 = ?
          AND 日期 >= ?
          AND 日期 <= ?
        ORDER BY 日期 ASC
        """
        df = pd.read_sql(
            query,
            conn,
            params=(symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")),
        )
        if not df.empty:
            df["日期"] = pd.to_datetime(df["日期"])
        return df
    finally:
        conn.close()


def get_stock_data(symbol: str, start_date, end_date) -> pd.DataFrame:
    init_db()
    db_min, db_max = get_db_range(symbol)
    need_fetch = db_min is None or start_date < db_min or end_date > db_max

    if need_fetch:
        df_new = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust="qfq",
        )
        if not df_new.empty:
            df_new["日期"] = pd.to_datetime(df_new["日期"])
            save_to_sqlite(df_new, symbol)

    return load_from_sqlite(symbol, start_date, end_date)


def get_stock_name(symbol: str) -> str:
    try:
        info = ak.stock_individual_info_em(symbol=symbol)
        name_row = info[info["item"] == "股票简称"]
        if not name_row.empty:
            return name_row["value"].values[0]
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
