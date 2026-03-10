from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Numeric,
    ForeignKey,
    Float,
    Boolean,
)
from sqlalchemy.orm import relationship
from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    transactions = relationship("Transaction", back_populates="user")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    transaction_id = Column(String, nullable=True, index=True)

    date = Column(Date, index=True)
    description = Column(String, nullable=False)
    merchant = Column(String, nullable=True)

    category = Column(String, nullable=True)

    amount = Column(Numeric, nullable=False)
    balance = Column(Numeric, nullable=True)

    currency = Column(String, nullable=True)

    anomaly_score = Column(Float, nullable=True)
    is_anomaly = Column(Boolean, default=False)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="transactions")
