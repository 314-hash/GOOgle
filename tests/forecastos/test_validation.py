import pytest
import pandas as pd
from forecastos.data.validation import (
    ValidationError,
    validate_dataframe,
    validate_time_series_input,
)


def test_validate_empty_series_raises_error():
    with pytest.raises(ValidationError):
        validate_time_series_input([])


def test_validate_mismatched_dates_raises_error():
    with pytest.raises(ValidationError):
        validate_time_series_input([10.0, 20.0], dates=["2026-01-01"])


def test_validate_valid_series():
    arr, dates = validate_time_series_input([10.0, 20.0, 30.0], dates=["2026-01-01", "2026-01-02", "2026-01-03"])
    assert len(arr) == 3
    assert len(dates) == 3


def test_validate_dataframe():
    df = pd.DataFrame({
        "timestamp": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "value": [100.0, 105.0, 110.0],
    })
    res = validate_dataframe(df)
    assert res["row_count"] == 3
    assert res["min_value"] == 100.0
    assert res["max_value"] == 110.0
