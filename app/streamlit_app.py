import os
import json
import math
import matplotlib.pyplot as plt

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

st.set_page_config(page_title="FYP Finance", layout="wide")

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_BASE = f"http://{API_HOST}:{API_PORT}"


CATEGORIES = sorted(
    [
        "income",
        "salary",
        "bonus",
        "refund",
        "interest",
        "dividend",
        "investment return",
        "sales revenue",
        "client payments",
        "contract income",
        "grant income",
        "loan received",
        "capital injection",
        "housing",
        "rent",
        "mortgage",
        "groceries",
        "dining",
        "coffee",
        "transport",
        "fuel",
        "parking",
        "utilities",
        "electricity",
        "gas",
        "water",
        "internet",
        "phone",
        "education",
        "entertainment",
        "streaming",
        "gaming",
        "health",
        "medical",
        "fitness",
        "shopping",
        "clothing",
        "travel",
        "insurance",
        "subscriptions",
        "charity",
        "family",
        "gifts",
        "savings",
        "cash withdrawal",
        "payroll",
        "contractor payments",
        "employee benefits",
        "tax payments",
        "vat",
        "corporation tax",
        "legal fees",
        "consulting fees",
        "bank fees",
        "payment processor fees",
        "software subscriptions",
        "saas tools",
        "cloud infrastructure",
        "hosting",
        "domains",
        "office supplies",
        "coworking",
        "equipment",
        "hardware",
        "software",
        "inventory",
        "supplier payments",
        "raw materials",
        "manufacturing costs",
        "shipping",
        "logistics",
        "delivery",
        "marketing",
        "advertising",
        "customer acquisition",
        "sales commission",
        "research and development",
        "training",
        "maintenance",
        "repairs",
        "licensing",
        "compliance",
        "professional services",
        "merchant services",
        "chargeback",
        "other",
        "system",
    ]
)


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


def _build_display_balance(df: pd.DataFrame) -> pd.Series:
    if "balance" in df.columns:
        numeric_balance = pd.to_numeric(df["balance"], errors="coerce")
        if numeric_balance.notna().any():
            return numeric_balance

    running = pd.to_numeric(df["amount"], errors="coerce").fillna(0).cumsum()
    return running


def _cost_type_for_category(category: str) -> str:
    fixed_categories = {
        "housing",
        "rent",
        "mortgage",
        "utilities",
        "electricity",
        "gas",
        "water",
        "internet",
        "phone",
        "insurance",
        "insurance business",
        "subscriptions",
        "software subscriptions",
        "saas tools",
        "cloud infrastructure",
        "hosting",
        "domains",
        "office rent",
        "coworking",
        "payroll",
        "employee benefits",
        "tax payments",
        "vat",
        "corporation tax",
        "accounting fees",
        "legal fees",
        "bank fees",
        "payment processor fees",
        "licensing",
        "compliance",
        "maintenance",
        "professional services",
        "merchant services",
        "office supplies",
        "software",
        "training",
        "research and development",
    }

    category_clean = str(category or "").strip().lower()
    return "Fixed" if category_clean in fixed_categories else "Variable"


def update_category(transaction_id, new_category):
    r = requests.patch(
        f"{API_BASE}/transactions/{transaction_id}/category",
        headers=_auth_headers(),
        json={"category": new_category},
        timeout=10,
    )
    return r.ok


