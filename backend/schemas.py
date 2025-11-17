from pydantic import BaseModel
from typing import List

class Transaction(BaseModel):
    date: str
    description: str
    amount: float

class SummaryRequest(BaseModel):
    transactions: List[Transaction]

class SummaryResponse(BaseModel):
    income: float
    expenses: float
    net: float
