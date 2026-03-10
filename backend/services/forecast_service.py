from __future__ import annotations

import pandas as pd
from prophet import Prophet


def generate_forecast(df: pd.DataFrame, days: int = 7):
    if df is None or df.empty or len(df) < 30:
        return None

    data = df[["日期", "收盘"]].rename(columns={"日期": "ds", "收盘": "y"}).copy()
    data["ds"] = pd.to_datetime(data["ds"])

    model = Prophet(daily_seasonality=True, changepoint_prior_scale=0.05)
    model.fit(data)
    future = model.make_future_dataframe(periods=days)
    return model.predict(future)
