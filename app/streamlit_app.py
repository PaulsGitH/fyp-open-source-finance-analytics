import os
import json

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


def update_category(transaction_id, new_category):

    r = requests.patch(
        f"{API_BASE}/transactions/{transaction_id}/category",
        headers=_auth_headers(),
        json={"category": new_category},
        timeout=10,
    )

    if r.ok:
        return True
    return False


def upload_csv_to_backend(uploaded_file):

    file_bytes = uploaded_file.getvalue()

    files = {
        "file": (uploaded_file.name, file_bytes, "text/csv"),
    }

    r = requests.post(
        f"{API_BASE}/transactions/upload",
        files=files,
        headers=_auth_headers(),
        timeout=30,
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

    if "flash_msg" not in st.session_state:
        st.session_state.flash_msg = None

    if "flash_msg":
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

    for _, row in df.iterrows():

        cols = st.columns([2, 4, 3, 3, 3, 3])

        date = row["date"]
        details = row["merchant"] or row["description"]
        category = row["category"] or "other"
        amount = float(row["amount"])
        balance = row["balance"]
        txn_id = row["id"]

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

        cols[3].write(money_in)
        cols[4].write(money_out)
        cols[5].write(f"€{float(balance):,.2f}" if balance else "")

    r = requests.get(
        f"{API_BASE}/transactions/summary",
        headers=_auth_headers(),
        params=params,
    )

    summary = r.json()

    st.subheader("Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric("Money in", f"€{summary['income']:,.2f}")
    col2.metric("Money out", f"€{summary['expenses']:,.2f}")
    col3.metric("Net change", f"€{summary['net']:,.2f}")


def show_login():

    st.title("FYP Finance login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Log in"):

        payload = {"email": email, "password": password}

        r = requests.post(
            f"{API_BASE}/login",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
        )

        if not r.ok:
            st.error("Login failed")
            return

        body = r.json()

        if body.get("success"):

            st.session_state.authenticated = True
            st.session_state.user_email = email
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
