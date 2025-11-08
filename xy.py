import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="💰 Personal Finance Tracker", layout="centered")

st.title("💰 Personal Finance Tracker")
st.write("""
Welcome to your **Personal Finance Dashboard**!  
Here, you can upload your expense data, visualize your spending habits, and calculate savings.  
Let's get started 👇
""")

# -------------------------------
# USER INPUTS
# -------------------------------
st.sidebar.header("⚙️ Input Options")

income = st.sidebar.number_input("💵 Monthly Income (₹):", min_value=0.0, step=100.0)
st.sidebar.write("---")

use_local_file = st.sidebar.checkbox("📂 Use local CSV file from Downloads")

if use_local_file:
    file_path = r"C:\Users\IT LAB-002\Downloads\Datasets - expenses.csv (1).csv"
    if os.path.exists(file_path):
        df = pd.read_csv(r"C:\Users\sunro\Downloads\Datasets - expenses.csv")
        st.success("✅ Local file loaded successfully!")
    else:
        st.error("❌ File not found. Please check the file path.")
        st.stop()
else:
    uploaded_file = st.file_uploader("📤 Upload your Expense CSV file", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("✅ File uploaded successfully!")
    else:
        st.info("Please upload a CSV file or select local file option from sidebar.")
        st.stop()

# -------------------------------
# DATA PREPARATION
# -------------------------------
df.columns = [col.strip().capitalize() for col in df.columns]

required_cols = {'Date', 'Category', 'Amount'}
if not required_cols.issubset(df.columns):
    st.error(f"Your file must contain columns: {', '.join(required_cols)}")
    st.stop()

df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df.dropna(subset=['Date'], inplace=True)
df['Month'] = df['Date'].dt.month_name()

# -------------------------------
# FILTER SECTION
# -------------------------------
st.sidebar.header("🔍 Filter Your Data")

months = df['Month'].unique().tolist()
categories = df['Category'].unique().tolist()

selected_months = st.sidebar.multiselect("📅 Select Month(s):", months, default=months)
selected_categories = st.sidebar.multiselect("🏷️ Select Category(s):", categories, default=categories)

filtered_df = df[(df['Month'].isin(selected_months)) & (df['Category'].isin(selected_categories))]

# -------------------------------
# CALCULATIONS
# -------------------------------
category_summary = filtered_df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
monthly_summary = filtered_df.groupby('Month')['Amount'].sum().sort_index()

avg_expense = np.mean(monthly_summary) if not monthly_summary.empty else 0
total_expense = filtered_df['Amount'].sum()
savings = income - avg_expense
savings_percentage = (savings / income) * 100 if income > 0 else 0

# -------------------------------
# DISPLAY METRICS
# -------------------------------
st.write("## 📈 Financial Overview")

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Expense", f"₹{total_expense:,.2f}")
col2.metric("💸 Avg. Monthly Expense", f"₹{avg_expense:,.2f}")
col3.metric("💵 Est. Savings", f"₹{savings:,.2f}")

if income > 0:
    st.progress(int(min(savings_percentage, 100)))
    st.caption(f"Savings: {savings_percentage:.1f}% of your income")

# -------------------------------
# EXPENSE ANALYSIS
# -------------------------------
st.write("## 📊 Expense Breakdown")

tab1, tab2, tab3 = st.tabs(["Category View", "Monthly Trend", "Data Table"])

with tab1:
    st.bar_chart(category_summary)
    fig1, ax1 = plt.subplots()
    ax1.pie(category_summary, labels=category_summary.index, autopct='%1.1f%%', startangle=90)
    ax1.axis("equal")
    st.pyplot(fig1)

with tab2:
    st.line_chart(monthly_summary)

with tab3:
    st.dataframe(filtered_df)

# -------------------------------
# INSIGHTS
# -------------------------------
st.write("## 💡 Insights & Highlights")

top3 = category_summary.head(3)
if not top3.empty:
    st.write("### 🏆 Top 3 Spending Categories:")
    for cat, val in top3.items():
        st.write(f"- **{cat}**: ₹{val:,.2f}")

    if savings > 0:
        st.success("✅ Great job! You're saving money each month.")
    elif savings == 0:
        st.warning("⚠️ You're breaking even. Try cutting small unnecessary costs.")
    else:
        st.error("🚨 You're spending more than you earn! Consider reviewing your top expense categories.")

# -------------------------------
# DOWNLOAD REPORT
# -------------------------------
st.write("## 📥 Download Your Report")

output = pd.DataFrame({
    "Category": category_summary.index,
    "Total Spent": category_summary.values
})

excel_path = "financial_summary.xlsx"
output.to_excel(excel_path, index=False)

with open(excel_path, "rb") as f:
    st.download_button(
        label="⬇️ Download Excel Report",
        data=f,
        file_name="financial_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.caption("💡 Tip: Use the filters in the sidebar to analyze specific months or categories.")
