"""SQLite persistence for Sleep System."""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any


DB_PATH = "sleep_system.db"
LEGACY_LOG_PATH = "log.json"


def connect_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with connect_db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        existing_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(daily_entries)").fetchall()
        }
        for column_name, column_type in (
            ("sleep_hours", "REAL"),
            ("recommendations", "TEXT"),
            ("insights", "TEXT"),
            ("north_star", "TEXT"),
            ("why_it_matters", "TEXT"),
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


def row_to_entry(row: sqlite3.Row) -> dict[str, Any]:
    entry = dict(row)
    for key in ("caffeine_events", "light", "recommendations", "insights", "behavior_flags", "ml_top_drivers", "tiny_steps"):
        raw = entry.get(key)
        entry[key] = json.loads(raw) if raw else []
    return entry


def normalize_entry(entry: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(entry)

    caffeine_events = normalized.get("caffeine_events")
    legacy_caffeine = normalized.get("caffeine")
    if not caffeine_events and isinstance(legacy_caffeine, list):
        caffeine_events = legacy_caffeine

    if isinstance(legacy_caffeine, list):
        normalized["caffeine"] = sum(
            event[0] for event in legacy_caffeine if isinstance(event, (list, tuple)) and len(event) >= 1
        )

    normalized["caffeine_events"] = caffeine_events or []
    normalized["light"] = normalized.get("light", [])

    if normalized.get("sleep_hours") is None:
        start = normalized.get("sleep_start")
        end = normalized.get("sleep_end")
        if isinstance(start, (int, float)) and isinstance(end, (int, float)):
            normalized["sleep_hours"] = round(end - start, 2) if end >= start else round((24 - start) + end, 2)

    return normalized


def list_entries(limit: int | None = None) -> list[dict[str, Any]]:
    query = "SELECT * FROM daily_entries ORDER BY date ASC, id ASC"
    params: tuple[Any, ...] = ()
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


def get_previous_entry(entry_id: int) -> dict[str, Any] | None:
    with connect_db() as connection:
        row = connection.execute(
            """
            SELECT * FROM daily_entries
            WHERE id < ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (entry_id,),
        ).fetchone()
    return row_to_entry(row) if row else None


def insert_entry(entry: dict[str, Any]) -> int:
    entry = normalize_entry(entry)
    payload = {
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
                date, sleep_start, sleep_end, sleep_hours, sleep_quality, training, caffeine,
                caffeine_events, light, focus_minutes, stress, screen_minutes,
                movement_minutes, social_quality, north_star, why_it_matters, priority_step,
                tiny_steps, latitude, longitude, sunrise_local,
                sunset_local, morning_light_window, evening_dim_window, energy, recovery, sleep_debt,
                circadian_shift, circadian_status, performance_score, tomorrow_score,
                ml_prediction, ml_training_rows, ml_validation_rmse, ml_top_drivers,
                actual_energy, actual_focus, actual_readiness, alive_moment, drained_moment,
                alignment_score, evening_lesson, feedback_notes, feedback_at,
                recommendations, insights,
                behavior_flags
            ) VALUES (
                :date, :sleep_start, :sleep_end, :sleep_hours, :sleep_quality, :training, :caffeine,
                :caffeine_events, :light, :focus_minutes, :stress, :screen_minutes,
                :movement_minutes, :social_quality, :north_star, :why_it_matters, :priority_step,
                :tiny_steps, :latitude, :longitude, :sunrise_local,
                :sunset_local, :morning_light_window, :evening_dim_window, :energy, :recovery, :sleep_debt,
                :circadian_shift, :circadian_status, :performance_score, :tomorrow_score,
                :ml_prediction, :ml_training_rows, :ml_validation_rmse, :ml_top_drivers,
                :actual_energy, :actual_focus, :actual_readiness, :alive_moment, :drained_moment,
                :alignment_score, :evening_lesson, :feedback_notes, :feedback_at,
                :recommendations, :insights,
                :behavior_flags
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
) -> None:
    with connect_db() as connection:
        connection.execute(
            """
            UPDATE daily_entries
            SET actual_energy = ?, actual_focus = ?, actual_readiness = ?,
                alive_moment = ?, drained_moment = ?, alignment_score = ?,
                evening_lesson = ?, feedback_notes = ?, feedback_at = ?
            WHERE id = ?
            """,
            (
                actual_energy,
                actual_focus,
                actual_readiness,
                alive_moment,
                drained_moment,
                alignment_score,
                evening_lesson,
                feedback_notes,
                feedback_at,
                entry_id,
            ),
        )


def ensure_seed_data() -> None:
    init_db()
    with connect_db() as connection:
        existing = connection.execute("SELECT COUNT(*) FROM daily_entries").fetchone()[0]
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
