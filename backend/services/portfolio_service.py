from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import delete, select

from backend.db import SessionLocal
from backend.models import InvestmentTransaction, StockInstrument, User, UserPortfolio
from backend.services.market_service import get_price_history_payload, get_stock_name, init_db, resolve_instrument


@dataclass
class PositionState:
    symbol: str
    stock_name: str
    quantity: float = 0
    cost_basis: float = 0
    total_buys: float = 0
    total_sells: float = 0
    total_fees: float = 0
    realized_pnl: float = 0

    @property
    def avg_cost(self) -> float:
        if self.quantity <= 0:
            return 0
        return self.cost_basis / self.quantity


def _require_user(username: str) -> None:
    with SessionLocal() as session:
        user = session.get(User, username)
        if user is None:
            raise ValueError("用户不存在，请先登录。")


def _ensure_default_portfolio(username: str) -> int:
    init_db()
    with SessionLocal() as session:
        portfolio = session.execute(
            select(UserPortfolio).where(UserPortfolio.username == username).order_by(UserPortfolio.id.asc())
        ).scalar_one_or_none()
        if portfolio is not None:
            return portfolio.id

        portfolio = UserPortfolio(username=username, name="默认组合", description="个人投资主组合")
        session.add(portfolio)
        session.commit()
        session.refresh(portfolio)
        return portfolio.id


def _upsert_instrument(symbol: str) -> tuple[str, str]:
    instrument = resolve_instrument(symbol, "CN")
    display_name = instrument.display_name
    if display_name == instrument.symbol:
        try:
            display_name = get_stock_name(instrument.symbol, "CN")
        except Exception:
            display_name = instrument.display_name

    with SessionLocal() as session:
        existing = session.get(StockInstrument, instrument.symbol)
        if existing is None:
            session.add(
                StockInstrument(
                    symbol=instrument.symbol,
                    market=instrument.market,
                    asset_type=instrument.asset_type,
                    display_name=display_name,
                    full_symbol=instrument.full_symbol,
                    exchange=instrument.exchange,
                    currency=instrument.currency or "CNY",
                    is_active=True,
                )
            )
            session.commit()
        elif existing.display_name != display_name or existing.full_symbol != instrument.full_symbol:
            existing.display_name = display_name
            existing.full_symbol = instrument.full_symbol
            existing.exchange = instrument.exchange
            existing.currency = instrument.currency or existing.currency
            session.commit()
    return instrument.symbol, display_name


def _resolve_display_name(symbol: str, stock_name: str | None = None) -> str:
    if stock_name and stock_name.strip() and stock_name.strip() != symbol:
        return stock_name.strip()

    try:
        with SessionLocal() as session:
            instrument = session.get(StockInstrument, symbol)
            if instrument is not None and instrument.display_name and instrument.display_name != symbol:
                return instrument.display_name
    except Exception:
        pass

    try:
        name = get_stock_name(symbol, "CN")
        if name and name != symbol:
            return name
    except Exception:
        pass

    return stock_name or symbol


def _load_transactions(username: str) -> list[InvestmentTransaction]:
    with SessionLocal() as session:
        return session.execute(
            select(InvestmentTransaction)
            .where(InvestmentTransaction.username == username)
            .order_by(InvestmentTransaction.trade_date.desc(), InvestmentTransaction.id.desc())
        ).scalars().all()


def _load_transactions_ascending(username: str) -> list[InvestmentTransaction]:
    with SessionLocal() as session:
        return session.execute(
            select(InvestmentTransaction)
            .where(InvestmentTransaction.username == username)
            .order_by(InvestmentTransaction.trade_date.asc(), InvestmentTransaction.id.asc())
        ).scalars().all()


def _build_position_states_from_transactions(rows: list[InvestmentTransaction]) -> dict[str, PositionState]:
    states: dict[str, PositionState] = {}
    for row in rows:
        state = states.setdefault(row.symbol, PositionState(symbol=row.symbol, stock_name=row.stock_name))
        gross_amount = float(row.price) * float(row.quantity)
        fee = float(row.fee or 0)
        state.total_fees += fee

        if row.trade_type == "buy":
            state.quantity += float(row.quantity)
            state.cost_basis += gross_amount + fee
            state.total_buys += gross_amount
        elif row.trade_type == "sell":
            if state.quantity <= 0 or float(row.quantity) > state.quantity + 1e-8:
                raise ValueError(f"{row.stock_name} 的卖出数量超过当前持仓。")
            avg_cost = state.avg_cost
            state.realized_pnl += gross_amount - avg_cost * float(row.quantity) - fee
            state.quantity -= float(row.quantity)
            state.cost_basis -= avg_cost * float(row.quantity)
            if abs(state.quantity) < 1e-8:
                state.quantity = 0
                state.cost_basis = 0
            state.total_sells += gross_amount
        else:
            raise ValueError(f"Unsupported trade_type: {row.trade_type}")
    return states


