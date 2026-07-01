"""SQLite persistence for Becoming — with user authentication."""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


# ─────────────────────────────────────────────
# USER CLASS
# Flask-Login needs a User object to track who
# is currently logged in. UserMixin gives us
# default implementations of four required
# properties (is_authenticated, is_active, etc.)
# We just add our own data on top.
# ─────────────────────────────────────────────

class User(UserMixin):
    def __init__(self, id: int, email: str, name: str):
        self.id = id
        self.email = email
        self.name = name


DB_PATH = os.getenv("SLEEP_SYSTEM_DB_PATH", "sleep_system.db")
LEGACY_LOG_PATH = "log.json"


def connect_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with connect_db() as connection:

        # ── USERS TABLE ──────────────────────────────
        # New table. Each row is one Becoming account.
        # password_hash: we NEVER store plain passwords.
        #   werkzeug hashes it before storing.
        # ─────────────────────────────────────────────
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ── DAILY ENTRIES TABLE ───────────────────────
        # Same as before but with user_id added.
        # REFERENCES users(id) means SQLite knows this
        # links to the users table.
        # ─────────────────────────────────────────────
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                date TEXT NOT NULL,
                sleep_start REAL,
                sleep_end REAL,
                sleep_hours REAL,
                sleep_quality TEXT,
                training INTEGER,
                caffeine INTEGER,
                caffeine_events TEXT,
                light TEXT,
                focus_minutes INTEGER,
                stress INTEGER,
                screen_minutes INTEGER,
                movement_minutes INTEGER,
                social_quality INTEGER,
                north_star TEXT,
                why_it_matters TEXT,
                show_up_style TEXT,
                gratitude_items TEXT,
                priority_step TEXT,
                tiny_steps TEXT,
                latitude REAL,
                longitude REAL,
                sunrise_local TEXT,
                sunset_local TEXT,
                morning_light_window TEXT,
                evening_dim_window TEXT,
                energy REAL,
                recovery REAL,
                sleep_debt REAL,
                circadian_shift REAL,
                circadian_status TEXT,
                performance_score REAL,
                tomorrow_score REAL,
                ml_prediction REAL,
                ml_training_rows INTEGER,
                ml_validation_rmse REAL,
                ml_top_drivers TEXT,
                action_steps TEXT,
                ai_coach_summary TEXT,
                ai_coach_model TEXT,
                ai_coach_status TEXT,
                becoming_readout TEXT,
                evening_readout TEXT,
                actual_energy REAL,
                actual_focus REAL,
                actual_readiness REAL,
                alive_moment TEXT,
                drained_moment TEXT,
                alignment_score REAL,
                evening_lesson TEXT,
                feedback_notes TEXT,
                feedback_at TEXT,
                recommendations TEXT,
                insights TEXT,
                behavior_flags TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ── MIGRATION ─────────────────────────────────
        # For columns that didn't exist in older versions
        # of the database, we add them safely here.
        # This runs every startup but only adds columns
        # that are actually missing.
        # ─────────────────────────────────────────────
        existing_columns = {
            row["name"] for row in connection.execute(
                "PRAGMA table_info(daily_entries)"
            ).fetchall()
        }
        for column_name, column_type in (
            ("user_id", "INTEGER"),
            ("sleep_hours", "REAL"),
            ("recommendations", "TEXT"),
            ("insights", "TEXT"),
            ("north_star", "TEXT"),
            ("why_it_matters", "TEXT"),
            ("show_up_style", "TEXT"),
            ("gratitude_items", "TEXT"),
            ("priority_step", "TEXT"),
            ("tiny_steps", "TEXT"),
            ("latitude", "REAL"),
            ("longitude", "REAL"),
            ("sunrise_local", "TEXT"),
            ("sunset_local", "TEXT"),
            ("morning_light_window", "TEXT"),
            ("evening_dim_window", "TEXT"),
            ("ml_prediction", "REAL"),
            ("ml_training_rows", "INTEGER"),
            ("ml_validation_rmse", "REAL"),
            ("ml_top_drivers", "TEXT"),
            ("action_steps", "TEXT"),
            ("ai_coach_summary", "TEXT"),
            ("ai_coach_model", "TEXT"),
            ("ai_coach_status", "TEXT"),
            ("becoming_readout", "TEXT"),
            ("evening_readout", "TEXT"),
            ("actual_energy", "REAL"),
            ("actual_focus", "REAL"),
            ("actual_readiness", "REAL"),
            ("alive_moment", "TEXT"),
            ("drained_moment", "TEXT"),
            ("alignment_score", "REAL"),
            ("evening_lesson", "TEXT"),
            ("feedback_notes", "TEXT"),
            ("feedback_at", "TEXT"),
        ):
            if column_name not in existing_columns:
                connection.execute(
                    f"ALTER TABLE daily_entries ADD COLUMN {column_name} {column_type}"
                )


