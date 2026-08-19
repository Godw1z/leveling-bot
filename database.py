import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "bot.db"
XP_COOLDOWN_SECONDS = 60


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS levels (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 0,
                last_xp_time REAL NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
            """
        )
        conn.commit()


def xp_for_level(level: int) -> int:
    return 5 * (level ** 2) + 50 * level + 100


def get_user(user_id: int, guild_id: int) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM levels WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id),
        ).fetchone()

        if row is None:
            conn.execute(
                "INSERT INTO levels (guild_id, user_id) VALUES (?, ?)",
                (guild_id, user_id),
            )
            conn.commit()
            return {
                "guild_id": guild_id,
                "user_id": user_id,
                "xp": 0,
                "level": 0,
                "last_xp_time": 0,
            }

        return dict(row)


def try_add_xp(user_id: int, guild_id: int, amount: int) -> dict | None:
    """Award XP if the cooldown has expired. Returns update info or None on cooldown."""
    now = time.time()
    user = get_user(user_id, guild_id)

    if now - user["last_xp_time"] < XP_COOLDOWN_SECONDS:
        return None

    new_xp = user["xp"] + amount
    new_level = user["level"]

    while new_xp >= xp_for_level(new_level + 1):
        new_level += 1

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE levels
            SET xp = ?, level = ?, last_xp_time = ?
            WHERE guild_id = ? AND user_id = ?
            """,
            (new_xp, new_level, now, guild_id, user_id),
        )
        conn.commit()

    return {
        "xp": new_xp,
        "level": new_level,
        "leveled_up": new_level > user["level"],
        "previous_level": user["level"],
    }


def get_rank(user_id: int, guild_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) + 1 AS rank
            FROM levels
            WHERE guild_id = ? AND xp > (
                SELECT xp FROM levels WHERE guild_id = ? AND user_id = ?
            )
            """,
            (guild_id, guild_id, user_id),
        ).fetchone()
        return row["rank"]


def get_leaderboard(guild_id: int, limit: int = 10) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT user_id, xp, level
            FROM levels
            WHERE guild_id = ?
            ORDER BY xp DESC, user_id ASC
            LIMIT ?
            """,
            (guild_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
