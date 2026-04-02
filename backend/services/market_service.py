from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from typing import Literal

import akshare as ak
import pandas as pd
import requests
from sqlalchemy import func, inspect, select, text

from backend.db import SessionLocal, engine
from backend.models import Base, StockHistory
from backend.utils.network_env import disable_proxy_env

disable_proxy_env()

try:
    import baostock as bs
except ImportError:  # pragma: no cover - optional dependency
    bs = None

Market = Literal["CN"]
AssetType = Literal["stock"]

LOCAL_CN_STOCK_NAMES = {
    "002594": "比亚迪",
    "300750": "宁德时代",
    "000625": "长安汽车",
}


@dataclass(slots=True)
class Instrument:
    id: str
    market: Market
    symbol: str
    full_symbol: str
    asset_type: AssetType
    display_name: str
    exchange: str | None = None
    currency: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class PriceBar:
    instrument_id: str
    market: Market
    symbol: str
    trade_date: str
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: float | None
    turnover: float | None
    amplitude: float | None
    pct_change: float | None
    price_change: float | None
    turnover_rate: float | None
    adjusted: str
    currency: str
    source: str
    source_symbol: str | None = None
    is_fallback: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class NewsItem:
    id: str
    instrument_id: str
    market: Market
    symbol: str
    title: str
    summary: str | None
    content: str | None
    source: str
    publisher: str | None
    url: str | None
    published_at: str
    language: str | None
    matched_by: str
    is_fallback: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class ProviderUnavailableError(RuntimeError):
    pass


class MarketProvider:
    name = "base"
    supported_markets: tuple[Market, ...] = ()

    @property
    def key(self) -> str:
        return f"{self.name}:{','.join(self.supported_markets)}"

    def resolve_instrument(self, symbol: str, market: Market) -> Instrument:
        raise NotImplementedError

    def get_price_history(self, instrument: Instrument, start_date: date, end_date: date) -> list[PriceBar]:
        raise NotImplementedError

    def get_news(self, instrument: Instrument, limit: int) -> tuple[list[NewsItem], bool]:
        raise NotImplementedError


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_runtime_schema()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def normalize_market(value: str | None) -> Market:
    if value is None:
        raise ValueError("market is required")
    upper = value.upper()
    if upper not in {"CN"}:
        raise ValueError(f"Unsupported market: {value}")
    return upper  # type: ignore[return-value]


def infer_market(symbol: str) -> Market:
    normalized = symbol.strip().upper()
    if normalized.isdigit():
        return "CN"
    raise ValueError(f"Unsupported symbol for CN market: {symbol}")


def normalize_symbol(symbol: str, market: Market) -> str:
    normalized = symbol.strip().upper()
    code = normalized.split(".")[0]
    if not code.isdigit():
        raise ValueError(f"Unsupported A-share symbol: {symbol}")
    return code.zfill(6)


def build_instrument(market: Market, symbol: str, display_name: str | None = None) -> Instrument:
    normalized_symbol = normalize_symbol(symbol, market)
    exchange = "SZSE" if normalized_symbol.startswith(("0", "3")) else "SSE"
    suffix = "SZ" if exchange == "SZSE" else "SH"
    currency = "CNY"
    return Instrument(
        id=f"{market}:{normalized_symbol}",
        market=market,
        symbol=normalized_symbol,
        full_symbol=f"{normalized_symbol}.{suffix}",
        asset_type="stock",
        display_name=display_name or normalized_symbol,
        exchange=exchange,
        currency=currency,
    )


class AkshareCNProvider(MarketProvider):
    name = "akshare"
    supported_markets: tuple[Market, ...] = ("CN",)

    def resolve_instrument(self, symbol: str, market: Market) -> Instrument:
        normalized_symbol = normalize_symbol(symbol, market)
        return build_instrument(market, normalized_symbol, _fetch_cn_stock_name(normalized_symbol))

    def get_price_history(self, instrument: Instrument, start_date: date, end_date: date) -> list[PriceBar]:
        df = _get_cn_price_history_cached(instrument.symbol, start_date, end_date)
        return _price_dataframe_to_bars(df, instrument, self.name, adjusted="qfq")

    def get_news(self, instrument: Instrument, limit: int) -> tuple[list[NewsItem], bool]:
        df, is_fallback = _get_cn_news(instrument.symbol, limit)
        return _news_dataframe_to_items(df, instrument, self.name, is_fallback), is_fallback


