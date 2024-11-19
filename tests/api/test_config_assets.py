from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@patch("core.config_assets_manager.ConfigAssetsManager.list_configs", return_value=[])
def test_list_configs_empty(mock_list_configs):
    response = client.get("/api/asset-configs")
    assert response.status_code == 200
    assert response.json() == {"message": "Nenhuma configuração encontrada."}
    mock_list_configs.assert_called_once()


@patch("core.config_assets_manager.ConfigAssetsManager.list_configs")
def test_list_configs_with_data(mock_list_configs):
    mock_list_configs.return_value = [
        {"symbol": "ADAUSDT", "quantity": 7.0, "leverage": 5}
    ]
    response = client.get("/api/asset-configs")
    assert response.status_code == 200
    assert response.json() == {
        "configs": [{"symbol": "ADAUSDT", "quantity": 7.0, "leverage": 5}]
    }
    mock_list_configs.assert_called_once()

@patch("core.config_assets_manager.ConfigAssetsManager.get_config")
def test_get_config_found(mock_get_config):
    mock_get_config.return_value = {"symbol": "ADAUSDT", "quantity": 7.0, "leverage": 5}
    response = client.get("/api/asset-configs/ADAUSDT")
    assert response.status_code == 200
    assert response.json() == {"symbol": "ADAUSDT", "quantity": 7.0, "leverage": 5}
    mock_get_config.assert_called_once_with("ADAUSDT")


@patch("core.config_assets_manager.ConfigAssetsManager.get_config", return_value=None)
def test_get_config_not_found(mock_get_config):
    response = client.get("/api/asset-configs/INVALID")
    assert response.status_code == 404
    assert response.json() == {"detail": "Configuração para INVALID não encontrada."}
    mock_get_config.assert_called_once_with("INVALID")

@patch("core.config_assets_manager.ConfigAssetsManager.add_or_update_config")
def test_add_or_update_config_success(mock_add_or_update_config):
    response = client.post(
        "/api/asset-configs",
        params={"symbol": "ADAUSDT", "quantity": 10.0, "leverage": 3},  # Envia como query params
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Configuração para ADAUSDT atualizada com sucesso."}
    mock_add_or_update_config.assert_called_once_with("ADAUSDT", 10.0, 3)



def test_add_or_update_config_invalid_values():
    response = client.post(
        "/api/asset-configs",
        params={"symbol": "ADAUSDT", "quantity": -1, "leverage": 0},  # Envia como query params
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Quantity e leverage devem ser maiores que zero."}

@patch("core.config_assets_manager.ConfigAssetsManager.get_config")
@patch("core.config_assets_manager.ConfigAssetsManager.remove_config")
def test_remove_config_success(mock_remove_config, mock_get_config):
    mock_get_config.return_value = {"symbol": "ADAUSDT", "quantity": 7.0, "leverage": 5}
    response = client.delete("/api/asset-configs/ADAUSDT")
    assert response.status_code == 200
    assert response.json() == {"message": "Configuração para ADAUSDT removida com sucesso."}
    mock_get_config.assert_called_once_with("ADAUSDT")
    mock_remove_config.assert_called_once_with("ADAUSDT")


@patch("core.config_assets_manager.ConfigAssetsManager.get_config", return_value=None)
def test_remove_config_not_found(mock_get_config):
    response = client.delete("/api/asset-configs/INVALID")
    assert response.status_code == 404
    assert response.json() == {"detail": "Configuração para INVALID não encontrada."}
    mock_get_config.assert_called_once_with("INVALID")
