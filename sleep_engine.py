"""Core domain logic for Sleep System."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from statistics import mean
from typing import Iterable


LOG_FILE = "log.json"


@dataclass
class CircadianRhythm:
    shift_minutes: float = 0.0

    def apply_light(self, hour: float, minutes: int = 30) -> None:
        if 6 <= hour <= 10:
            self.shift_minutes -= minutes
        elif 20 <= hour <= 24:
            self.shift_minutes += minutes

    def apply_screen(self, minutes: int) -> None:
        self.shift_minutes += minutes * 0.05

    def apply_late_caffeine(self, mg: int) -> None:
        self.shift_minutes += mg / 50

    def status(self) -> str:
        if self.shift_minutes <= -60:
            return "advanced"
        if self.shift_minutes >= 60:
            return "delayed"
        return "aligned"


@dataclass
class SleepSession:
    start: float
    end: float
    quality: str = "ok"

    def duration(self) -> float:
        if self.end >= self.start:
            return self.end - self.start
        return (24 - self.start) + self.end


@dataclass
class DayInput:
    day_date: str
    sleep: SleepSession
    caffeine_events: list[tuple[int, float]] = field(default_factory=list)
    light_events: list[tuple[float, int]] = field(default_factory=list)
    training_intensity: int = 0
    focus_minutes: int = 0
    stress: int = 0
    screen_minutes: int = 0
    movement_minutes: int = 0
    social_quality: int = 3
    north_star: str | None = None
    why_it_matters: str | None = None
    priority_step: str | None = None
    tiny_steps: list[str] = field(default_factory=list)
    latitude: float | None = None
    longitude: float | None = None
    sunrise_local: str | None = None
    sunset_local: str | None = None
    morning_light_window: str | None = None
    evening_dim_window: str | None = None

    def total_caffeine(self) -> int:
        return sum(mg for mg, _ in self.caffeine_events)


@dataclass
class Person:
    name: str
    sleep_need: float = 8.0
    base_energy: float = 50.0
    circadian: CircadianRhythm = field(default_factory=CircadianRhythm)
    energy: float = 50.0
    sleep_debt: float = 0.0
    recovery: float = 100.0
    training_load: float = 0.0
    caffeine_level: float = 0.0

    def reset_day(self) -> None:
        self.energy = self.base_energy
        self.caffeine_level = 0.0


@dataclass
class DailyResult:
    date: str
    sleep_hours: float
    focus_minutes: int
    energy: float
    recovery: float
    sleep_debt: float
    circadian_shift: float
    circadian_status: str
    total_caffeine: int
    performance_score: float
    tomorrow_score: float
    recommendations: list[str]
    insights: list[str]
    behavior_flags: list[str]

    def to_log_dict(self, day: DayInput) -> dict:
        return {
            "date": self.date,
            "sleep_hours": self.sleep_hours,
            "sleep_start": day.sleep.start,
            "sleep_end": day.sleep.end,
            "sleep_quality": day.sleep.quality,
            "training": day.training_intensity,
            "caffeine": self.total_caffeine,
            "caffeine_events": day.caffeine_events,
            "light": day.light_events,
            "focus_minutes": day.focus_minutes,
            "stress": day.stress,
            "screen_minutes": day.screen_minutes,
            "movement_minutes": day.movement_minutes,
            "social_quality": day.social_quality,
            "north_star": day.north_star,
            "why_it_matters": day.why_it_matters,
            "priority_step": day.priority_step,
            "tiny_steps": day.tiny_steps,
            "latitude": day.latitude,
            "longitude": day.longitude,
            "sunrise_local": day.sunrise_local,
            "sunset_local": day.sunset_local,
            "morning_light_window": day.morning_light_window,
            "evening_dim_window": day.evening_dim_window,
            "energy": self.energy,
            "recovery": self.recovery,
            "sleep_debt": self.sleep_debt,
            "circadian_shift": self.circadian_shift,
            "circadian_status": self.circadian_status,
            "performance_score": self.performance_score,
            "tomorrow_score": self.tomorrow_score,
            "recommendations": self.recommendations,
            "insights": self.insights,
            "behavior_flags": self.behavior_flags,
        }


class SleepSystemEngine:
    def __init__(self, person: Person):
        self.person = person

    def run_day(self, day: DayInput) -> DailyResult:
        person = self.person
        person.reset_day()

        sleep_hours = day.sleep.duration()
        delta_sleep = sleep_hours - person.sleep_need
        person.sleep_debt -= delta_sleep

        person.energy += sleep_hours * 5
        person.recovery = min(100.0, person.recovery + sleep_hours * 4)

        for mg, hour in day.caffeine_events:
            person.caffeine_level += mg
            person.energy += mg * 0.05
            if hour >= 14:
                person.sleep_debt += mg / 100
                person.circadian.apply_late_caffeine(mg)

        for hour, minutes in day.light_events:
            person.circadian.apply_light(hour, minutes)

        person.training_load += day.training_intensity * 10
        person.recovery -= day.training_intensity * 8
        person.recovery -= day.stress * 5
        person.recovery += min(day.movement_minutes, 60) * 0.15
        person.circadian.apply_screen(day.screen_minutes)

        if day.social_quality >= 4:
            person.recovery += 3
        elif day.social_quality <= 2:
            person.recovery -= 3

        person.recovery = max(0.0, min(100.0, person.recovery))
        person.energy *= person.recovery / 100
        person.energy = max(0.0, min(100.0, person.energy))

        performance_score = self._performance_score(day, person)
        tomorrow_score = self._tomorrow_score(day, person, sleep_hours)
        behavior_flags = self._behavior_flags(day, sleep_hours)
        recommendations = self._recommendations(day, person, sleep_hours, behavior_flags)
        insights = [
            self._primary_insight(day, person, sleep_hours, performance_score),
            self._circadian_insight(person),
        ]

        return DailyResult(
            date=day.day_date,
            sleep_hours=round(sleep_hours, 2),
            focus_minutes=day.focus_minutes,
            energy=round(person.energy, 1),
            recovery=round(person.recovery, 1),
            sleep_debt=round(person.sleep_debt, 2),
            circadian_shift=round(person.circadian.shift_minutes, 1),
            circadian_status=person.circadian.status(),
            total_caffeine=day.total_caffeine(),
            performance_score=performance_score,
            tomorrow_score=tomorrow_score,
            recommendations=recommendations,
            insights=insights,
            behavior_flags=behavior_flags,
        )

    @staticmethod
    def _performance_score(day: DayInput, person: Person) -> float:
        score = 0.0
        score += person.energy * 0.4
        score += min(day.focus_minutes, 180) / 180 * 30
        score += min(day.movement_minutes, 45) / 45 * 8
        score += day.social_quality * 1.5
        score -= day.stress * 4
        score -= min(day.screen_minutes, 180) / 180 * 10
        return round(max(0.0, min(100.0, score)), 1)

    @staticmethod
    def _tomorrow_score(day: DayInput, person: Person, sleep_hours: float) -> float:
        score = 55.0
        score += (sleep_hours - 8) * 6
        score += min(day.movement_minutes, 45) * 0.2
        score -= day.stress * 4
        score -= max(0, day.total_caffeine() - 250) * 0.03
        score -= max(0, day.screen_minutes - 60) * 0.06
        score -= max(0.0, person.circadian.shift_minutes) * 0.05
        return round(max(0.0, min(100.0, score)), 1)

    @staticmethod
    def _behavior_flags(day: DayInput, sleep_hours: float) -> list[str]:
        flags = []
        if sleep_hours < 7.5:
            flags.append("short_sleep")
        if any(hour >= 14 for _, hour in day.caffeine_events):
            flags.append("late_caffeine")
        if day.screen_minutes > 90:
            flags.append("high_screen")
        if day.stress >= 3:
            flags.append("high_stress")
        if day.focus_minutes >= 120:
            flags.append("strong_focus")
        if day.movement_minutes >= 30:
            flags.append("good_movement")
        return flags

    @staticmethod
    def _recommendations(
        day: DayInput,
        person: Person,
        sleep_hours: float,
        behavior_flags: list[str],
    ) -> list[str]:
        recs = []
        if sleep_hours < 8:
            recs.append("Protect an earlier sleep window tonight to recover lost sleep pressure.")
        if "late_caffeine" in behavior_flags:
            recs.append("Move all caffeine before 2:00 PM to reduce circadian delay.")
        if day.screen_minutes > 60:
            if day.evening_dim_window:
                recs.append(
                    f"Dim bright light and cut screens during {day.evening_dim_window} to protect melatonin timing."
                )
            else:
                recs.append("Trim evening screen exposure by 20-30 minutes to protect melatonin timing.")
        if day.stress >= 3:
            recs.append("Add a 10-minute downshift block tonight: walk, breathe, or stretch.")
        if day.focus_minutes < 60:
            recs.append("Schedule one 45-minute deep work block earlier in the day.")
        if day.morning_light_window:
            recs.append(f"Get outdoor light during {day.morning_light_window} to anchor circadian timing.")
        elif person.circadian.shift_minutes > 15:
            recs.append("Anchor tomorrow morning with outdoor light within the first hour awake.")
        if not recs:
            recs.append("Keep the current routine steady; today's inputs support a strong tomorrow.")
        return recs[:3]

    @staticmethod
    def _primary_insight(
        day: DayInput,
        person: Person,
        sleep_hours: float,
        performance_score: float,
    ) -> str:
        if sleep_hours >= 8.5 and day.focus_minutes >= 90:
            return "High sleep duration plus strong focus created a solid performance base today."
        if day.morning_light_window and not day.light_events:
            return f"You missed a strong circadian anchor today; sunrise-linked outdoor light was best during {day.morning_light_window}."
        if day.stress >= 3:
            return "Stress was the main drag on recovery and likely suppressed your usable energy."
        if any(hour >= 14 for _, hour in day.caffeine_events):
            return "Late caffeine likely helped short-term alertness but pushed your clock later."
        if performance_score < 50:
            return "Your system underperformed because recovery inputs were weaker than demand."
        return "Your current behaviors are supportive, but one stronger lever could raise tomorrow's score."

    @staticmethod
    def _circadian_insight(person: Person) -> str:
        status = person.circadian.status()
        if status == "advanced":
            return "Your circadian system is shifting earlier, which supports earlier sleep onset."
        if status == "delayed":
            return "Your circadian system is drifting later, so evening inputs need tightening."
        return "Your circadian timing is roughly aligned based on today's light and stimulant signals."


def load_logs(path: str = LOG_FILE) -> list[dict]:
    if not os.path.exists(path):
        return []
    logs = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return logs


def save_log(entry: dict, path: str = LOG_FILE) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def compare_to_previous(today: DailyResult, logs: Iterable[dict]) -> list[str]:
    previous = None
    for entry in reversed(list(logs)):
        if entry.get("date") != today.date:
            previous = entry
            break
    if not previous:
        return ["No prior day available for comparison."]

    deltas = []
    previous_score = previous.get("performance_score")
    if isinstance(previous_score, (int, float)):
        diff = round(today.performance_score - previous_score, 1)
        if abs(diff) >= 0.5:
            direction = "up" if diff > 0 else "down"
            deltas.append(f"Performance score is {direction} {abs(diff)} points versus the previous log.")

    previous_focus = previous.get("focus_minutes")
    if isinstance(previous_focus, (int, float)):
        focus_diff = today.focus_minutes - int(previous_focus)
        if focus_diff != 0:
            direction = "up" if focus_diff > 0 else "down"
            deltas.append(f"Focus minutes are {direction} {abs(focus_diff)} versus the previous log.")

    return deltas[:2] or ["Previous day exists, but there was not a meaningful performance change."]


def weekly_insights(logs: list[dict]) -> list[str]:
    recent = logs[-7:]
    if len(recent) < 3:
        return ["Not enough data yet for a weekly pattern read."]

    insights = []
    scores = [entry.get("performance_score") for entry in recent if isinstance(entry.get("performance_score"), (int, float))]
    if scores:
        insights.append(f"7-day average performance score: {round(mean(scores), 1)}.")

    late_caffeine_scores = []
    early_caffeine_scores = []
    for entry in recent:
        events = entry.get("caffeine_events", [])
        if not events:
            continue
        score = entry.get("performance_score")
        if not isinstance(score, (int, float)):
            continue
        if any(hour >= 14 for _, hour in events):
            late_caffeine_scores.append(score)
        else:
            early_caffeine_scores.append(score)

    if late_caffeine_scores and early_caffeine_scores:
        late_avg = mean(late_caffeine_scores)
        early_avg = mean(early_caffeine_scores)
        if abs(late_avg - early_avg) >= 2:
            better = "earlier" if early_avg > late_avg else "later"
            insights.append(
                f"Caffeine timing trend: {better.capitalize()} caffeine days outperform the alternative by {round(abs(early_avg - late_avg), 1)} points."
            )

    screen_heavy = [
        entry
        for entry in recent
        if isinstance(entry.get("screen_minutes"), (int, float)) and entry.get("screen_minutes") > 60
    ]
    if len(screen_heavy) >= 2:
        insights.append("Multiple recent days show elevated evening screen load, which may be limiting recovery.")

    return insights[:3] or ["Recent logs are stable, but no strong weekly pattern stood out yet."]


def summarize_metrics(logs: list[dict]) -> dict:
    recent = logs[-7:]
    latest = logs[-1] if logs else {}
    score_values = [entry.get("performance_score") for entry in recent if isinstance(entry.get("performance_score"), (int, float))]
    tomorrow_values = [entry.get("tomorrow_score") for entry in recent if isinstance(entry.get("tomorrow_score"), (int, float))]
    return {
        "tracked_days": len(logs),
        "latest_date": latest.get("date", "No data"),
        "latest_score": latest.get("performance_score"),
        "latest_tomorrow": latest.get("tomorrow_score"),
        "latest_recovery": latest.get("recovery"),
        "average_score": round(mean(score_values), 1) if score_values else None,
        "average_tomorrow": round(mean(tomorrow_values), 1) if tomorrow_values else None,
    }
