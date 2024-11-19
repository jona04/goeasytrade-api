from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app  # Importar o app principal

client = TestClient(app)

@patch("core.instances.trader_manager.start_trading")
def test_start_trading(mock_start_trading):
    mock_start_trading.return_value = {"status": "success", "message": "Trading started for BTCUSDT"}

    response = client.post(
        "/trading/start/BTCUSDT",
        params={
            "bar_length": "1h",
            "strategy_type": 1,
            "ema_s": 10,
            "emaper_s": 20,
            "emaper_l": 50,
            "emaper_force": 1.5,
            "sl_percent": 0.02,
        },  # Envia como query params
    )
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Trading started for BTCUSDT"}
    mock_start_trading.assert_called_once()


@patch("core.instances.trader_manager.start_trading")
def test_start_trading_already_active(mock_start_trading):
    mock_start_trading.return_value = {
        "status": "error",
        "message": "Trading is already running with the same parameters - trade_id_123",
    }

    response = client.post(
        "/trading/start/BTCUSDT",
        params={
            "bar_length": "1h",
            "strategy_type": 1,
            "ema_s": 10,
            "emaper_s": 20,
            "emaper_l": 50,
            "emaper_force": 1.5,
            "sl_percent": 0.02,
        },  # Envia como query params
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Trading is already running with the same parameters - trade_id_123"
    }
    mock_start_trading.assert_called_once()

@patch("core.instances.trader_manager.stop_trading")
def test_stop_trading(mock_stop_trading):
    mock_stop_trading.return_value = {"status": "success", "message": "Trading stopped for trade_id_123"}

    response = client.post("/trading/stop/trade_id/trade_id_123")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Trading stopped for trade_id_123"}
    mock_stop_trading.assert_called_once_with("trade_id_123")

@patch("core.instances.trader_manager.get_active_traders")
def test_get_active_traders(mock_get_active_traders):
    mock_get_active_traders.return_value = {
        "active_traders": [
            {"trade_id": "123", "symbol": "BTCUSDT", "active": True},
            {"trade_id": "124", "symbol": "ETHUSDT", "active": True},
        ]
    }

    response = client.get("/trading/active")
    assert response.status_code == 200
    assert response.json() == {
        "active_traders": [
            {"trade_id": "123", "symbol": "BTCUSDT", "active": True},
            {"trade_id": "124", "symbol": "ETHUSDT", "active": True},
        ]
    }
    mock_get_active_traders.assert_called_once()

@patch("core.instances.trader_manager.signal_manager.check_signals")
def test_check_signals(mock_check_signals):
    mock_check_signals.return_value = [{"signal": "buy", "symbol": "BTCUSDT"}]

    response = client.get("/trading/signals/check")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "signals": [{"signal": "buy", "symbol": "BTCUSDT"}]}
    mock_check_signals.assert_called_once()
