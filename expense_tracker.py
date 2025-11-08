"""
finance_hackathon_dashboard.py
Final Hackathon Edition – Professional Personal Finance Dashboard

📦 Dependencies (add to requirements.txt):
streamlit
pandas
numpy
plotly
openpyxl
scipy

▶️ Run:
pip install -r requirements.txt
streamlit run finance_hackathon_dashboard.py
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
# PAGE CONFIG & STYLES
# -------------------------------
st.set_page_config(
    page_title="Finance Hackathon Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polish
st.markdown("""
<style>
.big-header { font-size:28px; font-weight:700; }
.muted { color: #6c757d; }
.kpi { padding: 10px; border-radius: 10px; background: #f8f9fa; }
.stTabs [data-baseweb="tab-list"] { justify-content: center; }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# HEADER
# -------------------------------
col1, col2 = st.columns([6, 2])
with col1:
    st.image("https://upload.wikimedia.org/wikipedia/commons/3/3a/Logo_placeholder.png", width=120)
    st.markdown('<div class="big-header">💼 Finance Dashboard — Hackathon Edition</div>', unsafe_allow_html=True)
    st.caption("Interactive • Exportable • Data-Driven • Hackathon Ready")
with col2:
    theme = st.selectbox("Theme", ["Light", "Dark"])
    if theme == "Dark":
        st.markdown("<style>body{background-color:#0b1220;color:#e6eef8;}</style>", unsafe_allow_html=True)

st.write("---")

# -------------------------------
# SIDEBAR INPUTS
# -------------------------------
st.sidebar.header("⚙️ Settings")
income = st.sidebar.number_input("Monthly Income (₹)", value=30000.0, step=500.0, format="%.2f")
use_local = st.sidebar.checkbox("Use example dataset", value=True)

if use_local:
    example_path = "/mnt/data/Datasets - expenses.csv"
    if os.path.exists(example_path):
        df = pd.read_csv(example_path)
        st.sidebar.success("Loaded example dataset ✅")
        st.balloons()
    else:
        st.sidebar.warning("Example dataset not found. Please upload your own.")
        df = None
else:
    uploaded_file = st.sidebar.file_uploader("Upload CSV (Date, Category, Amount)", type=["csv"])
    df = pd.read_csv(uploaded_file) if uploaded_file is not None else None
    if uploaded_file:
        st.success("✅ File uploaded successfully!")
        st.balloons()

if df is None:
    st.warning("Please upload a dataset or enable the example dataset.")
    st.stop()

# -------------------------------
# SMART COLUMN MAPPING
# -------------------------------
col_map = {c.lower(): c for c in df.columns}
def find_col(possible):
    for p in possible:
        for k, original in col_map.items():
            if p.lower() == k:
                return original
    return None

date_col = find_col(["date", "transaction date", "txn_date", "dt"])
cat_col  = find_col(["category", "cat", "expense category"])
amt_col  = find_col(["amount", "amt", "value", "expense"])

if not (date_col and cat_col and amt_col):
    st.error("❌ CSV must include Date, Category, and Amount columns.")
    st.stop()

df = df.rename(columns={date_col: "Date", cat_col: "Category", amt_col: "Amount"})

# -------------------------------
# CLEAN & FEATURE ENGINEERING
# -------------------------------
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"])
df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)
df["YearMonth"] = df["Date"].dt.to_period("M").astype(str)
df["Month"] = df["Date"].dt.month_name()
df["Weekday"] = df["Date"].dt.day_name()
df["Category"] = df["Category"].astype(str).str.title().str.strip()

# -------------------------------
# FILTERS
# -------------------------------
st.sidebar.header("📅 Filters")
min_date, max_date = df["Date"].min(), df["Date"].max()
date_range = st.sidebar.date_input("Select date range", [min_date, max_date])
start_date, end_date = date_range

all_cats = sorted(df["Category"].unique())
sel_cats = st.sidebar.multiselect("Select categories", all_cats, default=all_cats)

filtered = df[(df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))]
filtered = filtered[filtered["Category"].isin(sel_cats)]

if filtered.empty:
    st.warning("No transactions found for the selected filters.")
    st.stop()

