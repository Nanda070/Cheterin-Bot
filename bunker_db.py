"""SQLite-хранилище игры «Бункер»: лобби/игры, игроки (карточки персонажей), голоса за
исключение, заявки на спец. возможности.

Синхронный sqlite3 (не aiosqlite) — тот же стиль хранения, что и mafia_db.py.
"""

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone

ACTIVE_STATUSES = ("lobby", "active")


def get_db_path() -> str:
    return os.getenv("BUNKER_DB_PATH", "bunker.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with closing(connect()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                voice_channel_id INTEGER,
                lobby_message_id INTEGER,
                vote_message_id INTEGER,
                status TEXT NOT NULL DEFAULT 'lobby',
                phase TEXT NOT NULL DEFAULT 'lobby',
                round_number INTEGER NOT NULL DEFAULT 0,
                phase_deadline_ts INTEGER,
                min_players INTEGER NOT NULL,
                max_players INTEGER NOT NULL,
                bunker_capacity INTEGER,
                unique_cards INTEGER NOT NULL DEFAULT 1,
                discussion_timer_sec INTEGER NOT NULL,
                vote_timer_sec INTEGER NOT NULL,
                catastrophe_name TEXT,
                catastrophe_description TEXT,
                bunker_conditions_name TEXT,
                bunker_conditions_description TEXT,
                created_by INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                ended_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE,
                character_json TEXT,
                revealed_fields_json TEXT NOT NULL DEFAULT '[]',
                alive INTEGER NOT NULL DEFAULT 1,
                eliminated_round INTEGER,
                joined_at TEXT NOT NULL,
                UNIQUE(game_id, user_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expulsion_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                voter_user_id INTEGER NOT NULL,
                target_user_id INTEGER,
                submitted_at TEXT NOT NULL,
                UNIQUE(game_id, round_number, voter_user_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ability_announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                player_user_id INTEGER NOT NULL,
                card_index INTEGER NOT NULL,
                card_name TEXT NOT NULL,
                target_user_id INTEGER,
                note TEXT NOT NULL DEFAULT '',
                applied INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                applied_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS round_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT,
                created_at TEXT NOT NULL
            )
        """)
        # Миграция для баз, созданных до появления этих колонок: CREATE TABLE IF NOT EXISTS
        # не добавляет колонки в существующую таблицу.
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(games)").fetchall()}
        for column, ddl in (
            ("voice_channel_id", "voice_channel_id INTEGER"),
            ("vote_message_id", "vote_message_id INTEGER"),
            ("unique_cards", "unique_cards INTEGER NOT NULL DEFAULT 1"),
            ("catastrophe_key", "catastrophe_key TEXT"),
            ("bunker_conditions_key", "bunker_conditions_key TEXT"),
        ):
            if column not in existing:
                conn.execute(f"ALTER TABLE games ADD COLUMN {ddl}")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_player(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    player = dict(row)
    player["character"] = json.loads(player["character_json"]) if player["character_json"] else None
    player["revealed_fields"] = json.loads(player["revealed_fields_json"])
    return player


# ────────────────────────── Игры ──────────────────────────

def create_game(
    guild_id: int, channel_id: int, created_by: int,
    min_players: int, max_players: int,
    discussion_timer_sec: int, vote_timer_sec: int,
    unique_cards: bool = True,
) -> dict:
    with closing(connect()) as conn, conn:
        cursor = conn.execute("""
            INSERT INTO games (
                guild_id, channel_id, min_players, max_players,
                discussion_timer_sec, vote_timer_sec, unique_cards, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            guild_id, channel_id, min_players, max_players,
            discussion_timer_sec, vote_timer_sec, int(unique_cards), created_by, _now(),
        ))
        game_id = cursor.lastrowid
    return get_game(game_id)


def get_game(game_id: int) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        return dict(row) if row else None


def get_game_by_lobby_message(message_id: int) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM games WHERE lobby_message_id = ?", (message_id,)).fetchone()
        return dict(row) if row else None


def get_active_game_in_channel(channel_id: int) -> dict | None:
    with closing(connect()) as conn:
        placeholders = ",".join("?" * len(ACTIVE_STATUSES))
        row = conn.execute(
            f"SELECT * FROM games WHERE channel_id = ? AND status IN ({placeholders})",
            (channel_id, *ACTIVE_STATUSES),
        ).fetchone()
        return dict(row) if row else None


def update_game(game_id: int, **fields) -> dict | None:
    if not fields:
        return get_game(game_id)
    columns = ", ".join(f"{key} = ?" for key in fields)
    with closing(connect()) as conn, conn:
        conn.execute(f"UPDATE games SET {columns} WHERE id = ?", (*fields.values(), game_id))
    return get_game(game_id)


def list_active_games(guild_id: int | None = None) -> list[dict]:
    with closing(connect()) as conn:
        placeholders = ",".join("?" * len(ACTIVE_STATUSES))
        if guild_id is None:
            rows = conn.execute(
                f"SELECT * FROM games WHERE status IN ({placeholders}) ORDER BY created_at DESC",
                ACTIVE_STATUSES,
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT * FROM games WHERE guild_id = ? AND status IN ({placeholders}) ORDER BY created_at DESC",
                (guild_id, *ACTIVE_STATUSES),
            ).fetchall()
        return [dict(r) for r in rows]


# ────────────────────────── Игроки ──────────────────────────

def add_player(game_id: int, user_id: int) -> bool:
    with closing(connect()) as conn, conn:
        try:
            conn.execute(
                "INSERT INTO players (game_id, user_id, joined_at) VALUES (?, ?, ?)",
                (game_id, user_id, _now()),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def remove_player(game_id: int, user_id: int) -> bool:
    with closing(connect()) as conn, conn:
        cursor = conn.execute("DELETE FROM players WHERE game_id = ? AND user_id = ?", (game_id, user_id))
        return cursor.rowcount > 0


def list_players(game_id: int) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute("SELECT * FROM players WHERE game_id = ? ORDER BY joined_at", (game_id,)).fetchall()
        return [_row_to_player(r) for r in rows]


def list_alive_players(game_id: int) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM players WHERE game_id = ? AND alive = 1 ORDER BY joined_at", (game_id,)
        ).fetchall()
        return [_row_to_player(r) for r in rows]


def count_players(game_id: int) -> int:
    with closing(connect()) as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM players WHERE game_id = ?", (game_id,)).fetchone()["c"]


def get_player(game_id: int, user_id: int) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT * FROM players WHERE game_id = ? AND user_id = ?", (game_id, user_id)
        ).fetchone()
        return _row_to_player(row)


