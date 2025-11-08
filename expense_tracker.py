"""
Finance Hackathon Pro Dashboard
---------------------------------
Feature-rich Personal Finance Tracker
Theme: Lifestyle / Data Awareness

Includes:
- Category budgets (editable)
- User filtering (if User column exists)
- Savings system (target-based)
- Trend, anomaly, and budget analytics
- Excel/CSV export

Run:
    streamlit run finance_dashboard_hackathon_pro.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime
from scipy import stats

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(
    page_title="Finance Hackathon Pro Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .big-header { font-size:28px; font-weight:700; }
        .muted { color:#6c757d; }
        .kpi { padding:10px; border-radius:10px; background:#f8f9fa; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------
# HEADER
# -------------------------------
col1, col2 = st.columns([6, 2])
with col1:
    st.markdown('<div class="big-header">💰 Personal Finance Dashboard — Hackathon Pro</div>', unsafe_allow_html=True)
    st.caption("Tracks expenses, savings, and spending patterns for multiple users.")
with col2:
    theme = st.selectbox("Theme", ["Light", "Dark"])
    if theme == "Dark":
        st.markdown("<style>body{background-color:#0b1220;color:#e6eef8;}</style>", unsafe_allow_html=True)

st.write("---")

# -------------------------------
# SIDEBAR — FILE UPLOAD
# -------------------------------
st.sidebar.header("📂 Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload your Expense CSV", type=["csv"])

if uploaded_file is None:
    st.warning("Please upload a CSV file with Date, Category, and Amount columns.")
    st.stop()

df = pd.read_csv(uploaded_file)

# -------------------------------
# SMART COLUMN DETECTION
# -------------------------------
col_map = {c.lower(): c for c in df.columns}

def find_col(possible):
    for p in possible:
        for k, v in col_map.items():
            if p.lower() == k:
                return v
    return None

date_col = find_col(["date", "transaction date"])
cat_col = find_col(["category", "cat"])
amt_col = find_col(["amount", "amt", "value"])
user_col = find_col(["user", "name", "person"])

if not (date_col and cat_col and amt_col):
    st.error("Your CSV must contain Date, Category, and Amount columns.")
    st.stop()

df = df.rename(columns={date_col: "Date", cat_col: "Category", amt_col: "Amount"})
if user_col:
    df = df.rename(columns={user_col: "User"})

# -------------------------------
# CLEAN DATA
# -------------------------------
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"])
df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
df["Month"] = df["Date"].dt.month_name()
df["YearMonth"] = df["Date"].dt.to_period("M").astype(str)
df["Category"] = df["Category"].astype(str).str.title().str.strip()

# -------------------------------
# SIDEBAR — FILTERS
# -------------------------------
st.sidebar.header("🔍 Filters")
min_date, max_date = df["Date"].min(), df["Date"].max()
date_range = st.sidebar.date_input("Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

all_cats = sorted(df["Category"].unique())
sel_cats = st.sidebar.multiselect("Categories", all_cats, default=all_cats)

if user_col:
    all_users = sorted(df["User"].unique())
    sel_users = st.sidebar.multiselect("Users", all_users, default=all_users)
else:
    sel_users = None

# -------------------------------
# SIDEBAR — BUDGETS
# -------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("💸 Budgets (Monthly)")
default_budgets = (df.groupby(["Category", "YearMonth"])["Amount"].sum().groupby("Category").mean()).to_dict()
budgets = {}
for cat in all_cats:
    default_val = float(default_budgets.get(cat, 500))
    budgets[cat] = st.sidebar.number_input(
        f"Budget — {cat}", min_value=0.0, value=round(default_val, 2), step=100.0, key=f"b_{cat}"
    )

# -------------------------------
# SIDEBAR — SAVINGS
# -------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("💰 Savings System")
savings_goal = st.sidebar.number_input("Monthly Savings Goal (₹)", min_value=0.0, value=5000.0, step=500.0)
savings_target = st.sidebar.slider("Target Saving % of Income", 0, 100, 20)

# -------------------------------
# FILTER DATA
# -------------------------------
start_date, end_date = date_range
filtered = df[(df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))]
filtered = filtered[filtered["Category"].isin(sel_cats)]
if sel_users:
    filtered = filtered[filtered["User"].isin(sel_users)]

if filtered.empty:
    st.warning("No transactions match your filters.")
    st.stop()

# -------------------------------
# COMPUTE STATS
# -------------------------------
monthly = filtered.groupby("YearMonth")["Amount"].sum().sort_index()
category_totals = filtered.groupby("Category")["Amount"].sum().sort_values(ascending=False)
total_spent = filtered["Amount"].sum()
avg_monthly = monthly.mean() if len(monthly) > 0 else 0.0

# Budget comparison
budget_df = pd.DataFrame({
    "Category": all_cats,
    "Actual": [category_totals.get(c, 0.0) for c in all_cats],
    "Budget": [budgets.get(c, 0.0) for c in all_cats],
})
budget_df["Pct"] = (budget_df["Actual"] / budget_df["Budget"].replace({0: np.nan})) * 100
budget_df = budget_df.fillna(0).sort_values("Pct", ascending=False)

# Savings system
total_budget = sum(budgets.values())
savings = total_budget - total_spent
savings_pct = (savings / total_budget * 100) if total_budget > 0 else 0
goal_status = "✅ Goal Met" if savings >= savings_goal else "⚠️ Below Goal"

# Forecast (trendline)
if len(monthly) >= 3:
    x = np.arange(len(monthly))
    y = monthly.values
    coeffs = np.polyfit(x, y, 1)
    trend_line = np.polyval(coeffs, x)
    forecast_next = float(np.polyval(coeffs, len(monthly)))
else:
    trend_line = None
    forecast_next = None

# -------------------------------
# KPIs
# -------------------------------
st.subheader("📈 Overview Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Spent", f"₹{total_spent:,.2f}")
col2.metric("Avg. Monthly Spend", f"₹{avg_monthly:,.2f}")
col3.metric("Savings Achieved", f"₹{savings:,.2f}")
col4.metric("Savings %", f"{savings_pct:.1f}%", goal_status)

# -------------------------------
# TABS
# -------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💰 Savings", "🔍 Deep Dive", "📂 Data"])

# OVERVIEW TAB
with tab1:
    st.markdown("### Spending by Category")
    fig_cat = px.bar(category_totals.head(10), orientation="h", title="Top 10 Spending Categories")
    st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("### Monthly Trend")
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(x=monthly.index, y=monthly.values, name="Monthly Spend"))
    if trend_line is not None:
        fig_trend.add_trace(go.Scatter(x=monthly.index, y=trend_line, mode="lines+markers", name="Trend"))
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("### Budget vs Actual")
    fig_budget = px.bar(budget_df, x="Category", y=["Actual", "Budget"], barmode="group")
    st.plotly_chart(fig_budget, use_container_width=True)

# SAVINGS TAB
with tab2:
    st.markdown("### 💰 Savings Progress")
    fig_saving = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=savings,
        title={"text": "Current Savings"},
        delta={"reference": savings_goal, "increasing": {"color": "green"}},
        gauge={"axis": {"range": [None, savings_goal * 2]}, "bar": {"color": "green"}},
    ))
    st.plotly_chart(fig_saving, use_container_width=True)

    st.markdown(f"**Target:** ₹{savings_goal:,.2f} | **Achieved:** ₹{savings:,.2f} ({savings_pct:.1f}%)")

    st.progress(min(savings_pct / 100, 1.0))
    if savings >= savings_goal:
        st.success("🎉 Congratulations! You met your savings goal!")
    else:
        st.warning("⚠️ Keep saving to reach your goal!")

# DEEP DIVE TAB
with tab3:
    filtered["zscore"] = filtered.groupby("Category")["Amount"].transform(lambda x: stats.zscore(x.fillna(0)))
    anomalies = filtered[filtered["zscore"].abs() > 2.5]
    st.markdown("### Anomaly Detection")
    if not anomalies.empty:
        st.dataframe(anomalies[["Date", "Category", "Amount", "zscore"]])
    else:
        st.info("No anomalies detected.")

# DATA TAB
with tab4:
    st.markdown("### Filtered Data")
    st.dataframe(filtered)

    def to_excel_bytes(df_in):
        out = BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            df_in.to_excel(writer, index=False, sheet_name="Filtered")
        out.seek(0)
        return out.getvalue()

    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    xlsx_bytes = to_excel_bytes(filtered)
    st.download_button("⬇️ Download CSV", data=csv_bytes, file_name="filtered_data.csv", mime="text/csv")
    st.download_button("⬇️ Download Excel", data=xlsx_bytes, file_name="finance_dashboard.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.write("---")
st.caption("Hackathon Pro Edition — Combining Insights, Budgets & Savings Goals.")
