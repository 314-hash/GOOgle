import pytest
from forecastos.engine.model import TimesFMAdapter, get_model_adapter


def test_adapter_initialization():
    adapter = get_model_adapter()
    assert adapter is not None
    assert adapter.loaded is True


def test_adapter_forecast_output_structure():
    adapter = get_model_adapter()
    series = [10.0, 12.0, 15.0, 14.0, 18.0, 20.0, 22.0]
    horizon = 14

    res = adapter.forecast(series=series, horizon=horizon)

    assert "point_forecast" in res
    assert "quantiles" in res
    assert len(res["point_forecast"]) == horizon
    assert "q10" in res["quantiles"]
    assert "q90" in res["quantiles"]
    assert len(res["quantiles"]["q50"]) == horizon
