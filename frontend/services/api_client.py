from __future__ import annotations

import os
import re
from datetime import date, datetime

import pandas as pd
import requests
import streamlit as st


DEFAULT_TIMEOUT = 60
DATETIME_COLUMNS = ("日期", "发布时间", "发布时间时间", "ds")


def _base_url() -> str:
    return (
        st.secrets.get("BACKEND_BASE_URL")
        or os.getenv("BACKEND_BASE_URL")
        or "http://127.0.0.1:8000"
    ).rstrip("/")


def _date_to_str(value) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _dataframe_from_records(records: list[dict] | None) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    for column in DATETIME_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def _dataframe_to_records(df: pd.DataFrame | None) -> list[dict]:
    if df is None or df.empty:
        return []

    payload = df.copy()
    for column in payload.columns:
        if pd.api.types.is_datetime64_any_dtype(payload[column]):
            payload[column] = payload[column].dt.strftime("%Y-%m-%d %H:%M:%S")
    payload = payload.where(pd.notna(payload), None)
    return payload.to_dict(orient="records")


def _request(method: str, path: str, **kwargs):
    response = requests.request(method, f"{_base_url()}{path}", timeout=DEFAULT_TIMEOUT, **kwargs)
    if not response.ok:
        detail = ""
        try:
            payload = response.json()
            if isinstance(payload, dict):
                detail = payload.get("detail", "")
        except Exception:
            detail = response.text[:500]
        message = f"{response.status_code} Server Error: {response.reason} for url: {response.url}"
        if detail:
            message = f"{message}\n后端详情: {detail}"
        raise requests.HTTPError(message, response=response)
    return response


def get_stock_name(symbol: str) -> str:
    try:
        response = _request("GET", f"/stocks/name/{symbol}")
        return response.json()["name"]
    except Exception:
        return symbol


def get_stock_data(symbol: str, start_date, end_date) -> pd.DataFrame:
    response = _request(
        "POST",
        "/stocks/data",
        json={
            "symbol": symbol,
            "start_date": _date_to_str(start_date),
            "end_date": _date_to_str(end_date),
        },
    )
    return _dataframe_from_records(response.json().get("records"))


def get_stock_news(symbol: str, stock_name: str | None = None, limit: int = 10):
    response = _request(
        "POST",
        "/stocks/news",
        json={"symbol": symbol, "stock_name": stock_name, "limit": limit},
    )
    payload = response.json()
    return _dataframe_from_records(payload.get("records")), payload.get("is_fallback", False)


def register_user(username: str, password: str):
    response = _request("POST", "/auth/register", json={"username": username, "password": password})
    payload = response.json()
    return payload["success"], payload["message"]


def login_user(username: str, password: str) -> bool:
    response = _request("POST", "/auth/login", json={"username": username, "password": password})
    return response.json()["success"]


def get_user_history(username: str):
    response = _request("GET", f"/users/{username}/history")
    items = response.json().get("items", [])
    return [(item["id"], item["stock_name"], item["stock_code"], item["visit_time_str"]) for item in items]


def log_history(username: str, stock_name: str, stock_code: str) -> None:
    _request(
        "POST",
        "/users/history/log",
        json={"username": username, "stock_name": stock_name, "stock_code": stock_code},
    )


def delete_history_item(item_id: int) -> None:
    _request("DELETE", f"/users/history/{item_id}")


def delete_all_user_history(username: str) -> None:
    _request("DELETE", f"/users/{username}/history")


def generate_forecast(df: pd.DataFrame, days: int = 7):
    response = _request(
        "POST",
        "/forecast",
        json={"records": _dataframe_to_records(df), "days": days},
    )
    forecast_df = _dataframe_from_records(response.json().get("records"))
    return forecast_df, None


def get_deepseek_chat_stream(messages: list[dict], temperature: float = 1.1):
    try:
        with requests.post(
            f"{_base_url()}/ai/chat/stream",
            json={"messages": messages, "temperature": temperature},
            timeout=(10, 300),
            stream=True,
        ) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    yield chunk
    except Exception as exc:
        yield f"⚠️ **AI 连接失败**: {exc}\n\n请检查后端服务、API Key 和网络。"


def get_agent_chat_stream(messages: list[dict], context: dict | None = None):
    try:
        with requests.post(
            f"{_base_url()}/ai/agent/stream",
            json={"messages": messages, "context": context or {}},
            timeout=(10, 300),
            stream=True,
        ) as response:
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    yield chunk
    except Exception as exc:
        yield f"⚠️ **Agent 连接失败**: {exc}\n\n请检查后端服务、API Key 和网络。"


def get_agent_response(messages: list[dict], context: dict | None = None) -> dict:
    response = _request(
        "POST",
        "/ai/agent/respond",
        json={"messages": messages, "context": context or {}},
    )
    payload = response.json()
    return {"content": payload.get("content", ""), "actions": payload.get("actions", [])}


def generate_pdf_report(symbol: str, start_date, end_date, stock_name: str | None = None):
    response = _request(
        "POST",
        "/reports/pdf",
        json={
            "symbol": symbol,
            "stock_name": stock_name,
            "start_date": _date_to_str(start_date),
            "end_date": _date_to_str(end_date),
        },
    )

    disposition = response.headers.get("Content-Disposition", "")
    match = re.search(r'filename="([^"]+)"', disposition)
    filename = match.group(1) if match else f"{symbol}_report.pdf"
    if stock_name:
        filename = f"{stock_name}_{symbol}_report.pdf"
    return response.content, filename
