"""SQLite-хранилище экономики: балансы и журнал операций.

Per-guild изоляция: все таблицы ключуются по guild_id.
Списания атомарны: UPDATE с условием balance >= amount — баланс никогда
не уходит в минус, даже при гонке двух одновременных покупок.
"""

import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone

# Ошибочный sentinel первой per-guild миграции (легаси уезжало на guild_id=404).
_MISATTRIBUTED_GUILD = 404


def get_main_guild_id() -> int:
    """Мейн-сервер для миграции легаси-строк без guild_id."""
    return int(os.getenv("GUILD_ID") or os.getenv("MAIN_GUILD_ID") or "1324239354154975252")


def __getattr__(name: str):
    # Обратная совместимость: economy_db.MAIN_GUILD читает актуальный env.
    if name == "MAIN_GUILD":
        return get_main_guild_id()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_db_path() -> str:
    return os.getenv("ECONOMY_DB_PATH", "economy.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def _table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def _repair_misattributed_guild(conn: sqlite3.Connection) -> None:
    """Перенести строки с guild_id=404 на реальный MAIN_GUILD_ID.

    Ранняя миграция ошибочно писала легаси на sentinel 404 — на настоящем мейне
    балансы выглядели обнулёнными, хотя данные оставались в БД.
    """
    real_main = get_main_guild_id()
    if real_main == _MISATTRIBUTED_GUILD:
        return

    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}

    if "balances" in tables and "guild_id" in _table_columns(conn, "balances"):
        for row in conn.execute(
            "SELECT user_id, balance FROM balances WHERE guild_id = ?",
            (_MISATTRIBUTED_GUILD,),
        ).fetchall():
            existing = conn.execute(
                "SELECT balance FROM balances WHERE guild_id = ? AND user_id = ?",
                (real_main, row["user_id"]),
            ).fetchone()
            if existing is None:
                conn.execute(
                    "UPDATE balances SET guild_id = ? WHERE guild_id = ? AND user_id = ?",
                    (real_main, _MISATTRIBUTED_GUILD, row["user_id"]),
                )
            else:
                conn.execute(
                    "UPDATE balances SET balance = balance + ? WHERE guild_id = ? AND user_id = ?",
                    (int(row["balance"]), real_main, row["user_id"]),
                )
                conn.execute(
                    "DELETE FROM balances WHERE guild_id = ? AND user_id = ?",
                    (_MISATTRIBUTED_GUILD, row["user_id"]),
                )

    if "history" in tables and "guild_id" in _table_columns(conn, "history"):
        conn.execute(
            "UPDATE history SET guild_id = ? WHERE guild_id = ?",
            (real_main, _MISATTRIBUTED_GUILD),
        )

    for table, key_cols in (
        ("daily_bonus", ("user_id",)),
        ("owned_cosmetics", ("user_id", "item_id")),
        ("equipped_cosmetics", ("user_id", "kind")),
    ):
        if table not in tables or "guild_id" not in _table_columns(conn, table):
            continue
        rows = conn.execute(f"SELECT * FROM {table} WHERE guild_id = ?", (_MISATTRIBUTED_GUILD,)).fetchall()
        for row in rows:
            where = " AND ".join(f"{c} = ?" for c in key_cols)
            exists = conn.execute(
                f"SELECT 1 FROM {table} WHERE guild_id = ? AND {where}",
                [real_main] + [row[c] for c in key_cols],
            ).fetchone()
            key_vals = [row[c] for c in key_cols]
            if exists is None:
                set_keys = " AND ".join(f"{c} = ?" for c in key_cols)
                conn.execute(
                    f"UPDATE {table} SET guild_id = ? WHERE guild_id = ? AND {set_keys}",
                    [real_main, _MISATTRIBUTED_GUILD] + key_vals,
                )
            else:
                conn.execute(
                    f"DELETE FROM {table} WHERE guild_id = ? AND {where}",
                    [_MISATTRIBUTED_GUILD] + key_vals,
                )


