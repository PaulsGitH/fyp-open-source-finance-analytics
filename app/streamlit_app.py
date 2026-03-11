import os
import json
import math

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

st.set_page_config(page_title="FYP Finance", layout="wide")

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_BASE = f"http://{API_HOST}:{API_PORT}"


CATEGORIES = [
    "income",
    "housing",
    "groceries",
    "dining",
    "transport",
    "utilities",
    "education",
    "entertainment",
    "health",
    "shopping",
    "savings",
    "other",
    "system",
]


def _auth_headers():
    email = st.session_state.get("user_email")
    if not email:
        return {}
    return {"X-User-Email": email}


def _safe_balance_text(value):
    if value is None:
        return ""
    try:
        numeric = float(value)
        if math.isnan(numeric):
            return ""
        return f"€{numeric:,.2f}"
    except Exception:
        return ""


def update_category(transaction_id, new_category):
    r = requests.patch(
        f"{API_BASE}/transactions/{transaction_id}/category",
        headers=_auth_headers(),
        json={"category": new_category},
        timeout=10,
    )
    return r.ok


def upload_csv_to_backend(uploaded_file):
    file_bytes = uploaded_file.getvalue()

    files = {
        "file": (uploaded_file.name, file_bytes, "text/csv"),
    }

    r = requests.post(
        f"{API_BASE}/transactions/upload",
        files=files,
        headers=_auth_headers(),
        timeout=120,
    )

    if r.ok:
        body = r.json()
        inserted = body.get("inserted", 0)
        skipped = body.get("skipped", 0)
        categorised = body.get("categorised", 0)

        return (
            True,
            f"CSV uploaded successfully. Inserted {inserted}. Skipped {skipped}. Categorised {categorised}.",
        )

    return False, f"Upload failed {r.status_code}"


def show_dashboard():
    st.title("Open Source Finance Analytics")
    account_type = st.session_state.get("account_type", "Personal")
    st.caption(f"Active account: {account_type}")

    if "flash_msg" not in st.session_state:
        st.session_state.flash_msg = None

    if st.session_state.flash_msg:
        st.success(st.session_state.flash_msg)
        st.session_state.flash_msg = None

    st.subheader("Upload CSV")

    uploaded = st.file_uploader("Choose a CSV file", type=["csv"])

    if st.button("Upload selected CSV"):
        if uploaded is None:
            st.error("Please choose a file first")
        else:
            ok, msg = upload_csv_to_backend(uploaded)
            if ok:
                st.session_state.flash_msg = msg
                st.rerun()
            else:
                st.error(msg)

    st.subheader("Filters")

    col1, col2, col3 = st.columns(3)

    start_date = col1.date_input("Start date", value=None)
    end_date = col2.date_input("End date", value=None)
    kind = col3.selectbox("Type", ["all", "income", "expense"])

    params = {"kind": kind}

    if start_date:
        params["start_date"] = start_date.isoformat()

    if end_date:
        params["end_date"] = end_date.isoformat()

    r = requests.get(
        f"{API_BASE}/transactions",
        headers=_auth_headers(),
        params=params,
        timeout=10,
    )

    if not r.ok:
        st.error("Failed to load transactions")
        return

    rows = r.json()

    if not rows:
        st.info("No transactions found")
        return

    df = pd.DataFrame(rows)

    st.subheader("Transactions")

    header_cols = st.columns([2, 4, 3, 3, 3, 3, 3])
    header_cols[0].write("Date")
    header_cols[1].write("Details")
    header_cols[2].write("Category")
    header_cols[3].write("Flag")
    header_cols[4].write("Money In")
    header_cols[5].write("Money Out")
    header_cols[6].write("Balance")

    for _, row in df.iterrows():
        cols = st.columns([2, 4, 3, 3, 3, 3, 3])

        date = row["date"]
        details = row["merchant"] or row["description"]
        category = row["category"] or "other"
        amount = float(row["amount"])
        balance = row["balance"]
        txn_id = row["id"]
        is_anomaly = bool(row.get("is_anomaly", False))
        anomaly_score = row.get("anomaly_score", None)

        money_in = f"€{amount:,.2f}" if amount > 0 else "€0.00"
        money_out = f"€{abs(amount):,.2f}" if amount < 0 else "€0.00"

        cols[0].write(date)
        cols[1].write(details)

        new_category = cols[2].selectbox(
            "Category",
            CATEGORIES,
            index=CATEGORIES.index(category) if category in CATEGORIES else 0,
            key=f"cat_{txn_id}",
            label_visibility="collapsed",
        )

        if new_category != category:
            if update_category(txn_id, new_category):
                st.session_state.flash_msg = "Category updated"
                st.rerun()

        if is_anomaly:
            if anomaly_score is not None:
                cols[3].write(f"⚠ Anomaly ({anomaly_score:.3f})")
            else:
                cols[3].write("⚠ Anomaly")
        else:
            cols[3].write("Normal")

        cols[4].write(money_in)
        cols[5].write(money_out)
        cols[6].write(_safe_balance_text(balance))

    anomaly_count = int(df["is_anomaly"].fillna(False).astype(bool).sum())
    if anomaly_count > 0:
        st.warning(
            f"{anomaly_count} unusual transaction(s) detected in the current view."
        )

    r = requests.get(
        f"{API_BASE}/transactions/summary",
        headers=_auth_headers(),
        params=params,
        timeout=10,
    )

    if not r.ok:
        st.error("Failed to load summary")
        return

    summary = r.json()

    st.subheader("Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric("Money in", f"€{summary['income']:,.2f}")
    col2.metric("Money out", f"€{summary['expenses']:,.2f}")
    col3.metric("Net change", f"€{summary['net']:,.2f}")


def show_login():
    st.title("FYP Finance login")

    account_type = st.radio(
        "Account type",
        ["Personal", "Business"],
        horizontal=True,
    )

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Log in"):

        if account_type == "Personal":
            email = email or "demo@example.com"
        else:
            email = email or "business@example.com"

        payload = {"email": email, "password": password}

        r = requests.post(
            f"{API_BASE}/login",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=5,
        )

        if not r.ok:
            st.error("Login failed")
            return

        body = r.json()

        if body.get("success"):
            st.session_state.authenticated = True
            st.session_state.user_email = email
            st.session_state.account_type = account_type
            st.rerun()
        else:
            st.error(body.get("message"))


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_email = None

if not st.session_state.authenticated:
    show_login()
else:
    show_dashboard()
