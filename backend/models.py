from sqlalchemy import Column, Integer, Date, Numeric, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from .db import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    transaction_id = Column(String, nullable=True)
    date = Column(Date, nullable=True)
    description = Column(String, nullable=True)
    merchant = Column(String, nullable=True)
    category = Column(String, nullable=True)

    amount = Column(Numeric(12, 2), nullable=True)
    balance = Column(Numeric(12, 2), nullable=True)

    currency = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
