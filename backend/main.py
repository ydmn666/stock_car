from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from backend.schemas import (
    AgentRequest,
    ChatRequest,
    ForecastRequest,
    LogHistoryRequest,
    LoginRequest,
    RegisterRequest,
    StockDataRequest,
    StockNewsRequest,
)
from backend.agents.stock_agent import stream_agent
from backend.serialization import dataframe_to_records, records_to_dataframe
from backend.services.ai_service import stream_chat
from backend.services.auth_service import (
    delete_all_user_history,
    delete_history_item,
    get_user_history,
    log_history,
    login_user,
    register_user,
)
from backend.services.forecast_service import generate_forecast
from backend.services.market_service import get_stock_data, get_stock_name, get_stock_news, init_db


app = FastAPI(title="stock_car v2 backend")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/stocks/name/{symbol}")
def stock_name(symbol: str):
    return {"name": get_stock_name(symbol)}


@app.post("/stocks/data")
def stock_data(payload: StockDataRequest):
    try:
        df = get_stock_data(
            payload.symbol,
            datetime.strptime(payload.start_date, "%Y-%m-%d").date(),
            datetime.strptime(payload.end_date, "%Y-%m-%d").date(),
        )
        return {"records": dataframe_to_records(df)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/stocks/news")
def stock_news(payload: StockNewsRequest):
    try:
        df, is_fallback = get_stock_news(payload.symbol, payload.stock_name, payload.limit)
        return {"records": dataframe_to_records(df), "is_fallback": is_fallback}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/auth/register")
def auth_register(payload: RegisterRequest):
    success, message = register_user(payload.username, payload.password)
    return {"success": success, "message": message}


@app.post("/auth/login")
def auth_login(payload: LoginRequest):
    return {"success": login_user(payload.username, payload.password)}


@app.get("/users/{username}/history")
def user_history(username: str):
    return {"items": get_user_history(username)}


@app.post("/users/history/log")
def user_history_log(payload: LogHistoryRequest):
    log_history(payload.username, payload.stock_name, payload.stock_code)
    return JSONResponse({"success": True})


@app.delete("/users/history/{item_id}")
def user_history_delete(item_id: int):
    delete_history_item(item_id)
    return JSONResponse({"success": True})


@app.delete("/users/{username}/history")
def user_history_clear(username: str):
    delete_all_user_history(username)
    return JSONResponse({"success": True})


@app.post("/forecast")
def forecast(payload: ForecastRequest):
    try:
        df = records_to_dataframe(payload.records)
        forecast_df = generate_forecast(df, payload.days)
        return {"records": dataframe_to_records(forecast_df)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ai/chat/stream")
def ai_chat_stream(payload: ChatRequest):
    try:
        return StreamingResponse(
            stream_chat([message.model_dump() for message in payload.messages], payload.temperature),
            media_type="text/plain; charset=utf-8",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ai/agent/stream")
def ai_agent_stream(payload: AgentRequest):
    try:
        return StreamingResponse(
            stream_agent([message.model_dump() for message in payload.messages]),
            media_type="text/plain; charset=utf-8",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
