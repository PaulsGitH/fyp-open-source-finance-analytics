from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel
from pydantic import ConfigDict


# Existing summary models for the hello world prototype

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


# New models for the PostgreSQL backed transactions API

class TransactionBase(BaseModel):
    txn_date: date
    description: str
    amount: Decimal
    category: str | None = None
    source: str | None = None


class TransactionDB(TransactionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str

class TransactionOut(BaseModel):
    transaction_id: str | None = None
    date: str
    description: str
    merchant: str | None = None
    category: str | None = None
    amount: float
    balance: float | None = None
    currency: str | None = None
    user_id: int | None = None

    model_config = ConfigDict(from_attributes=True)