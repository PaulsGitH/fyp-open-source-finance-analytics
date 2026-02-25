import os
import json
from pathlib import Path
import hashlib

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

st.set_page_config(page_title="FYP Finance", layout="wide")

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_BASE = f"http://{API_HOST}:{API_PORT}"


def _auth_headers() -> dict:
    email = st.session_state.get("user_email")
    if not email:
        return {}
    return {"X-User-Email": email}


def load_transactions_from_db() -> pd.DataFrame:
    try:
        r = requests.get(
            f"{API_BASE}/transactions",
            headers=_auth_headers(),
            timeout=5,
        )
        if not r.ok:
            return None
        rows = r.json()
        return pd.DataFrame(rows)
    except Exception:
        return None


def _file_sig(uploaded_file) -> str:
    b = uploaded_file.getvalue()
    h = hashlib.sha256(b).hexdigest()[:16]
    return f"{uploaded_file.name}|{len(b)}|{h}"


def upload_csv_to_backend(uploaded_file) -> tuple[bool, str]:
    try:
        health = requests.get(
            f"{API_BASE}/health",
            headers=_auth_headers(),
            timeout=3,
        )
        if not health.ok:
            return False, f"Backend not ready. {health.status_code} {health.text}"

        file_bytes = uploaded_file.getvalue()

        files = {
            "file": (uploaded_file.name, file_bytes, "text/csv"),
        }

        r = requests.post(
            f"{API_BASE}/transactions/upload",
            files=files,
            headers=_auth_headers(),
            timeout=20,
        )

        if r.ok:
            body = r.json()
            inserted = body.get("inserted", 0)
            skipped = body.get("skipped", 0)
            return (
                True,
                f"CSV uploaded successfully. Inserted {inserted}. Skipped {skipped}.",
            )
        return False, f"Upload failed. {r.status_code} {r.text}"
    except Exception as e:
        return False, f"Upload failed. Details: {e}"


def show_dashboard() -> None:
    st.title("Open Source Finance Analytics")

    if "last_upload_sig" not in st.session_state:
        st.session_state.last_upload_sig = None

    left, right = st.columns([3, 2])
    with left:
        uploaded = st.file_uploader("Upload CSV", type=["csv"], key="uploader")

    if "flash_msg" not in st.session_state:
        st.session_state.flash_msg = None
    if "flash_kind" not in st.session_state:
        st.session_state.flash_kind = None
    if "rerun_after_upload" not in st.session_state:
        st.session_state.rerun_after_upload = False

    if st.session_state.flash_msg:
        if st.session_state.flash_kind == "success":
            st.success(st.session_state.flash_msg)
        else:
            st.error(st.session_state.flash_msg)
        st.session_state.flash_msg = None
        st.session_state.flash_kind = None

    if uploaded is not None:
        sig = _file_sig(uploaded)
        if st.session_state.last_upload_sig != sig:
            ok, msg = upload_csv_to_backend(uploaded)
            st.session_state.last_upload_sig = sig
            st.session_state.flash_msg = msg
            st.session_state.flash_kind = "success" if ok else "error"
            st.session_state.rerun_after_upload = ok

    if st.session_state.rerun_after_upload:
        st.session_state.rerun_after_upload = False
        st.rerun()

    st.subheader("Filters")

    kind = st.selectbox(
        "Transaction type",
        options=["all", "income", "expense"],
        index=0,
    )

    date_filter_enabled = st.checkbox("Enable date range filter", value=False)

    start_date = None
    end_date = None
    if date_filter_enabled:
        c1, c2 = st.columns(2)
        with c1:
            start_date = st.date_input("Start date")
        with c2:
            end_date = st.date_input("End date")

    params = {"kind": kind}
    if date_filter_enabled and start_date and end_date:
        params["start_date"] = start_date.isoformat()
        params["end_date"] = end_date.isoformat()

    df = None
    try:
        r = requests.get(
            f"{API_BASE}/transactions",
            headers=_auth_headers(),
            params=params,
            timeout=5,
        )
        if r.ok:
            rows = r.json()
            if rows:
                df = pd.DataFrame(rows)
    except Exception:
        df = None

    if df is not None:
        st.subheader("Transactions")

        df_display = df.copy()

        if "merchant" in df_display.columns and "description" in df_display.columns:
            df_display["Details"] = df_display["merchant"].fillna("").astype(str)
            missing = df_display["Details"].str.strip().eq("")
            df_display.loc[missing, "Details"] = (
                df_display.loc[missing, "description"].fillna("").astype(str)
            )
        elif "merchant" in df_display.columns:
            df_display["Details"] = df_display["merchant"].fillna("").astype(str)
        elif "description" in df_display.columns:
            df_display["Details"] = df_display["description"].fillna("").astype(str)
        else:
            df_display["Details"] = ""

        if "amount" in df_display.columns:
            df_display["Money In"] = df_display["amount"].apply(
                lambda x: float(x) if x is not None and float(x) > 0 else 0.0
            )
            df_display["Money Out"] = df_display["amount"].apply(
                lambda x: abs(float(x)) if x is not None and float(x) < 0 else 0.0
            )
        else:
            df_display["Money In"] = 0.0
            df_display["Money Out"] = 0.0

        if "balance" not in df_display.columns:
            df_display["balance"] = 0.0

        df_display["Money In"] = df_display["Money In"].apply(lambda x: f"€{x:,.2f}")
        df_display["Money Out"] = df_display["Money Out"].apply(lambda x: f"€{x:,.2f}")
        df_display["balance"] = df_display["balance"].apply(
            lambda x: f"€{float(x):,.2f}"
        )

        display_cols = ["date", "Details", "Money In", "Money Out", "balance"]
        display_cols = [c for c in display_cols if c in df_display.columns]

        st.dataframe(
            df_display[display_cols],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No transactions found for selected filters.")

    summary = {"income": 0.0, "expenses": 0.0, "net": 0.0}
    try:
        r = requests.get(
            f"{API_BASE}/transactions/summary",
            headers=_auth_headers(),
            params=params,
            timeout=5,
        )
        if r.ok:
            summary = r.json()
    except Exception:
        pass

    st.subheader("Summary")
    a, b, c = st.columns(3)
    a.metric("Total Money In", f"€{summary['income']:,.2f}")
    b.metric("Total Money Out", f"€{summary['expenses']:,.2f}")
    c.metric("Net Movement", f"€{summary['net']:,.2f}")


def show_login() -> None:
    st.title("FYP Finance login")

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
