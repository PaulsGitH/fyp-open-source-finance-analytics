import os
import json
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

st.set_page_config(page_title="FYP Finance", layout="wide")

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_BASE = f"http://{API_HOST}:{API_PORT}"


def load_sample() -> pd.DataFrame:
    sample_path = Path(__file__).resolve().parents[1] / "data" / "samples.csv"
    if sample_path.exists():
        return pd.read_csv(sample_path)
    return pd.DataFrame(
        {
            "date": ["2025-10-01", "2025-10-02", "2025-10-03"],
            "description": ["salary Job", "Coffee Shop", "Rent"],
            "amount": [2500.00, -3.50, -1200.00],
        }
    )


def load_transactions_from_db() -> pd.DataFrame:
    try:
        r = requests.get(f"{API_BASE}/transactions", timeout=5)
        if not r.ok:
            return None
        rows = r.json()
        return pd.DataFrame(rows)
    except Exception:
        return None


def upload_csv_to_backend(uploaded_file) -> tuple[bool, str]:
    try:
        health = requests.get(f"{API_BASE}/health", timeout=3)
        if not health.ok:
            return False, f"Backend not ready. {health.status_code} {health.text}"

        file_bytes = uploaded_file.getvalue()

        files = {
            "file": (uploaded_file.name, file_bytes, "text/csv"),
        }

        st.write("API_BASE:", API_BASE)
        st.write("Uploading endpoint:", f"{API_BASE}/transactions/upload")

        r = requests.post(
            f"{API_BASE}/transactions/upload",
            files=files,
            timeout=20,
        )

        if r.ok:
            return True, "CSV uploaded successfully."
        return False, f"Upload failed. {r.status_code} {r.text}"
    except Exception as e:
        return False, f"Upload failed. Details: {e}"


def show_dashboard() -> None:
    st.title("Open Source Finance Analytics")
    st.caption("Upload a CSV or use the sample to preview metrics.")

    left, right = st.columns([3, 2])
    with left:
        use_sample = st.checkbox("Use sample data", value=False)
        uploaded = st.file_uploader("Upload CSV", type=["csv"])

        st.write("API_BASE:", API_BASE)
        st.write("Uploading endpoint:", f"{API_BASE}/transactions/upload")

    df = None

    if uploaded is not None:
        ok, msg = upload_csv_to_backend(uploaded)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)
            return

    if use_sample:
        df = load_sample()
    else:
        db_df = load_transactions_from_db()
        if db_df is not None and not db_df.empty:
            df = db_df

    if df is not None:
        st.subheader("Transactions")

        display_cols = [
            c
            for c in [
                "date",
                "description",
                "merchant",
                "category",
                "amount",
                "balance",
                "currency",
            ]
            if c in df.columns
        ]

        if display_cols:
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

        if "amount" in df.columns:
            income_local = df.loc[df["amount"] > 0, "amount"].sum()
            expense_local = -df.loc[df["amount"] < 0, "amount"].sum()
            net_local = income_local - expense_local
        else:
            income_local = 0.0
            expense_local = 0.0
            net_local = 0.0

        summary = {
            "income": float(income_local),
            "expenses": float(expense_local),
            "net": float(net_local),
        }

        try:
            if all(c in df.columns for c in ["date", "description", "amount"]):
                payload = {
                    "transactions": [
                        {
                            "date": str(r["date"]),
                            "description": str(r["description"]),
                            "amount": float(r["amount"]),
                        }
                        for _, r in df.iterrows()
                    ]
                }
                r = requests.post(
                    f"{API_BASE}/summary",
                    data=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                    timeout=5,
                )
                if r.ok:
                    summary = r.json()
        except Exception:
            pass

        st.subheader("Summary")
        a, b, c = st.columns(3)
        a.metric("Total income", f"€{summary['income']:,.2f}")
        b.metric("Total expenses", f"€{summary['expenses']:,.2f}")
        c.metric("Net", f"€{summary['net']:,.2f}")
    else:
        st.info(
            "Upload a CSV to ingest into PostgreSQL, or enable sample data to preview metrics."
        )


def show_login() -> None:
    st.title("FYP Finance login")
    st.caption("Enter your email and password to access the dashboard.")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    login_clicked = st.button("Log in")

    if login_clicked:
        if not email or not password:
            st.error("Please enter both email and password.")
            return

        try:
            payload = {"email": email, "password": password}
            r = requests.post(
                f"{API_BASE}/login",
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
        except Exception as e:
            st.error(f"Could not contact backend. Details: {e}")
            return

        if not r.ok:
            st.error("Login failed. Backend returned an error.")
            return

        body = r.json()
        if body.get("success"):
            import time

            st.success("Login successful.")
            time.sleep(2.5)
            st.session_state.authenticated = True
            st.session_state.user_email = email
            st.rerun()
        else:
            st.error(body.get("message") or "Invalid credentials.")


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_email = None

if not st.session_state.authenticated:
    show_login()
else:
    show_dashboard()