def upload_csv_to_backend(uploaded_file):
    try:
        file_bytes = uploaded_file.getvalue()

        files = {
            "file": (uploaded_file.name, file_bytes, "text/csv"),
        }

        r = requests.post(
            f"{API_BASE}/transactions/upload",
            files=files,
            headers=_auth_headers(),
            timeout=320,
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

        return False, f"Upload failed {r.status_code}. {r.text}"

    except requests.exceptions.ReadTimeout:
        return (
            False,
            "Upload timed out while the backend was processing the file. Please try again.",
        )
    except Exception as e:
        return False, f"Upload failed. Details: {e}"


def _style_dark_chart(ax):
    ax.set_facecolor("#0f1117")
    ax.figure.set_facecolor("#0f1117")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")

    for spine in ax.spines.values():
        spine.set_color("white")


def show_dashboard():
    header_col1, header_col2 = st.columns([6, 1])

    with header_col1:
        st.title("Open Source Finance Analytics")
        account_type = st.session_state.get("account_type", "Personal")
        st.caption(f"Active account: {account_type}")

    with header_col2:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.session_state.account_type = None
            st.rerun()

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

    if st.button("Delete all transactions for this account"):
        r = requests.delete(
            f"{API_BASE}/transactions",
            headers=_auth_headers(),
            timeout=10,
        )

        if r.ok:
            st.session_state.flash_msg = "All transactions deleted"
            st.rerun()
        else:
            st.error("Failed to delete transactions")

    st.subheader("Filters")

    col1, col2, col3, col4 = st.columns(4)

    start_date = col1.date_input("Start date", value=None)
    end_date = col2.date_input("End date", value=None)
    kind = col3.selectbox("Type", ["all", "income", "expense"])
    category_filter = col4.selectbox("Category", ["all"] + CATEGORIES)

    params = {"kind": kind, "category": category_filter}

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

    if "date" in df.columns:
        df["date_sort"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values(by=["date_sort", "id"], ascending=[True, True]).reset_index(
            drop=True
        )

    df["display_balance"] = _build_display_balance(df)
    df["amount_num"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["category_clean"] = df["category"].fillna("other").replace("", "other")
    df["is_anomaly_bool"] = df["is_anomaly"].fillna(False).astype(bool)

    st.subheader("Transactions")

    header_cols = st.columns([2, 4, 3, 3, 3, 3, 3, 1])
    header_cols[0].write("Date")
    header_cols[1].write("Details")
    header_cols[2].write("Category")
    header_cols[3].write("Flag")
    header_cols[4].write("Money In")
    header_cols[5].write("Money Out")
    header_cols[6].write("Balance")
    header_cols[7].write("Delete")

    for _, row in df.iterrows():
        cols = st.columns([2, 4, 3, 3, 3, 3, 3, 1])

        date = row["date"]
        details = row["merchant"] or row["description"]
        category = row["category"] or "other"
        amount = float(row["amount"])
        balance = row["display_balance"]
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
            cols[3].write("⚠ Anomaly")
        else:
            cols[3].write("Normal")

        cols[4].write(money_in)
        cols[5].write(money_out)
        cols[6].write(_safe_balance_text(balance))

        if cols[7].button("X", key=f"del_{txn_id}"):
            r = requests.delete(
                f"{API_BASE}/transactions/{txn_id}",
                headers=_auth_headers(),
                timeout=10,
            )

            if r.ok:
                st.session_state.flash_msg = "Transaction deleted"
                st.rerun()
            else:
                st.error("Delete failed")

    anomaly_count = int(df["is_anomaly_bool"].sum())
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

    st.subheader("Analytics")

    account_type = st.session_state.get("account_type", "Personal")

    if account_type == "Business":

        st.caption("Net Cash Flow Trend (Last 6 Months)")

        df_month = df.copy()

        df_month["date_sort"] = pd.to_datetime(df_month["date"], errors="coerce")
        df_month["month"] = df_month["date_sort"].dt.to_period("M").dt.to_timestamp()

        monthly = df_month.groupby("month")["amount_num"].sum().tail(6)

        if not monthly.empty:

            fig, ax = plt.subplots(figsize=(10, 5))

            ax.plot(monthly.index, monthly.values, marker="o", linewidth=2)

            ax.set_ylabel("Net Cash Flow (€)")
            ax.set_xlabel("Month")

            ax.axhline(0, linestyle="--", linewidth=1)

            _style_dark_chart(ax)

            st.pyplot(fig)

        else:
            st.info("Not enough transaction data for trend analysis.")

        st.caption("Monthly Revenue Trend (Last 6 Months)")

        revenue_df = df[df["amount_num"] > 0].copy()

        revenue_df["date_sort"] = pd.to_datetime(revenue_df["date"], errors="coerce")
        revenue_df["month"] = (
            revenue_df["date_sort"].dt.to_period("M").dt.to_timestamp()
        )

        monthly_revenue = revenue_df.groupby("month")["amount_num"].sum().tail(6)

        if not monthly_revenue.empty:

            fig, ax = plt.subplots(figsize=(10, 5))

            ax.plot(
                monthly_revenue.index,
                monthly_revenue.values,
                marker="o",
                linewidth=2,
                color="green",
            )

            ax.set_ylabel("Revenue (€)")
            ax.set_xlabel("Month")

            _style_dark_chart(ax)

            st.pyplot(fig)

        else:
            st.info("Not enough revenue data for trend analysis.")

    expense_df = df[df["amount_num"] < 0].copy()
    expense_df["expense_abs"] = expense_df["amount_num"].abs()

    if not expense_df.empty:
        expense_df["cost_type"] = expense_df["category_clean"].apply(
            _cost_type_for_category
        )
        category_spend = (
            expense_df.groupby("category_clean", dropna=False)["expense_abs"]
            .sum()
            .sort_values(ascending=False)
        )
    else:
        category_spend = pd.Series(dtype=float)

    income_df = df[df["amount_num"] > 0].copy()
    income_df["income_val"] = income_df["amount_num"]

    if not category_spend.empty:
        st.caption("Expense by Category")

        fig, ax = plt.subplots(figsize=(10, 5))
        colors = plt.cm.tab20.colors[: len(category_spend)]

        ax.bar(category_spend.index, category_spend.values, color=colors)
        ax.set_ylabel("Amount (€)")
        ax.tick_params(axis="x", rotation=45)

        _style_dark_chart(ax)
        st.pyplot(fig)
    else:
        st.caption("Expense by Category")
        st.info("No expense transactions in the current view.")

    analytics_col1, analytics_col2 = st.columns(2)

    with analytics_col1:
        cashflow_df = pd.DataFrame(
            {
                "Metric": ["Money In", "Money Out"],
                "Amount": [summary["income"], summary["expenses"]],
            }
        )

        st.caption("Money In vs Money Out")

        fig, ax = plt.subplots()
        colors = ["green", "red"]

        ax.bar(cashflow_df["Metric"], cashflow_df["Amount"], color=colors)
        ax.set_ylabel("Amount (€)")
        ax.set_xlabel("")

        _style_dark_chart(ax)
        st.pyplot(fig)

    with analytics_col2:
        if not income_df.empty:
            category_income = (
                income_df.groupby("category_clean", dropna=False)["income_val"]
                .sum()
                .sort_values(ascending=False)
            )
            st.caption("Income by Category")

            fig, ax = plt.subplots()
            colors = plt.cm.Set2.colors[: len(category_income)]

            ax.bar(category_income.index, category_income.values, color=colors)
            ax.set_ylabel("Amount (€)")
            ax.tick_params(axis="x", rotation=45)

            _style_dark_chart(ax)
            st.pyplot(fig)
        else:
            st.caption("Income by Category")
            st.info("No income transactions in the current view.")

    if not expense_df.empty:
        fixed_variable = (
            expense_df.groupby("cost_type", dropna=False)["expense_abs"]
            .sum()
            .reindex(["Fixed", "Variable"], fill_value=0.0)
        )

        st.caption("Fixed vs Variable Costs")

        fv_col1, fv_col2, fv_col3 = st.columns([2, 1, 1])

        with fv_col1:
            fig, ax = plt.subplots()

            labels = ["Fixed", "Variable"]
            values = [fixed_variable["Fixed"], fixed_variable["Variable"]]
            colors = ["blue", "orange"]

            ax.bar(labels, values, color=colors)
            ax.set_ylabel("Amount (€)")

            _style_dark_chart(ax)

            st.pyplot(fig)

        with fv_col2:
            st.metric("Fixed costs", f"€{fixed_variable['Fixed']:,.2f}")

        with fv_col3:
            st.metric("Variable costs", f"€{fixed_variable['Variable']:,.2f}")

        fixed_breakdown = (
            expense_df[expense_df["cost_type"] == "Fixed"]
            .groupby("category_clean", dropna=False)["expense_abs"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

        variable_breakdown = (
            expense_df[expense_df["cost_type"] == "Variable"]
            .groupby("category_clean", dropna=False)["expense_abs"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

        breakdown_col1, breakdown_col2 = st.columns(2)

        with breakdown_col1:
            st.caption("Fixed cost breakdown")
            if not fixed_breakdown.empty:
                fixed_breakdown.columns = ["Category", "Amount"]
                fixed_breakdown["Amount"] = fixed_breakdown["Amount"].apply(
                    lambda x: f"€{x:,.2f}"
                )
                st.dataframe(
                    fixed_breakdown,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No fixed costs in the current view.")

        with breakdown_col2:
            st.caption("Variable cost breakdown")
            if not variable_breakdown.empty:
                variable_breakdown.columns = ["Category", "Amount"]
                variable_breakdown["Amount"] = variable_breakdown["Amount"].apply(
                    lambda x: f"€{x:,.2f}"
                )
                st.dataframe(
                    variable_breakdown,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No variable costs in the current view.")

        if not expense_df.empty:
            top_expenses = (
                expense_df.sort_values(by="expense_abs", ascending=False)[
                    ["description", "expense_abs"]
                ]
                .head(5)
                .copy()
            )

            st.caption("Top 5 Expenses")

            chart_col, legend_col = st.columns([3, 2])

            with chart_col:
                fig, ax = plt.subplots(figsize=(6, 6))

                def autopct_if_large(pct):
                    return f"{pct:.1f}%" if pct >= 5 else ""

                ax.pie(
                    top_expenses["expense_abs"],
                    labels=None,
                    autopct=autopct_if_large,
                    startangle=90,
                    pctdistance=0.65,
                )

                _style_dark_chart(ax)
                ax.axis("equal")
                st.pyplot(fig)

            with legend_col:
                legend_labels = [
                    f"{desc} - €{amt:,.2f}"
                    for desc, amt in zip(
                        top_expenses["description"],
                        top_expenses["expense_abs"],
                    )
                ]

                st.markdown("Expense breakdown")

                for i, label in enumerate(legend_labels, start=1):
                    st.write(f"{i}. {label}")


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
