from fastapi.testclient import TestClient
from forecastos.api.main import app

client = TestClient(app)


def test_chat_forecast_query():
    payload = {
        "message": "Forecast the next 14 days of sales",
        "series": [100.0, 105.0, 110.0, 115.0, 120.0],
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert data["intent"] == "forecast_execution"
    assert "suggestions" in data


def test_chat_anomaly_query():
    payload = {
        "message": "Are there any anomalies in my data?",
        "series": [10.0, 11.0, 12.0, 150.0, 14.0],
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert data["intent"] == "anomaly_check"


def test_chat_blockchain_query():
    payload = {
        "message": "What is the smart contract address and ABI?",
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert data["intent"] == "blockchain_info"
    assert "contract_address" in data["action_data"]
