import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="Personal Finance Tracker", layout="centered")

st.title("💰 Personal Finance Tracker (CSV Version)")
st.write("Analyze your expenses, savings, and spending trends from a CSV file!")

# -------------------------------
# USER INPUT
# -------------------------------
income = st.number_input("Enter your Monthly Income (₹):", min_value=0.0, step=100.0)

# You can either upload OR use your fixed local file path
use_local_file = st.checkbox("Use local CSV file from Downloads folder")

if use_local_file:
    file_path = r"C:\Users\IT LAB-002\Downloads\Datasets - expenses.csv (1).csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        st.error("❌ File not found at given path.")
        st.stop()
else:
    uploaded_file = st.file_uploader("Upload your Expense CSV file", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        st.info("Please upload a CSV file or select local file option.")
        st.stop()

# -------------------------------
# PROCESS DATA
# -------------------------------
df.columns = [col.strip().capitalize() for col in df.columns]  # Normalize headers

required_cols = {'Date', 'Category', 'Amount'}
if not required_cols.issubset(df.columns):
    st.error(f"Your file must contain columns: {', '.join(required_cols)}")
    st.stop()

# Clean and process
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df.dropna(subset=['Date'], inplace=True)
df['Month'] = df['Date'].dt.month_name()

category_summary = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
monthly_summary = df.groupby('Month')['Amount'].sum()

avg_expense = np.mean(monthly_summary)
total_expense = df['Amount'].sum()
savings = income - avg_expense
savings_percentage = (savings / income) * 100 if income > 0 else 0

# -------------------------------
# DISPLAY RESULTS
# -------------------------------
st.subheader("📊 Expense Summary")
st.write("### Total Spending by Category")
st.dataframe(category_summary)

st.write("### Monthly Spending Trend")
st.bar_chart(monthly_summary)

# Pie chart
st.write("### Spending Distribution")
fig, ax = plt.subplots()
ax.pie(category_summary, labels=category_summary.index, autopct='%1.1f%%', startangle=90)
ax.axis("equal")
st.pyplot(fig)

# -------------------------------
# INSIGHTS
# -------------------------------
st.subheader("💡 Insights")
st.write(f"*Average Monthly Expense:* ₹{avg_expense:,.2f}")
st.write(f"*Estimated Monthly Savings:* ₹{savings:,.2f}")
st.write(f"*Savings Percentage:* {savings_percentage:.2f}%")

top3 = category_summary.head(3)
st.write("*Top 3 Spending Categories:*")
for cat, val in top3.items():
    st.write(f"- {cat}: ₹{val:,.2f}")

# -------------------------------
# DOWNLOAD REPORT
# -------------------------------
st.subheader("📥 Download Report")
output = pd.DataFrame({
    "Category": category_summary.index,
    "Total Spent": category_summary.values
})

excel_path = "financial_summary.xlsx"
output.to_excel(excel_path, index=False)

with open(excel_path, "rb") as f:
    st.download_button(
        label="Download Excel Report",
        data=f,
        file_name="financial_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )