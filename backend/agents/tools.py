from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
from langchain_core.tools import tool

from backend.services.forecast_service import generate_forecast
from backend.services.market_service import get_stock_data, get_stock_name, get_stock_news
from backend.services.portfolio_service import get_user_portfolio_snapshot


def _resolve_date_range(start_date: str | None, end_date: str | None) -> tuple[date, date]:
    end_value = date.today() if not end_date else date.fromisoformat(end_date)
    start_value = end_value - timedelta(days=180) if not start_date else date.fromisoformat(start_date)
    return start_value, end_value


@tool
def lookup_stock_name(symbol: str) -> str:
    """Return the display name for an A-share stock symbol such as 002594."""

    return get_stock_name(symbol)


@tool
def get_stock_price_summary(symbol: str, start_date: str | None = None, end_date: str | None = None) -> str:
    """Summarize recent stock price performance for a stock code and optional ISO date range."""

    start_value, end_value = _resolve_date_range(start_date, end_date)
    df = get_stock_data(symbol, start_value, end_value)
    if df is None or df.empty:
        return f"未获取到 {symbol} 的行情数据。"

    calc_df = df.sort_values("trade_date").reset_index(drop=True)
    first_row = calc_df.iloc[0]
    last_row = calc_df.iloc[-1]
    start_price = float(first_row["close"])
    end_price = float(last_row["close"])
    pct = ((end_price - start_price) / start_price * 100) if start_price else 0.0
    high_price = float(calc_df["high"].max())
    low_price = float(calc_df["low"].min())
    avg_volume = float(calc_df["volume"].tail(min(20, len(calc_df))).mean())
    stock_name = get_stock_name(symbol)

    return (
        f"{stock_name}({symbol}) 在 {start_value.isoformat()} 到 {end_value.isoformat()} 期间，"
        f"起始收盘价 {start_price:.2f}，最新收盘价 {end_price:.2f}，区间涨跌幅 {pct:.2f}%。"
        f"区间最高价 {high_price:.2f}，最低价 {low_price:.2f}，近 20 个交易日平均成交量约 {avg_volume:.0f}。"
    )


@tool
def get_stock_news_summary(symbol: str, limit: int = 5) -> str:
    """Return a compact news summary for a stock symbol. Use a small limit such as 3 to 5."""

    stock_name = get_stock_name(symbol)
    news_df, is_fallback = get_stock_news(symbol, stock_name, limit)
    if news_df is None or news_df.empty:
        return f"未获取到 {stock_name}({symbol}) 的相关资讯。"

    lines: list[str] = []
    for _, row in news_df.head(limit).iterrows():
        prefix = ""
        if "published_at" in news_df.columns and pd.notna(row.get("published_at")):
            try:
                prefix = pd.to_datetime(row["published_at"]).strftime("%Y-%m-%d") + " "
            except Exception:
                prefix = ""
        lines.append(f"- {prefix}{row['title']}")

    source_hint = "行业回退资讯" if is_fallback else "个股资讯"
    return f"{stock_name}({symbol}) 的最新 {source_hint}：\n" + "\n".join(lines)


@tool
def get_stock_forecast_summary(symbol: str, days: int = 7) -> str:
    """Return a short Prophet-based forecast summary for a stock symbol."""

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
        f"理论涨跌幅约 {growth:.2f}%，预测目标价约 {end_price:.2f}。"
        f"末日预测区间 [{lower:.2f}, {upper:.2f}]，不确定性约 {uncertainty:.2f}%。"
    )


@tool
def get_user_portfolio_summary(username: str) -> str:
    """Return the current user's portfolio snapshot including summary, holdings, and recent transactions."""

    snapshot = get_user_portfolio_snapshot(username)
    summary = snapshot["summary"]
    positions = snapshot["positions"]
    recent_transactions = snapshot["recent_transactions"]

    is_flat = summary["position_count"] == 0
    pct_text = "--" if summary["unrealized_pnl_pct"] is None else f"{summary['unrealized_pnl_pct']:.2f}%"
    lines: list[str] = [
        f"用户 {username} 的个人投资概况：",
        f"- {'累计回笼资金' if is_flat else '净投入'}：{(summary['cash_returned'] if is_flat else summary['net_invested']):.2f}",
        f"- 当前市值：{summary['market_value']:.2f}",
        f"- {'已实现盈亏' if is_flat else '浮动盈亏'}：{(summary['realized_pnl'] if is_flat else summary['unrealized_pnl']):.2f}",
        f"- {'浮动收益率' if not is_flat else '持仓状态'}：{pct_text if not is_flat else '当前已清仓'}",
        f"- 当前持仓只数：{summary['position_count']}",
        f"- 交易记录笔数：{summary['transaction_count']}",
    ]

    if positions:
        lines.append("当前持仓：")
        for item in positions[:5]:
            item_pct = "--" if item["unrealized_pnl_pct"] is None else f"{item['unrealized_pnl_pct']:.2f}%"
            latest_price = "--" if item["latest_price"] is None else f"{item['latest_price']:.2f}"
            pnl_text = f"{(item['unrealized_pnl'] or 0):.2f}"
            lines.append(
                f"- {item['stock_name']}({item['symbol']})：{item['quantity']:.0f} 股，成本价 {item['avg_cost']:.2f}，"
                f"最新价 {latest_price}，浮盈 {pnl_text}，收益率 {item_pct}"
            )
    else:
        lines.append("当前没有持仓。")

    if recent_transactions:
        lines.append("最近交易：")
        for item in recent_transactions[:5]:
            direction = "买入" if item["trade_type"] == "buy" else "卖出"
            lines.append(
                f"- {item['trade_date']} {direction} {item['stock_name']}({item['symbol']})，价格 {item['price']:.2f}，股数 {item['quantity']:.0f}"
            )

    return "\n".join(lines)


TOOLS = [
    lookup_stock_name,
    get_stock_price_summary,
    get_stock_news_summary,
    get_stock_forecast_summary,
    get_user_portfolio_summary,
]
