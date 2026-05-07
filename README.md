# BasketCraft Dashboard

**Live app:** https://basket-craft-dashboard-bc3nhi7erntkycsmujvrak.streamlit.app

A Streamlit dashboard connected to a Snowflake data warehouse, built for ISBA 4715.

## Features

- **Headline metrics** — total revenue, orders, average order value, and items sold with month-over-month delta
- **Revenue trend** — monthly line chart with interactive date range filter
- **Top products by revenue** — horizontal bar chart that respects the date filter

## Running locally

```bash
pip install -r requirements.txt
```

Add a `.env` file with your Snowflake credentials:

```
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USER=
SNOWFLAKE_PASSWORD=
SNOWFLAKE_ROLE=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_DATABASE=
SNOWFLAKE_SCHEMA=
```

```bash
streamlit run app.py
```

## Deploying to Streamlit Cloud

Add the same credentials as secrets in the app's **Manage app → Secrets** panel.
