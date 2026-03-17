from __future__ import annotations

from typing import Optional

CATEGORY_LABELS = [
    "Food & Dining",
    "Transportation",
    "Shopping & Retail",
    "Entertainment & Recreation",
    "Healthcare & Medical",
    "Utilities & Services",
    "Financial Services",
    "Income",
    "Government & Legal",
    "Charity & Donations",
]

EXPENSE_CATEGORY_LABELS = [label for label in CATEGORY_LABELS if label != "Income"]


class TransactionCategoriser:
    def __init__(self) -> None:
        self._classifier = None
        self._classifier_attempted = False

    def normalise_category(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        cleaned = str(value).strip().lower()
        category_map = {label.lower(): label for label in CATEGORY_LABELS}
        return category_map.get(cleaned)

    def categorise(
        self,
        description: Optional[str],
        merchant: Optional[str] = None,
        amount: Optional[float] = None,
    ) -> str:
        try:
            if amount is not None and float(amount) > 0:
                return "Income"
        except Exception:
            pass

        text = self._build_text(description=description, merchant=merchant)

        if not text:
            return "Financial Services"

        classifier = self._get_classifier()
        if classifier is None:
            return "Shopping & Retail"

        try:
            result = classifier(
                text,
                EXPENSE_CATEGORY_LABELS,
                hypothesis_template="This bank transaction belongs to the category {}.",
            )
            labels = result.get("labels", [])
            if not labels:
                return "Shopping & Retail"

            return str(labels[0]).strip()
        except Exception:
            return "Shopping & Retail"

    def _build_text(
        self,
        description: Optional[str],
        merchant: Optional[str],
    ) -> str:
        parts = []

        merchant_text = self._clean_text(merchant)
        description_text = self._clean_text(description)

        if merchant_text:
            parts.append(f"merchant: {merchant_text}")

        if description_text:
            parts.append(f"description: {description_text}")

        return " | ".join(parts).strip()

    def _clean_text(self, value: Optional[str]) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _get_classifier(self):
        if self._classifier_attempted:
            return self._classifier

        self._classifier_attempted = True

        try:
            from transformers import pipeline

            self._classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
            )
        except Exception:
            self._classifier = None

        return self._classifier


categoriser = TransactionCategoriser()
