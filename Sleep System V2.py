# Keenan Ray
# Sleep System Project - Refined + Runnable
# 04/02/2025

from datetime import date
import json
import os

# -----------------------------
# MODELS
# -----------------------------

class CircadianRhythm:
    def __init__(self, phase="aligned"):
        self.phase = phase
        self.shift_minutes = 0

    def apply_light(self, hour, minutes=30):
        if 6 <= hour <= 10:
            self.shift_minutes -= minutes
        elif 20 <= hour <= 24:
            self.shift_minutes += minutes

    def apply_screen(self, minutes):
        self.shift_minutes += minutes * 0.05

    def apply_late_caffeine(self, mg):
        self.shift_minutes += mg / 50

    def status(self):
        if self.shift_minutes <= -60:
            return "advanced"
        elif self.shift_minutes >= 60:
            return "delayed"
        return "aligned"


class SleepSession:
    def __init__(self, start, end, quality="ok"):
        self.start = start
        self.end = end
        self.quality = quality

    def duration(self):
        if self.end >= self.start:
            return self.end - self.start
        return (24 - self.start) + self.end


class Person:
    def __init__(self, name, circadian):
        self.name = name
        self.circadian = circadian

        self.base_energy = 50
        self.energy = self.base_energy

        self.sleep_need = 8
        self.sleep_debt = 0

        self.caffeine_level = 0
        self.recovery = 100
        self.training_load = 0

    def reset_day(self):
        self.energy = self.base_energy

    def apply_sleep(self, session):
        hours = session.duration()
        self.reset_day()

        delta = hours - self.sleep_need
        self.sleep_debt -= delta

        self.energy += hours * 5
        self.recovery = min(100, self.recovery + hours * 5)

        self.energy *= (self.recovery / 100)

    def drink_caffeine(self, mg, hour):
        self.caffeine_level += mg
        self.energy += mg * 0.05

        if hour >= 14:
            self.sleep_debt += mg / 100
            self.circadian.apply_late_caffeine(mg)

    def train(self, intensity):
        self.training_load += intensity * 10
        self.recovery -= intensity * 8


class Day:
    def __init__(self, date):
        self.date = date

        self.sleep = None
        self.training = 0
        self.caffeine = []
        self.light = []

        self.focus_minutes = 0
        self.stress = 0
        self.screen_minutes = 0

    def total_caffeine(self):
        return sum(mg for mg, _ in self.caffeine)


# -----------------------------
# ENGINE
# -----------------------------

class SleepEngine:
    def __init__(self, person):
        self.person = person

    def run(self, day):
        p = self.person

        if day.sleep:
            p.apply_sleep(day.sleep)

        for mg, hour in day.caffeine:
            p.drink_caffeine(mg, hour)

        for hour, minutes in day.light:
            p.circadian.apply_light(hour, minutes)

        p.train(day.training)

        p.recovery -= day.stress * 5
        p.circadian.apply_screen(day.screen_minutes)

        p.energy = max(0, min(100, p.energy))


# -----------------------------
# ANALYTICS
# -----------------------------

class PerformanceModel:
    @staticmethod
    def score(day, person):
        score = 0

        score += person.energy * 0.4
        score += min(day.focus_minutes, 180) / 180 * 30
        score -= day.stress
        score -= min(day.screen_minutes, 120) / 120 * 10

        return max(0, round(score, 1))


def compute_delta(today, yesterday):
    if not yesterday:
        return ["No prior day"]

    deltas = []

    diff = today["score"] - yesterday["score"]
    if abs(diff) > 0.5:
        deltas.append(f"Score {'up' if diff > 0 else 'down'} {round(diff,1)}")

    return deltas


def predict_performance(features):
    # simple baseline model (placeholder for AI later)
    score = 50

    score += features["sleep_hours"] * 5
    score -= features["screen"] * 0.05
    score -= features["stress"] * 5

    if features["caffeine"] > 300:
        score -= 5

    return round(max(0, min(100, score)), 1)


# -----------------------------
# STORAGE
# -----------------------------

LOG_FILE = "log.json"

def save_day(data):
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")


def load_last_day():
    if not os.path.exists(LOG_FILE):
        return None

    with open(LOG_FILE, "r") as f:
        lines = f.readlines()

    if len(lines) < 1:
        return None

    return json.loads(lines[-1])


# -----------------------------
# MAIN (RUN THIS)
# -----------------------------

if __name__ == "__main__":

    # Create system
    circadian = CircadianRhythm()
    person = Person("Keenan", circadian)
    engine = SleepEngine(person)

    # Create day
    day = Day(date.today().isoformat())

    # ---- INPUTS (EDIT HERE) ----
    day.sleep = SleepSession(22, 6.5)
    day.caffeine.append((120, 8))
    day.light.append((7, 20))
    day.training = 2
    day.focus_minutes = 90
    day.stress = 1
    day.screen_minutes = 45

    # ---- RUN ENGINE ----
    engine.run(day)

    score = PerformanceModel.score(day, person)

    # ---- FEATURES (for AI) ----
    features = {
        "sleep_hours": day.sleep.duration(),
        "caffeine": day.total_caffeine(),
        "screen": day.screen_minutes,
        "stress": day.stress,
        "circadian_shift": person.circadian.shift_minutes
    }

    predicted = predict_performance(features)

    # ---- LOAD YESTERDAY ----
    last_day = load_last_day()

    today_data = {
        "date": day.date,
        "score": score
    }

    # ---- OUTPUT ----
    print("\n--- DAILY SUMMARY ---")
    print("Energy:", round(person.energy, 1))
    print("Recovery:", round(person.recovery, 1))
    print("Circadian:", person.circadian.status())
    print("Shift:", round(person.circadian.shift_minutes, 1))
    print("Performance Score:", score)
    print("Predicted Score (AI baseline):", predicted)

    print("\nDelta vs Yesterday:")
    for d in compute_delta(today_data, last_day):
        print("•", d)

    # ---- SAVE ----
    save_day(today_data)
