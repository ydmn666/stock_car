from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

MarketType = Literal["CN"]
USERNAME_PATTERN = re.compile(r"^\S{4,20}$")


def normalize_username(value: str) -> str:
    return value.strip()


def validate_username(value: str) -> str:
    normalized = normalize_username(value)
    if not USERNAME_PATTERN.fullmatch(normalized):
        raise ValueError("用户名需为 4-20 位，且不能包含空格。")
    return normalized


def validate_password(value: str) -> str:
    if len(value) < 6 or len(value) > 20:
        raise ValueError("密码长度需为 6-20 位。")
    return value


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

    @field_validator("username")
    @classmethod
    def _validate_username(cls, value: str) -> str:
        return validate_username(value)

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        return validate_password(value)


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def _validate_username(cls, value: str) -> str:
        return validate_username(value)

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        return validate_password(value)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @field_validator("old_password")
    @classmethod
    def _validate_old_password(cls, value: str) -> str:
        if not value:
            raise ValueError("请输入当前密码。")
        return value

    @field_validator("new_password")
    @classmethod
    def _validate_new_password(cls, value: str) -> str:
        return validate_password(value)


class LogHistoryRequest(BaseModel):
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


class CreateTransactionRequest(BaseModel):
    symbol: str
    trade_type: Literal["buy", "sell"]
    trade_date: str
    price: float
    quantity: float
    fee: float = 0
    note: str | None = None


class UpdateTransactionRequest(BaseModel):
    symbol: str
    trade_type: Literal["buy", "sell"]
    trade_date: str
    price: float
    quantity: float
    fee: float = 0
    note: str | None = None
