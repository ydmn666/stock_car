from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

MarketType = Literal["CN"]


class ResolveInstrumentRequest(BaseModel):
    symbol: str
    market: MarketType | None = None


class StockDataRequest(BaseModel):
    market: MarketType | None = None
    symbol: str
    start_date: str
    end_date: str
    debug_fail_providers: list[str] = Field(default_factory=list)


class StockNewsRequest(BaseModel):
    market: MarketType | None = None
    symbol: str
    stock_name: str | None = None
    limit: int = 10
    debug_fail_providers: list[str] = Field(default_factory=list)


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LogHistoryRequest(BaseModel):
    username: str
    stock_name: str
    stock_code: str


class ForecastRequest(BaseModel):
    records: list[dict] = Field(default_factory=list)
    days: int = 7


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    temperature: float = 1.1


class AgentRequest(BaseModel):
    messages: list[ChatMessage]
    context: dict = Field(default_factory=dict)


class ReportRequest(BaseModel):
    market: MarketType | None = None
    symbol: str
    stock_name: str | None = None
    start_date: str
    end_date: str
