from datetime import date
from decimal import Decimal
from typing import List, Optional

import io
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from .db import SessionLocal
from . import models, schemas, auth
from .categoriser import categoriser
from .anomaly import score_transactions


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


def get_current_user(
    db: Session = Depends(get_db),
    x_user_email: Optional[str] = Header(default=None),
) -> models.User:
    if not x_user_email:
        raise HTTPException(status_code=401, detail="Missing X-User-Email")

    user = db.query(models.User).filter(models.User.email == x_user_email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid user")

    return user


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
def list_transactions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    kind: str = Query(default="all", pattern="^(all|income|expense)$"),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")

    q = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    )

    if start_date is not None:
        q = q.filter(models.Transaction.date >= start_date)
    if end_date is not None:
        q = q.filter(models.Transaction.date <= end_date)

    if kind == "income":
        q = q.filter(models.Transaction.amount > 0)
    elif kind == "expense":
        q = q.filter(models.Transaction.amount < 0)

    rows = q.order_by(models.Transaction.date).all()

    result = []
    for row in rows:
        result.append(
            schemas.TransactionOut(
                id=getattr(row, "id", None),
                transaction_id=getattr(row, "transaction_id", None),
                date=row.date.isoformat() if row.date is not None else None,
                description=row.description or "",
                merchant=getattr(row, "merchant", None),
                category=getattr(row, "category", None),
                amount=float(row.amount) if row.amount is not None else 0.0,
                balance=float(row.balance) if row.balance is not None else None,
                currency=getattr(row, "currency", None),
                anomaly_score=getattr(row, "anomaly_score", None),
                is_anomaly=getattr(row, "is_anomaly", None),
                user_id=getattr(row, "user_id", None),
            )
        )

    return result


@app.get("/transactions/summary", response_model=schemas.SummaryResponse)
def transactions_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    kind: str = Query(default="all", pattern="^(all|income|expense)$"),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")

    q = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    )

    if start_date is not None:
        q = q.filter(models.Transaction.date >= start_date)
    if end_date is not None:
        q = q.filter(models.Transaction.date <= end_date)

    if kind == "income":
        q = q.filter(models.Transaction.amount > 0)
    elif kind == "expense":
        q = q.filter(models.Transaction.amount < 0)

    income_expr = func.coalesce(
        func.sum(
            case(
                (models.Transaction.amount > 0, models.Transaction.amount),
                else_=0,
            )
        ),
        0,
    )

    expenses_expr = func.coalesce(
        func.sum(
            case(
                (models.Transaction.amount < 0, -models.Transaction.amount),
                else_=0,
            )
        ),
        0,
    )

    income_val, expenses_val = q.with_entities(income_expr, expenses_expr).one()

    income = Decimal(str(income_val))
    expenses = Decimal(str(expenses_val))
    net = income - expenses

    return schemas.SummaryResponse(
        income=float(income),
        expenses=float(expenses),
        net=float(net),
    )


