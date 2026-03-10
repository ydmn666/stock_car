from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
from langchain_core.tools import tool

from backend.services.forecast_service import generate_forecast
from backend.services.market_service import get_stock_data, get_stock_name, get_stock_news


def _resolve_date_range(start_date: str | None, end_date: str | None) -> tuple[date, date]:
    end_value = date.today() if not end_date else date.fromisoformat(end_date)
    start_value = end_value - timedelta(days=180) if not start_date else date.fromisoformat(start_date)
    return start_value, end_value


@tool
def lookup_stock_name(symbol: str) -> str:
    """Return the display name for an A-share stock code such as 002594."""

    return get_stock_name(symbol)


@tool
def get_stock_price_summary(symbol: str, start_date: str | None = None, end_date: str | None = None) -> str:
    """Summarize recent stock price performance for a stock code and optional ISO date range."""

    start_value, end_value = _resolve_date_range(start_date, end_date)
    df = get_stock_data(symbol, start_value, end_value)
    if df is None or df.empty:
        return f"未获取到 {symbol} 的行情数据。"

    calc_df = df.sort_values("日期").reset_index(drop=True)
    first_row = calc_df.iloc[0]
    last_row = calc_df.iloc[-1]
    start_price = float(first_row["收盘"])
    end_price = float(last_row["收盘"])
    pct = ((end_price - start_price) / start_price * 100) if start_price else 0.0
    high_price = float(calc_df["最高"].max())
    low_price = float(calc_df["最低"].min())
    avg_volume = float(calc_df["成交量"].tail(min(20, len(calc_df))).mean())
    stock_name = get_stock_name(symbol)

    return (
        f"{stock_name}({symbol}) 在 {start_value.isoformat()} 到 {end_value.isoformat()} 期间，"
        f"起始收盘价 {start_price:.2f}，最新收盘价 {end_price:.2f}，区间涨跌幅 {pct:.2f}%。"
        f"区间最高价 {high_price:.2f}，最低价 {low_price:.2f}，近20个交易日平均成交量约 {avg_volume:.0f}。"
    )


@tool
def get_stock_news_summary(symbol: str, limit: int = 5) -> str:
    """Return a compact news summary for a stock code. Use a small limit such as 3 to 5."""

    stock_name = get_stock_name(symbol)
    news_df, is_fallback = get_stock_news(symbol, stock_name, limit)
    if news_df is None or news_df.empty:
        return f"未获取到 {stock_name}({symbol}) 的相关新闻。"

    title_col = "新闻标题" if "新闻标题" in news_df.columns else news_df.columns[-1]
    time_col = "发布时间" if "发布时间" in news_df.columns else None

    lines: list[str] = []
    for _, row in news_df.head(limit).iterrows():
        prefix = ""
        if time_col:
            try:
                prefix = pd.to_datetime(row[time_col]).strftime("%Y-%m-%d") + " "
            except Exception:
                prefix = ""
        lines.append(f"- {prefix}{row[title_col]}")

    source_hint = "行业资讯回退结果" if is_fallback else "个股资讯"
    return f"{stock_name}({symbol}) 的最新{source_hint}：\n" + "\n".join(lines)


@tool
def get_stock_forecast_summary(symbol: str, days: int = 7) -> str:
    """Return a short Prophet-based forecast summary for a stock code."""

    end_value = date.today()
    start_value = end_value - timedelta(days=365)
    df = get_stock_data(symbol, start_value, end_value)
    if df is None or df.empty:
        return f"未获取到 {symbol} 的预测基础数据。"

    forecast_df = generate_forecast(df, days)
    if forecast_df is None or forecast_df.empty:
        return f"{symbol} 的历史数据不足，暂时无法生成 Prophet 预测。"

    future = forecast_df.tail(days)
    if future.empty:
        return f"{symbol} 的预测结果为空。"

    start_price = float(future.iloc[0]["yhat"])
    end_price = float(future.iloc[-1]["yhat"])
    growth = ((end_price - start_price) / start_price * 100) if start_price else 0.0
    upper = float(future.iloc[-1]["yhat_upper"])
    lower = float(future.iloc[-1]["yhat_lower"])
    uncertainty = ((upper - lower) / end_price * 100) if end_price else 0.0
    direction = "看涨" if growth >= 0 else "看跌"
    stock_name = get_stock_name(symbol)

    return (
        f"{stock_name}({symbol}) 基于 Prophet 的未来 {days} 天预测方向为 {direction}，"
        f"理论涨跌幅 {growth:.2f}%，预测目标价约 {end_price:.2f}。"
        f"末日预测区间 [{lower:.2f}, {upper:.2f}]，不确定性约 {uncertainty:.2f}%。"
    )


TOOLS = [
    lookup_stock_name,
    get_stock_price_summary,
    get_stock_news_summary,
    get_stock_forecast_summary,
]

