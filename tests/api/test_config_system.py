import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_system_config_not_found():
    response = client.get("/api/system-configs")
    assert response.status_code == 200

def test_update_system_config():
    response = client.post(
        "/api/system-configs",
        params={"total_earnings": 500.0, "percentage_of_total": 10.0, "breakeven_profit_threshold": 0.005},  # Envia como query params
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "Configurações gerais atualizadas com sucesso.",
        "total_earnings": 500.0,
        "percentage_of_total": 10.0,
    }


def test_update_system_config_invalid_values():
    response = client.post(
        "/api/system-configs",
        params={"total_earnings": -1.0, "percentage_of_total": 5.0, "breakeven_profit_threshold": 0.005},  # Envia como query params
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Os valores devem ser positivos."}


def test_remove_system_config():
    client.post(
        "/api/system-configs",
        params={"total_earnings": 500.0, "percentage_of_total": 10.0, "breakeven_profit_threshold": 0.005},
    )
    response = client.delete("/api/system-configs")
    assert response.status_code == 200
    assert response.json() == {"message": "Configurações gerais removidas com sucesso."}

def test_remove_system_config_not_found():
    response = client.delete("/api/system-configs")
    assert response.status_code == 200
