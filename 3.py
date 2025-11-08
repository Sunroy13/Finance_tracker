"""
finance_hackathon_dashboard.py
Hackathon Edition — User Filter + Category Filter + Professional Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime
from scipy import stats
import os

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(
    page_title="Finance Hackathon Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------
# STYLES
# -------------------------------
st.markdown("""
<style>
.big-header { font-size:28px; font-weight:700; }
.kpi { padding: 10px; border-radius: 10px; background: #f8f9fa; }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# HEADER
# -------------------------------
col1, col2 = st.columns([6, 2])
with col1:
    st.markdown('<div class="big-header">💼 Personal Finance Tracker — Hackathon Edition</div>', unsafe_allow_html=True)
    st.caption("Interactive • Exportable • User-based • Hackathon Ready")
with col2:
    theme = st.selectbox("Theme", ["Light", "Dark"])
    if theme == "Dark":
        st.markdown("<style>body{background-color:#0b1220;color:#e6eef8;}</style>", unsafe_allow_html=True)

st.write("---")

# -------------------------------
# SIDEBAR SETTINGS
# -------------------------------
st.sidebar.header("⚙️ Data Settings")
use_local = st.sidebar.checkbox("Use example dataset", value=True)

if use_local:
    example_path = "/mnt/data/Datasets - expenses.csv"
    if os.path.exists(example_path):
        df = pd.read_csv(example_path)
        st.sidebar.success("✅ Loaded example dataset")
    else:
        st.sidebar.error("Example dataset not found!")
        st.stop()
else:
    uploaded_file = st.sidebar.file_uploader("Upload CSV (Date, Category, Amount, User)", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.sidebar.success("✅ File uploaded successfully!")
    else:
        st.warning("Please upload a dataset.")
        st.stop()

# -------------------------------
# NORMALIZE COLUMN NAMES
# -------------------------------
df.columns = [c.strip().capitalize() for c in df.columns]

# Detect important columns automatically
required_cols = {"Date", "Category", "Amount"}
optional_user_col = None
for col in df.columns:
    if "user" in col.lower():
        optional_user_col = col
        break

if not required_cols.issubset(df.columns):
    st.error(f"❌ Missing columns. File must contain: {', '.join(required_cols)}")
    st.stop()

# -------------------------------
# CLEANING
# -------------------------------
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df.dropna(subset=["Date"], inplace=True)
df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
df["Month"] = df["Date"].dt.month_name()
df["YearMonth"] = df["Date"].dt.to_period("M").astype(str)
df["Category"] = df["Category"].astype(str).str.title().str.strip()

if optional_user_col:
    df["User"] = df[optional_user_col].astype(str).str.title().str.strip()
else:
    df["User"] = "Default User"

# -------------------------------
# SIDEBAR FILTERS
# -------------------------------
st.sidebar.header("📅 Filters")

# User filter (NEW)
all_users = sorted(df["User"].unique())
selected_users = st.sidebar.multiselect(
    "Select User(s)", all_users, default=all_users[:1],
    help="Filter transactions by specific user(s)"
)

filtered = df[df["User"].isin(selected_users)]

# Date range filter
min_date, max_date = filtered["Date"].min(), filtered["Date"].max()
date_range = st.sidebar.date_input("Select date range", [min_date, max_date])
start_date, end_date = date_range
filtered = filtered[(filtered["Date"] >= pd.to_datetime(start_date)) & (filtered["Date"] <= pd.to_datetime(end_date))]

if filtered.empty:
    st.warning("No data available for the selected user(s) or date range.")
    st.stop()

# -------------------------------
# MAIN PAGE CATEGORY FILTER
# -------------------------------
all_cats = sorted(filtered["Category"].unique())
selected_categories = st.multiselect(
    "🎯 Select categories to analyze:",
    all_cats,
    default=all_cats[:3] if len(all_cats) > 3 else all_cats,
    help="Filter data interactively by expense category"
)

filtered = filtered[filtered["Category"].isin(selected_categories)]

if filtered.empty:
    st.warning("No transactions match your filters.")
    st.stop()

# -------------------------------
# METRICS
# -------------------------------
monthly = filtered.groupby("YearMonth")["Amount"].sum().sort_index()
category_sum = filtered.groupby("Category")["Amount"].sum().sort_values(ascending=False)
total_expense = filtered["Amount"].sum()
avg_expense = monthly.mean() if not monthly.empty else 0

# -------------------------------
# DISPLAY METRICS
# -------------------------------
st.subheader("📈 Financial Summary")
k1, k2 = st.columns(2)
k1.metric("Total Spent", f"₹{total_expense:,.2f}")
k2.metric("Average Monthly Expense", f"₹{avg_expense:,.2f}")

st.info(f"Showing data for **{', '.join(selected_users)}** from {start_date} → {end_date}")

# -------------------------------
# VISUALIZATIONS
# -------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Overview", "🔍 Category Analysis", "📜 Raw Data"])

# Overview
with tab1:
    st.markdown("### Monthly Spending Trend")
    fig_trend = px.bar(
        monthly,
        x=monthly.index,
        y=monthly.values,
        title="Spending Over Time",
        labels={"x": "Month", "y": "Amount (₹)"},
        color_discrete_sequence=px.colors.sequential.Teal
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("### Spending Distribution by Category")
    fig_pie = px.pie(
        names=category_sum.index,
        values=category_sum.values,
        title="Expense Breakdown by Category",
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# Category Analysis
with tab2:
    st.markdown("### Category-wise Breakdown")
    fig_cat = px.bar(
        category_sum,
        x=category_sum.values,
        y=category_sum.index,
        orientation="h",
        title="Top Spending Categories",
        labels={"x": "Amount (₹)", "y": "Category"},
        color_discrete_sequence=px.colors.sequential.Blues
    )
    st.plotly_chart(fig_cat, use_container_width=True)

# Raw Data
with tab3:
    st.markdown("### Filtered Expense Data")
    st.dataframe(filtered.sort_values("Date", ascending=False))

    def to_excel_bytes(df_in):
        out = BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            df_in.to_excel(writer, index=False, sheet_name="Expenses")
            pd.DataFrame({
                "Metric": ["Total Spent", "Avg Monthly"],
                "Value": [total_expense, avg_expense]
            }).to_excel(writer, index=False, sheet_name="Summary")
        out.seek(0)
        return out.getvalue()

    excel_bytes = to_excel_bytes(filtered)
    st.download_button(
        "📥 Download Excel Report",
        data=excel_bytes,
        file_name="finance_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# -------------------------------
# FOOTER
# -------------------------------
st.write("---")
st.caption(
    f"Users: {', '.join(selected_users)} • Categories: {len(selected_categories)} • Transactions: {len(filtered):,} • Date Range: {min_date.date()} → {max_date.date()}"
)
