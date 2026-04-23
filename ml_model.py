"""Simple trainable ML layer for Sleep System."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


FEATURE_NAMES = [
    "sleep_hours",
    "focus_minutes",
    "stress",
    "screen_minutes",
    "movement_minutes",
    "social_quality",
    "caffeine",
    "training",
    "circadian_shift",
]


def numeric_value(entry: dict, key: str, default: float = 0.0) -> float:
    value = entry.get(key, default)
    return float(value) if isinstance(value, (int, float)) else default


def feature_vector(entry: dict) -> list[float]:
    return [numeric_value(entry, name) for name in FEATURE_NAMES]


@dataclass
class TomorrowModel:
    intercept: float
    coefficients: np.ndarray
    feature_means: np.ndarray
    feature_stds: np.ndarray
    training_rows: int
    validation_rows: int
    validation_rmse: float | None

    def predict(self, entry: dict) -> float:
        features = np.array(feature_vector(entry), dtype=float)
        standardized = (features - self.feature_means) / self.feature_stds
        prediction = self.intercept + standardized @ self.coefficients
        return round(float(np.clip(prediction, 0.0, 100.0)), 1)

    def top_drivers(self, entry: dict, limit: int = 3) -> list[str]:
        features = np.array(feature_vector(entry), dtype=float)
        standardized = (features - self.feature_means) / self.feature_stds
        contributions = standardized * self.coefficients

        ranked = sorted(
            zip(FEATURE_NAMES, contributions),
            key=lambda item: abs(item[1]),
            reverse=True,
        )

        drivers = []
        for name, contribution in ranked[:limit]:
            direction = "raised" if contribution > 0 else "lowered"
            label = name.replace("_", " ")
            drivers.append(f"{label.title()} {direction} the ML prediction")
        return drivers


def train_tomorrow_model(entries: list[dict], alpha: float = 1.0) -> TomorrowModel | None:
    usable = [
        entry for entry in entries
        if isinstance(entry.get("actual_readiness"), (int, float))
        or isinstance(entry.get("tomorrow_score"), (int, float))
        or isinstance(entry.get("performance_score"), (int, float))
    ]

    if len(usable) < 12:
        return None

    x = np.array([feature_vector(entry) for entry in usable], dtype=float)
    y = np.array(
        [
            float(entry["actual_readiness"])
            if isinstance(entry.get("actual_readiness"), (int, float))
            else float(entry["tomorrow_score"])
            if isinstance(entry.get("tomorrow_score"), (int, float))
            else float(entry["performance_score"])
            for entry in usable
        ],
        dtype=float,
    )

    split_index = max(8, int(len(usable) * 0.8))
    x_train, x_valid = x[:split_index], x[split_index:]
    y_train, y_valid = y[:split_index], y[split_index:]

    feature_means = x_train.mean(axis=0)
    feature_stds = x_train.std(axis=0)
    feature_stds[feature_stds == 0] = 1.0

    x_train_std = (x_train - feature_means) / feature_stds
    design = np.column_stack([np.ones(len(x_train_std)), x_train_std])

    identity = np.eye(design.shape[1])
    identity[0, 0] = 0.0
    weights = np.linalg.solve(design.T @ design + alpha * identity, design.T @ y_train)

    intercept = float(weights[0])
    coefficients = weights[1:]

    validation_rmse = None
    if len(x_valid):
        x_valid_std = (x_valid - feature_means) / feature_stds
        predictions = intercept + x_valid_std @ coefficients
        validation_rmse = float(math.sqrt(np.mean((predictions - y_valid) ** 2)))

    return TomorrowModel(
        intercept=intercept,
        coefficients=coefficients,
        feature_means=feature_means,
        feature_stds=feature_stds,
        training_rows=len(x_train),
        validation_rows=len(x_valid),
        validation_rmse=round(validation_rmse, 2) if validation_rmse is not None else None,
    )
