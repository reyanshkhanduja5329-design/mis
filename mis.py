import streamlit as st
import pandas as pd
import os
import bcrypt
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# 💾 PERMANENT STORAGE SYSTEM
# =========================================================


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "mis_data.csv")

def save_permanent(df):
    df.to_csv(DATA_FILE, index=False)

def load_permanent():
    try:
        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
            return pd.read_csv(DATA_FILE)
    except:
        pass
    return pd.DataFrame()
# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Advanced MIS Dashboard",
    layout="wide",
    page_icon="📊"
)

st.title("🏢 Advanced Company MIS Dashboard")

# =========================================================
# SESSION STATE
# =========================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "df" not in st.session_state:
    st.session_state.df = None


# AUTO LOAD DATA WHEN APP STARTS
st.session_state.df = load_permanent()

# =========================================================
# USERS
# =========================================================
USERS = {
    "admin": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()),
    "employee": bcrypt.hashpw("emp123".encode(), bcrypt.gensalt())
}

# =========================================================
# LOGIN PAGE
# =========================================================
def login():

    st.subheader("🔐 Secure Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if username in USERS:

            if bcrypt.checkpw(
                password.encode(),
                USERS[username]
            ):

                st.session_state.logged_in = True
                st.success("Login Successful")
                st.rerun()

        st.error("Invalid Credentials")


# =========================================================
# FILE UPLOAD
# =========================================================
def add_data_page():

    st.subheader("📝 Manual Data Sheet (Live Entry)")

    # If no data exists, create empty table
    if st.session_state.df is None:
        st.session_state.df = pd.DataFrame()

    # Editable spreadsheet
    edited_df = st.data_editor(
        st.session_state.df,
        num_rows="dynamic",
        use_container_width=True
    )

    # Save button
    if st.button("💾 Save Data Permanently"):

        st.session_state.df = edited_df
        save_permanent(edited_df)

        st.success("Data saved permanently!")
# =========================================================
# KPI SECTION
# =========================================================
def show_kpis(df, numeric_cols):

    st.subheader("📈 Business KPIs")

    cols = st.columns(min(4, len(numeric_cols)))

    for i, col in enumerate(numeric_cols[:4]):

        total = df[col].sum()

        growth = 0

        if len(df[col]) > 1:

            first = df[col].iloc[0]
            last = df[col].iloc[-1]

            if first != 0:
                growth = ((last - first) / first) * 100

        cols[i].metric(
            label=col,
            value=f"{total:,.2f}",
            delta=f"{growth:.2f}%"
        )


# =========================================================
# DASHBOARD PAGE
# =========================================================
def dashboard():

    st.subheader("📊 Executive Dashboard")

    df = st.session_state.df

    if df is None:
        st.warning("Please upload data first")
        return

    # DISPLAY DATA
    with st.expander("📄 View Raw Data"):
        st.dataframe(df, use_container_width=True)

    # GET NUMERIC COLUMNS
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    if not numeric_cols:
        st.error("No numeric columns found")
        return

    # DATE COLUMN DETECTION
    date_col = None

    for col in df.columns:
        if "date" in col.lower() or "month" in col.lower():
            date_col = col
            break

    # SIDEBAR FILTERS
    st.sidebar.subheader("📌 Dashboard Filters")

    selected_metrics = st.sidebar.multiselect(
        "Select Metrics",
        numeric_cols,
        default=numeric_cols[:3]
    )

    chart_type = st.sidebar.selectbox(
        "Chart Type",
        ["Line", "Bar", "Area"]
    )

    # KPI DISPLAY
    show_kpis(df, numeric_cols)

    # =====================================================
    # TREND CHARTS
    # =====================================================
    st.subheader("📉 Trend Analysis")

    x_axis = date_col if date_col else df.index

    for metric in selected_metrics:

        if chart_type == "Line":

            fig = px.line(
                df,
                x=x_axis,
                y=metric,
                markers=True,
                title=f"{metric} Trend"
            )

        elif chart_type == "Bar":

            fig = px.bar(
                df,
                x=x_axis,
                y=metric,
                title=f"{metric} Comparison"
            )

        else:

            fig = px.area(
                df,
                x=x_axis,
                y=metric,
                title=f"{metric} Area Analysis"
            )

        st.plotly_chart(fig, use_container_width=True)

    # =====================================================
    # MULTI METRIC COMPARISON
    # =====================================================
    st.subheader("📊 Multi-Metric Comparison")

    if len(selected_metrics) >= 2:

        fig = px.line(
            df,
            x=x_axis,
            y=selected_metrics,
            markers=True,
            title="Business Metrics Comparison"
        )

        st.plotly_chart(fig, use_container_width=True)

    # =====================================================
    # PIE CHART
    # =====================================================
    st.subheader("🥧 Distribution Analysis")

    pie_metric = st.selectbox(
        "Select Metric for Pie Chart",
        numeric_cols
    )

    fig = px.pie(
        df,
        names=df.index,
        values=pie_metric,
        title=f"{pie_metric} Distribution"
    )

    st.plotly_chart(fig, use_container_width=True)

    # =====================================================
    # CORRELATION HEATMAP
    # =====================================================
    st.subheader("🔥 Correlation Heatmap")

    corr = df[numeric_cols].corr()

    fig = px.imshow(
        corr,
        text_auto=True,
        aspect="auto",
        title="Metric Correlation"
    )

    st.plotly_chart(fig, use_container_width=True)


# =========================================================
# AI INSIGHTS PAGE
# =========================================================
def insights():

    st.subheader("🧠 AI Business Insights")

    df = st.session_state.df

    if df is None:
        st.warning("Upload data first")
        return

    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    for col in numeric_cols:

        total = df[col].sum()
        avg = df[col].mean()
        highest = df[col].max()
        lowest = df[col].min()

        growth = 0

        if len(df[col]) > 1:

            first = df[col].iloc[0]
            last = df[col].iloc[-1]

            if first != 0:
                growth = ((last - first) / first) * 100

        with st.container():

            st.markdown(f"## 📌 {col}")

            c1, c2, c3, c4 = st.columns(4)

            c1.metric("Total", f"{total:,.2f}")
            c2.metric("Average", f"{avg:,.2f}")
            c3.metric("Highest", f"{highest:,.2f}")
            c4.metric("Growth", f"{growth:.2f}%")

            if growth > 0:
                st.success(f"{col} is growing positively 📈")
            else:
                st.error(f"{col} is declining 📉")

            st.divider()


# =========================================================
# SMART AI MIS CHATBOT
# =========================================================
def chatbot():

    import pandas as pd
    import plotly.express as px
    import streamlit as st

    st.subheader("🤖 Smart MIS AI Assistant")

    df = st.session_state.df

    if df is None:
        st.warning("Upload data first")
        return

    q = st.text_input(
        "Ask business questions",
        placeholder="""
Examples:
- sales in jan
- rahul salary
- compare sales in jan and feb
- compare rahul and amit salary
- profit in march
- highest sales
"""
    )

    if not q:
        return

    q = q.lower()

    # =====================================================
    # COLUMN DETECTION
    # =====================================================
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    text_cols = df.select_dtypes(include="object").columns.tolist()

    # =====================================================
    # DETECT METRIC COLUMN
    # =====================================================
    selected_metric = None

    for col in numeric_cols:

        if col.lower() in q:
            selected_metric = col
            break

    # =====================================================
    # QUERY WORDS
    # =====================================================
    query_words = q.split()

    # =====================================================
    # COMPARE LOGIC
    # =====================================================
    if "compare" in q:

        matched_values = []

        for col in text_cols:

            unique_vals = (
                df[col]
                .astype(str)
                .str.lower()
                .unique()
            )

            for val in unique_vals:

                if val in q:
                    matched_values.append(val)

        matched_values = list(set(matched_values))

        if len(matched_values) >= 2 and selected_metric:

            comparison_data = []

            for val in matched_values[:2]:

                temp = df[
                    df.astype(str)
                    .apply(
                        lambda row:
                        row.str.lower()
                        .str.contains(val)
                        .any(),
                        axis=1
                    )
                ]

                if not temp.empty:

                    total = temp[selected_metric].sum()

                    comparison_data.append({
                        "Category": val.title(),
                        "Value": total
                    })

            if comparison_data:

                compare_df = pd.DataFrame(comparison_data)

                st.subheader(
                    f"📊 Comparison of {selected_metric}"
                )

                st.dataframe(
                    compare_df,
                    use_container_width=True
                )

                fig = px.bar(
                    compare_df,
                    x="Category",
                    y="Value",
                    title=f"{selected_metric} Comparison"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

                return

    # =====================================================
    # FILTER ROWS
    # =====================================================
    filtered_df = df.copy()

    for word in query_words:

        if word in [
            "compare",
            "total",
            "highest",
            "lowest",
            "average",
            "trend",
            "profit",
            "salary",
            "sales",
            "expenses"
        ]:
            continue

        found = False

        for col in text_cols:

            mask = (
                filtered_df[col]
                .astype(str)
                .str.lower()
                .str.contains(word)
            )

            if mask.any():

                filtered_df = filtered_df[mask]

                found = True

                break

    # =====================================================
    # NO RESULTS
    # =====================================================
    if filtered_df.empty:

        st.error("No matching data found")

        return

    # =====================================================
    # SHOW DATA
    # =====================================================
    st.success(
        f"Found {len(filtered_df)} matching rows"
    )

    st.dataframe(
        filtered_df,
        use_container_width=True
    )

    # =====================================================
    # PROFIT CALCULATION
    # =====================================================
    if "profit" in q:

        sales_col = None
        expense_col = None

        for col in numeric_cols:

            if "sale" in col.lower():
                sales_col = col

            if "expense" in col.lower():
                expense_col = col

        if sales_col and expense_col:

            total_sales = filtered_df[sales_col].sum()

            total_expenses = (
                filtered_df[expense_col].sum()
            )

            profit = total_sales - total_expenses

            st.subheader("💰 Profit Analysis")

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "Sales",
                f"{total_sales:,.2f}"
            )

            c2.metric(
                "Expenses",
                f"{total_expenses:,.2f}"
            )

            c3.metric(
                "Profit",
                f"{profit:,.2f}"
            )

            profit_df = pd.DataFrame({
                "Category": [
                    "Sales",
                    "Expenses",
                    "Profit"
                ],
                "Amount": [
                    total_sales,
                    total_expenses,
                    profit
                ]
            })

            fig = px.bar(
                profit_df,
                x="Category",
                y="Amount",
                title="Profit Breakdown"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            return

    # =====================================================
    # TOTAL
    # =====================================================
    if "total" in q and selected_metric:

        total = filtered_df[selected_metric].sum()

        st.metric(
            f"Total {selected_metric}",
            f"{total:,.2f}"
        )

    # =====================================================
    # AVERAGE
    # =====================================================
    elif "average" in q and selected_metric:

        avg = filtered_df[selected_metric].mean()

        st.metric(
            f"Average {selected_metric}",
            f"{avg:,.2f}"
        )

    # =====================================================
    # HIGHEST
    # =====================================================
    elif "highest" in q and selected_metric:

        highest = filtered_df[selected_metric].max()

        highest_row = filtered_df[
            filtered_df[selected_metric]
            == highest
        ]

        st.metric(
            f"Highest {selected_metric}",
            f"{highest:,.2f}"
        )

        st.subheader("🏆 Highest Record")

        st.dataframe(
            highest_row,
            use_container_width=True
        )

    # =====================================================
    # LOWEST
    # =====================================================
    elif "lowest" in q and selected_metric:

        lowest = filtered_df[selected_metric].min()

        lowest_row = filtered_df[
            filtered_df[selected_metric]
            == lowest
        ]

        st.metric(
            f"Lowest {selected_metric}",
            f"{lowest:,.2f}"
        )

        st.subheader("📉 Lowest Record")

        st.dataframe(
            lowest_row,
            use_container_width=True
        )

    # =====================================================
    # TREND
    # =====================================================
    elif "trend" in q and selected_metric:

        fig = px.line(
            filtered_df,
            y=selected_metric,
            markers=True,
            title=f"{selected_metric} Trend"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # =====================================================
    # GENERAL METRIC DISPLAY
    # =====================================================
    elif selected_metric:

        total = filtered_df[selected_metric].sum()

        avg = filtered_df[selected_metric].mean()

        highest = filtered_df[selected_metric].max()

        lowest = filtered_df[selected_metric].min()

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Total",
            f"{total:,.2f}"
        )

        c2.metric(
            "Average",
            f"{avg:,.2f}"
        )

        c3.metric(
            "Highest",
            f"{highest:,.2f}"
        )

        c4.metric(
            "Lowest",
            f"{lowest:,.2f}"
        )

        fig = px.bar(
            filtered_df,
            y=selected_metric,
            title=f"{selected_metric} Analysis"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # =====================================================
    # HELP MESSAGE
    # =====================================================
    else:

        st.info("""
Supported Questions:

• sales in jan
• rahul salary
• compare sales in jan and feb
• compare rahul and amit salary
• total sales
• average salary
• highest sales
• lowest expenses
• salary trend
• profit in march
• profit for rahul
""")
        

# =========================================================
# ✏️ IN-APP DATA EDITOR
# =========================================================


# =========================================================
# MAIN APP
# =========================================================
def main():

    if not st.session_state.logged_in:
        login()
        st.stop()

    # SIDEBAR
    st.sidebar.title("📌 Navigation")

    menu = st.sidebar.radio(
    "Go To",
    [
        "Add Data",
        "Dashboard",
        "AI Insights",
        "AI Chatbot",
        "Logout"
    ]
)

    if menu == "Add Data":
        add_data_page()

    elif menu == "Dashboard":
        dashboard()

    elif menu == "AI Insights":
        insights()

    elif menu == "AI Chatbot":
        chatbot()



    elif menu == "Logout":

        st.session_state.logged_in = False
        st.rerun()


# =========================================================
# RUN APP
# =========================================================
main()
