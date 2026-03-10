from __future__ import annotations

import pandas as pd


DATETIME_COLUMNS = ("日期", "发布时间", "发布时间时间", "ds")


def dataframe_to_records(df: pd.DataFrame | None) -> list[dict]:
    if df is None or df.empty:
        return []

    payload = df.copy()
    for column in payload.columns:
        if pd.api.types.is_datetime64_any_dtype(payload[column]):
            payload[column] = payload[column].dt.strftime("%Y-%m-%d %H:%M:%S")
    payload = payload.where(pd.notna(payload), None)
    return payload.to_dict(orient="records")


def records_to_dataframe(records: list[dict] | None) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    for column in DATETIME_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")
    return df
