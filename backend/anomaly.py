from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any


@dataclass
class AnomalyResult:
    transaction_id: int | None
    anomaly_score: float
    is_anomaly: bool


def _read_value(
    row: Any, field_name: str, default=None
):  # Support dict or ORM object access for flexible input types
    if isinstance(row, dict):
        return row.get(field_name, default)
    return getattr(row, field_name, default)


def score_transactions(
    rows: list[Any],
) -> list[
    AnomalyResult
]:  # Score transactions using relative expense size vs average spend
    if not rows:
        return []

    expense_amounts = []  # Collect only expense values (negative amounts)

    for row in rows:
        amount = float(_read_value(row, "amount", 0.0) or 0.0)
        if amount < 0:  # Treat negative values as outgoing transactions
            expense_amounts.append(abs(amount))

    if not expense_amounts:  # No expenses means no anomalies can be detected
        return [
            AnomalyResult(
                transaction_id=_read_value(row, "id"),
                anomaly_score=0.0,
                is_anomaly=False,
            )
            for row in rows
        ]

    average_expense = mean(
        expense_amounts
    )  # Compute baseline average spend for comparison
    threshold_multiplier = (
        4.0  # Define anomaly threshold (4x average + minimum baseline)
    )
    minimum_baseline = 100.0

    results = []

    for row in rows:
        transaction_id = _read_value(row, "id")
        amount = float(_read_value(row, "amount", 0.0) or 0.0)

        if amount >= 0:  # Skip income transactions from anomaly detection
            results.append(
                AnomalyResult(
                    transaction_id=transaction_id,
                    anomaly_score=0.0,
                    is_anomaly=False,
                )
            )
            continue

        expense_abs = abs(amount)

        if average_expense <= 0:
            anomaly_score = 0.0
            is_anomaly = False
        else:
            anomaly_score = (
                expense_abs / average_expense
            )  # Score based on relative size vs average expense
            is_anomaly = (
                expense_abs > minimum_baseline
                and expense_abs
                > (  # Flag only large outliers beyond threshold conditions
                    average_expense * threshold_multiplier
                )
            )

        results.append(
            AnomalyResult(
                transaction_id=transaction_id,
                anomaly_score=float(anomaly_score),
                is_anomaly=is_anomaly,
            )
        )

    return results