def init():
    with closing(connect()) as conn, conn:
        main_guild = get_main_guild_id()
        # ── balances: user_id PK → (guild_id, user_id) PK ──
        cols = _table_columns(conn, "balances")
        if cols and "guild_id" not in cols:
            conn.execute("ALTER TABLE balances RENAME TO balances_old")
            conn.execute("""
                CREATE TABLE balances (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    balance INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            conn.execute(
                "INSERT INTO balances (guild_id, user_id, balance) SELECT ?, user_id, balance FROM balances_old",
                (main_guild,),
            )
            conn.execute("DROP TABLE balances_old")
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS balances (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    balance INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)

        # ── history: добавить guild_id ──
        cols = _table_columns(conn, "history")
        if cols and "guild_id" not in cols:
            conn.execute("ALTER TABLE history RENAME TO history_old")
            conn.execute("""
                CREATE TABLE history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    delta INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute(
                """INSERT INTO history (guild_id, user_id, delta, reason, created_at)
                   SELECT ?, user_id, delta, reason, created_at FROM history_old""",
                (main_guild,),
            )
            conn.execute("DROP TABLE history_old")
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    delta INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_history_guild_user ON history(guild_id, user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_history_guild_created ON history(guild_id, created_at)")

        # ── daily_bonus: user_id PK → (guild_id, user_id) PK ──
        cols = _table_columns(conn, "daily_bonus")
        if cols and "guild_id" not in cols:
            conn.execute("ALTER TABLE daily_bonus RENAME TO daily_bonus_old")
            conn.execute("""
                CREATE TABLE daily_bonus (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    streak INTEGER NOT NULL DEFAULT 0,
                    last_claim_date TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            conn.execute(
                """INSERT INTO daily_bonus (guild_id, user_id, streak, last_claim_date)
                   SELECT ?, user_id, streak, last_claim_date FROM daily_bonus_old""",
                (main_guild,),
            )
            conn.execute("DROP TABLE daily_bonus_old")
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_bonus (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    streak INTEGER NOT NULL DEFAULT 0,
                    last_claim_date TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (guild_id, user_id)
                )
            """)

        # ── owned_cosmetics: (user_id, item_id) → (guild_id, user_id, item_id) ──
        cols = _table_columns(conn, "owned_cosmetics")
        if cols and "guild_id" not in cols:
            conn.execute("ALTER TABLE owned_cosmetics RENAME TO owned_cosmetics_old")
            conn.execute("""
                CREATE TABLE owned_cosmetics (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    item_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    value TEXT NOT NULL,
                    name TEXT NOT NULL,
                    PRIMARY KEY (guild_id, user_id, item_id)
                )
            """)
            conn.execute(
                """INSERT INTO owned_cosmetics (guild_id, user_id, item_id, kind, value, name)
                   SELECT ?, user_id, item_id, kind, value, name FROM owned_cosmetics_old""",
                (main_guild,),
            )
            conn.execute("DROP TABLE owned_cosmetics_old")
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS owned_cosmetics (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    item_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    value TEXT NOT NULL,
                    name TEXT NOT NULL,
                    PRIMARY KEY (guild_id, user_id, item_id)
                )
            """)

        # ── equipped_cosmetics: (user_id, kind) → (guild_id, user_id, kind) ──
        cols = _table_columns(conn, "equipped_cosmetics")
        if cols and "guild_id" not in cols:
            conn.execute("ALTER TABLE equipped_cosmetics RENAME TO equipped_cosmetics_old")
            conn.execute("""
                CREATE TABLE equipped_cosmetics (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    PRIMARY KEY (guild_id, user_id, kind)
                )
            """)
            conn.execute(
                """INSERT INTO equipped_cosmetics (guild_id, user_id, kind, item_id)
                   SELECT ?, user_id, kind, item_id FROM equipped_cosmetics_old""",
                (main_guild,),
            )
            conn.execute("DROP TABLE equipped_cosmetics_old")
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS equipped_cosmetics (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    PRIMARY KEY (guild_id, user_id, kind)
                )
            """)

        _repair_misattributed_guild(conn)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(conn: sqlite3.Connection, guild_id: int, user_id: int, delta: int, reason: str) -> None:
    conn.execute(
        "INSERT INTO history (guild_id, user_id, delta, reason, created_at) VALUES (?, ?, ?, ?, ?)",
        (guild_id, user_id, delta, reason, _now()),
    )


def get_balance(guild_id: int, user_id: int) -> int:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT balance FROM balances WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()
    return row["balance"] if row else 0


def add(guild_id: int, user_id: int, amount: int, reason: str) -> int:
    """Начислить монеты (amount > 0). Возвращает новый баланс."""
    if amount <= 0:
        return get_balance(guild_id, user_id)
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT INTO balances (guild_id, user_id, balance) VALUES (?, ?, ?)
               ON CONFLICT(guild_id, user_id) DO UPDATE SET balance = balance + excluded.balance""",
            (guild_id, user_id, amount),
        )
        _log(conn, guild_id, user_id, amount, reason)
        return conn.execute(
            "SELECT balance FROM balances WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()["balance"]


def try_spend(guild_id: int, user_id: int, amount: int, reason: str) -> bool:
    """Атомарно списать монеты; False — не хватает средств."""
    if amount <= 0:
        return False
    with closing(connect()) as conn, conn:
        cursor = conn.execute(
            "UPDATE balances SET balance = balance - ? WHERE guild_id = ? AND user_id = ? AND balance >= ?",
            (amount, guild_id, user_id, amount),
        )
        if cursor.rowcount == 0:
            return False
        _log(conn, guild_id, user_id, -amount, reason)
        return True


def transfer(guild_id: int, from_id: int, to_id: int, amount: int, fee: int) -> bool:
    """Атомарный перевод: у отправителя списывается amount + fee, получателю
    приходит amount. False — не хватает средств."""
    if amount <= 0 or fee < 0:
        return False
    total = amount + fee
    with closing(connect()) as conn, conn:
        cursor = conn.execute(
            "UPDATE balances SET balance = balance - ? WHERE guild_id = ? AND user_id = ? AND balance >= ?",
            (total, guild_id, from_id, total),
        )
        if cursor.rowcount == 0:
            return False
        conn.execute(
            """INSERT INTO balances (guild_id, user_id, balance) VALUES (?, ?, ?)
               ON CONFLICT(guild_id, user_id) DO UPDATE SET balance = balance + excluded.balance""",
            (guild_id, to_id, amount),
        )
        _log(conn, guild_id, from_id, -total, f"transfer_to_{to_id}")
        _log(conn, guild_id, to_id, amount, f"transfer_from_{from_id}")
        return True


def set_balance(guild_id: int, user_id: int, value: int, reason: str) -> int:
    """Установить точный баланс (админ из дашборда)."""
    with closing(connect()) as conn, conn:
        old = conn.execute(
            "SELECT balance FROM balances WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()
        old_value = old["balance"] if old else 0
        conn.execute(
            """INSERT INTO balances (guild_id, user_id, balance) VALUES (?, ?, ?)
               ON CONFLICT(guild_id, user_id) DO UPDATE SET balance = excluded.balance""",
            (guild_id, user_id, value),
        )
        _log(conn, guild_id, user_id, value - old_value, reason)
    return value


def reset_all_balances(guild_id: int) -> int:
    """Обнулить все балансы сервера. Возвращает число затронутых строк."""
    with closing(connect()) as conn, conn:
        rows = conn.execute(
            "SELECT user_id, balance FROM balances WHERE guild_id = ? AND balance != 0",
            (guild_id,),
        ).fetchall()
        for row in rows:
            _log(conn, guild_id, row["user_id"], -int(row["balance"]), "dashboard_reset_all")
        cursor = conn.execute(
            "UPDATE balances SET balance = 0 WHERE guild_id = ?",
            (guild_id,),
        )
        return int(cursor.rowcount)


def top(guild_id: int, limit: int = 10) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            """SELECT user_id, balance FROM balances
               WHERE guild_id = ? AND balance > 0
               ORDER BY balance DESC LIMIT ?""",
            (guild_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def rank_of(guild_id: int, user_id: int) -> int | None:
    """Место в топе (1-based); None, если баланса нет."""
    balance = get_balance(guild_id, user_id)
    if balance <= 0:
        return None
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS above FROM balances WHERE guild_id = ? AND balance > ?",
            (guild_id, balance),
        ).fetchone()
    return row["above"] + 1


def recent_history(guild_id: int, user_id: int, limit: int = 10) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            """SELECT delta, reason, created_at FROM history
               WHERE guild_id = ? AND user_id = ?
               ORDER BY id DESC LIMIT ?""",
            (guild_id, user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def weekly_report(guild_id: int, days: int = 7) -> list[dict]:
    """Сводка за период: {user_id, earned, spent, net} по журналу history."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with closing(connect()) as conn:
        rows = conn.execute(
            """
            SELECT user_id,
                   COALESCE(SUM(CASE WHEN delta > 0 THEN delta ELSE 0 END), 0) AS earned,
                   COALESCE(SUM(CASE WHEN delta < 0 THEN -delta ELSE 0 END), 0) AS spent,
                   COALESCE(SUM(delta), 0) AS net
            FROM history
            WHERE guild_id = ? AND created_at >= ?
            GROUP BY user_id
            ORDER BY net DESC
            """,
            (guild_id, cutoff),
        ).fetchall()
    return [dict(r) for r in rows]


def get_daily_bonus(guild_id: int, user_id: int) -> dict:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT streak, last_claim_date FROM daily_bonus WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()
    return dict(row) if row else {"streak": 0, "last_claim_date": ""}


def set_daily_bonus(guild_id: int, user_id: int, streak: int, claim_date: str) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT INTO daily_bonus (guild_id, user_id, streak, last_claim_date) VALUES (?, ?, ?, ?)
               ON CONFLICT(guild_id, user_id) DO UPDATE SET
                 streak = excluded.streak, last_claim_date = excluded.last_claim_date""",
            (guild_id, user_id, streak, claim_date),
        )


# ────────────────────────── Косметика (рамка карточки, титул) ──────────────────────────

def owns_cosmetic(guild_id: int, user_id: int, item_id: str) -> bool:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT 1 FROM owned_cosmetics WHERE guild_id = ? AND user_id = ? AND item_id = ?",
            (guild_id, user_id, item_id),
        ).fetchone()
    return row is not None


def grant_cosmetic(guild_id: int, user_id: int, item_id: str, kind: str, value: str, name: str) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT OR IGNORE INTO owned_cosmetics
               (guild_id, user_id, item_id, kind, value, name) VALUES (?, ?, ?, ?, ?, ?)""",
            (guild_id, user_id, item_id, kind, value, name),
        )