def _build_position_states(username: str) -> dict[str, PositionState]:
    return _build_position_states_from_transactions(_load_transactions_ascending(username))


def _serialize_transaction(transaction: InvestmentTransaction) -> dict:
    return {
        "id": transaction.id,
        "username": transaction.username,
        "symbol": transaction.symbol,
        "stock_name": _resolve_display_name(transaction.symbol, transaction.stock_name),
        "trade_type": transaction.trade_type,
        "trade_date": transaction.trade_date.isoformat(),
        "price": float(transaction.price),
        "quantity": float(transaction.quantity),
        "fee": float(transaction.fee),
        "amount": float(transaction.price) * float(transaction.quantity),
        "note": transaction.note,
    }


def _validate_transaction_input(username: str, price: float, quantity: float, fee: float) -> None:
    if not username.strip():
        raise ValueError("用户名不能为空。")
    if quantity <= 0:
        raise ValueError("股数必须大于 0。")
    if price <= 0:
        raise ValueError("成交价格必须大于 0。")
    if fee < 0:
        raise ValueError("手续费不能小于 0。")


def _build_transaction_preview(
    *,
    template: InvestmentTransaction | None,
    portfolio_id: int,
    username: str,
    symbol: str,
    stock_name: str,
    trade_type: str,
    trade_date: date,
    price: float,
    quantity: float,
    fee: float,
    note: str | None,
) -> InvestmentTransaction:
    return InvestmentTransaction(
        id=template.id if template is not None else None,
        portfolio_id=portfolio_id,
        username=username,
        symbol=symbol,
        stock_name=stock_name,
        trade_type=trade_type,
        trade_date=trade_date,
        quantity=quantity,
        price=price,
        fee=fee,
        note=note.strip() if note else None,
    )


def _validate_transaction_timeline(username: str, candidate: InvestmentTransaction, replace_transaction_id: int | None = None) -> None:
    rows = _load_transactions_ascending(username)
    if replace_transaction_id is not None:
        rows = [row for row in rows if row.id != replace_transaction_id]
    rows.append(candidate)
    rows.sort(key=lambda item: (item.trade_date, item.id or 0))
    _build_position_states_from_transactions(rows)


def _fetch_price_map(symbol: str, start_date: date, end_date: date) -> dict[str, float]:
    try:
        payload = get_price_history_payload(symbol, start_date, end_date, "CN")
    except Exception:
        return {}

    prices: dict[str, float] = {}
    for record in payload.get("records", []):
        close = record.get("close")
        trade_date = record.get("trade_date")
        if close is not None and trade_date:
            prices[str(trade_date)] = float(close)
    return prices


def _latest_close_for_symbol(symbol: str) -> float | None:
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    price_map = _fetch_price_map(symbol, start_date, end_date)
    if not price_map:
        return None
    latest_date = max(price_map)
    return price_map[latest_date]


def create_transaction(
    username: str,
    symbol: str,
    trade_type: str,
    trade_date: date,
    price: float,
    quantity: float,
    fee: float = 0,
    note: str | None = None,
) -> dict:
    _validate_transaction_input(username, price, quantity, fee)
    _require_user(username)
    portfolio_id = _ensure_default_portfolio(username)
    normalized_symbol, stock_name = _upsert_instrument(symbol)
    candidate = _build_transaction_preview(
        template=None,
        portfolio_id=portfolio_id,
        username=username,
        symbol=normalized_symbol,
        stock_name=stock_name,
        trade_type=trade_type,
        trade_date=trade_date,
        price=price,
        quantity=quantity,
        fee=fee,
        note=note,
    )
    _validate_transaction_timeline(username, candidate)

    init_db()
    with SessionLocal() as session:
        transaction = candidate
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        return _serialize_transaction(transaction)