def get_player_by_token(token: str) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM players WHERE token = ?", (token,)).fetchone()
        return _row_to_player(row)


def assign_character(game_id: int, user_id: int, character: dict, token: str) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            "UPDATE players SET character_json = ?, token = ? WHERE game_id = ? AND user_id = ?",
            (json.dumps(character, ensure_ascii=False), token, game_id, user_id),
        )


def set_player_character(game_id: int, user_id: int, character: dict) -> None:
    """Полная перезапись карточки — используется админ-панелью при ручном применении спец. возможности."""
    with closing(connect()) as conn, conn:
        conn.execute(
            "UPDATE players SET character_json = ? WHERE game_id = ? AND user_id = ?",
            (json.dumps(character, ensure_ascii=False), game_id, user_id),
        )


def reveal_fields(game_id: int, user_id: int, field_keys: list[str]) -> None:
    player = get_player(game_id, user_id)
    if player is None:
        return
    revealed = set(player["revealed_fields"])
    revealed.update(field_keys)
    with closing(connect()) as conn, conn:
        conn.execute(
            "UPDATE players SET revealed_fields_json = ? WHERE game_id = ? AND user_id = ?",
            (json.dumps(sorted(revealed)), game_id, user_id),
        )


def eliminate_player(game_id: int, user_id: int, round_number: int) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            "UPDATE players SET alive = 0, eliminated_round = ? WHERE game_id = ? AND user_id = ?",
            (round_number, game_id, user_id),
        )


# ────────────────────────── Голоса за исключение ──────────────────────────

def upsert_vote(game_id: int, round_number: int, voter_user_id: int, target_user_id: int | None) -> None:
    with closing(connect()) as conn, conn:
        conn.execute("""
            INSERT OR REPLACE INTO expulsion_votes (game_id, round_number, voter_user_id, target_user_id, submitted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (game_id, round_number, voter_user_id, target_user_id, _now()))


def get_votes(game_id: int, round_number: int) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM expulsion_votes WHERE game_id = ? AND round_number = ?", (game_id, round_number)
        ).fetchall()
        return [dict(r) for r in rows]


def get_vote(game_id: int, round_number: int, voter_user_id: int) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute(
            "SELECT * FROM expulsion_votes WHERE game_id = ? AND round_number = ? AND voter_user_id = ?",
            (game_id, round_number, voter_user_id),
        ).fetchone()
        return dict(row) if row else None


# ────────────────────────── Заявки на спец. возможности ──────────────────────────

def create_ability_announcement(
    game_id: int, round_number: int, player_user_id: int,
    card_index: int, card_name: str, target_user_id: int | None, note: str = "",
) -> dict:
    with closing(connect()) as conn, conn:
        cursor = conn.execute("""
            INSERT INTO ability_announcements
            (game_id, round_number, player_user_id, card_index, card_name, target_user_id, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (game_id, round_number, player_user_id, card_index, card_name, target_user_id, note, _now()))
        announcement_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM ability_announcements WHERE id = ?", (announcement_id,)).fetchone()
        return dict(row)


def list_ability_announcements(game_id: int) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM ability_announcements WHERE game_id = ? ORDER BY id", (game_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_ability_announcement(announcement_id: int) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM ability_announcements WHERE id = ?", (announcement_id,)).fetchone()
        return dict(row) if row else None


def mark_ability_announcement_applied(announcement_id: int) -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            "UPDATE ability_announcements SET applied = 1, applied_at = ? WHERE id = ?",
            (_now(), announcement_id),
        )


# ────────────────────────── События раунда ──────────────────────────

def add_round_event(game_id: int, round_number: int, event_type: str, payload: str = "") -> None:
    with closing(connect()) as conn, conn:
        conn.execute(
            "INSERT INTO round_events (game_id, round_number, event_type, payload, created_at) VALUES (?, ?, ?, ?, ?)",
            (game_id, round_number, event_type, payload, _now()),
        )


def list_round_events(game_id: int) -> list[dict]:
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT * FROM round_events WHERE game_id = ? ORDER BY id", (game_id,)
        ).fetchall()
        return [dict(r) for r in rows]
