from __future__ import annotations

from pydantic import BaseModel, Field


class StockDataRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str


class StockNewsRequest(BaseModel):
    symbol: str
    stock_name: str | None = None
    limit: int = 10


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
