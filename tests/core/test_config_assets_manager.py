from unittest.mock import patch, MagicMock
import pytest
from core.config_assets_manager import ConfigAssetsManager

@pytest.fixture
def manager():
    return ConfigAssetsManager()

@patch("data.database.DataDB.update_one")
def test_add_or_update_config(mock_update_one, manager):
    manager.add_or_update_config("ADAUSDT", 10.0, 5)
    mock_update_one.assert_called_once_with(
        "config_assets",
        {"symbol": "ADAUSDT"},
        {"symbol": "ADAUSDT", "quantity": 10.0, "leverage": 5},
        upsert=True
    )

@patch("data.database.DataDB.query_single")
def test_get_config(mock_query_single, manager):
    mock_query_single.return_value = {"symbol": "ADAUSDT", "quantity": 10.0, "leverage": 5}
    config = manager.get_config("ADAUSDT")
    assert config == {"symbol": "ADAUSDT", "quantity": 10.0, "leverage": 5}
    mock_query_single.assert_called_once_with("config_assets", symbol="ADAUSDT")

@patch("data.database.DataDB.query_all")
def test_list_configs(mock_query_all, manager):
    mock_query_all.return_value = [
        {"symbol": "ADAUSDT", "quantity": 10.0, "leverage": 5},
        {"symbol": "BTCUSDT", "quantity": 20.0, "leverage": 10},
    ]
    configs = manager.list_configs()
    assert len(configs) == 2
    assert configs[0]["symbol"] == "ADAUSDT"
    mock_query_all.assert_called_once_with("config_assets")

@patch("data.database.DataDB.delete_single")
def test_remove_config(mock_delete_single, manager):
    manager.remove_config("ADAUSDT")
    mock_delete_single.assert_called_once_with("config_assets", symbol="ADAUSDT")
