# Revenue Trend Chart — Design Spec
**Date:** 2026-04-29
**Status:** Approved

## Summary

Add a monthly revenue line chart below the existing headline metrics, with date-picker controls that filter the visible range without re-querying Snowflake.

## Data

- **Source table:** `orders` in the `basket_craft.raw` schema
- **Date field:** `created_at` (nanosecond epoch — convert with `TO_TIMESTAMP_NTZ(created_at, 9)`)
- **Granularity:** monthly (`DATE_TRUNC('month', ...)`)
- **Metric:** `SUM(price_usd)` per month
- **Range:** March 2023 – March 2026 (37 months)
- **Fetch strategy:** pull all 37 rows in one cached query; filter in Python. No re-queries on filter change.

## Query

```sql
SELECT
    DATE_TRUNC('month', TO_TIMESTAMP_NTZ(created_at, 9)::DATE) AS month,
    SUM(price_usd) AS revenue
FROM orders
GROUP BY 1
ORDER BY 1
```

Returned as a pandas DataFrame with columns `month` (date) and `revenue` (float).

## Caching

`@st.cache_data(ttl=600)` — same TTL as existing `headline_metrics()`. No cache-key parameters; the full series is always fetched and sliced in Python.

## Date Filter UI

- Two `st.date_input` widgets placed in a row above the chart: **Start date** and **End date**.
- Defaults: Start = earliest month in the data, End = latest month in the data.
- Filtering is applied to the cached DataFrame in Python (`df[(df.month >= start) & (df.month <= end)]`).
- The headline metrics cards are **not** affected by the date filter — they always reflect the two most recent months.

## Chart

- Library: **Altair** (already installed as a Streamlit transitive dependency — no new packages).
- Chart type: `mark_line()` + `mark_point()` overlay so individual months are visible as dots.
- Tooltip: month (formatted as "Mon YYYY") and revenue (formatted as "$X,XXX.XX").
- Y-axis: starts at zero, labelled in dollars.
- X-axis: month labels, no manual tick specification needed.
- Rendered via `st.altair_chart(chart, use_container_width=True)`.

## Layout

```
[Title]
[Caption: showing Month A vs Month B]
[col1: Total Revenue] [col2: Total Orders] [col3: AOV] [col4: Items Sold]

--- Revenue Trend ---
[Start date picker]  [End date picker]
[Line chart — full width]
```

## Scope Boundaries

- No changes to `headline_metrics()` or its query.
- No additional metrics on the chart (orders, AOV overlays, etc.) — revenue only.
- No weekly/daily toggle — monthly only.
- No export button.