# -------------------------------
# METRICS & KPIs
# -------------------------------
monthly = filtered.groupby("YearMonth")["Amount"].sum().sort_index()
category_totals = filtered.groupby("Category")["Amount"].sum().sort_values(ascending=False)
total_spent = filtered["Amount"].sum()
avg_monthly = monthly.mean() if len(monthly) > 0 else 0.0
estimated_savings = income - avg_monthly
savings_pct = (estimated_savings / income * 100) if income > 0 else 0

# -------------------------------
# FORECAST & ANOMALY DETECTION
# -------------------------------
filtered["Amount_z"] = filtered.groupby("Category")["Amount"].transform(lambda x: stats.zscore(x.fillna(0)))
filtered["Is_Anomaly"] = filtered["Amount_z"].abs() > 2.5

forecast_next = None
if len(monthly) >= 3:
    x = np.arange(len(monthly))
    y = monthly.values
    coeffs = np.polyfit(x, y, 1)
    trend_line = np.polyval(coeffs, x)
    forecast_next = float(np.polyval(coeffs, len(monthly)))
else:
    trend_line = None

# -------------------------------
# DISPLAY METRICS
# -------------------------------
st.subheader("📈 Financial Summary")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Spent", f"₹{total_spent:,.2f}")
k2.metric("Average Monthly", f"₹{avg_monthly:,.2f}")
k3.metric("Estimated Savings", f"₹{estimated_savings:,.2f}")
if forecast_next:
    k4.metric("Forecast Next Month", f"₹{forecast_next:,.2f}")
else:
    k4.metric("Forecast Next Month", "—")

st.success(f"💡 You saved {savings_pct:.1f}% of your income! Great progress 🎉")

# -------------------------------
# SAVINGS GAUGE
# -------------------------------
gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=savings_pct,
    title={'text': "Savings % of Income"},
    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "green"}}
))
gauge.update_layout(height=300, margin=dict(t=0, b=0))
st.plotly_chart(gauge, use_container_width=True)

# -------------------------------
# TABS: Presentation / Deep Dive / Raw Data
# -------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Presentation", "🔍 Deep Dive", "📜 Raw Data"])

# Presentation
with tab1:
    st.markdown("### Spending by Category")
    fig_cat = px.bar(category_totals.head(10), x=category_totals.head(10).values, y=category_totals.head(10).index,
                     orientation="h", title="Top 10 Spending Categories", labels={'x': 'Amount (₹)', 'y': 'Category'})
    fig_cat.update_layout(height=400)
    st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("### Monthly Spending Trend")
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(x=monthly.index, y=monthly.values, name="Monthly Spend"))
    if trend_line is not None:
        fig_trend.add_trace(go.Scatter(x=monthly.index, y=trend_line, name="Trend", mode="lines+markers"))
    st.plotly_chart(fig_trend, use_container_width=True)

# Deep Dive
with tab2:
    st.markdown("### Spending Distribution")
    fig_pie = px.pie(names=category_totals.index, values=category_totals.values, title="Expense Breakdown by Category")
    st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("### Anomalies Detected")
    anomalies = filtered[filtered["Is_Anomaly"]]
    if not anomalies.empty:
        st.dataframe(anomalies[["Date", "Category", "Amount", "Amount_z"]].sort_values("Amount", ascending=False))
    else:
        st.info("No anomalies detected in this dataset.")

# Raw Data
with tab3:
    st.dataframe(filtered.sort_values("Date", ascending=False))

    def to_excel_bytes(df_in):
        out = BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            df_in.to_excel(writer, index=False, sheet_name="Transactions")
            pd.DataFrame({
                "Metric": ["Total Spent", "Avg Monthly", "Savings %"],
                "Value": [total_spent, avg_monthly, savings_pct]
            }).to_excel(writer, index=False, sheet_name="Summary")
        out.seek(0)
        return out.getvalue()

    xlsx_bytes = to_excel_bytes(filtered)
    st.download_button("📥 Download Excel Report", data=xlsx_bytes, file_name="finance_report.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# -------------------------------
# FOOTER
# -------------------------------
st.write("---")
st.caption(f"Data range: {df['Date'].min().date()} → {df['Date'].max().date()} • Transactions: {len(filtered):,}")
