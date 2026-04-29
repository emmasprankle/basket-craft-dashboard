import datetime
import pandas as pd
import sys
import os
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
