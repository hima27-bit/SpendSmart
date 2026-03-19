import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import anthropic_advisor as advisor
from data_handler import load_data, save_data, add_expense, delete_expense, get_sample_data

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SpendSmart",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .metric-card {
        background: white;
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        text-align: center;
        border-left: 4px solid #1B3A6B;
    }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #1B3A6B; }
    .metric-label { font-size: 0.85rem; color: #666; margin-top: 0.2rem; }
    .section-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1B3A6B;
        border-bottom: 2px solid #1B3A6B;
        padding-bottom: 6px;
        margin-bottom: 16px;
    }
    .advice-box {
        background: #EEF4FF;
        border-left: 4px solid #2E5FA3;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-top: 0.5rem;
        color: #1a1a2e;
        line-height: 1.6;
    }
    .stButton>button {
        background-color: #1B3A6B;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.45rem 1.2rem;
        font-weight: 600;
    }
    .stButton>button:hover { background-color: #2E5FA3; }
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = load_data()
if "advice" not in st.session_state:
    st.session_state.advice = ""
if "advice_loading" not in st.session_state:
    st.session_state.advice_loading = False

df = st.session_state.df

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 SpendSmart")
    st.markdown("*Expense Interpreter & Financial Advisor*")
    st.divider()

    st.markdown("### ➕ Add Expense")
    with st.form("add_form", clear_on_submit=True):
        date_input = st.date_input("Date", value=datetime.today())
        category = st.selectbox("Category", [
            "Food & Dining", "Transport", "Shopping", "Entertainment",
            "Utilities", "Healthcare", "Education", "Others"
        ])
        amount = st.number_input("Amount (₹)", min_value=0.01, step=10.0, format="%.2f")
        description = st.text_input("Description", placeholder="e.g. Grocery run")
        submitted = st.form_submit_button("Add Expense")
        if submitted and amount > 0:
            st.session_state.df = add_expense(
                st.session_state.df, str(date_input), category, amount, description
            )
            save_data(st.session_state.df)
            st.success("Expense added!")
            df = st.session_state.df
            st.rerun()

    st.divider()
    if st.button("🔄 Load Sample Data"):
        st.session_state.df = get_sample_data()
        save_data(st.session_state.df)
        df = st.session_state.df
        st.rerun()

    if st.button("🗑️ Clear All Data"):
        st.session_state.df = pd.DataFrame(columns=["Date", "Category", "Amount", "Description"])
        save_data(st.session_state.df)
        df = st.session_state.df
        st.rerun()

# ── Main Layout ───────────────────────────────────────────────────────────────
st.markdown("# 💰 SpendSmart")
st.markdown("*Your personal expense interpreter and AI-powered financial advisor*")
st.divider()

if df.empty:
    st.info("👈 No expenses yet. Add one from the sidebar or load sample data to get started.")
    st.stop()

# ── KPI Metrics ───────────────────────────────────────────────────────────────
df["Date"] = pd.to_datetime(df["Date"])
df["Month"] = df["Date"].dt.to_period("M")

total = df["Amount"].sum()
avg_per_day = df.groupby(df["Date"].dt.date)["Amount"].sum().mean()
top_category = df.groupby("Category")["Amount"].sum().idxmax()
current_month = df["Month"].max()
monthly_total = df[df["Month"] == current_month]["Amount"].sum()

col1, col2, col3, col4 = st.columns(4)
for col, value, label in [
    (col1, f"₹{total:,.0f}", "Total Spent"),
    (col2, f"₹{monthly_total:,.0f}", f"This Month ({current_month})"),
    (col3, f"₹{avg_per_day:,.0f}", "Avg / Day"),
    (col4, top_category, "Top Category"),
]:
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts Row ────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1.1, 1])

with col_left:
    st.markdown('<div class="section-header">📊 Spending by Category</div>', unsafe_allow_html=True)
    cat_data = df.groupby("Category")["Amount"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    colors = sns.color_palette("Blues_d", len(cat_data))
    bars = ax.barh(cat_data.index, cat_data.values, color=colors)
    ax.set_xlabel("Amount (₹)", fontsize=10)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x:,.0f}"))
    for bar, val in zip(bars, cat_data.values):
        ax.text(bar.get_width() + total * 0.005, bar.get_y() + bar.get_height() / 2,
                f"₹{val:,.0f}", va='center', fontsize=8.5, color="#333")
    ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close()

with col_right:
    st.markdown('<div class="section-header">🗓️ Monthly Trend</div>', unsafe_allow_html=True)
    monthly = df.groupby("Month")["Amount"].sum().reset_index()
    monthly["Month_str"] = monthly["Month"].astype(str)
    fig2, ax2 = plt.subplots(figsize=(5.5, 3.8))
    ax2.plot(monthly["Month_str"], monthly["Amount"], marker='o', color="#1B3A6B",
             linewidth=2.5, markersize=7, markerfacecolor="#2E5FA3")
    ax2.fill_between(monthly["Month_str"], monthly["Amount"], alpha=0.12, color="#1B3A6B")
    ax2.set_ylabel("Amount (₹)", fontsize=10)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"₹{x:,.0f}"))
    ax2.tick_params(axis='x', rotation=30, labelsize=8.5)
    ax2.spines[['top', 'right']].set_visible(False)
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close()

# ── Category Pie ──────────────────────────────────────────────────────────────
col_pie, col_table = st.columns([1, 1.2])

with col_pie:
    st.markdown('<div class="section-header">🥧 Expense Share</div>', unsafe_allow_html=True)
    fig3, ax3 = plt.subplots(figsize=(5, 3.6))
    wedge_colors = sns.color_palette("Blues", len(cat_data))
    ax3.pie(cat_data.values, labels=cat_data.index, autopct='%1.1f%%',
            colors=wedge_colors, startangle=90,
            textprops={'fontsize': 8.5}, pctdistance=0.8)
    ax3.axis('equal')
    fig3.tight_layout()
    st.pyplot(fig3)
    plt.close()

with col_table:
    st.markdown('<div class="section-header">📋 Recent Transactions</div>', unsafe_allow_html=True)
    recent = df.sort_values("Date", ascending=False).head(10).copy()
    recent["Date"] = recent["Date"].dt.strftime("%d %b %Y")
    recent["Amount"] = recent["Amount"].apply(lambda x: f"₹{x:,.2f}")
    recent = recent[["Date", "Category", "Amount", "Description"]].reset_index(drop=True)

    # Delete rows
    display_df = recent.copy()
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    del_idx = st.number_input("Delete row # (from full table, 0-indexed):", min_value=0,
                               max_value=max(len(df)-1, 0), step=1, value=0)
    if st.button("🗑 Delete Row"):
        st.session_state.df = delete_expense(st.session_state.df, del_idx)
        save_data(st.session_state.df)
        st.rerun()

# ── AI Financial Advisor ──────────────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-header">🤖 AI Financial Advisor</div>', unsafe_allow_html=True)
st.markdown("Get personalised, data-driven financial advice based on your actual spending.")

if st.button("✨ Analyse My Spending & Get Advice"):
    st.session_state.advice_loading = True
    summary = advisor.build_summary(df)
    with st.spinner("Analysing your expenses..."):
        st.session_state.advice = advisor.get_advice(summary)
    st.session_state.advice_loading = False

if st.session_state.advice:
    st.markdown(f'<div class="advice-box">{st.session_state.advice}</div>', unsafe_allow_html=True)