class BaostockCNProvider(MarketProvider):
    name = "baostock"
    supported_markets: tuple[Market, ...] = ("CN",)

    def resolve_instrument(self, symbol: str, market: Market) -> Instrument:
        return build_instrument(market, symbol, _fetch_cn_stock_name(symbol))

    def get_price_history(self, instrument: Instrument, start_date: date, end_date: date) -> list[PriceBar]:
        df = _get_cn_price_history_from_baostock(instrument.symbol, start_date, end_date)
        return _price_dataframe_to_bars(df, instrument, self.name, adjusted="qfq", source_symbol=instrument.full_symbol)

    def get_news(self, instrument: Instrument, limit: int) -> tuple[list[NewsItem], bool]:
        raise ProviderUnavailableError("Baostock does not provide stock news.")


PROVIDERS: list[MarketProvider] = [
    AkshareCNProvider(),
    BaostockCNProvider(),
]


def get_instrument_payload(symbol: str, market: str | None = None) -> dict:
    return resolve_instrument(symbol, market).to_dict()


def resolve_instrument(symbol: str, market: str | None = None) -> Instrument:
    resolved_market = normalize_market(market) if market else infer_market(symbol)
    normalized_symbol = normalize_symbol(symbol, resolved_market)
    for provider in _providers_for_market(resolved_market):
        try:
            return provider.resolve_instrument(normalized_symbol, resolved_market)
        except Exception:
            continue
    return build_instrument(resolved_market, normalized_symbol)


def get_price_history_payload(
    symbol: str,
    start_date: date,
    end_date: date,
    market: str | None = None,
    fail_providers: list[str] | None = None,
) -> dict:
    instrument = resolve_instrument(symbol, market)
    disabled = {item.strip() for item in (fail_providers or []) if str(item).strip()}
    attempted_providers: list[dict[str, str]] = []
    errors: list[str] = []
    for index, provider in enumerate(_providers_for_market(instrument.market)):
        attempted_providers.append({"provider": provider.name, "provider_key": provider.key})
        try:
            _raise_if_provider_disabled(provider, disabled)
            records = provider.get_price_history(instrument, start_date, end_date)
            if records:
                return {
                    "instrument": instrument.to_dict(),
                    "records": [record.to_dict() for record in records],
                    "meta": {
                        "provider": provider.name,
                        "provider_key": provider.key,
                        "fallback_used": index > 0,
                        "attempted_providers": attempted_providers,
                        "requested_market": instrument.market,
                        "requested_symbol": instrument.symbol,
                        "currency": instrument.currency,
                        "adjusted": records[0].adjusted if records else "none",
                    },
                }
            errors.append(f"{provider.key}: empty result")
        except Exception as exc:
            errors.append(f"{provider.key}: {exc}")

    detail = "; ".join(errors) if errors else "No provider available."
    raise RuntimeError(f"Unable to load price history for {instrument.full_symbol}. {detail}")


def get_news_payload(
    symbol: str,
    stock_name: str | None = None,
    limit: int = 10,
    market: str | None = None,
    fail_providers: list[str] | None = None,
) -> dict:
    instrument = resolve_instrument(symbol, market)
    if stock_name and instrument.display_name == instrument.symbol:
        instrument = build_instrument(instrument.market, instrument.symbol, stock_name)

    disabled = {item.strip() for item in (fail_providers or []) if str(item).strip()}
    attempted_providers: list[dict[str, str]] = []
    errors: list[str] = []
    for index, provider in enumerate(_providers_for_market(instrument.market)):
        attempted_providers.append({"provider": provider.name, "provider_key": provider.key})
        try:
            _raise_if_provider_disabled(provider, disabled)
            records, is_fallback = provider.get_news(instrument, limit)
            if records:
                return {
                    "instrument": instrument.to_dict(),
                    "records": [record.to_dict() for record in records],
                    "meta": {
                        "provider": provider.name,
                        "provider_key": provider.key,
                        "fallback_used": is_fallback or index > 0,
                        "attempted_providers": attempted_providers,
                    },
                }
            errors.append(f"{provider.key}: empty result")
        except Exception as exc:
            errors.append(f"{provider.key}: {exc}")

    detail = "; ".join(errors) if errors else "No provider available."
    return {
        "instrument": instrument.to_dict(),
        "records": [],
        "meta": {
            "provider": "none",
            "provider_key": "none",
            "fallback_used": False,
            "attempted_providers": attempted_providers,
            "requested_market": instrument.market,
            "requested_symbol": instrument.symbol,
            "warning": f"Unable to load news for {instrument.full_symbol}. {detail}",
        },
    }


