from __future__ import annotations

from typing import Optional

CATEGORY_LABELS = [
    "income",
    "salary",
    "bonus",
    "refund",
    "interest",
    "dividend",
    "investment return",
    "sales revenue",
    "client payments",
    "contract income",
    "grant income",
    "loan received",
    "capital injection",
    "housing",
    "rent",
    "mortgage",
    "groceries",
    "dining",
    "coffee",
    "transport",
    "fuel",
    "public transport",
    "parking",
    "utilities",
    "electricity",
    "gas",
    "water",
    "internet",
    "phone",
    "education",
    "entertainment",
    "streaming",
    "gaming",
    "health",
    "medical",
    "fitness",
    "shopping",
    "clothing",
    "travel",
    "insurance",
    "subscriptions",
    "charity",
    "family",
    "gifts",
    "savings",
    "cash withdrawal",
    "payroll",
    "contractor payments",
    "employee benefits",
    "tax payments",
    "vat",
    "corporation tax",
    "accounting fees",
    "legal fees",
    "consulting fees",
    "bank fees",
    "payment processor fees",
    "software subscriptions",
    "saas tools",
    "cloud infrastructure",
    "hosting",
    "domains",
    "office supplies",
    "office rent",
    "coworking",
    "equipment purchase",
    "hardware",
    "software",
    "inventory",
    "supplier payments",
    "raw materials",
    "manufacturing costs",
    "shipping",
    "logistics",
    "delivery",
    "marketing",
    "advertising",
    "customer acquisition",
    "sales commission",
    "research and development",
    "training",
    "travel business",
    "meals business",
    "insurance business",
    "maintenance",
    "repairs",
    "licensing",
    "compliance",
    "professional services",
    "merchant services",
    "chargeback",
    "refund issued",
    "other",
    "system",
]

MERCHANT_RULES = {
    "aldi": "groceries",
    "lidl": "groceries",
    "tesco": "groceries",
    "supervalu": "groceries",
    "dunnes": "groceries",
    "marks & spencer": "groceries",
    "m&s": "groceries",
    "starbucks": "coffee",
    "costa": "coffee",
    "mcdonald": "dining",
    "burger king": "dining",
    "subway": "dining",
    "deliveroo": "dining",
    "just eat": "dining",
    "uber eats": "dining",
    "irish rail": "public transport",
    "luas": "public transport",
    "dublin bus": "public transport",
    "bus eireann": "public transport",
    "uber": "transport",
    "free now": "transport",
    "circle k": "fuel",
    "apple green": "fuel",
    "topaz": "fuel",
    "electric ireland": "electricity",
    "bord gais": "gas",
    "sse airtricity": "utilities",
    "eir": "internet",
    "vodafone": "phone",
    "three": "phone",
    "virgin media": "internet",
    "netflix": "streaming",
    "spotify": "streaming",
    "steam": "gaming",
    "playstation": "gaming",
    "xbox": "gaming",
    "cineworld": "entertainment",
    "omniplex": "entertainment",
    "boots": "medical",
    "lloyds pharmacy": "medical",
    "chemist": "medical",
    "udemy": "training",
    "coursera": "training",
    "setu": "education",
    "amazon": "shopping",
    "ebay": "shopping",
    "asos": "clothing",
    "zara": "clothing",
    "ikea": "office supplies",
    "aws": "cloud infrastructure",
    "amazon web services": "cloud infrastructure",
    "azure": "cloud infrastructure",
    "google cloud": "cloud infrastructure",
    "digitalocean": "cloud infrastructure",
    "hetzner": "hosting",
    "cloudflare": "hosting",
    "namecheap": "domains",
    "godaddy": "domains",
    "stripe": "payment processor fees",
    "paypal": "payment processor fees",
    "quickbooks": "accounting fees",
    "xero": "accounting fees",
    "sage": "accounting fees",
    "zoom": "software subscriptions",
    "notion": "software subscriptions",
    "slack": "software subscriptions",
    "atlassian": "software subscriptions",
    "jira": "software subscriptions",
    "figma": "software subscriptions",
    "canva": "software subscriptions",
    "github": "software subscriptions",
    "openai": "software subscriptions",
    "google ads": "advertising",
    "meta ads": "advertising",
    "linkedin ads": "advertising",
    "office depot": "office supplies",
    "viking direct": "office supplies",
    "dell": "hardware",
    "lenovo": "hardware",
    "hp": "hardware",
    "apple": "hardware",
    "intel": "hardware",
    "microsoft": "software",
    "adobe": "software",
    "shopify": "saas tools",
    "hubspot": "saas tools",
    "salesforce": "saas tools",
    "mailchimp": "marketing",
    "dhl": "shipping",
    "ups": "shipping",
    "fedex": "shipping",
    "dpd": "delivery",
    "an post": "delivery",
    "revenue": "tax payments",
    "inspector of taxes": "tax payments",
    "companies registration office": "compliance",
    "cro": "compliance",
    "legal": "legal fees",
    "solicitor": "legal fees",
    "accountant": "accounting fees",
    "consulting": "consulting fees",
    "contractor": "contractor payments",
    "freelancer": "contractor payments",
    "landlord": "office rent",
    "wework": "coworking",
}

