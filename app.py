import os
import streamlit as st
import snowflake.connector
from dotenv import load_dotenv
import pandas as pd
import altair as alt

load_dotenv()

def get_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )


def filter_by_date_range(df, start, end):
    mask = (df["month"] >= pd.Timestamp(start)) & (df["month"] <= pd.Timestamp(end))
    return df[mask].copy()


@st.cache_data(ttl=600)
def revenue_trend():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                DATE_TRUNC('month', TO_TIMESTAMP_NTZ(created_at, 9)::DATE) AS month,
                SUM(price_usd) AS revenue
            FROM orders
            GROUP BY 1
            ORDER BY 1
        """)
        rows = cur.fetchall()
    finally:
        conn.close()
    df = pd.DataFrame(rows, columns=["month", "revenue"])
    df["month"] = pd.to_datetime(df["month"])
    return df


@st.cache_data(ttl=600)
def top_products(start, end):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                p.product_name,
                SUM(oi.price_usd) AS revenue
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE TO_TIMESTAMP_NTZ(oi.created_at, 9)::DATE BETWEEN %s AND %s
            GROUP BY 1
            ORDER BY 2 DESC
        """, (start, end))
        rows = cur.fetchall()
    finally:
        conn.close()
    return pd.DataFrame(rows, columns=["product", "revenue"])


@st.cache_data(ttl=600)
def headline_metrics():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            WITH months AS (
                SELECT
                    DATE_TRUNC('month', TO_TIMESTAMP_NTZ(created_at, 9)::DATE) AS month,
                    SUM(price_usd)                               AS revenue,
                    COUNT(order_id)                              AS orders,
                    SUM(items_purchased)                         AS items_sold,
                    SUM(price_usd) / NULLIF(COUNT(order_id), 0) AS aov
                FROM orders
                GROUP BY 1
            ),
            ranked AS (
                SELECT *, ROW_NUMBER() OVER (ORDER BY month DESC) AS rn FROM months
            )
            SELECT
                MAX(CASE WHEN rn = 1 THEN revenue    END),
                MAX(CASE WHEN rn = 2 THEN revenue    END),
                MAX(CASE WHEN rn = 1 THEN orders     END),
                MAX(CASE WHEN rn = 2 THEN orders     END),
                MAX(CASE WHEN rn = 1 THEN aov        END),
                MAX(CASE WHEN rn = 2 THEN aov        END),
                MAX(CASE WHEN rn = 1 THEN items_sold END),
                MAX(CASE WHEN rn = 2 THEN items_sold END),
                MAX(CASE WHEN rn = 1 THEN month      END),
                MAX(CASE WHEN rn = 2 THEN month      END)
            FROM ranked WHERE rn <= 2
        """)
        row = cur.fetchone()
    finally:
        conn.close()
    return row


def pct_delta(curr, prev):
    """Return percentage change as a signed string like '+4.2%'."""
    if prev and prev != 0:
        pct = (curr - prev) / prev * 100
        return f"{pct:+.1f}%"
    return "N/A"

# ── Layout ────────────────────────────────────────────────────────────────────
st.title("BasketCraft Dashboard")

(
    curr_rev, prev_rev,
    curr_ord, prev_ord,
    curr_aov, prev_aov,
    curr_items, prev_items,
    curr_month, prev_month,
) = headline_metrics()

curr_label = curr_month.strftime("%b %Y") if curr_month else "Current"
prev_label = prev_month.strftime("%b %Y") if prev_month else "Prior"

st.caption(f"Showing **{curr_label}** vs **{prev_label}**")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Revenue",
    f"${curr_rev:,.2f}",
    delta=pct_delta(curr_rev, prev_rev),
)
col2.metric(
    "Total Orders",
    f"{curr_ord:,}",
    delta=pct_delta(curr_ord, prev_ord),
)
col3.metric(
    "Avg Order Value",
    f"${curr_aov:,.2f}",
    delta=pct_delta(curr_aov, prev_aov),
)
col4.metric(
    "Items Sold",
    f"{curr_items:,}",
    delta=pct_delta(curr_items, prev_items),
)

# ── Revenue Trend ─────────────────────────────────────────────────────────────
st.subheader("Revenue Trend")

trend_df = revenue_trend()

st.sidebar.header("Filters")
end_date = st.sidebar.date_input(
    "End date",
    value=trend_df["month"].max().date(),
    min_value=trend_df["month"].min().date(),
    max_value=trend_df["month"].max().date(),
)
start_date = st.sidebar.date_input(
    "Start date",
    value=trend_df["month"].min().date(),
    min_value=trend_df["month"].min().date(),
    max_value=end_date,
)

filtered_df = filter_by_date_range(trend_df, start_date, end_date)

if filtered_df.empty:
    st.info("No data in the selected date range.")
else:
    base = alt.Chart(filtered_df).encode(
        x=alt.X("month:T", title="Month", axis=alt.Axis(format="%b %Y", labelAngle=-45)),
        y=alt.Y("revenue:Q", title="Revenue ($)", scale=alt.Scale(zero=True)),
        tooltip=[
            alt.Tooltip("month:T", title="Month", format="%b %Y"),
            alt.Tooltip("revenue:Q", title="Revenue ($)", format="$,.2f"),
        ],
    )
    chart = base.mark_line() + base.mark_point(size=60)
    st.altair_chart(chart, use_container_width=True)

# ── Top Products by Revenue ───────────────────────────────────────────────────
st.subheader("Top Products by Revenue")

products_df = top_products(start_date, end_date)

if products_df.empty:
    st.info("No data in the selected date range.")
else:
    bar = alt.Chart(products_df).mark_bar().encode(
        x=alt.X("revenue:Q", title="Revenue ($)"),
        y=alt.Y("product:N", sort="-x", title=None),
        tooltip=[
            alt.Tooltip("product:N", title="Product"),
            alt.Tooltip("revenue:Q", title="Revenue ($)", format="$,.2f"),
        ],
    )
    st.altair_chart(bar, use_container_width=True)