def update_transaction(
    username: str,
    transaction_id: int,
    symbol: str,
    trade_type: str,
    trade_date: date,
    price: float,
    quantity: float,
    fee: float = 0,
    note: str | None = None,
) -> dict:
    _validate_transaction_input(username, price, quantity, fee)
    _require_user(username)
    portfolio_id = _ensure_default_portfolio(username)
    normalized_symbol, stock_name = _upsert_instrument(symbol)

    with SessionLocal() as session:
        transaction = session.execute(
            select(InvestmentTransaction).where(
                InvestmentTransaction.id == transaction_id,
                InvestmentTransaction.username == username,
            )
        ).scalar_one_or_none()
        if transaction is None:
            raise ValueError("未找到需要编辑的交易记录。")

        candidate = _build_transaction_preview(
            template=transaction,
            portfolio_id=portfolio_id,
            username=username,
            symbol=normalized_symbol,
            stock_name=stock_name,
            trade_type=trade_type,
            trade_date=trade_date,
            price=price,
            quantity=quantity,
            fee=fee,
            note=note,
        )
        _validate_transaction_timeline(username, candidate, replace_transaction_id=transaction_id)

        transaction.portfolio_id = portfolio_id
        transaction.symbol = normalized_symbol
        transaction.stock_name = stock_name
        transaction.trade_type = trade_type
        transaction.trade_date = trade_date
        transaction.price = price
        transaction.quantity = quantity
        transaction.fee = fee
        transaction.note = note.strip() if note else None
        session.commit()
        session.refresh(transaction)
        return _serialize_transaction(transaction)


def list_transactions(username: str) -> list[dict]:
    _require_user(username)
    return [_serialize_transaction(row) for row in _load_transactions(username)]


def delete_transaction(username: str, transaction_id: int) -> None:
    _require_user(username)
    with SessionLocal() as session:
        session.execute(
            delete(InvestmentTransaction).where(
                InvestmentTransaction.id == transaction_id,
                InvestmentTransaction.username == username,
            )
        )
        session.commit()


def get_positions(username: str) -> list[dict]:
    _require_user(username)
    states = _build_position_states(username)
    rows: list[dict] = []
    for symbol, state in states.items():
        if state.quantity <= 0:
            continue
        latest_price = _latest_close_for_symbol(symbol)
        market_value = state.quantity * latest_price if latest_price is not None else None
        unrealized_pnl = market_value - state.cost_basis if market_value is not None else None
        unrealized_pnl_pct = ((unrealized_pnl / state.cost_basis) * 100) if market_value is not None and state.cost_basis > 0 else None
        display_name = _resolve_display_name(symbol, state.stock_name)
        rows.append(
            {
                "symbol": symbol,
                "stock_name": display_name,
                "quantity": state.quantity,
                "avg_cost": state.avg_cost,
                "cost_basis": state.cost_basis,
                "latest_price": latest_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct,
            }
        )
    rows.sort(key=lambda item: (item["market_value"] is None, -(item["market_value"] or 0), item["symbol"]))
    return rows


def get_portfolio_summary(username: str) -> dict:
    _require_user(username)
    states = _build_position_states(username)
    positions = get_positions(username)

    total_buy_amount = sum(state.total_buys for state in states.values())
    total_sell_amount = sum(state.total_sells for state in states.values())
    total_fees = sum(state.total_fees for state in states.values())
    total_realized_pnl = sum(state.realized_pnl for state in states.values())
    total_cost_basis = sum(state.cost_basis for state in states.values() if state.quantity > 0)
    total_market_value = sum((item["market_value"] or 0) for item in positions if item["market_value"] is not None)
    total_unrealized_pnl = total_market_value - total_cost_basis
    total_unrealized_pnl_pct = (total_unrealized_pnl / total_cost_basis) * 100 if total_cost_basis > 0 else None

    return {
        "total_buy_amount": total_buy_amount,
        "total_sell_amount": total_sell_amount,
        "total_fees": total_fees,
        "net_invested": total_buy_amount + total_fees - total_sell_amount,
        "cash_returned": total_sell_amount - total_fees,
        "realized_pnl": total_realized_pnl,
        "holding_cost": total_cost_basis,
        "market_value": total_market_value,
        "unrealized_pnl": total_unrealized_pnl,
        "unrealized_pnl_pct": total_unrealized_pnl_pct,
        "position_count": len(positions),
        "transaction_count": len(_load_transactions(username)),
    }


