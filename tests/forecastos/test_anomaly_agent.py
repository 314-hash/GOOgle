from forecastos.agents.anomaly_agent import AnomalyAgent


def test_context_anomaly_detection():
    agent = AnomalyAgent()
    # Baseline linear values
    series = [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0]
    # Inject large outlier spike
    series[5] = 150.0

    res = agent.detect_context_anomalies(series)
    assert len(res) >= 1
    assert any(a["step"] == 5 and a["severity"] == "CRITICAL" for a in res)


def test_forecast_anomaly_detection():
    agent = AnomalyAgent()
    actuals = [100.0, 250.0]  # Step 1 is outside q10-q90 interval
    points = [100.0, 105.0]
    quantiles = {
        "q10": [90.0, 95.0],
        "q90": [110.0, 115.0],
        "q20": [93.0, 98.0],
        "q80": [107.0, 112.0],
    }

    res = agent.detect_forecast_anomalies(actuals, points, quantiles)
    assert len(res) == 1
    assert res[0]["step"] == 1
    assert res[0]["severity"] == "CRITICAL"