def get_stock_name(symbol: str, market: str | None = None) -> str:
    return resolve_instrument(symbol, market).display_name


def get_stock_data(symbol: str, start_date: date, end_date: date, market: str | None = None) -> pd.DataFrame:
    payload = get_price_history_payload(symbol, start_date, end_date, market)
    return price_bars_to_dataframe(payload["records"])


def get_stock_news(symbol: str, stock_name: str | None = None, limit: int = 10, market: str | None = None) -> tuple[pd.DataFrame, bool]:
    payload = get_news_payload(symbol, stock_name, limit, market)
    return news_items_to_dataframe(payload["records"]), bool(payload["meta"]["fallback_used"])


def price_bars_to_dataframe(records: list[dict] | list[PriceBar]) -> pd.DataFrame:
    rows = []
    for item in records:
        record = item.to_dict() if isinstance(item, PriceBar) else item
        rows.append(
            {
                "trade_date": pd.to_datetime(record["trade_date"]),
                "open": record.get("open"),
                "close": record.get("close"),
                "high": record.get("high"),
                "low": record.get("low"),
                "volume": record.get("volume"),
                "turnover": record.get("turnover"),
                "amplitude": record.get("amplitude"),
                "pct_change": record.get("pct_change"),
                "price_change": record.get("price_change"),
                "turnover_rate": record.get("turnover_rate"),
                "symbol": record.get("symbol"),
                "market": record.get("market"),
                "currency": record.get("currency"),
                "source": record.get("source"),
            }
        )
    return pd.DataFrame(rows)


def news_items_to_dataframe(records: list[dict] | list[NewsItem]) -> pd.DataFrame:
    rows = []
    for item in records:
        record = item.to_dict() if isinstance(item, NewsItem) else item
        rows.append(
            {
                "published_at": pd.to_datetime(record["published_at"]),
                "title": record.get("title"),
                "summary": record.get("summary"),
                "url": record.get("url"),
                "publisher": record.get("publisher") or record.get("source"),
                "source": record.get("source"),
                "symbol": record.get("symbol"),
                "market": record.get("market"),
            }
        )
    return pd.DataFrame(rows)


def _providers_for_market(market: Market) -> list[MarketProvider]:
    return [provider for provider in PROVIDERS if market in provider.supported_markets]


def _raise_if_provider_disabled(provider: MarketProvider, disabled: set[str]) -> None:
    if provider.name in disabled or provider.key in disabled:
        raise ProviderUnavailableError(f"Provider {provider.key} was disabled for this request.")


def _fetch_cn_stock_name(symbol: str) -> str:
    try:
        info = ak.stock_individual_info_em(symbol=symbol)
        name_row = info[info["item"] == "股票简称"]
        if not name_row.empty:
            return str(name_row["value"].values[0])
    except Exception:
        pass
    return LOCAL_CN_STOCK_NAMES.get(symbol, symbol)