def get_portfolio_performance(username: str) -> dict:
    _require_user(username)
    transactions = _load_transactions_ascending(username)
    if not transactions:
        return {
            "curve": [],
            "allocation": [],
            "stats": {
                "latest_market_value": 0,
                "latest_unrealized_pnl": 0,
                "latest_unrealized_pnl_pct": None,
                "max_market_value": 0,
                "min_market_value": 0,
            },
        }

    start_date = min(row.trade_date for row in transactions)
    end_date = date.today()
    symbols = sorted({row.symbol for row in transactions})
    price_maps = {symbol: _fetch_price_map(symbol, start_date - timedelta(days=5), end_date) for symbol in symbols}

    trade_dates = {row.trade_date.isoformat() for row in transactions}
    price_dates = {day for price_map in price_maps.values() for day in price_map.keys()}
    timeline = sorted(price_dates | trade_dates)

    transaction_map: dict[str, list[InvestmentTransaction]] = {}
    for row in transactions:
        transaction_map.setdefault(row.trade_date.isoformat(), []).append(row)

    holdings: dict[str, float] = {symbol: 0 for symbol in symbols}
    cost_basis: dict[str, float] = {symbol: 0 for symbol in symbols}
    last_price: dict[str, float | None] = {symbol: None for symbol in symbols}
    running_buy_amount = 0.0
    running_sell_amount = 0.0
    running_fees = 0.0
    running_realized_pnl = 0.0
    curve: list[dict] = []

    for day in timeline:
        for row in transaction_map.get(day, []):
            gross_amount = float(row.price) * float(row.quantity)
            fee = float(row.fee or 0)
            running_fees += fee
            if row.trade_type == "buy":
                holdings[row.symbol] = holdings.get(row.symbol, 0) + float(row.quantity)
                cost_basis[row.symbol] = cost_basis.get(row.symbol, 0) + gross_amount + fee
                running_buy_amount += gross_amount
            elif row.trade_type == "sell":
                current_quantity = holdings.get(row.symbol, 0)
                if current_quantity > 0:
                    avg_cost = cost_basis.get(row.symbol, 0) / current_quantity if current_quantity else 0
                    running_realized_pnl += gross_amount - avg_cost * float(row.quantity) - fee
                    holdings[row.symbol] = current_quantity - float(row.quantity)
                    cost_basis[row.symbol] = max(0, cost_basis.get(row.symbol, 0) - avg_cost * float(row.quantity))
                    if holdings[row.symbol] <= 1e-8:
                        holdings[row.symbol] = 0
                        cost_basis[row.symbol] = 0
                running_sell_amount += gross_amount

        total_market_value = 0.0
        total_holding_cost = 0.0
        for symbol in symbols:
            if day in price_maps[symbol]:
                last_price[symbol] = price_maps[symbol][day]
            if holdings.get(symbol, 0) <= 0:
                continue
            total_holding_cost += cost_basis[symbol]
            if last_price[symbol] is None:
                continue
            total_market_value += holdings[symbol] * float(last_price[symbol])

        unrealized_pnl = total_market_value - total_holding_cost
        unrealized_pnl_pct = (unrealized_pnl / total_holding_cost) * 100 if total_holding_cost > 0 else None
        curve.append(
            {
                "date": day,
                "net_invested": running_buy_amount + running_fees - running_sell_amount,
                "cash_returned": running_sell_amount - running_fees,
                "holding_cost": total_holding_cost,
                "market_value": total_market_value,
                "realized_pnl": running_realized_pnl,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct,
            }
        )

    positions = get_positions(username)
    total_market_value = sum(item["market_value"] or 0 for item in positions if item["market_value"] is not None)
    allocation = [
        {
            "symbol": item["symbol"],
            "stock_name": _resolve_display_name(item["symbol"], item["stock_name"]),
            "market_value": item["market_value"],
            "weight_pct": ((item["market_value"] or 0) / total_market_value * 100) if total_market_value > 0 and item["market_value"] is not None else None,
            "unrealized_pnl": item["unrealized_pnl"],
        }
        for item in positions
    ]

    market_values = [item["market_value"] for item in curve]
    latest_point = curve[-1] if curve else None
    return {
        "curve": curve,
        "allocation": allocation,
        "stats": {
            "latest_market_value": latest_point["market_value"] if latest_point else 0,
            "latest_cash_returned": latest_point["cash_returned"] if latest_point else 0,
            "latest_realized_pnl": latest_point["realized_pnl"] if latest_point else 0,
            "latest_unrealized_pnl": latest_point["unrealized_pnl"] if latest_point else 0,
            "latest_unrealized_pnl_pct": latest_point["unrealized_pnl_pct"] if latest_point else None,
            "max_market_value": max(market_values) if market_values else 0,
            "min_market_value": min(market_values) if market_values else 0,
        },
    }


def get_user_portfolio_snapshot(username: str) -> dict:
    summary = get_portfolio_summary(username)
    positions = get_positions(username)
    transactions = list_transactions(username)[:5]
    return {
        "summary": summary,
        "positions": positions,
        "recent_transactions": transactions,
    }
