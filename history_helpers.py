"""Presentation helpers for charts and history views."""

from __future__ import annotations

from statistics import mean


def numeric_series(entries: list[dict], key: str) -> list[float | None]:
    values = []
    for entry in entries:
        value = entry.get(key)
        values.append(float(value) if isinstance(value, (int, float)) else None)
    return values


def sleep_series(entries: list[dict]) -> list[float | None]:
    values = []
    for entry in entries:
        start = entry.get("sleep_start")
        end = entry.get("sleep_end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            values.append(None)
            continue
        if end >= start:
            values.append(round(end - start, 2))
        else:
            values.append(round((24 - start) + end, 2))
    return values


def summary_metrics(entries: list[dict]) -> dict:
    recent = entries[-7:]
    latest = entries[-1] if entries else {}
    score_values = [entry.get("performance_score") for entry in recent if isinstance(entry.get("performance_score"), (int, float))]
    tomorrow_values = [entry.get("tomorrow_score") for entry in recent if isinstance(entry.get("tomorrow_score"), (int, float))]
    return {
        "tracked_days": len(entries),
        "latest_date": latest.get("date", "No data"),
        "latest_score": latest.get("performance_score"),
        "latest_tomorrow": latest.get("tomorrow_score"),
        "latest_recovery": latest.get("recovery"),
        "average_score": round(mean(score_values), 1) if score_values else None,
        "average_tomorrow": round(mean(tomorrow_values), 1) if tomorrow_values else None,
    }


def feedback_metrics(entries: list[dict]) -> dict:
    usable = [
        entry for entry in entries
        if isinstance(entry.get("actual_readiness"), (int, float))
    ]
    if not usable:
        return {
            "feedback_count": 0,
            "rule_mae": None,
            "ml_mae": None,
        }

    rule_errors = []
    ml_errors = []
    for entry in usable:
        actual = float(entry["actual_readiness"])
        if isinstance(entry.get("tomorrow_score"), (int, float)):
            rule_errors.append(abs(float(entry["tomorrow_score"]) - actual))
        if isinstance(entry.get("ml_prediction"), (int, float)):
            ml_errors.append(abs(float(entry["ml_prediction"]) - actual))

    return {
        "feedback_count": len(usable),
        "rule_mae": round(mean(rule_errors), 2) if rule_errors else None,
        "ml_mae": round(mean(ml_errors), 2) if ml_errors else None,
    }


def alignment_metrics(entries: list[dict]) -> dict:
    scores = [
        float(entry["alignment_score"])
        for entry in entries
        if isinstance(entry.get("alignment_score"), (int, float))
    ]
    if not scores:
        return {"alignment_count": 0, "average_alignment": None}
    return {
        "alignment_count": len(scores),
        "average_alignment": round(mean(scores), 2),
    }


def sparkline_points(values: list[float | None], width: int = 360, height: int = 120) -> str:
    clean = [value for value in values if value is not None]
    if len(clean) < 2:
        return ""

    minimum = min(clean)
    maximum = max(clean)
    if maximum == minimum:
        maximum += 1
        minimum -= 1

    step_x = width / max(len(values) - 1, 1)
    points = []
    for index, value in enumerate(values):
        if value is None:
            continue
        normalized = (value - minimum) / (maximum - minimum)
        x = round(index * step_x, 1)
        y = round(height - normalized * height, 1)
        points.append(f"{x},{y}")
    return " ".join(points)
