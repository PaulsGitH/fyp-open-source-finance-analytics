from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AnomalyResult:
    transaction_id: int | None
    anomaly_score: float
    is_anomaly: bool


def _read_value(row: Any, field_name: str, default=None):
    if isinstance(row, dict):
        return row.get(field_name, default)
    return getattr(row, field_name, default)


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def score_transactions(rows: list[Any]) -> list[AnomalyResult]:
    if not rows:
        return []

    suspicious_keywords = [
        "atm",
        "withdrawal",
        "wire",
        "international",
        "foreign",
        "crypto",
        "casino",
        "bet",
        "gambling",
        "lottery",
        "jet",
        "helicopter",
        "charter",
        "auction",
        "antique",
        "diamond",
        "luxury",
        "marketplace",
        "rare",
        "private",
        "supplier",
        "reversal",
        "urgent",
        "liquidation",
        "claim",
        "payout",
        "refund",
        "chargeback",
        "collectible",
        "tokyo",
        "bonus",
        "cash",
        "transfer",
        "investment",
        "ring",
        "legal settlement",
        "gaming",
        "microtransactions",
        "equity",
        "deposit",
    ]

    results = []

    for row in rows:
        transaction_id = _read_value(row, "id")
        merchant = _clean_text(_read_value(row, "merchant", ""))
        description = _clean_text(_read_value(row, "description", ""))
        amount = abs(float(_read_value(row, "amount", 0.0) or 0.0))

        combined_text = f"{merchant} {description}".strip()

        keyword_hits = sum(
            1 for keyword in suspicious_keywords if keyword in combined_text
        )

        score = 0.0

        if amount >= 1000:
            score += 1.0
        if amount >= 3000:
            score += 1.0
        if amount >= 7000:
            score += 2.0
        if amount >= 15000:
            score += 2.0
        if amount >= 50000:
            score += 3.0

        if keyword_hits > 0:
            score += 2.0 + (0.5 * max(0, keyword_hits - 1))

        repeated_cash_like = (
            "atm" in combined_text
            or "withdrawal" in combined_text
            or "cash" in combined_text
            or "wire" in combined_text
            or "crypto" in combined_text
        )
        if repeated_cash_like and amount >= 1000:
            score += 1.5

        high_risk_combo = amount >= 3000 and keyword_hits > 0
        if high_risk_combo:
            score += 2.0

        is_anomaly = score >= 2.0

        results.append(
            AnomalyResult(
                transaction_id=transaction_id,
                anomaly_score=float(score),
                is_anomaly=is_anomaly,
            )
        )

    return results