# ─────────────────────────────────────────────
# USER FUNCTIONS
# These three functions are all app.py needs
# to handle registration and login.
# ─────────────────────────────────────────────

def create_user(email: str, password: str, name: str) -> User | None:
    """
    Create a new user account. Returns the User if successful,
    None if the email is already taken.

    generate_password_hash() turns 'mypassword123' into a long
    scrambled string like '$2b$12$...' that can't be reversed.
    """
    password_hash = generate_password_hash(password)
    try:
        with connect_db() as connection:
            cursor = connection.execute(
                "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
                (email.lower().strip(), password_hash, name.strip()),
            )
            return User(id=cursor.lastrowid, email=email, name=name)
    except sqlite3.IntegrityError:
        # Email already exists — UNIQUE constraint fired
        return None


def get_user_by_email(email: str, password: str) -> User | None:
    """
    Look up a user by email and verify their password.
    Returns User if credentials are correct, None otherwise.

    check_password_hash() compares a plain password against
    the stored hash — returns True if they match.
    """
    with connect_db() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.lower().strip(),),
        ).fetchone()

    if row is None:
        return None

    if not check_password_hash(row["password_hash"], password):
        return None

    return User(id=row["id"], email=row["email"], name=row["name"])


def get_user_by_id(user_id: int) -> User | None:
    """
    Load a user by their ID. Flask-Login calls this on every
    page load to restore the session — it's how the app knows
    who's logged in after they close and reopen their browser.
    """
    with connect_db() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    if row is None:
        return None

    return User(id=row["id"], email=row["email"], name=row["name"])


# ─────────────────────────────────────────────
# ENTRY FUNCTIONS — now user-aware
# ─────────────────────────────────────────────

def row_to_entry(row: sqlite3.Row) -> dict[str, Any]:
    entry = dict(row)
    for key in ("caffeine_events", "light", "recommendations", "action_steps",
                "insights", "behavior_flags", "ml_top_drivers", "tiny_steps",
                "gratitude_items"):
        raw = entry.get(key)
        entry[key] = json.loads(raw) if raw else []
    raw = entry.get("becoming_readout")
    if isinstance(raw, dict):
        entry["becoming_readout"] = raw
    elif isinstance(raw, str):
        entry["becoming_readout"] = json.loads(raw)
    else:
        entry["becoming_readout"] = None
    raw = entry.get("evening_readout")
    entry["evening_readout"] = json.loads(raw) if isinstance(raw, str) else raw
    return entry


def normalize_entry(entry: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(entry)
    caffeine_events = normalized.get("caffeine_events")
    legacy_caffeine = normalized.get("caffeine")
    if not caffeine_events and isinstance(legacy_caffeine, list):
        caffeine_events = legacy_caffeine
    if isinstance(legacy_caffeine, list):
        normalized["caffeine"] = sum(
            event[0] for event in legacy_caffeine
            if isinstance(event, (list, tuple)) and len(event) >= 1
        )
    normalized["caffeine_events"] = caffeine_events or []
    normalized["light"] = normalized.get("light", [])
    if normalized.get("sleep_hours") is None:
        start = normalized.get("sleep_start")
        end = normalized.get("sleep_end")
        if isinstance(start, (int, float)) and isinstance(end, (int, float)):
            normalized["sleep_hours"] = (
                round(end - start, 2) if end >= start
                else round((24 - start) + end, 2)
            )
    return normalized


def list_entries(
    limit: int | None = None,
    user_id: int | None = None,
) -> list[dict[str, Any]]:
    """
    List entries. If user_id is provided, only return that
    user's entries. If None, return all (used for ML model).
    """
    if user_id is not None:
        query = "SELECT * FROM daily_entries WHERE user_id = ? ORDER BY date ASC, id ASC"
        params: tuple[Any, ...] = (user_id,)
        if limit is not None:
            query += " LIMIT ?"
            params = (user_id, limit)
    else:
        query = "SELECT * FROM daily_entries ORDER BY date ASC, id ASC"
        params = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)

    with connect_db() as connection:
        rows = connection.execute(query, params).fetchall()
    return [row_to_entry(row) for row in rows]


