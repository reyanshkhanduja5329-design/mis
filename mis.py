import streamlit as st
import pandas as pd
import os
import bcrypt
import plotly.express as px
import plotly.graph_objects as go
import json



#####


try:
    with open("data.json", "r") as f:
        data = json.load(f)
except:
    data = []







# =========================================================
# 💾 PERMANENT STORAGE SYSTEM
# =========================================================


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "mis_data.csv")

def save_permanent(df):
    df.to_csv(DATA_FILE, index=False)

def load_permanent():

    if (
        os.path.exists(DATA_FILE)
        and os.path.getsize(DATA_FILE) > 0
    ):

        try:
            return pd.read_csv(DATA_FILE, dtype=str)

        except pd.errors.EmptyDataError:
            return pd.DataFrame()

    return pd.DataFrame()

###


if "monthly_data" not in st.session_state:

    st.session_state.monthly_data = {}

    saved_df = load_permanent()

    if not saved_df.empty and "Month" in saved_df.columns:

        if "monthly_data" not in st.session_state:

            st.session_state.monthly_data = {}

    saved_df = load_permanent()

    if not saved_df.empty and "Month" in saved_df.columns:

        for month in saved_df["Month"].unique():

            month_df = saved_df[
                saved_df["Month"] == month
            ].copy()

            # remove Month column inside sheet
            month_df = month_df.drop(
                columns=["Month"],
                errors="ignore"
            )

            st.session_state.monthly_data[month] = month_df.reset_index(drop=True)



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
# ADD DATA
# =========================================================
def add_data_page():

    st.subheader("📝 Monthly Data Sheet (Multi-Month System)")

    # Month selector

    import datetime


    months = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ]

    current_month = datetime.datetime.now().strftime("%B")

    if "selected_month" not in st.session_state:
        st.session_state.selected_month = current_month

    st.session_state.selected_month = st.selectbox(
        "Select Month",
        months,
        index=months.index(st.session_state.selected_month)
    )
    

    # Load month data
    month = st.session_state.selected_month
    if month not in st.session_state.monthly_data:
        st.session_state.monthly_data[month] = pd.DataFrame({
    "Name": pd.Series(dtype="str"),
    "Sales": pd.Series(dtype="float"),
    "Expenses": pd.Series(dtype="float"),
    "Date": pd.Series(dtype="str"),
    "Month": pd.Series(dtype="str")
})


    st.write(f"### 📅 Editing: {month}")

    # Editable sheet
    edited_df = st.data_editor(
        st.session_state.monthly_data[month],
        num_rows="dynamic",
        use_container_width=True
    )
    edited_df["Month"] = month

    # Save button
    if st.button("💾 Save Month Data"):

        edited_df["Month"] = month.lower()

        st.session_state.monthly_data[month] = edited_df

        # Combine all months into one file
        combined = pd.concat(
    [
        d.assign(Month=m)
        for m, d in st.session_state.monthly_data.items()
        if not d.empty
    ],
    ignore_index=True
)

        save_permanent(combined)

        st.success(f"{month} data saved permanently!")
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

    df = get_combined_df()
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.fillna(0)

    if df.empty:
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

    df = get_combined_df()
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.fillna(0)

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

            elif growth < 0:
                st.error(f"{col} is declining 📉")

            else:
                st.info(f"{col} has no growth change ➖")

            st.divider()


# =========================================================
# SMART AI MIS CHATBOT
# =========================================================
def chatbot():

    import pandas as pd
    import plotly.express as px
    import streamlit as st

    st.subheader("🤖 Smart MIS AI Assistant")

    df = get_combined_df()

    ##
    if "Month" in df.columns:
        df["Month"] = df["Month"].astype(str).str.title()
    else:
        df["Month"] = ""
    ##

        # convert numeric columns safely
    for col in df.columns:

        if col.lower() not in ["name", "month", "date"]:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    # safety check
    if df.empty:
      st.warning("Upload data first")
      return

   # ensure Month column exists safely
    if "Month" not in df.columns:
     df["Month"] = ""

    df["Month"] = df["Month"].astype(str).str.lower()

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


    month_map = {
    "jan": "January",
    "january": "January",
    "feb": "February",
    "february": "February",
    "mar": "March",
    "march": "March",
    "apr": "April",
    "april": "April",
    "may": "May",
    "jun": "June",
    "june": "June",
    "jul": "July",
    "july": "July",
    "aug": "August",
    "august": "August",
    "sep": "September",
    "september": "September",
    "oct": "October",
    "october": "October",
    "nov": "November",
    "november": "November",
    "dec": "December",
    "december": "December"
}
    
    selected_month = None

    for key, value in month_map.items():

        if key in q:
            selected_month = value.strip().lower()
            break

    # =====================================================
    # COLUMN DETECTION
    # =====================================================
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    text_cols = df.select_dtypes(include="object").columns.tolist()

    # ensure Month is included properly
    if "Month" not in text_cols and "month" in df.columns:
        text_cols.append("Month")

    # =====================================================
    # DETECT METRIC COLUMN
    # =====================================================
    selected_metric = None

    for col in numeric_cols:
      if col.lower() in q:
        selected_metric = col
        break

