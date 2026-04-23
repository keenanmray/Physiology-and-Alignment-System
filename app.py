"""Flask app for Sleep System."""

from __future__ import annotations

from datetime import date, datetime

from flask import Flask, redirect, render_template, request, url_for

from database import (
    ensure_seed_data,
    get_entry,
    get_previous_entry,
    insert_entry,
    list_entries,
    update_feedback,
)
from history_helpers import alignment_metrics, feedback_metrics, numeric_series, sleep_series, sparkline_points, summary_metrics
from ml_model import train_tomorrow_model
from solar_service import fetch_solar_context

from sleep_engine import (
    DayInput,
    Person,
    SleepSession,
    SleepSystemEngine,
    weekly_insights,
)


app = Flask(__name__)
ensure_seed_data()


DEFAULT_FORM = {
    "sleep_start": "21:15",
    "sleep_end": "06:15",
    "sleep_quality": "good",
    "caffeine_mg": "140",
    "caffeine_time": "08:00",
    "light_minutes": "20",
    "light_time": "07:00",
    "training_intensity": "2",
    "focus_minutes": "120",
    "stress": "1",
    "screen_minutes": "45",
    "movement_minutes": "35",
    "social_quality": "4",
    "north_star": "",
    "why_it_matters": "",
    "tiny_step_1": "",
    "tiny_step_2": "",
    "tiny_step_3": "",
    "priority_step": "",
    "latitude": "41.8781",
    "longitude": "-87.6298",
}


def clock_to_decimal(raw: str, fallback: float) -> float:
    value = raw.strip()
    if not value:
        return fallback
    if ":" in value:
        hours_text, minutes_text = value.split(":", 1)
        try:
            hours = int(hours_text)
            minutes = int(minutes_text)
        except ValueError:
            return fallback
        return hours + (minutes / 60)
    try:
        return float(value)
    except ValueError:
        return fallback


def parse_float(name: str, fallback: float) -> float:
    raw = request.form.get(name, str(fallback)).strip()
    try:
        return float(raw)
    except ValueError:
        return fallback


def parse_int(name: str, fallback: int) -> int:
    raw = request.form.get(name, str(fallback)).strip()
    try:
        return int(float(raw))
    except ValueError:
        return fallback