def get_entry(entry_id: int) -> dict[str, Any] | None:
    with connect_db() as connection:
        row = connection.execute(
            "SELECT * FROM daily_entries WHERE id = ?",
            (entry_id,),
        ).fetchone()
    return row_to_entry(row) if row else None


def get_previous_entry(
    entry_id: int,
    user_id: int | None = None,
) -> dict[str, Any] | None:
    """
    Get the entry just before entry_id for the same user.
    """
    with connect_db() as connection:
        if user_id is not None:
            row = connection.execute(
                """
                SELECT * FROM daily_entries
                WHERE id < ? AND user_id = ?
                ORDER BY id DESC LIMIT 1
                """,
                (entry_id, user_id),
            ).fetchone()
        else:
            row = connection.execute(
                """
                SELECT * FROM daily_entries
                WHERE id < ?
                ORDER BY id DESC LIMIT 1
                """,
                (entry_id,),
            ).fetchone()
    return row_to_entry(row) if row else None


def insert_entry(entry: dict[str, Any]) -> int:
    entry = normalize_entry(entry)
    payload = {
        "user_id": entry.get("user_id"),   # ← NEW
        "date": entry.get("date"),
        "sleep_start": entry.get("sleep_start"),
        "sleep_end": entry.get("sleep_end"),
        "sleep_hours": entry.get("sleep_hours"),
        "sleep_quality": entry.get("sleep_quality"),
        "training": entry.get("training"),
        "caffeine": entry.get("caffeine"),
        "caffeine_events": json.dumps(entry.get("caffeine_events", [])),
        "light": json.dumps(entry.get("light", [])),
        "focus_minutes": entry.get("focus_minutes"),
        "stress": entry.get("stress"),
        "screen_minutes": entry.get("screen_minutes"),
        "movement_minutes": entry.get("movement_minutes"),
        "social_quality": entry.get("social_quality"),
        "north_star": entry.get("north_star"),
        "why_it_matters": entry.get("why_it_matters"),
        "show_up_style": entry.get("show_up_style"),
        "gratitude_items": json.dumps(entry.get("gratitude_items", [])),
        "priority_step": entry.get("priority_step"),
        "tiny_steps": json.dumps(entry.get("tiny_steps", [])),
        "latitude": entry.get("latitude"),
        "longitude": entry.get("longitude"),
        "sunrise_local": entry.get("sunrise_local"),
        "sunset_local": entry.get("sunset_local"),
        "morning_light_window": entry.get("morning_light_window"),
        "evening_dim_window": entry.get("evening_dim_window"),
        "energy": entry.get("energy"),
        "recovery": entry.get("recovery"),
        "sleep_debt": entry.get("sleep_debt"),
        "circadian_shift": entry.get("circadian_shift"),
        "circadian_status": entry.get("circadian_status"),
        "performance_score": entry.get("performance_score"),
        "tomorrow_score": entry.get("tomorrow_score"),
        "ml_prediction": entry.get("ml_prediction"),
        "ml_training_rows": entry.get("ml_training_rows"),
        "ml_validation_rmse": entry.get("ml_validation_rmse"),
        "ml_top_drivers": json.dumps(entry.get("ml_top_drivers", [])),
        "action_steps": json.dumps(entry.get("action_steps", [])),
        "ai_coach_summary": entry.get("ai_coach_summary"),
        "ai_coach_model": entry.get("ai_coach_model"),
        "ai_coach_status": entry.get("ai_coach_status"),
        "becoming_readout": json.dumps(entry.get("becoming_readout")) if entry.get("becoming_readout") else None,
        "evening_readout": json.dumps(entry.get("evening_readout")) if entry.get("evening_readout") else None,
        "actual_energy": entry.get("actual_energy"),
        "actual_focus": entry.get("actual_focus"),
        "actual_readiness": entry.get("actual_readiness"),
        "alive_moment": entry.get("alive_moment"),
        "drained_moment": entry.get("drained_moment"),
        "alignment_score": entry.get("alignment_score"),
        "evening_lesson": entry.get("evening_lesson"),
        "feedback_notes": entry.get("feedback_notes"),
        "feedback_at": entry.get("feedback_at"),
        "recommendations": json.dumps(entry.get("recommendations", [])),
        "insights": json.dumps(entry.get("insights", [])),
        "behavior_flags": json.dumps(entry.get("behavior_flags", [])),
    }

    with connect_db() as connection:
        cursor = connection.execute(
            """
            INSERT INTO daily_entries (
                user_id,
                date, sleep_start, sleep_end, sleep_hours, sleep_quality, training, caffeine,
                caffeine_events, light, focus_minutes, stress, screen_minutes,
                movement_minutes, social_quality, north_star, why_it_matters, show_up_style,
                gratitude_items, priority_step, tiny_steps, latitude, longitude, sunrise_local,
                sunset_local, morning_light_window, evening_dim_window, energy, recovery,
                sleep_debt, circadian_shift, circadian_status, performance_score, tomorrow_score,
                ml_prediction, ml_training_rows, ml_validation_rmse, ml_top_drivers,
                action_steps, ai_coach_summary, ai_coach_model, ai_coach_status,
                becoming_readout, evening_readout,
                actual_energy, actual_focus, actual_readiness, alive_moment, drained_moment,
                alignment_score, evening_lesson, feedback_notes, feedback_at,
                recommendations, insights, behavior_flags
            ) VALUES (
                :user_id,
                :date, :sleep_start, :sleep_end, :sleep_hours, :sleep_quality, :training,
                :caffeine, :caffeine_events, :light, :focus_minutes, :stress, :screen_minutes,
                :movement_minutes, :social_quality, :north_star, :why_it_matters, :show_up_style,
                :gratitude_items, :priority_step, :tiny_steps, :latitude, :longitude,
                :sunrise_local, :sunset_local, :morning_light_window, :evening_dim_window,
                :energy, :recovery, :sleep_debt, :circadian_shift, :circadian_status,
                :performance_score, :tomorrow_score, :ml_prediction, :ml_training_rows,
                :ml_validation_rmse, :ml_top_drivers, :action_steps, :ai_coach_summary,
                :ai_coach_model, :ai_coach_status, :becoming_readout, :evening_readout,
                :actual_energy, :actual_focus, :actual_readiness, :alive_moment, :drained_moment,
                :alignment_score, :evening_lesson, :feedback_notes, :feedback_at,
                :recommendations, :insights, :behavior_flags
            )
            """,
            payload,
        )
        return int(cursor.lastrowid)


