from datetime import date
from decimal import Decimal
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from .db import SessionLocal
from . import models, schemas, auth


app = FastAPI(
    title="FYP Finance API",
    version="0.2.0",
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/summary", response_model=schemas.SummaryResponse)
def calculate_summary(payload: schemas.SummaryRequest):
    income = Decimal("0")
    expenses = Decimal("0")

    for txn in payload.transactions:
        if txn.amount >= 0:
            income += Decimal(str(txn.amount))
        else:
            expenses += Decimal(str(abs(txn.amount)))

    net = income - expenses
    return schemas.SummaryResponse(
        income=float(income),
        expenses=float(expenses),
        net=float(net),
    )


@app.get("/transactions", response_model=List[schemas.Transaction])
def list_transactions(db: Session = Depends(get_db)):
    rows = db.query(models.Transaction).order_by(models.Transaction.date).all()

    result: List[schemas.Transaction] = []
    for row in rows:
        result.append(
            schemas.Transaction(
                date=row.date.isoformat() if isinstance(row.date, date) else str(row.date),
                description=row.description,
                amount=float(row.amount),
            )
        )
    return result


@app.post("/login", response_model=schemas.LoginResponse)
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not auth.verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return schemas.LoginResponse(success=True, message="Login successful")
