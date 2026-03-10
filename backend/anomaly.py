from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Any

import numpy as np
from sklearn.ensemble import IsolationForest


@dataclass
class AnomalyResult:
    transaction_id: int | None
    anomaly_score: float
    is_anomaly: bool


def _read_value(row: Any, field_name: str, default=None):
    if isinstance(row, dict):
        return row.get(field_name, default)
    return getattr(row, field_name, default)


def _amount_features(amount: float) -> list[float]:
    signed_amount = float(amount)
    absolute_amount = abs(signed_amount)
    direction = 1.0 if signed_amount > 0 else -1.0 if signed_amount < 0 else 0.0
    return [signed_amount, absolute_amount, direction]


def build_feature_matrix(rows: Iterable[Any]) -> np.ndarray:
    features = []

    for row in rows:
        amount = _read_value(row, "amount", 0.0)
        if amount is None:
            amount = 0.0
        features.append(_amount_features(float(amount)))

    if not features:
        return np.empty((0, 3), dtype=float)

    return np.array(features, dtype=float)


def score_transactions(
    rows: list[Any],
    contamination: float = 0.1,
    random_state: int = 42,
) -> list[AnomalyResult]:
    if not rows:
        return []

    feature_matrix = build_feature_matrix(rows)

    if len(rows) < 5:
        results = []
        for row in rows:
            results.append(
                AnomalyResult(
                    transaction_id=_read_value(row, "id"),
                    anomaly_score=0.0,
                    is_anomaly=False,
                )
            )
        return results

    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=200,
    )

    model.fit(feature_matrix)

    predictions = model.predict(feature_matrix)
    raw_scores = model.decision_function(feature_matrix)

    results = []
    for index, row in enumerate(rows):
        results.append(
            AnomalyResult(
                transaction_id=_read_value(row, "id"),
                anomaly_score=float(-raw_scores[index]),
                is_anomaly=bool(predictions[index] == -1),
            )
        )

    return results
