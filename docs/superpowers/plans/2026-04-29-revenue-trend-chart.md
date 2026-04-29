# Revenue Trend Chart Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a monthly revenue line chart with Altair below the headline metrics, filterable by start and end date pickers.

**Architecture:** A single cached Snowflake query fetches all 37 months of revenue into a pandas DataFrame. A pure `filter_by_date_range()` helper slices it based on `st.date_input` widget values. An Altair layered chart (line + point) renders the filtered data with hover tooltips. The existing `headline_metrics()` function and its query are untouched.

**Tech Stack:** Python 3.12, Streamlit 1.57, Altair 6.1, pandas, snowflake-connector-python, pytest 8.4

---

### Task 1: Write failing tests for `filter_by_date_range`

**Files:**
- Create: `tests/test_revenue_trend.py`

- [ ] **Step 1: Create the test file**

```python
# tests/test_revenue_trend.py
import datetime
import pandas as pd
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import filter_by_date_range


def _make_df():
    return pd.DataFrame({
        "month": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01"]),
        "revenue": [1000.0, 2000.0, 3000.0, 4000.0],
    })


def test_filter_keeps_rows_within_range():
    df = _make_df()
    result = filter_by_date_range(df, datetime.date(2024, 2, 1), datetime.date(2024, 3, 1))
    assert len(result) == 2
    assert list(result["revenue"]) == [2000.0, 3000.0]


def test_filter_inclusive_bounds():
    df = _make_df()
    result = filter_by_date_range(df, datetime.date(2024, 1, 1), datetime.date(2024, 4, 1))
    assert len(result) == 4


def test_filter_returns_empty_when_range_outside_data():
    df = _make_df()
    result = filter_by_date_range(df, datetime.date(2025, 1, 1), datetime.date(2025, 3, 1))
    assert len(result) == 0


def test_filter_preserves_column_names():
    df = _make_df()
    result = filter_by_date_range(df, datetime.date(2024, 1, 1), datetime.date(2024, 4, 1))
    assert list(result.columns) == ["month", "revenue"]
```

- [ ] **Step 2: Run the tests — expect ImportError on `filter_by_date_range`**

```
cd /Users/emmasprankle/Desktop/isba-4715/basket-craft-dashboard
python -m pytest tests/test_revenue_trend.py -v
```

Expected output contains: `ImportError` or `cannot import name 'filter_by_date_range'`

---

### Task 2: Implement `filter_by_date_range` and the `revenue_trend` query in `app.py`

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Add `import pandas as pd` and the two new functions**

At the top of `app.py`, after `from dotenv import load_dotenv`, add:

```python
import pandas as pd
```

After the existing `get_connection()` function (before `headline_metrics`), add:

```python
def filter_by_date_range(df, start, end):
    mask = (df["month"] >= pd.Timestamp(start)) & (df["month"] <= pd.Timestamp(end))
    return df[mask].copy()


@st.cache_data(ttl=600)
def revenue_trend():
    conn = get_connection()
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
    conn.close()
    df = pd.DataFrame(rows, columns=["month", "revenue"])
    df["month"] = pd.to_datetime(df["month"])
    return df
```

- [ ] **Step 2: Run the tests — all four should pass**

```
python -m pytest tests/test_revenue_trend.py -v
```

Expected output:
```
PASSED tests/test_revenue_trend.py::test_filter_keeps_rows_within_range
PASSED tests/test_revenue_trend.py::test_filter_inclusive_bounds
PASSED tests/test_revenue_trend.py::test_filter_returns_empty_when_range_outside_data
PASSED tests/test_revenue_trend.py::test_filter_preserves_column_names
4 passed
```

- [ ] **Step 3: Commit**

```bash
git add app.py tests/test_revenue_trend.py
git commit -m "feat: add revenue_trend query and filter_by_date_range helper"
```

---

### Task 3: Add date pickers and Altair chart to the dashboard

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Add the chart section at the bottom of `app.py`**

Add `import altair as alt` at the top of `app.py` with the other imports.

Then append this block at the bottom of `app.py`, after the existing `col4.metric(...)` call:

```python
# ── Revenue Trend ─────────────────────────────────────────────────────────────
st.subheader("Revenue Trend")

trend_df = revenue_trend()

date_col1, date_col2 = st.columns(2)
start_date = date_col1.date_input(
    "Start date",
    value=trend_df["month"].min().date(),
    min_value=trend_df["month"].min().date(),
    max_value=trend_df["month"].max().date(),
)
end_date = date_col2.date_input(
    "End date",
    value=trend_df["month"].max().date(),
    min_value=trend_df["month"].min().date(),
    max_value=trend_df["month"].max().date(),
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
```

- [ ] **Step 2: Verify the app loads without error**

```
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501/healthz
```

Expected: `200`

If the server isn't running:
```
streamlit run app.py --server.headless true &
sleep 4
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501/healthz
```

- [ ] **Step 3: Open http://localhost:8501 and manually verify**

Checklist:
- [ ] "Revenue Trend" subheader appears below the four metric cards
- [ ] Two date pickers show correct default values (2023-03-01 and 2026-03-01)
- [ ] Line chart renders with 37 monthly data points
- [ ] Hovering a point shows a tooltip with month name and dollar-formatted revenue
- [ ] Changing the start date to 2025-01-01 re-renders the chart with fewer points
- [ ] Setting start date after end date shows the "No data in the selected date range" message

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: add revenue trend line chart with date range filter"
```