def _clean_text(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if "�" in text or "Ã" in text or "ç" in text or "ä" in text or "æ" in text:
        try:
            repaired = text.encode("latin1").decode("utf-8")
            if repaired:
                return repaired.strip()
        except Exception:
            pass
    return text


def _get_cn_news(symbol: str, limit: int) -> tuple[pd.DataFrame, bool]:
    try:
        news_df = ak.stock_news_em(symbol=symbol)
        if news_df is None or news_df.empty:
            return _get_cn_sector_news_fallback(limit)
        if "发布时间" in news_df.columns:
            news_df["发布时间"] = pd.to_datetime(news_df["发布时间"])
            news_df = news_df.sort_values(by="发布时间", ascending=False)
        return news_df.head(limit), False
    except Exception:
        return _get_cn_sector_news_fallback(limit)


def _get_cn_sector_news_fallback(limit: int) -> tuple[pd.DataFrame, bool]:
    try:
        df = ak.stock_news_em(symbol="399976")
        if df is not None and not df.empty:
            if "发布时间" in df.columns:
                df["发布时间"] = pd.to_datetime(df["发布时间"])
                df = df.sort_values(by="发布时间", ascending=False)
            return df.head(limit), True
    except Exception:
        pass
    return pd.DataFrame(), False


def _news_dataframe_to_items(df: pd.DataFrame, instrument: Instrument, source: str, is_fallback: bool) -> list[NewsItem]:
    if df is None or df.empty:
        return []

    title_column = next((column for column in ("新闻标题", "标题", "title") if column in df.columns), df.columns[-1])
    time_column = next((column for column in ("发布时间", "date", "published_at") if column in df.columns), None)
    url_column = next((column for column in ("链接", "url", "URL", "source_url", "网址") if column in df.columns), None)

    items: list[NewsItem] = []
    for _, row in df.iterrows():
        title = _clean_text(row.get(title_column))
        if not title:
            continue
        published_at = datetime.now().isoformat(timespec="seconds")
        if time_column and pd.notna(row.get(time_column)):
            published_at = pd.to_datetime(row.get(time_column)).isoformat(timespec="seconds")
        items.append(
            NewsItem(
                id=hashlib.sha256(f"{instrument.id}:{published_at}:{title}".encode("utf-8")).hexdigest()[:16],
                instrument_id=instrument.id,
                market=instrument.market,
                symbol=instrument.symbol,
                title=title,
                summary=_clean_text(row.get("内容摘要")) if pd.notna(row.get("内容摘要")) else None,
                content=None,
                source=source,
                publisher=_clean_text(row.get("来源")) if pd.notna(row.get("来源")) else None,
                url=str(row.get(url_column)) if url_column and pd.notna(row.get(url_column)) else None,
                published_at=published_at,
                language="zh-CN",
                matched_by="symbol",
                is_fallback=is_fallback,
            )
        )
    return items


def _price_dataframe_to_bars(
    df: pd.DataFrame,
    instrument: Instrument,
    source: str,
    adjusted: str,
    source_symbol: str | None = None,
) -> list[PriceBar]:
    if df is None or df.empty:
        return []

    records: list[PriceBar] = []
    for _, row in df.sort_values("日期").iterrows():
        records.append(
            PriceBar(
                instrument_id=instrument.id,
                market=instrument.market,
                symbol=instrument.symbol,
                trade_date=pd.to_datetime(row["日期"]).date().isoformat(),
                open=_safe_float(row.get("开盘")),
                high=_safe_float(row.get("最高")),
                low=_safe_float(row.get("最低")),
                close=_safe_float(row.get("收盘")),
                volume=_safe_float(row.get("成交量")),
                turnover=_safe_float(row.get("成交额")),
                amplitude=_safe_float(row.get("振幅")),
                pct_change=_safe_float(row.get("涨跌幅")),
                price_change=_safe_float(row.get("涨跌额")),
                turnover_rate=_safe_float(row.get("换手率")),
                adjusted=adjusted,
                currency=instrument.currency or "CNY",
                source=source,
                source_symbol=source_symbol or instrument.symbol,
            )
        )
    return records


def _get_cn_price_history_cached(symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
    init_db()
    db_min, db_max = _get_db_range(symbol)

    try:
        if db_min is None or db_max is None:
            fetched = _fetch_cn_history_from_akshare(symbol, start_date, end_date)
            _save_to_db(fetched, symbol)
            return _load_from_db(symbol, start_date, end_date)

        if start_date < db_min:
            fetched = _fetch_cn_history_from_akshare(symbol, start_date, db_min - timedelta(days=1))
            _save_to_db(fetched, symbol)

        if end_date > db_max:
            fetched = _fetch_cn_history_from_akshare(symbol, db_max + timedelta(days=1), end_date)
            _save_to_db(fetched, symbol)

        return _load_from_db(symbol, start_date, end_date)
    except Exception:
        cached = _load_from_db(symbol, start_date, end_date)
        if not cached.empty:
            return cached
        raise


def _get_db_range(symbol: str) -> tuple[date | None, date | None]:
    with SessionLocal() as session:
        stmt = select(func.min(StockHistory.trade_date), func.max(StockHistory.trade_date)).where(
            StockHistory.stock_code == symbol
        )
        result = session.execute(stmt).one()
        return result[0], result[1]


def _fetch_cn_history_from_akshare(symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
    if start_date > end_date:
        return pd.DataFrame()

    last_error = None
    for _ in range(3):
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq",
            )
            if df is None or df.empty:
                return pd.DataFrame()
            payload = df.copy()
            payload["日期"] = pd.to_datetime(payload["日期"])
            return payload
        except requests.exceptions.RequestException as exc:
            last_error = exc
        except Exception as exc:
            last_error = exc

    raise RuntimeError(
        f"AkShare failed to fetch CN price history, symbol={symbol}, start={start_date}, end={end_date}, error={last_error}"
    )


def _get_cn_price_history_from_baostock(symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
    if bs is None:
        raise ProviderUnavailableError("baostock is not installed.")

    code = f"sh.{symbol}" if symbol.startswith(("6", "9")) else f"sz.{symbol}"
    login_result = bs.login()
    if login_result.error_code != "0":
        raise ProviderUnavailableError(f"Baostock login failed: {login_result.error_msg}")

    try:
        rs = bs.query_history_k_data_plus(
            code,
            "date,open,high,low,close,volume,amount,pctChg",
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            frequency="d",
            adjustflag="2",
        )
        if rs.error_code != "0":
            raise ProviderUnavailableError(f"Baostock query failed: {rs.error_msg}")

        rows: list[list[str]] = []
        while rs.next():
            rows.append(rs.get_row_data())
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=rs.fields)
        payload = pd.DataFrame(
            {
                "日期": pd.to_datetime(df["date"]),
                "开盘": pd.to_numeric(df["open"], errors="coerce"),
                "收盘": pd.to_numeric(df["close"], errors="coerce"),
                "最高": pd.to_numeric(df["high"], errors="coerce"),
                "最低": pd.to_numeric(df["low"], errors="coerce"),
                "成交量": pd.to_numeric(df["volume"], errors="coerce"),
                "成交额": pd.to_numeric(df["amount"], errors="coerce"),
                "振幅": ((pd.to_numeric(df["high"], errors="coerce") - pd.to_numeric(df["low"], errors="coerce")) / pd.to_numeric(df["close"], errors="coerce").shift(1)) * 100,
                "涨跌幅": pd.to_numeric(df.get("pctChg"), errors="coerce"),
                "涨跌额": pd.to_numeric(df["close"], errors="coerce").diff(),
                "换手率": None,
            }
        )
        return payload
    finally:
        try:
            bs.logout()
        except Exception:
            pass


def _save_to_db(df: pd.DataFrame, symbol: str) -> None:
    if df.empty:
        return

    with SessionLocal() as session:
        for _, row in df.iterrows():
            session.merge(
                StockHistory(
                    stock_code=symbol,
                    trade_date=row["日期"].date(),
                    open_price=_safe_float(row.get("开盘")),
                    close_price=_safe_float(row.get("收盘")),
                    high_price=_safe_float(row.get("最高")),
                    low_price=_safe_float(row.get("最低")),
                    volume=_safe_float(row.get("成交量")),
                    turnover=_safe_float(row.get("成交额")),
                    amplitude=_safe_float(row.get("振幅")),
                    pct_change=_safe_float(row.get("涨跌幅")),
                    price_change=_safe_float(row.get("涨跌额")),
                    turnover_rate=_safe_float(row.get("换手率")),
                )
            )
        session.commit()


def _load_from_db(symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
    with SessionLocal() as session:
        stmt = (
            select(StockHistory)
            .where(
                StockHistory.stock_code == symbol,
                StockHistory.trade_date >= start_date,
                StockHistory.trade_date <= end_date,
            )
            .order_by(StockHistory.trade_date.asc())
        )
        rows = session.execute(stmt).scalars().all()

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(
        [
            {
                "日期": pd.to_datetime(row.trade_date),
                "开盘": row.open_price,
                "收盘": row.close_price,
                "最高": row.high_price,
                "最低": row.low_price,
                "成交量": row.volume,
                "成交额": row.turnover,
                "振幅": row.amplitude,
                "涨跌幅": row.pct_change,
                "涨跌额": row.price_change,
                "换手率": row.turnover_rate,
                "股票代码": row.stock_code,
            }
            for row in rows
        ]
    )


def _coerce_timestamp(value: object) -> str:
    if value is None:
        return datetime.now().isoformat(timespec="seconds")
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value).isoformat(timespec="seconds")
    text = str(value).strip()
    if not text:
        return datetime.now().isoformat(timespec="seconds")
    try:
        return pd.to_datetime(text).to_pydatetime().isoformat(timespec="seconds")
    except Exception:
        return datetime.now().isoformat(timespec="seconds")


def _safe_float(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _ensure_runtime_schema() -> None:
    inspector = inspect(engine)

    if inspector.has_table("investment_transactions"):
        columns = {column["name"] for column in inspector.get_columns("investment_transactions")}
        statements: list[str] = []
        if "stock_name" not in columns:
            statements.append("ALTER TABLE investment_transactions ADD COLUMN stock_name VARCHAR(100)")

        if statements:
            with engine.begin() as connection:
                for statement in statements:
                    connection.execute(text(statement))







