from __future__ import annotations

import pandas as pd
from prophet import Prophet

from backend.utils.network_env import disable_proxy_env

disable_proxy_env()


def _pick_column(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    for column in candidates:
        if column in df.columns:
            return column
    return None


def generate_forecast(df: pd.DataFrame, days: int = 7):
    if df is None or df.empty or len(df) < 30:
        return None

    date_column = _pick_column(df, ("trade_date", "日期"))
    close_column = _pick_column(df, ("close", "收盘"))
    if date_column is None or close_column is None:
        return None

    data = df[[date_column, close_column]].rename(columns={date_column: "ds", close_column: "y"}).copy()
    data["ds"] = pd.to_datetime(data["ds"])
    data["y"] = pd.to_numeric(data["y"], errors="coerce")
    data = data.dropna(subset=["ds", "y"])
    if len(data) < 30:
        return None

    model = Prophet(daily_seasonality=True, changepoint_prior_scale=0.05)
    model.fit(data)
    future = model.make_future_dataframe(periods=days)
    return model.predict(future)
