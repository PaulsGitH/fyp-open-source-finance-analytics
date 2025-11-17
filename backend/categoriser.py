from typing import Iterable

KEYWORDS = {
    "salary": "income",
    "payroll": "income",
    "rent": "fixed",
    "subscription": "fixed",
    "coffee": "variable",
    "groceries": "variable",
}

def label(description: str) -> str:
    s = description.lower()
    for k, v in KEYWORDS.items():
        if k in s:
            return v
    return "unknown"

def count_labels(descriptions: Iterable[str]) -> dict:
    counts = {"income": 0, "fixed": 0, "variable": 0, "unknown": 0}
    for d in descriptions:
        counts[label(d)] += 1
    return counts
