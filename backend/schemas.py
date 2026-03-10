from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


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


class TransactionBase(BaseModel):
    txn_date: date
    description: str
    amount: Decimal
    category: str | None = None
    source: str | None = None


class TransactionDB(TransactionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str


class TransactionOut(BaseModel):
    id: int | None = None
    transaction_id: str | None = None
    date: Optional[str] = None
    description: str
    merchant: str | None = None
    category: str | None = None
    amount: float
    balance: float | None = None
    currency: str | None = None
    user_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class UploadResponse(BaseModel):
    inserted: int
    skipped: int
    categorised: int
    errors: list[dict]


class CategoryBreakdownItem(BaseModel):
    category: str
    count: int


class CategoryUpdateRequest(BaseModel):
    category: str


class CategoryUpdateResponse(BaseModel):
    id: int
    category: str


class TransactionAnomalyOut(BaseModel):
    id: int | None = None
    date: Optional[str] = None
    description: str
    merchant: str | None = None
    category: str | None = None
    amount: float
    anomaly_score: float
    is_anomaly: bool