# default to Sales if user only says "sales"
    if selected_metric is None:

      for col in numeric_cols:

        if "sale" in col.lower():
            selected_metric = col
            break

    # =====================================================
    # QUERY WORDS
    # =====================================================
    query_words = q.split()

     # =========================
    # COMPARE FEATURE
    # =========================

    if "compare" in q:

        comparison_items = []

        # detect months
        for key, value in month_map.items():

            if key in q:
                comparison_items.append(value)

        comparison_items = list(set(comparison_items))

        # detect metric automatically
        if selected_metric is None:

            for col in numeric_cols:

                col_lower = col.lower()

                if "sale" in q and "sale" in col_lower:
                    selected_metric = col

                elif (
                    "expense" in q or
                    "expenditure" in q
                ) and (
                    "expense" in col_lower or
                    "expenditure" in col_lower
                ):
                    selected_metric = col

                elif "profit" in q and "profit" in col_lower:
                    selected_metric = col

        # fallback
        if selected_metric is None and numeric_cols:
            selected_metric = numeric_cols[0]
        

   

        # safety check
        if selected_metric is None:
            st.error("No metric found to compare")
            return

        # compare months
        if len(comparison_items) >= 2:

            compare_data = []

            for month in comparison_items[:2]:

                temp_df = df[
                    df["Month"].astype(str).str.lower() == month.lower()
                ]

                total = pd.to_numeric(
                    temp_df[selected_metric],
                    errors="coerce"
                ).fillna(0).sum()

                compare_data.append({
                    "Month": month.title(),
                    "Value": total
                })

            compare_df = pd.DataFrame(compare_data)

            st.subheader(
                f"📊 {selected_metric} Comparison"
            )

            st.dataframe(
                compare_df,
                use_container_width=True
            )

            fig = px.bar(
                compare_df,
                x="Month",
                y="Value",
                title=f"{selected_metric} Comparison"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            return

        else:
            st.error(
                "Please mention 2 months to compare"
            )
            return
    # =====================================================
    # FILTER ROWS
    # =====================================================
    filtered_df = df.copy()

    # normalize once (IMPORTANT)
    df["Month"] = df["Month"].astype(str).str.strip().str.lower()

    selected_month = selected_month.strip().lower() if selected_month else None

    if selected_month and "Month" in df.columns:
        filtered_df = df[df["Month"] == selected_month]
    else:
        filtered_df = df.copy()

    for word in query_words:

        for col in text_cols:

            mask = filtered_df[col].astype(str).str.lower().str.contains(word)

            if mask.any():
                filtered_df = filtered_df[mask]
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

    
    # =========================
    # CLEAR ALL DATA
    # =========================

    st.sidebar.subheader("⚠️ Danger Zone")

    confirm_delete = st.sidebar.checkbox(
        "I understand this will delete everything"
    )

    if st.sidebar.button("🗑️ Clear All Data"):

        if confirm_delete:

            st.session_state.monthly_data = {}

            empty_df = pd.DataFrame()

            save_permanent(empty_df)

            st.success("All data deleted successfully")

            st.rerun()

        else:

            st.warning("Please confirm deletion first")

    
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


###
def get_combined_df():

    if "monthly_data" not in st.session_state:
        return pd.DataFrame()

    dfs = [
        df for df in st.session_state.monthly_data.values()
        if isinstance(df, pd.DataFrame) and not df.empty
    ]

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True)
###


# =========================================================
# RUN APP
# =========================================================
main()





