from __future__ import annotations

from typing import Optional

CATEGORY_LABELS = [
    "income",
    "groceries",
    "dining",
    "transport",
    "utilities",
    "housing",
    "health",
    "entertainment",
    "shopping",
    "education",
    "savings",
    "other",
]

MERCHANT_RULES = {
    "aldi": "groceries",
    "lidl": "groceries",
    "tesco": "groceries",
    "supervalu": "groceries",
    "dunnes": "groceries",
    "marks & spencer": "groceries",
    "m&s": "groceries",
    "starbucks": "dining",
    "costa": "dining",
    "mcdonald": "dining",
    "burger king": "dining",
    "subway": "dining",
    "deliveroo": "dining",
    "just eat": "dining",
    "uber eats": "dining",
    "irish rail": "transport",
    "luas": "transport",
    "dublin bus": "transport",
    "bus eireann": "transport",
    "uber": "transport",
    "free now": "transport",
    "electric ireland": "utilities",
    "bord gais": "utilities",
    "sse airtricity": "utilities",
    "eir": "utilities",
    "vodafone": "utilities",
    "three": "utilities",
    "netflix": "entertainment",
    "spotify": "entertainment",
    "steam": "entertainment",
    "playstation": "entertainment",
    "xbox": "entertainment",
    "cineworld": "entertainment",
    "omniplex": "entertainment",
    "boots": "health",
    "lloyds pharmacy": "health",
    "chemist": "health",
    "udemy": "education",
    "coursera": "education",
    "setu": "education",
    "amazon": "shopping",
    "ebay": "shopping",
    "asos": "shopping",
    "zara": "shopping",
    "ikea": "shopping",
}

DESCRIPTION_RULES = {
    "salary": "income",
    "payroll": "income",
    "wages": "income",
    "bonus": "income",
    "refund": "income",
    "interest": "income",
    "dividend": "income",
    "grocer": "groceries",
    "grocery": "groceries",
    "supermarket": "groceries",
    "coffee": "dining",
    "restaurant": "dining",
    "cafe": "dining",
    "lunch": "dining",
    "dinner": "dining",
    "breakfast": "dining",
    "fuel": "transport",
    "petrol": "transport",
    "diesel": "transport",
    "taxi": "transport",
    "train": "transport",
    "bus": "transport",
    "parking": "transport",
    "electric": "utilities",
    "gas bill": "utilities",
    "broadband": "utilities",
    "internet": "utilities",
    "mobile bill": "utilities",
    "rent": "housing",
    "landlord": "housing",
    "mortgage": "housing",
    "pharmacy": "health",
    "doctor": "health",
    "dentist": "health",
    "hospital": "health",
    "netflix": "entertainment",
    "spotify": "entertainment",
    "cinema": "entertainment",
    "game": "entertainment",
    "tuition": "education",
    "course": "education",
    "book": "education",
    "transfer to savings": "savings",
    "savings": "savings",
}


class TransactionCategoriser:
    def __init__(self) -> None:
        self._classifier = None
        self._classifier_attempted = False

    def normalise_category(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = str(value).strip().lower()
        return cleaned or None

    def categorise(
        self,
        description: Optional[str],
        merchant: Optional[str] = None,
    ) -> str:
        merchant_text = self._clean_text(merchant)
        description_text = self._clean_text(description)

        if not merchant_text and not description_text:
            return "other"

        rule_match = self._match_rules(merchant_text, description_text)
        if rule_match is not None:
            return rule_match

        hf_match = self._classify_with_huggingface(merchant_text, description_text)
        if hf_match is not None:
            return hf_match

        return "other"

    def _clean_text(self, value: Optional[str]) -> str:
        if value is None:
            return ""
        return str(value).strip().lower()

    def _match_rules(self, merchant_text: str, description_text: str) -> Optional[str]:
        for keyword, category in MERCHANT_RULES.items():
            if keyword in merchant_text:
                return category

        combined_text = f"{merchant_text} {description_text}".strip()
        for keyword, category in DESCRIPTION_RULES.items():
            if keyword in combined_text:
                return category

        return None

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

    def _classify_with_huggingface(
        self,
        merchant_text: str,
        description_text: str,
    ) -> Optional[str]:
        classifier = self._get_classifier()
        if classifier is None:
            return None

        text = f"{merchant_text} {description_text}".strip()
        if not text:
            return "other"

        try:
            result = classifier(text, CATEGORY_LABELS)
            labels = result.get("labels", [])
            if not labels:
                return None

            top_label = str(labels[0]).strip().lower()
            if top_label in CATEGORY_LABELS:
                return top_label
        except Exception:
            return None

        return None


categoriser = TransactionCategoriser()