def update_feedback(
    entry_id: int,
    actual_energy: float | None,
    actual_focus: float | None,
    actual_readiness: float | None,
    alive_moment: str,
    drained_moment: str,
    alignment_score: float | None,
    evening_lesson: str,
    feedback_notes: str,
    feedback_at: str,
    evening_readout: str | None = None,
) -> None:
    with connect_db() as connection:
        connection.execute(
            """
            UPDATE daily_entries
            SET actual_energy = ?, actual_focus = ?, actual_readiness = ?,
                alive_moment = ?, drained_moment = ?, alignment_score = ?,
                evening_lesson = ?, feedback_notes = ?, feedback_at = ?,
                evening_readout = ?
            WHERE id = ?
            """,
            (
                actual_energy, actual_focus, actual_readiness,
                alive_moment, drained_moment, alignment_score,
                evening_lesson, feedback_notes, feedback_at,
                evening_readout, entry_id,
            ),
        )


def ensure_seed_data() -> None:
    init_db()
    with connect_db() as connection:
        existing = connection.execute(
            "SELECT COUNT(*) FROM daily_entries"
        ).fetchone()[0]
    if existing or not os.path.exists(LEGACY_LOG_PATH):
        return

    with open(LEGACY_LOG_PATH, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            insert_entry(entry)