DESCRIPTION_RULES = {
    "salary": "salary",
    "payroll": "payroll",
    "wages": "payroll",
    "bonus": "bonus",
    "refund": "refund",
    "interest": "interest",
    "dividend": "dividend",
    "investment return": "investment return",
    "sales revenue": "sales revenue",
    "client payment": "client payments",
    "contract income": "contract income",
    "grant": "grant income",
    "loan received": "loan received",
    "capital injection": "capital injection",
    "grocer": "groceries",
    "grocery": "groceries",
    "supermarket": "groceries",
    "restaurant": "dining",
    "cafe": "coffee",
    "coffee": "coffee",
    "lunch": "dining",
    "dinner": "dining",
    "breakfast": "dining",
    "fuel": "fuel",
    "petrol": "fuel",
    "diesel": "fuel",
    "train": "public transport",
    "bus": "public transport",
    "parking": "parking",
    "taxi": "transport",
    "electric": "electricity",
    "gas bill": "gas",
    "water bill": "water",
    "broadband": "internet",
    "internet": "internet",
    "mobile bill": "phone",
    "phone bill": "phone",
    "rent": "rent",
    "mortgage": "mortgage",
    "insurance": "insurance",
    "pharmacy": "medical",
    "doctor": "medical",
    "dentist": "medical",
    "hospital": "medical",
    "gym": "fitness",
    "streaming": "streaming",
    "gaming": "gaming",
    "cinema": "entertainment",
    "tuition": "education",
    "course": "training",
    "book": "education",
    "transfer to savings": "savings",
    "savings": "savings",
    "atm withdrawal": "cash withdrawal",
    "cash withdrawal": "cash withdrawal",
    "employee benefits": "employee benefits",
    "vat": "vat",
    "corporation tax": "corporation tax",
    "tax payment": "tax payments",
    "accounting fee": "accounting fees",
    "legal fee": "legal fees",
    "consulting fee": "consulting fees",
    "bank fee": "bank fees",
    "processing fee": "payment processor fees",
    "software subscription": "software subscriptions",
    "saas": "saas tools",
    "cloud": "cloud infrastructure",
    "hosting": "hosting",
    "domain": "domains",
    "office supplies": "office supplies",
    "office rent": "office rent",
    "coworking": "coworking",
    "equipment": "equipment purchase",
    "hardware": "hardware",
    "software": "software",
    "inventory": "inventory",
    "supplier payment": "supplier payments",
    "raw materials": "raw materials",
    "manufacturing": "manufacturing costs",
    "shipping": "shipping",
    "logistics": "logistics",
    "delivery": "delivery",
    "marketing": "marketing",
    "advertising": "advertising",
    "customer acquisition": "customer acquisition",
    "sales commission": "sales commission",
    "research": "research and development",
    "development": "research and development",
    "training": "training",
    "business travel": "travel business",
    "business meal": "meals business",
    "business insurance": "insurance business",
    "maintenance": "maintenance",
    "repair": "repairs",
    "licence": "licensing",
    "license": "licensing",
    "compliance": "compliance",
    "professional services": "professional services",
    "merchant services": "merchant services",
    "chargeback": "chargeback",
    "refund issued": "refund issued",
    "account opening": "system",
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
