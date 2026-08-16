from fastapi.testclient import TestClient
from forecastos.api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_create_forecast_endpoint():
    payload = {
        "series": [100.0, 105.0, 108.0, 115.0, 120.0],
        "horizon": 14,
        "frequency": "D",
        "options": {
            "quantiles": True,
            "business_context": "sales",
        },
    }
    response = client.post("/api/v1/forecast", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["horizon"] == 14
    assert len(data["point_forecast"]) == 14
    assert "quantiles" in data
    assert "hashes" in data
    assert "blockchain_audit" in data


def test_natural_language_forecast_endpoint():
    payload = {
        "prompt": "Forecast the next 14 days of sales",
        "series": [10.0, 12.0, 14.0, 16.0, 18.0],
        "frequency": "D",
    }
    response = client.post("/api/v1/forecast/natural", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["horizon"] == 14


def test_blockchain_contract_info_endpoint():
    response = client.get("/api/v1/blockchain/contract-info")
    assert response.status_code == 200
    data = response.json()
    assert data["contract_name"] == "ForecastAuditRegistry"
    assert "contract_address" in data
    assert "abi" in data
    assert len(data["abi"]) >= 3