@app.get(
    "/transactions/category-breakdown",
    response_model=List[schemas.CategoryBreakdownItem],
)
def transaction_category_breakdown(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")

    q = db.query(
        models.Transaction.category,
        func.count(models.Transaction.id),
    ).filter(
        models.Transaction.user_id == current_user.id,
        models.Transaction.category.is_not(None),
    )

    if start_date is not None:
        q = q.filter(models.Transaction.date >= start_date)
    if end_date is not None:
        q = q.filter(models.Transaction.date <= end_date)

    rows = (
        q.group_by(models.Transaction.category)
        .order_by(func.count(models.Transaction.id).desc(), models.Transaction.category)
        .all()
    )

    result = []
    for category, count in rows:
        result.append(
            schemas.CategoryBreakdownItem(
                category=category,
                count=count,
            )
        )

    return result


@app.get(
    "/transactions/anomalies",
    response_model=List[schemas.TransactionAnomalyOut],
)
def list_transaction_anomalies(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    kind: str = Query(default="all", pattern="^(all|income|expense)$"),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")

    q = db.query(models.Transaction).filter(
        models.Transaction.user_id == current_user.id
    )

    if start_date is not None:
        q = q.filter(models.Transaction.date >= start_date)
    if end_date is not None:
        q = q.filter(models.Transaction.date <= end_date)

    if kind == "income":
        q = q.filter(models.Transaction.amount > 0)
    elif kind == "expense":
        q = q.filter(models.Transaction.amount < 0)

    rows = q.order_by(models.Transaction.date).all()
    anomaly_results = score_transactions(rows)

    score_map = {item.transaction_id: item for item in anomaly_results}

    result = []
    for row in rows:
        anomaly = score_map.get(getattr(row, "id", None))
        result.append(
            schemas.TransactionAnomalyOut(
                id=getattr(row, "id", None),
                date=row.date.isoformat() if row.date is not None else None,
                description=row.description or "",
                merchant=getattr(row, "merchant", None),
                category=getattr(row, "category", None),
                amount=float(row.amount) if row.amount is not None else 0.0,
                anomaly_score=anomaly.anomaly_score if anomaly else 0.0,
                is_anomaly=anomaly.is_anomaly if anomaly else False,
            )
        )

    return result


@app.post("/transactions/upload", response_model=schemas.UploadResponse)
def upload_transactions_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
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

    user_id = current_user.id

    df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce").dt.date

    txn_ids = set(
        str(x).strip()
        for x in df.get("transaction_id", pd.Series([])).dropna().tolist()
        if str(x).strip()
    )

    existing_ids = set()
    if txn_ids:
        rows = (
            db.query(models.Transaction.transaction_id)
            .filter(
                models.Transaction.user_id == user_id,
                models.Transaction.transaction_id.in_(list(txn_ids)),
            )
            .all()
        )
        existing_ids = {r[0] for r in rows if r[0]}

    inserted = 0
    skipped = 0
    categorised = 0
    errors = []

    for i, row in df.iterrows():
        try:
            parsed_date = row.get("date_parsed")
            if parsed_date is None or pd.isna(parsed_date):
                raise ValueError("Invalid date")

            amount = row.get("amount")
            if amount is None or (isinstance(amount, float) and pd.isna(amount)):
                raise ValueError("Invalid amount")

            txn_id = row.get("transaction_id")
            txn_id = (
                str(txn_id).strip()
                if txn_id is not None and str(txn_id).strip()
                else None
            )

            if txn_id and txn_id in existing_ids:
                skipped += 1
                continue

            if not txn_id:
                exists = (
                    db.query(models.Transaction.id)
                    .filter(
                        models.Transaction.user_id == user_id,
                        models.Transaction.date == parsed_date,
                        models.Transaction.description == row.get("description"),
                        models.Transaction.amount == amount,
                        models.Transaction.balance == row.get("balance"),
                    )
                    .first()
                )
                if exists:
                    skipped += 1
                    continue

            raw_category = categoriser.normalise_category(row.get("category"))

            if raw_category is None:
                raw_category = categoriser.categorise(
                    description=row.get("description"),
                    merchant=row.get("merchant"),
                )
                categorised += 1

            txn = models.Transaction(
                transaction_id=txn_id,
                date=parsed_date,
                description=row.get("description"),
                merchant=row.get("merchant"),
                category=raw_category,
                amount=amount,
                balance=row.get("balance"),
                currency=row.get("currency"),
                user_id=user_id,
            )

            db.add(txn)
            inserted += 1

            if txn_id:
                existing_ids.add(txn_id)

        except Exception as e:
            errors.append({"row": int(i), "error": str(e)})

    db.commit()

    # recompute anomalies for this user
    rows = (
        db.query(models.Transaction).filter(models.Transaction.user_id == user_id).all()
    )

    results = score_transactions(rows)

    for result in results:
        txn = (
            db.query(models.Transaction)
            .filter(models.Transaction.id == result.transaction_id)
            .first()
        )
    if txn:
        txn.anomaly_score = result.anomaly_score
        txn.is_anomaly = result.is_anomaly

    db.commit()

    return schemas.UploadResponse(
        inserted=inserted,
        skipped=skipped,
        categorised=categorised,
        errors=errors,
    )


@app.patch(
    "/transactions/{transaction_id}/category",
    response_model=schemas.CategoryUpdateResponse,
)
def update_transaction_category(
    transaction_id: int,
    payload: schemas.CategoryUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    txn = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.id == transaction_id,
            models.Transaction.user_id == current_user.id,
        )
        .first()
    )

    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    new_category = payload.category.strip().lower()

    if not new_category:
        raise HTTPException(status_code=400, detail="Category cannot be empty")

    txn.category = new_category

    db.commit()
    db.refresh(txn)

    return schemas.CategoryUpdateResponse(
        id=txn.id,
        category=txn.category,
    )


@app.post("/login", response_model=schemas.LoginResponse)
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not auth.verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return schemas.LoginResponse(success=True, message="Login successful")
