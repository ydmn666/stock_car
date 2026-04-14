from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy import delete, select

from backend.db import SessionLocal
from backend.models import User, UserHistory
from backend.schemas import normalize_username
from backend.services.market_service import hash_password, init_db
from backend.utils.network_env import disable_proxy_env

disable_proxy_env()

TOKEN_TTL = timedelta(days=7)
AUTH_SECRET = os.getenv("AUTH_SECRET", "stock-car-dev-secret-change-me")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def _sign_token(payload_b64: str) -> str:
    return hmac.new(AUTH_SECRET.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()


def hash_password_secure(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, stored_hash: str) -> bool:
    if stored_hash.startswith("$2"):
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    return hmac.compare_digest(hash_password(password), stored_hash)


def create_access_token(username: str) -> str:
    normalized = normalize_username(username)
    payload = {
        "sub": normalized,
        "exp": int((_utc_now() + TOKEN_TTL).timestamp()),
    }
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    return f"{payload_b64}.{_sign_token(payload_b64)}"


def verify_access_token(token: str) -> str:
    try:
        payload_b64, signature = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("登录状态无效，请重新登录。") from exc

    expected = _sign_token(payload_b64)
    if not hmac.compare_digest(signature, expected):
        raise ValueError("登录状态无效，请重新登录。")

    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception as exc:
        raise ValueError("登录状态无效，请重新登录。") from exc

    username = normalize_username(str(payload.get("sub", "")))
    exp = int(payload.get("exp", 0))
    if not username or exp <= int(_utc_now().timestamp()):
        raise ValueError("登录状态已过期，请重新登录。")
    return username


def register_user(username: str, password: str):
    normalized = normalize_username(username)
    init_db()
    with SessionLocal() as session:
        existing = session.get(User, normalized)
        if existing is not None:
            return False, "用户名已被占用。"

        session.add(User(username=normalized, password_hash=hash_password_secure(password)))
        session.commit()
        return True, "注册成功，请登录。"


def login_user(username: str, password: str) -> tuple[bool, str | None]:
    normalized = normalize_username(username)
    init_db()
    with SessionLocal() as session:
        user = session.get(User, normalized)
        if user is None or not verify_password(password, user.password_hash):
            return False, None

        if not user.password_hash.startswith("$2"):
            user.password_hash = hash_password_secure(password)
            session.commit()

        return True, create_access_token(user.username)


def change_password(username: str, old_password: str, new_password: str) -> None:
    normalized = normalize_username(username)
    init_db()
    with SessionLocal() as session:
        user = session.get(User, normalized)
        if user is None:
            raise ValueError("用户不存在，请重新登录。")
        if not verify_password(old_password, user.password_hash):
            raise ValueError("当前密码输入错误。")
        if old_password == new_password:
            raise ValueError("新密码不能与当前密码相同。")

        user.password_hash = hash_password_secure(new_password)
        session.commit()


def log_history(username: str, stock_name: str, stock_code: str) -> None:
    normalized = normalize_username(username)
    if not normalized or not stock_name:
        return

    init_db()
    with SessionLocal() as session:
        last = session.execute(
            select(UserHistory)
            .where(UserHistory.username == normalized)
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
                    username=normalized,
                    stock_name=stock_name,
                    stock_code=stock_code,
                    visit_time_str=current_time_str,
                    timestamp=current_time,
                )
            )
        session.commit()


def get_user_history(username: str) -> list[dict]:
    normalized = normalize_username(username)
    init_db()
    with SessionLocal() as session:
        rows = session.execute(
            select(UserHistory)
            .where(UserHistory.username == normalized)
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


def delete_history_item(username: str, item_id: int) -> None:
    normalized = normalize_username(username)
    init_db()
    with SessionLocal() as session:
        session.execute(
            delete(UserHistory).where(
                UserHistory.id == item_id,
                UserHistory.username == normalized,
            )
        )
        session.commit()


def delete_all_user_history(username: str) -> None:
    normalized = normalize_username(username)
    init_db()
    with SessionLocal() as session:
        session.execute(delete(UserHistory).where(UserHistory.username == normalized))
        session.commit()