def parse_optional_float(name: str) -> float | None:
    raw = request.form.get(name, "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def parse_clock_time(name: str, fallback: float) -> float:
    raw = request.form.get(name, "").strip()
    return clock_to_decimal(raw, fallback)


def build_day_input() -> DayInput:
    sleep_start = parse_clock_time("sleep_start", 21.25)
    sleep_end = parse_clock_time("sleep_end", 6.25)
    caffeine_mg = parse_int("caffeine_mg", 140)
    caffeine_time = parse_clock_time("caffeine_time", 8.0)
    light_minutes = parse_int("light_minutes", 20)
    light_time = parse_clock_time("light_time", 7.0)
    latitude = parse_float("latitude", 41.8781)
    longitude = parse_float("longitude", -87.6298)

    solar_context = {}
    try:
        timezone_name = datetime.now().astimezone().tzinfo.key  # type: ignore[attr-defined]
    except AttributeError:
        timezone_name = "America/Chicago"

    try:
        solar_context = fetch_solar_context(latitude, longitude, date.today().isoformat(), timezone_name)
    except Exception:
        solar_context = {
            "latitude": latitude,
            "longitude": longitude,
            "sunrise_local": None,
            "sunset_local": None,
            "morning_light_window": None,
            "evening_dim_window": None,
        }

    return DayInput(
        day_date=date.today().isoformat(),
        sleep=SleepSession(
            start=sleep_start,
            end=sleep_end,
            quality=request.form.get("sleep_quality", "good").strip() or "good",
        ),
        caffeine_events=[(caffeine_mg, caffeine_time)] if caffeine_mg > 0 else [],
        light_events=[(light_time, light_minutes)] if light_minutes > 0 else [],
        training_intensity=parse_int("training_intensity", 2),
        focus_minutes=parse_int("focus_minutes", 120),
        stress=parse_int("stress", 1),
        screen_minutes=parse_int("screen_minutes", 45),
        movement_minutes=parse_int("movement_minutes", 35),
        social_quality=parse_int("social_quality", 4),
        north_star=request.form.get("north_star", "").strip() or None,
        why_it_matters=request.form.get("why_it_matters", "").strip() or None,
        priority_step=request.form.get("priority_step", "").strip() or None,
        tiny_steps=[
            step for step in [
                request.form.get("tiny_step_1", "").strip(),
                request.form.get("tiny_step_2", "").strip(),
                request.form.get("tiny_step_3", "").strip(),
            ] if step
        ],
        latitude=solar_context.get("latitude"),
        longitude=solar_context.get("longitude"),
        sunrise_local=solar_context.get("sunrise_local"),
        sunset_local=solar_context.get("sunset_local"),
        morning_light_window=solar_context.get("morning_light_window"),
        evening_dim_window=solar_context.get("evening_dim_window"),
    )


def compare_saved_entry(entry: dict | None, previous: dict | None) -> list[str]:
    if not entry or not previous:
        return ["No prior day available for comparison."]

    deltas = []
    current_score = entry.get("performance_score")
    previous_score = previous.get("performance_score")
    if isinstance(current_score, (int, float)) and isinstance(previous_score, (int, float)):
        diff = round(current_score - previous_score, 1)
        if abs(diff) >= 0.5:
            direction = "up" if diff > 0 else "down"
            deltas.append(f"Performance score is {direction} {abs(diff)} points versus the previous log.")

    current_focus = entry.get("focus_minutes")
    previous_focus = previous.get("focus_minutes")
    if isinstance(current_focus, (int, float)) and isinstance(previous_focus, (int, float)):
        focus_diff = int(current_focus) - int(previous_focus)
        if focus_diff != 0:
            direction = "up" if focus_diff > 0 else "down"
            deltas.append(f"Focus minutes are {direction} {abs(focus_diff)} versus the previous log.")

    return deltas[:2] or ["Previous day exists, but there was not a meaningful performance change."]


def build_trend_cards(entries: list[dict]) -> list[dict]:
    return [
        {
            "title": "Performance Score",
            "latest": entries[-1].get("performance_score") if entries else None,
            "points": sparkline_points(numeric_series(entries, "performance_score")),
            "stroke": "var(--accent)",
        },
        {
            "title": "Tomorrow Score",
            "latest": entries[-1].get("tomorrow_score") if entries else None,
            "points": sparkline_points(numeric_series(entries, "tomorrow_score")),
            "stroke": "var(--accent-3)",
        },
        {
            "title": "Sleep Hours",
            "latest": entries[-1].get("sleep_hours") if entries else None,
            "points": sparkline_points(sleep_series(entries)),
            "stroke": "var(--accent-2)",
        },
    ]


def enrich_with_ml(entry: dict, model) -> dict:
    if model is None:
        entry["ml_prediction"] = None
        entry["ml_training_rows"] = 0
        entry["ml_validation_rmse"] = None
        entry["ml_top_drivers"] = []
        return entry

    entry["ml_prediction"] = model.predict(entry)
    entry["ml_training_rows"] = model.training_rows
    entry["ml_validation_rmse"] = model.validation_rmse
    entry["ml_top_drivers"] = model.top_drivers(entry)
    return entry


@app.route("/", methods=["GET", "POST"])
def index():
    entries = list_entries()
    ml_model = train_tomorrow_model(entries)
    metrics = summary_metrics(entries)
    feedback_summary = feedback_metrics(entries)
    alignment_summary = alignment_metrics(entries)
    result = None
    deltas = []
    weekly = weekly_insights(entries)
    trend_cards = build_trend_cards(entries[-14:])
    form_data = DEFAULT_FORM.copy()
    saved_entry_id = request.args.get("saved", type=int)

    if request.method == "POST":
        form_data.update(request.form.to_dict())
        day = build_day_input()
        engine = SleepSystemEngine(Person(name="Keenan"))
        result = engine.run_day(day)
        entry_payload = enrich_with_ml(result.to_log_dict(day), ml_model)
        entry_id = insert_entry(entry_payload)
        return redirect(url_for("index", saved=entry_id))

    if saved_entry_id:
        result = get_entry(saved_entry_id)
        deltas = compare_saved_entry(result, get_previous_entry(saved_entry_id))

    return render_template(
        "index.html",
        form_data=form_data,
        result=result,
        deltas=deltas,
        weekly=weekly,
        metrics=metrics,
        feedback_summary=feedback_summary,
        alignment_summary=alignment_summary,
        trend_cards=trend_cards,
        ml_model=ml_model,
        active_page="dashboard",
    )


@app.route("/history")
def history():
    entries = list_entries()
    history_entries = list(reversed(entries[-30:]))
    metrics = summary_metrics(entries)
    return render_template(
        "history.html",
        entries=history_entries,
        metrics=metrics,
        feedback_summary=feedback_metrics(entries),
        alignment_summary=alignment_metrics(entries),
        trend_cards=build_trend_cards(entries[-30:]),
        ml_model=train_tomorrow_model(entries),
        active_page="history",
    )


@app.route("/feedback/<int:entry_id>", methods=["GET", "POST"])
def feedback(entry_id: int):
    entry = get_entry(entry_id)
    if entry is None:
        return redirect(url_for("history"))

    if request.method == "POST":
        update_feedback(
            entry_id=entry_id,
            actual_energy=parse_optional_float("actual_energy"),
            actual_focus=parse_optional_float("actual_focus"),
            actual_readiness=parse_optional_float("actual_readiness"),
            alive_moment=request.form.get("alive_moment", "").strip(),
            drained_moment=request.form.get("drained_moment", "").strip(),
            alignment_score=parse_optional_float("alignment_score"),
            evening_lesson=request.form.get("evening_lesson", "").strip(),
            feedback_notes=request.form.get("feedback_notes", "").strip(),
            feedback_at=datetime.now().isoformat(timespec="minutes"),
        )
        return redirect(url_for("history"))

    return render_template(
        "feedback.html",
        entry=entry,
        active_page="history",
    )


if __name__ == "__main__":
    print("Sleep System running at http://127.0.0.1:8000")
    app.run(host="127.0.0.1", port=8000, debug=False)
