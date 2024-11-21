from unittest.mock import patch, MagicMock
import pytest
from core.config_system_manager import ConfigSystemManager

@pytest.fixture
def manager():
    return ConfigSystemManager()

@patch("data.database.DataDB.update_one")
def test_update_system_config(mock_update_one, manager):
    manager.update_system_config(1000.0, 50.0, 5.0)
    mock_update_one.assert_called_once_with(
        "config_system",
        {},
        {"$set": {
            "total_earnings": 1000.0,
            "percentage_of_total": 50.0,
            "breakeven_profit_threshold": 5.0,
        }},
        upsert=True
    )

@patch("data.database.DataDB.query_single")
def test_get_system_config(mock_query_single, manager):
    mock_query_single.return_value = {
        "total_earnings": 1000.0,
        "percentage_of_total": 50.0,
        "breakeven_profit_threshold": 5.0,
    }
    config = manager.get_system_config()
    assert config["total_earnings"] == 1000.0
    assert config["percentage_of_total"] == 50.0
    mock_query_single.assert_called_once_with("config_system")

@patch("data.database.DataDB.delete_many")
def test_remove_system_config(mock_delete_many, manager):
    manager.remove_system_config()
    mock_delete_many.assert_called_once_with("config_system", {})
