from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select

from backend.db import SessionLocal
from backend.models import User, UserHistory
from backend.services.market_service import hash_password, init_db


def register_user(username: str, password: str):
    init_db()
    with SessionLocal() as session:
        existing = session.get(User, username)
        if existing is not None:
            return False, "该用户名已被占用。"

        session.add(User(username=username, password_hash=hash_password(password)))
        session.commit()
        return True, "注册成功，请登录。"


def login_user(username: str, password: str) -> bool:
    init_db()
    with SessionLocal() as session:
        user = session.get(User, username)
        if user is None:
            return False
        return user.password_hash == hash_password(password)


def log_history(username: str, stock_name: str, stock_code: str) -> None:
    if not username or not stock_name:
        return

    init_db()
    with SessionLocal() as session:
        last = session.execute(
            select(UserHistory)
            .where(UserHistory.username == username)
            .order_by(UserHistory.id.desc())
            .limit(1)
        ).scalar_one_or_none()

        current_time = datetime.now()
        current_time_str = current_time.strftime("%Y-%m-%d %H:%M")
        if last and last.stock_code == stock_code:
            last.visit_time_str = current_time_str
            last.timestamp = current_time
        else:
            session.add(
                UserHistory(
                    username=username,
                    stock_name=stock_name,
                    stock_code=stock_code,
                    visit_time_str=current_time_str,
                    timestamp=current_time,
                )
            )
        session.commit()


def get_user_history(username: str) -> list[dict]:
    init_db()
    with SessionLocal() as session:
        rows = session.execute(
            select(UserHistory)
            .where(UserHistory.username == username)
            .order_by(UserHistory.id.desc())
            .limit(20)
        ).scalars().all()

    return [
        {
            "id": row.id,
            "stock_name": row.stock_name,
            "stock_code": row.stock_code,
            "visit_time_str": row.visit_time_str,
        }
        for row in rows
    ]


def delete_history_item(item_id: int) -> None:
    init_db()
    with SessionLocal() as session:
        session.execute(delete(UserHistory).where(UserHistory.id == item_id))
        session.commit()


def delete_all_user_history(username: str) -> None:
    init_db()
    with SessionLocal() as session:
        session.execute(delete(UserHistory).where(UserHistory.username == username))
        session.commit()
