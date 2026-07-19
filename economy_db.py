"""SQLite-хранилище экономики: балансы и журнал операций.

Списания атомарны: UPDATE с условием balance >= amount — баланс никогда
не уходит в минус, даже при гонке двух одновременных покупок.
"""

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone


def get_db_path() -> str:
    return os.getenv("ECONOMY_DB_PATH", "economy.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with closing(connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS balances (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                delta INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_bonus (
                user_id INTEGER PRIMARY KEY,
                streak INTEGER NOT NULL DEFAULT 0,
                last_claim_date TEXT NOT NULL DEFAULT ''
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS owned_cosmetics (
                user_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                value TEXT NOT NULL,
                name TEXT NOT NULL,
                PRIMARY KEY (user_id, item_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS equipped_cosmetics (
                user_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                item_id TEXT NOT NULL,
                PRIMARY KEY (user_id, kind)
            )
        """)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(conn: sqlite3.Connection, user_id: int, delta: int, reason: str) -> None:
    conn.execute(
        "INSERT INTO history (user_id, delta, reason, created_at) VALUES (?, ?, ?, ?)",
        (user_id, delta, reason, _now()),
    )


def get_balance(user_id: int) -> int:
    with closing(connect()) as conn:
        row = conn.execute("SELECT balance FROM balances WHERE user_id = ?", (user_id,)).fetchone()
    return row["balance"] if row else 0


def add(user_id: int, amount: int, reason: str) -> int:
    """Начислить монеты (amount > 0). Возвращает новый баланс."""
    if amount <= 0:
        return get_balance(user_id)
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT INTO balances (user_id, balance) VALUES (?, ?)
               ON CONFLICT(user_id) DO UPDATE SET balance = balance + excluded.balance""",
            (user_id, amount),
        )
        _log(conn, user_id, amount, reason)
        return conn.execute("SELECT balance FROM balances WHERE user_id = ?", (user_id,)).fetchone()["balance"]


def try_spend(user_id: int, amount: int, reason: str) -> bool:
    """Атомарно списать монеты; False — не хватает средств."""
    if amount <= 0:
        return False
    with closing(connect()) as conn, conn:
        cursor = conn.execute(
            "UPDATE balances SET balance = balance - ? WHERE user_id = ? AND balance >= ?",
            (amount, user_id, amount),
        )
        if cursor.rowcount == 0:
            return False
        _log(conn, user_id, -amount, reason)
        return True


def transfer(from_id: int, to_id: int, amount: int, fee: int) -> bool:
    """Атомарный перевод: у отправителя списывается amount + fee, получателю
    приходит amount. False — не хватает средств."""
    if amount <= 0 or fee < 0:
        return False
    total = amount + fee
    with closing(connect()) as conn, conn:
        cursor = conn.execute(
            "UPDATE balances SET balance = balance - ? WHERE user_id = ? AND balance >= ?",
            (total, from_id, total),
        )
        if cursor.rowcount == 0:
            return False
        conn.execute(
            """INSERT INTO balances (user_id, balance) VALUES (?, ?)
               ON CONFLICT(user_id) DO UPDATE SET balance = balance + excluded.balance""",
            (to_id, amount),
        )
        _log(conn, from_id, -total, f"transfer_to_{to_id}")
        _log(conn, to_id, amount, f"transfer_from_{from_id}")
        return True


def set_balance(user_id: int, value: int, reason: str) -> int:
    """Установить точный баланс (админ из дашборда)."""
    with closing(connect()) as conn, conn:
        old = conn.execute("SELECT balance FROM balances WHERE user_id = ?", (user_id,)).fetchone()
        old_value = old["balance"] if old else 0
        conn.execute(
            """INSERT INTO balances (user_id, balance) VALUES (?, ?)
               ON CONFLICT(user_id) DO UPDATE SET balance = excluded.balance""",
            (user_id, value),
        )
        _log(conn, user_id, value - old_value, reason)
    return value


def top(limit: int = 10) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT user_id, balance FROM balances WHERE balance > 0 ORDER BY balance DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def rank_of(user_id: int) -> int | None:
    """Место в топе (1-based); None, если баланса нет."""
    balance = get_balance(user_id)
    if balance <= 0:
        return None
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS above FROM balances WHERE balance > ?", (balance,)
        ).fetchone()
    return row["above"] + 1


def recent_history(user_id: int, limit: int = 10) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT delta, reason, created_at FROM history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_daily_bonus(user_id: int) -> dict:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT streak, last_claim_date FROM daily_bonus WHERE user_id = ?", (user_id,)
        ).fetchone()
    return dict(row) if row else {"streak": 0, "last_claim_date": ""}


def set_daily_bonus(user_id: int, streak: int, claim_date: str) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT INTO daily_bonus (user_id, streak, last_claim_date) VALUES (?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET streak = excluded.streak, last_claim_date = excluded.last_claim_date""",
            (user_id, streak, claim_date),
        )


# ────────────────────────── Косметика (рамка карточки, титул) ──────────────────────────

def owns_cosmetic(user_id: int, item_id: str) -> bool:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT 1 FROM owned_cosmetics WHERE user_id = ? AND item_id = ?", (user_id, item_id)
        ).fetchone()
    return row is not None


def grant_cosmetic(user_id: int, item_id: str, kind: str, value: str, name: str) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            "INSERT OR IGNORE INTO owned_cosmetics (user_id, item_id, kind, value, name) VALUES (?, ?, ?, ?, ?)",
            (user_id, item_id, kind, value, name),
        )


def list_owned_cosmetics(user_id: int, kind: str) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT item_id, value, name FROM owned_cosmetics WHERE user_id = ? AND kind = ? ORDER BY rowid",
            (user_id, kind),
        ).fetchall()
    return [dict(r) for r in rows]


def set_equipped(user_id: int, kind: str, item_id: str) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT INTO equipped_cosmetics (user_id, kind, item_id) VALUES (?, ?, ?)
               ON CONFLICT(user_id, kind) DO UPDATE SET item_id = excluded.item_id""",
            (user_id, kind, item_id),
        )


def clear_equipped(user_id: int, kind: str) -> None:
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM equipped_cosmetics WHERE user_id = ? AND kind = ?", (user_id, kind))


def get_equipped(user_id: int, kind: str) -> dict | None:
    """Экипированный предмет с его значением (цвет/текст) — джойн с owned_cosmetics
    на случай, если товар позже убрали из магазина: у владельца он остаётся."""
    with closing(connect()) as conn:
        row = conn.execute(
            """SELECT o.item_id, o.value, o.name FROM equipped_cosmetics e
               JOIN owned_cosmetics o ON o.user_id = e.user_id AND o.item_id = e.item_id
               WHERE e.user_id = ? AND e.kind = ?""",
            (user_id, kind),
        ).fetchone()
    return dict(row) if row else None
