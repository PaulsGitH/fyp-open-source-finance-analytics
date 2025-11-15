import os
import json
import requests
import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="FYP Finance", layout="wide")

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_BASE = f"http://{API_HOST}:{API_PORT}"

st.title("Open Source Finance Analytics")
st.caption("Semester 1 hello world. Upload a CSV or use the sample to preview metrics.")

def load_sample() -> pd.DataFrame:
    sample_path = Path(__file__).resolve().parents[1] / "data" / "samples.csv"
    if sample_path.exists():
        return pd.read_csv(sample_path)
    return pd.DataFrame(
        {
            "date": ["2025-10-01", "2025-10-02", "2025-10-03"],
            "description": ["Salary ACME", "Coffee Shop", "Rent"],
            "amount": [2500.00, -3.50, -1200.00],
        }
    )

left, right = st.columns([3, 2])
with left:
    use_sample = st.checkbox("Use sample data", value=True)
    uploaded = st.file_uploader("Upload CSV", type=["csv"])

df = None
if use_sample and uploaded is None:
    df = load_sample()
elif uploaded is not None:
    try:
        df = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Could not read CSV. Details: {e}")

if df is not None:
    st.subheader("Transactions")
    st.dataframe(df, use_container_width=True, hide_index=True)

    income_local = df.loc[df["amount"] > 0, "amount"].sum()
    expense_local = -df.loc[df["amount"] < 0, "amount"].sum()
    net_local = income_local - expense_local

    summary = {"income": float(income_local), "expenses": float(expense_local), "net": float(net_local)}

    try:
        payload = {
            "transactions": [
                {"date": str(r["date"]), "description": str(r["description"]), "amount": float(r["amount"])}
                for _, r in df.iterrows()
            ]
        }
        r = requests.post(
            f"{API_BASE}/summary",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=3,
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
    st.info("Select Use sample data or upload a CSV to continue.")
