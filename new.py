# -----------------------------------
# 📊 PERSONAL FINANCE TRACKER (Full Version)
# -----------------------------------
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.linear_model import LinearRegression

# -----------------------------------
# PAGE CONFIG
# -----------------------------------
st.set_page_config(page_title="💰 Personal Finance Tracker", layout="wide")
st.title("💰 Personal Finance Tracker (Full CSV Version)")
st.write("Analyze your expenses, savings, and spending trends using an easy upload or local CSV file.")

# -----------------------------------
# USER INPUT
# -----------------------------------
st.sidebar.header("📥 Data Input")

income = st.sidebar.number_input("Enter your Monthly Income (₹):", min_value=0.0, step=100.0)

use_local_file = st.sidebar.checkbox("Use local CSV file from Downloads folder")

if use_local_file:
    file_path = r"C:\Users\IT LAB-002\Downloads\Datasets - expenses.csv (1).csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        st.error("❌ File not found at given path.")
        st.stop()
else:
    uploaded_file = st.sidebar.file_uploader("Upload your Expense CSV file", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        st.info("Please upload a CSV file or select local file option.")
        st.stop()

# -----------------------------------
# PROCESS DATA
# -----------------------------------
df.columns = [col.strip().capitalize() for col in df.columns]  # Normalize headers
required_cols = {'Date', 'Category', 'Amount'}

if not required_cols.issubset(df.columns):
    st.error(f"Your file must contain columns: {', '.join(required_cols)}")
    st.stop()

# Clean and process
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df.dropna(subset=['Date'], inplace=True)
df = df[df['Amount'] > 0]  # Remove invalid entries
df['Month'] = df['Date'].dt.month_name()

# -----------------------------------
# SIDEBAR FILTERS
# -----------------------------------
st.sidebar.header("🔍 Filters")

start_date = st.sidebar.date_input("Start Date", df['Date'].min())
end_date = st.sidebar.date_input("End Date", df['Date'].max())

df = df[(df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))]

categories = st.sidebar.multiselect("Select Categories", df['Category'].unique(), default=df['Category'].unique())
df = df[df['Category'].isin(categories)]

# -----------------------------------
# SUMMARY CALCULATIONS
# -----------------------------------
category_summary = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
monthly_summary = df.groupby('Month')['Amount'].sum()

avg_expense = np.mean(monthly_summary)
total_expense = df['Amount'].sum()
savings = income - avg_expense
savings_percentage = (savings / income) * 100 if income > 0 else 0

# -----------------------------------
# EXPENSE TABLES
# -----------------------------------
st.subheader("📊 Expense Summary")

col1, col2 = st.columns(2)

with col1:
    st.write("### Total Spending by Category")
    st.dataframe(category_summary)

with col2:
    st.write("### Monthly Spending Trend")
    st.bar_chart(monthly_summary)

# -----------------------------------
# VISUALIZATIONS
# -----------------------------------
st.write("### Spending Distribution")
fig, ax = plt.subplots()
ax.pie(category_summary, labels=category_summary.index, autopct='%1.1f%%', startangle=90)
ax.axis("equal")
st.pyplot(fig)

st.write("### Expense Trend Over Time")
st.line_chart(df.groupby('Date')['Amount'].sum())

pivot = pd.pivot_table(df, values='Amount', index='Category', columns='Month', aggfunc='sum', fill_value=0)
st.write("### Category-wise Monthly Heatmap")
st.dataframe(pivot.style.background_gradient(cmap="YlGnBu"))

# -----------------------------------
# INSIGHTS
# -----------------------------------
st.subheader("💡 Insights")

col1, col2, col3 = st.columns(3)
col1.metric("Average Monthly Expense", f"₹{avg_expense:,.2f}")
col2.metric("Estimated Monthly Savings", f"₹{savings:,.2f}")
col3.metric("Savings Percentage", f"{savings_percentage:.2f}%")

# Top spending day
daily_max = df.groupby('Date')['Amount'].sum().idxmax()
st.write(f"🗓️ **Most expensive day:** {daily_max.strftime('%d %B %Y')}")

# Savings suggestions
if savings_percentage < 20:
    st.warning("⚠️ Your savings rate is below 20%. Try reducing discretionary expenses.")
elif savings_percentage > 40:
    st.success("💪 Excellent! You’re saving more than 40% of your income!")

# Top 3 categories
st.write("### 🏆 Top 3 Spending Categories:")
top3 = category_summary.head(3)
for cat, val in top3.items():
    st.write(f"- {cat}: ₹{val:,.2f}")

# -----------------------------------
# GOAL PROGRESS BAR
# -----------------------------------
st.subheader("🎯 Savings Goal Tracker")

goal = st.number_input("Set Monthly Saving Goal (₹):", min_value=0.0, step=100.0)
if goal > 0:
    progress = min((savings / goal) * 100, 100)
    st.progress(progress / 100)
    st.write(f"🎯 {progress:.1f}% of your goal achieved")

# -----------------------------------
# SIMPLE EXPENSE PREDICTION
# -----------------------------------
st.subheader("🤖 Next Month Expense Prediction (Simple Linear Trend)")

try:
    month_num = df['Date'].dt.month.values.reshape(-1, 1)
    amounts = df['Amount'].values
    model = LinearRegression().fit(month_num, amounts)
    pred = model.predict([[month_num.max() + 1]])
    st.info(f"📅 Predicted Next Month’s Expense: ₹{pred[0]:,.2f}")
except Exception:
    st.info("Not enough data to predict next month’s expenses.")

# -----------------------------------
# ALL TRANSACTIONS TABLE
# -----------------------------------
st.subheader("🧾 Detailed Transactions")
st.dataframe(df.sort_values('Date', ascending=False))

# -----------------------------------
# DOWNLOAD SECTION
# -----------------------------------
st.subheader("📤 Download Reports")

# Excel summary
output = pd.DataFrame({
    "Category": category_summary.index,
    "Total Spent": category_summary.values
})
excel_path = "financial_summary.xlsx"
output.to_excel(excel_path, index=False)

with open(excel_path, "rb") as f:
    st.download_button(
        label="⬇️ Download Excel Summary",
        data=f,
        file_name="financial_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# CSV download
csv_data = df.to_csv(index=False).encode('utf-8')
st.download_button(
    "⬇️ Download Cleaned CSV",
    csv_data,
    "cleaned_expenses.csv",
    "text/csv"
)
