"""Persistence for Becoming — SQLite locally, PostgreSQL on Render."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from typing import Any

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# ─────────────────────────────────────────────────────────
# DATABASE MODE DETECTION
# Render sets DATABASE_URL when you add a PostgreSQL service.
# Locally it's not set — so we fall back to SQLite.
# ─────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")
IS_POSTGRES = bool(DATABASE_URL)
PH = "%s" if IS_POSTGRES else "?"   # placeholder character differs

if IS_POSTGRES:
    import psycopg2
    import psycopg2.extras

DB_PATH = os.getenv("SLEEP_SYSTEM_DB_PATH", "sleep_system.db")
LEGACY_LOG_PATH = "log.json"


# ─────────────────────────────────────────────────────────
# USER CLASS
# ─────────────────────────────────────────────────────────

class User(UserMixin):
    def __init__(self, id: int, email: str, name: str):
        self.id = id
        self.email = email
        self.name = name


# ─────────────────────────────────────────────────────────
# CONNECTION HELPERS
# ─────────────────────────────────────────────────────────

def connect_db():
    if IS_POSTGRES:
        return psycopg2.connect(
            DATABASE_URL,
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Open a connection, commit on success, rollback on error, always close."""
    conn = connect_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _x(conn, sql: str, params=None):
    """Run a SQL statement and return the cursor."""
    cur = conn.cursor()
    if params is not None:
        cur.execute(sql, params)
    else:
        cur.execute(sql)
    return cur


# ─────────────────────────────────────────────────────────
# SCHEMA
# ─────────────────────────────────────────────────────────