def list_owned_cosmetics(guild_id: int, user_id: int, kind: str) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            """SELECT item_id, value, name FROM owned_cosmetics
               WHERE guild_id = ? AND user_id = ? AND kind = ? ORDER BY rowid""",
            (guild_id, user_id, kind),
        ).fetchall()
    return [dict(r) for r in rows]


def set_equipped(guild_id: int, user_id: int, kind: str, item_id: str) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            """INSERT INTO equipped_cosmetics (guild_id, user_id, kind, item_id) VALUES (?, ?, ?, ?)
               ON CONFLICT(guild_id, user_id, kind) DO UPDATE SET item_id = excluded.item_id""",
            (guild_id, user_id, kind, item_id),
        )


def clear_equipped(guild_id: int, user_id: int, kind: str) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            "DELETE FROM equipped_cosmetics WHERE guild_id = ? AND user_id = ? AND kind = ?",
            (guild_id, user_id, kind),
        )


def get_equipped(guild_id: int, user_id: int, kind: str) -> dict | None:
    """Экипированный предмет с его значением (цвет/текст) — джойн с owned_cosmetics
    на случай, если товар позже убрали из магазина: у владельца он остаётся."""
    with closing(connect()) as conn:
        row = conn.execute(
            """SELECT o.item_id, o.value, o.name FROM equipped_cosmetics e
               JOIN owned_cosmetics o
                 ON o.guild_id = e.guild_id AND o.user_id = e.user_id AND o.item_id = e.item_id
               WHERE e.guild_id = ? AND e.user_id = ? AND e.kind = ?""",
            (guild_id, user_id, kind),
        ).fetchone()
    return dict(row) if row else None
