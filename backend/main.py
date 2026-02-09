from datetime import date
from decimal import Decimal
from typing import List
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from .db import SessionLocal
from . import models, schemas, auth
import io
import pandas as pd
from fastapi import UploadFile, File

print("LOADING BACKEND FROM", __file__)

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


@app.on_event("startup")
def _print_routes() -> None:
    print("ROUTES LOADED:")
    for r in app.routes:
        path = getattr(r, "path", None)
        methods = getattr(r, "methods", None)
        if path:
            print(f"  {path}  {sorted(list(methods)) if methods else ''}")


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


@app.get("/transactions", response_model=List[schemas.TransactionOut])
def list_transactions(db: Session = Depends(get_db)):
    rows = db.query(models.Transaction).order_by(models.Transaction.date).all()

    result = []
    for row in rows:
        result.append(
            schemas.TransactionOut(
                transaction_id=getattr(row, "transaction_id", None),
                date=row.date.isoformat(),
                description=row.description,
                merchant=getattr(row, "merchant", None),
                category=getattr(row, "category", None),
                amount=float(row.amount),
                balance=(
                    float(row.balance)
                    if getattr(row, "balance", None) is not None
                    else None
                ),
                currency=getattr(row, "currency", None),
                user_id=getattr(row, "user_id", None),
            )
        )

    return result


@app.post("/transactions/upload")
def upload_transactions_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    print("HIT /transactions/upload", file.filename)

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files supported")

    contents = file.file.read()

    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid CSV file")

    required = {"date", "description", "amount"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {sorted(list(missing))}",
        )

    inserted = 0
    errors = []

    for i, row in df.iterrows():
        try:
            parsed_date = pd.to_datetime(row.get("date"), errors="coerce")
            if pd.isna(parsed_date):
                raise ValueError("Invalid date")

            amount = row.get("amount")
            if amount is None or (isinstance(amount, float) and pd.isna(amount)):
                raise ValueError("Invalid amount")

            txn = models.Transaction(
                transaction_id=row.get("transaction_id"),
                date=parsed_date.date(),
                description=row.get("description"),
                merchant=row.get("merchant"),
                category=row.get("category"),
                amount=amount,
                balance=row.get("balance"),
                currency=row.get("currency"),
                user_id=1,
            )

            db.add(txn)
            inserted += 1

        except Exception as e:
            errors.append({"row": int(i), "error": str(e)})

    db.commit()
    return {"inserted": inserted, "errors": errors}


@app.post("/login", response_model=schemas.LoginResponse)
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not auth.verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return schemas.LoginResponse(success=True, message="Login successful")