def init_db() -> None:
    pk = "SERIAL PRIMARY KEY" if IS_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"

    with get_db() as conn:
        _x(conn, f"""
            CREATE TABLE IF NOT EXISTS users (
                id {pk},
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        _x(conn, f"""
            CREATE TABLE IF NOT EXISTS daily_entries (
                id {pk},
                user_id INTEGER REFERENCES users(id),
                date TEXT NOT NULL,
                sleep_start REAL, sleep_end REAL, sleep_hours REAL,
                sleep_quality TEXT, training INTEGER, caffeine INTEGER,
                caffeine_events TEXT, light TEXT, focus_minutes INTEGER,
                stress INTEGER, screen_minutes INTEGER, movement_minutes INTEGER,
                social_quality INTEGER, north_star TEXT, why_it_matters TEXT,
                show_up_style TEXT, gratitude_items TEXT, priority_step TEXT,
                tiny_steps TEXT, latitude REAL, longitude REAL,
                sunrise_local TEXT, sunset_local TEXT,
                morning_light_window TEXT, evening_dim_window TEXT,
                energy REAL, recovery REAL, sleep_debt REAL,
                circadian_shift REAL, circadian_status TEXT,
                performance_score REAL, tomorrow_score REAL,
                ml_prediction REAL, ml_training_rows INTEGER,
                ml_validation_rmse REAL, ml_top_drivers TEXT,
                action_steps TEXT, ai_coach_summary TEXT,
                ai_coach_model TEXT, ai_coach_status TEXT,
                becoming_readout TEXT, evening_readout TEXT,
                actual_energy REAL, actual_focus REAL, actual_readiness REAL,
                alive_moment TEXT, drained_moment TEXT, alignment_score REAL,
                evening_lesson TEXT, feedback_notes TEXT, feedback_at TEXT,
                recommendations TEXT, insights TEXT, behavior_flags TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migration: add any columns missing from older schema versions
        if IS_POSTGRES:
            cur = _x(conn, """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'daily_entries'
            """)
            existing = {row['column_name'] for row in cur.fetchall()}
        else:
            cur = _x(conn, "PRAGMA table_info(daily_entries)")
            existing = {row['name'] for row in cur.fetchall()}

        migrations = [
            ("user_id", "INTEGER"), ("sleep_hours", "REAL"),
            ("recommendations", "TEXT"), ("insights", "TEXT"),
            ("north_star", "TEXT"), ("why_it_matters", "TEXT"),
            ("show_up_style", "TEXT"), ("gratitude_items", "TEXT"),
            ("priority_step", "TEXT"), ("tiny_steps", "TEXT"),
            ("latitude", "REAL"), ("longitude", "REAL"),
            ("sunrise_local", "TEXT"), ("sunset_local", "TEXT"),
            ("morning_light_window", "TEXT"), ("evening_dim_window", "TEXT"),
            ("ml_prediction", "REAL"), ("ml_training_rows", "INTEGER"),
            ("ml_validation_rmse", "REAL"), ("ml_top_drivers", "TEXT"),
            ("action_steps", "TEXT"), ("ai_coach_summary", "TEXT"),
            ("ai_coach_model", "TEXT"), ("ai_coach_status", "TEXT"),
            ("becoming_readout", "TEXT"), ("evening_readout", "TEXT"),
            ("actual_energy", "REAL"), ("actual_focus", "REAL"),
            ("actual_readiness", "REAL"), ("alive_moment", "TEXT"),
            ("drained_moment", "TEXT"), ("alignment_score", "REAL"),
            ("evening_lesson", "TEXT"), ("feedback_notes", "TEXT"),
            ("feedback_at", "TEXT"),
        ]
        for col_name, col_type in migrations:
            if col_name not in existing:
                if IS_POSTGRES:
                    _x(conn, f"ALTER TABLE daily_entries ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
                else:
                    _x(conn, f"ALTER TABLE daily_entries ADD COLUMN {col_name} {col_type}")


# ─────────────────────────────────────────────────────────
# USER FUNCTIONS
# ─────────────────────────────────────────────────────────

def create_user(email: str, password: str, name: str) -> User | None:
    hash_ = generate_password_hash(password)
    try:
        with get_db() as conn:
            if IS_POSTGRES:
                cur = _x(conn,
                    f"INSERT INTO users (email, password_hash, name) VALUES ({PH},{PH},{PH}) RETURNING id",
                    (email.lower().strip(), hash_, name.strip()),
                )
                uid = cur.fetchone()['id']
            else:
                cur = _x(conn,
                    f"INSERT INTO users (email, password_hash, name) VALUES ({PH},{PH},{PH})",
                    (email.lower().strip(), hash_, name.strip()),
                )
                uid = cur.lastrowid
        return User(id=uid, email=email, name=name)
    except Exception:
        return None


def get_user_by_email(email: str, password: str) -> User | None:
    with get_db() as conn:
        cur = _x(conn, f"SELECT * FROM users WHERE email = {PH}", (email.lower().strip(),))
        row = cur.fetchone()
    if not row:
        return None
    row = dict(row)
    if not check_password_hash(row['password_hash'], password):
        return None
    return User(id=row['id'], email=row['email'], name=row['name'])


def get_user_by_id(user_id: int) -> User | None:
    with get_db() as conn:
        cur = _x(conn, f"SELECT * FROM users WHERE id = {PH}", (user_id,))
        row = cur.fetchone()
    if not row:
        return None
    row = dict(row)
    return User(id=row['id'], email=row['email'], name=row['name'])


# ─────────────────────────────────────────────────────────
# ENTRY HELPERS
# ─────────────────────────────────────────────────────────

def row_to_entry(row) -> dict[str, Any]:
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
    n = dict(entry)
    caffeine_events = n.get("caffeine_events")
    legacy = n.get("caffeine")
    if not caffeine_events and isinstance(legacy, list):
        caffeine_events = legacy
    if isinstance(legacy, list):
        n["caffeine"] = sum(
            e[0] for e in legacy if isinstance(e, (list, tuple)) and len(e) >= 1
        )
    n["caffeine_events"] = caffeine_events or []
    n["light"] = n.get("light", [])
    if n.get("sleep_hours") is None:
        s, e = n.get("sleep_start"), n.get("sleep_end")
        if isinstance(s, (int, float)) and isinstance(e, (int, float)):
            n["sleep_hours"] = round(e - s, 2) if e >= s else round((24 - s) + e, 2)
    return n


# ─────────────────────────────────────────────────────────
# ENTRY CRUD
# ─────────────────────────────────────────────────────────

def list_entries(limit: int | None = None, user_id: int | None = None) -> list[dict[str, Any]]:
    conditions, params = [], []
    if user_id is not None:
        conditions.append(f"user_id = {PH}")
        params.append(user_id)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM daily_entries {where} ORDER BY date ASC, id ASC"
    if limit is not None:
        sql += f" LIMIT {PH}"
        params.append(limit)
    with get_db() as conn:
        cur = _x(conn, sql, tuple(params) if params else None)
        rows = cur.fetchall()
    return [row_to_entry(r) for r in rows]


def get_entry(entry_id: int) -> dict[str, Any] | None:
    with get_db() as conn:
        cur = _x(conn, f"SELECT * FROM daily_entries WHERE id = {PH}", (entry_id,))
        row = cur.fetchone()
    return row_to_entry(row) if row else None


def get_previous_entry(entry_id: int, user_id: int | None = None) -> dict[str, Any] | None:
    with get_db() as conn:
        if user_id is not None:
            cur = _x(conn,
                f"SELECT * FROM daily_entries WHERE id < {PH} AND user_id = {PH} ORDER BY id DESC LIMIT 1",
                (entry_id, user_id),
            )
        else:
            cur = _x(conn,
                f"SELECT * FROM daily_entries WHERE id < {PH} ORDER BY id DESC LIMIT 1",
                (entry_id,),
            )
        row = cur.fetchone()
    return row_to_entry(row) if row else None


def insert_entry(entry: dict[str, Any]) -> int:
    entry = normalize_entry(entry)
    payload = {
        "user_id": entry.get("user_id"),
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

    cols = list(payload.keys())
    vals = [payload[c] for c in cols]

    with get_db() as conn:
        if IS_POSTGRES:
            ph_list = ", ".join(["%s"] * len(cols))
            sql = f"INSERT INTO daily_entries ({', '.join(cols)}) VALUES ({ph_list}) RETURNING id"
            cur = _x(conn, sql, vals)
            return cur.fetchone()['id']
        else:
            named = ", ".join(f":{c}" for c in cols)
            sql = f"INSERT INTO daily_entries ({', '.join(cols)}) VALUES ({named})"
            cur = _x(conn, sql, payload)
            return cur.lastrowid


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
    with get_db() as conn:
        _x(conn, f"""
            UPDATE daily_entries
            SET actual_energy = {PH}, actual_focus = {PH}, actual_readiness = {PH},
                alive_moment = {PH}, drained_moment = {PH}, alignment_score = {PH},
                evening_lesson = {PH}, feedback_notes = {PH}, feedback_at = {PH},
                evening_readout = {PH}
            WHERE id = {PH}
        """, (
            actual_energy, actual_focus, actual_readiness,
            alive_moment, drained_moment, alignment_score,
            evening_lesson, feedback_notes, feedback_at,
            evening_readout, entry_id,
        ))


def ensure_seed_data() -> None:
    init_db()
    with get_db() as conn:
        cur = _x(conn, "SELECT COUNT(*) FROM daily_entries")
        row = cur.fetchone()
        existing = list(dict(row).values())[0]
    if existing or not os.path.exists(LEGACY_LOG_PATH):
        return
    with open(LEGACY_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                insert_entry(json.loads(line))
            except json.JSONDecodeError:
                continue