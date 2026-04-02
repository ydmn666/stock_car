from __future__ import annotations

from backend.utils.network_env import disable_proxy_env
disable_proxy_env()
from datetime import datetime
import traceback

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from backend.schemas import (
    AgentRequest,
    ChatRequest,
    CreateTransactionRequest,
    ForecastRequest,
    LogHistoryRequest,
    LoginRequest,
    ResolveInstrumentRequest,
    RegisterRequest,
    ReportRequest,
    StockDataRequest,
    StockNewsRequest,
    UpdateTransactionRequest,
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
from backend.services.market_service import get_instrument_payload, get_news_payload, get_price_history_payload, get_stock_name, init_db
from backend.services.portfolio_service import (
    create_transaction,
    delete_transaction,
    get_portfolio_performance,
    get_portfolio_summary,
    get_positions,
    list_transactions,
    update_transaction,
)
from backend.services.report_service import cleanup_expired_reports, get_or_create_stock_report


app = FastAPI()

# 允许前端容器与本地开发环境直接访问后端 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 椤烘墜鍔犱竴涓€滄闂ㄢ€濓紝鏀惧湪 @app.on_event("startup") 涓嬫柟鍗冲彲
# 杩欎釜鏄负浜嗛槻姝綘鐩存帴璁块棶閾炬帴鏃剁湅鍒版伡浜虹殑 {"detail":"Not Found"}
@app.get("/")
def read_root():
    return {"status": "ok", "message": "后端服务已启动。"}


@app.on_event("startup")
def on_startup():
    init_db()
    cleanup_expired_reports()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/stocks/name/{symbol}")
def stock_name(symbol: str, market: str | None = None):
    try:
        return {"name": get_stock_name(symbol, market)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/instruments/resolve")
def resolve_stock_instrument(payload: ResolveInstrumentRequest):
    try:
        return get_instrument_payload(payload.symbol, payload.market)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/stocks/data")
def stock_data(payload: StockDataRequest):
    try:
        return get_price_history_payload(
            payload.symbol,
            datetime.strptime(payload.start_date, "%Y-%m-%d").date(),
            datetime.strptime(payload.end_date, "%Y-%m-%d").date(),
            payload.market,
            payload.debug_fail_providers,
        )
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail=f"股票数据源访问失败，请稍后重试。{exc}"
        ) from exc


@app.post("/stocks/news")
def stock_news(payload: StockNewsRequest):
    try:
        return get_news_payload(payload.symbol, payload.stock_name, payload.limit, payload.market, payload.debug_fail_providers)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
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


@app.get("/portfolio/{username}/summary")
def portfolio_summary(username: str):
    try:
        return get_portfolio_summary(username)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/portfolio/{username}/positions")
def portfolio_positions(username: str):
    try:
        return {"items": get_positions(username)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/portfolio/{username}/performance")
def portfolio_performance(username: str):
    try:
        return get_portfolio_performance(username)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/portfolio/{username}/transactions")
def portfolio_transactions(username: str):
    try:
        return {"items": list_transactions(username)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/portfolio/transactions")
def portfolio_transaction_create(payload: CreateTransactionRequest):
    try:
        return create_transaction(
            username=payload.username,
            symbol=payload.symbol,
            trade_type=payload.trade_type,
            trade_date=datetime.strptime(payload.trade_date, "%Y-%m-%d").date(),
            price=payload.price,
            quantity=payload.quantity,
            fee=payload.fee,
            note=payload.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/portfolio/{username}/transactions/{transaction_id}")
def portfolio_transaction_delete(username: str, transaction_id: int):
    try:
        delete_transaction(username, transaction_id)
        return {"success": True}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/portfolio/{username}/transactions/{transaction_id}")
def portfolio_transaction_update(username: str, transaction_id: int, payload: UpdateTransactionRequest):
    if payload.username != username:
        raise HTTPException(status_code=400, detail="请求用户与路径用户不一致。")
    try:
        return update_transaction(
            username=payload.username,
            transaction_id=transaction_id,
            symbol=payload.symbol,
            trade_type=payload.trade_type,
            trade_date=datetime.strptime(payload.trade_date, "%Y-%m-%d").date(),
            price=payload.price,
            quantity=payload.quantity,
            fee=payload.fee,
            note=payload.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
            market=payload.market,
        )
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc




