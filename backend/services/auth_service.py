from __future__ import annotations

import sqlite3
from datetime import datetime

from backend.services.market_service import DB_FILE, hash_password, init_db


def register_user(username: str, password: str):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password)),
        )
        conn.commit()
        return True, "注册成功，请登录。"
    except sqlite3.IntegrityError:
        return False, "该用户名已被占用。"
    finally:
        conn.close()


def login_user(username: str, password: str) -> bool:
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT 1 FROM users WHERE username = ? AND password_hash = ?",
            (username, hash_password(password)),
        )
        return cursor.fetchone() is not None
    finally:
        conn.close()


def log_history(username: str, stock_name: str, stock_code: str) -> None:
    if not username or not stock_name:
        return

    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, stock_code FROM user_history WHERE username = ? ORDER BY id DESC LIMIT 1",
            (username,),
        )
        last = cursor.fetchone()
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        if last and last[1] == stock_code:
            cursor.execute(
                """
                UPDATE user_history
                SET visit_time_str = ?, timestamp = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (current_time_str, last[0]),
            )
        else:
            cursor.execute(
                """
                INSERT INTO user_history (username, stock_name, stock_code, visit_time_str)
                VALUES (?, ?, ?, ?)
                """,
                (username, stock_name, stock_code, current_time_str),
            )
        conn.commit()
    finally:
        conn.close()


def get_user_history(username: str) -> list[dict]:
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, stock_name, stock_code, visit_time_str
            FROM user_history
            WHERE username = ?
            ORDER BY id DESC
            LIMIT 20
            """,
            (username,),
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "stock_name": row[1],
                "stock_code": row[2],
                "visit_time_str": row[3],
            }
            for row in rows
        ]
    finally:
        conn.close()


def delete_history_item(item_id: int) -> None:
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM user_history WHERE id = ?", (item_id,))
        conn.commit()
    finally:
        conn.close()


def delete_all_user_history(username: str) -> None:
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM user_history WHERE username = ?", (username,))
        conn.commit()
    finally:
        conn.close()
