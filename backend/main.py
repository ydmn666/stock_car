from __future__ import annotations

from datetime import datetime
import traceback

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from backend.schemas import (
    AgentRequest,
    ChatRequest,
    ForecastRequest,
    LogHistoryRequest,
    LoginRequest,
    RegisterRequest,
    ReportRequest,
    StockDataRequest,
    StockNewsRequest,
)
from backend.agents.stock_agent import run_agent_with_actions, stream_agent
from backend.serialization import dataframe_to_records, records_to_dataframe
from backend.services.ai_service import respond_chat, stream_chat
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
from backend.services.report_service import cleanup_expired_reports, get_or_create_stock_report


app = FastAPI(title="stock_car v2 backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    cleanup_expired_reports()


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
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ai/chat/respond")
def ai_chat_respond(payload: ChatRequest):
    try:
        content = respond_chat([message.model_dump() for message in payload.messages], payload.temperature)
        return {"content": content}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ai/agent/stream")
def ai_agent_stream(payload: AgentRequest):
    try:
        return StreamingResponse(
            stream_agent([message.model_dump() for message in payload.messages], payload.context),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ai/agent/respond")
def ai_agent_respond(payload: AgentRequest):
    try:
        return run_agent_with_actions([message.model_dump() for message in payload.messages], payload.context)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/reports/pdf")
def generate_pdf_report(payload: ReportRequest):
    try:
        pdf_bytes, filename = get_or_create_stock_report(
            symbol=payload.symbol,
            stock_name=payload.stock_name,
            start_date=payload.start_date,
            end_date=payload.end_date,
        )
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
