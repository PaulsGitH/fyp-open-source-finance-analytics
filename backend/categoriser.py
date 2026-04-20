from __future__ import annotations

from typing import Optional

CATEGORY_LABELS = [  # Fixed category set to keep outputs consistent across the system
    "Food & Dining",
    "Groceries",
    "Transportation",
    "Fuel",
    "Shopping & Retail",
    "Entertainment & Recreation",
    "Subscriptions",
    "Healthcare & Medical",
    "Utilities & Services",
    "Financial Services",
    "Income",
    "Government & Legal",
    "Charity & Donations",
    "Education",
    "Travel",
    "Housing",
]

EXPENSE_CATEGORY_LABELS = [
    label for label in CATEGORY_LABELS if label != "Income"
]  # Exclude Income so expense classification only targets spending categories

HIGH_CONFIDENCE_CATEGORY_RULES = (
    {  # Handle common transaction patterns with rules before using ML
        "Subscriptions": [
            "netflix",
            "spotify",
            "disney+",
            "disney plus",
            "prime video",
            "apple music",
            "youtube premium",
            "paramount+",
            "paramount plus",
            "tidal",
            "deezer",
            "chatgpt",
            "openai subscription",
            "adobe subscription",
            "microsoft 365",
            "office 365",
            "icloud",
            "google one",
            "patreon",
            "google workspace",
            "workspace subscription",
            "gsuite",
            "jira software subscription",
            "atlassian jira",
        ],
        "Utilities & Services": [
            "electric ireland",
            "bord gais",
            "sse airtricity",
            "eir",
            "vodafone",
            "three",
            "virgin media",
            "sky",
            "broadband",
            "internet",
            "wifi",
            "mobile bill",
            "phone bill",
            "electricity",
            "gas bill",
            "water bill",
            "utility bill",
            "prepay power",
            "pinergy",
            "aws cloud hosting",
            "cloud hosting services",
            "hosting services",
        ],
        "Housing": [
            "rent",
            "mortgage",
            "landlord",
            "property management",
            "letting",
            "lease payment",
            "office rent",
            "commercial rent",
            "apartment",
            "tenancy",
            "rental",
        ],
        "Shopping & Retail": [
            "viking direct",
            "office supplies",
            "office equipment",
            "office furniture",
            "amazon business",
            "ikea ireland",
            "meta ads",
            "facebook ads",
            "instagram ads",
            "ads campaign",
            "marketing spend",
        ],
        "Financial Services": [
            "stripe payment processing fee",
            "payment processing fee",
            "contractor payment",
            "frontend developer",
            "backend developer",
            "software developer",
            "full stack developer",
            "ux designer",
            "developer payment",
            "consultant",
            "freelancer",
        ],
    }
)


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

    def _match_high_confidence_category(
        self,
        description: Optional[str],
        merchant: Optional[str] = None,
        amount: Optional[float] = None,
    ) -> Optional[str]:
        try:
            if (
                amount is not None and float(amount) > 0
            ):  # Treat positive amounts as Income to avoid incorrect expense classification
                return "Income"
        except Exception:
            pass

        text = self._build_text(
            description=description, merchant=merchant
        ).lower()  # Combine merchant and description to improve matching context

        if any(  # Prioritise housing keywords to avoid misclassification of rent-related transactions
            keyword in text
            for keyword in [
                "rent",
                "mortgage",
                "apartment",
                "landlord",
                "lease",
                "tenancy",
                "rental",
                "office rent",
                "commercial rent",
            ]
        ):
            return "Housing"

        if not text:
            return None

        for category, keywords in HIGH_CONFIDENCE_CATEGORY_RULES.items():
            for keyword in keywords:
                if keyword in text:
                    return category

        return None

    def categorise(
        self,
        description: Optional[str],
        merchant: Optional[str] = None,
        amount: Optional[float] = None,
    ) -> str:
        high_confidence_match = self._match_high_confidence_category(  # Apply rule-based categorisation before fallback to ML
            description=description,
            merchant=merchant,
            amount=amount,
        )
        if high_confidence_match is not None:
            return high_confidence_match

        text = self._build_text(description=description, merchant=merchant)

        if not text:
            return "Financial Services"

        classifier = (
            self._get_classifier()
        )  # Use zero-shot model only for transactions not handled by rules
        if classifier is None:
            return "Shopping & Retail"

        try:
            result = classifier(  # Rank text against predefined categories to keep predictions controlled
                text,
                EXPENSE_CATEGORY_LABELS,
                hypothesis_template="This bank transaction belongs to the category {}.",
            )
            labels = result.get("labels", [])
            if not labels:
                return "Shopping & Retail"

            predicted = str(labels[0]).strip()
            cleaned = self.normalise_category(predicted)
            return cleaned or "Financial Services"
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
        if (
            self._classifier_attempted
        ):  # Load and cache model once to avoid repeated initialisation
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
