import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from core.manager import TraderManager

@pytest.fixture
def trader_manager():
    return TraderManager()

@patch("core.manager.BinanceSocketManager")
@patch("core.manager.AsyncClient.create", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_init_binance_client(mock_async_client, mock_socket_manager, trader_manager):
    # Configura os mocks
    mock_client_instance = MagicMock()
    mock_async_client.return_value = mock_client_instance
    mock_socket_manager_instance = MagicMock()
    mock_socket_manager.return_value = mock_socket_manager_instance

    # Chama o método
    await trader_manager.init_binance_client()

    # Verifica se os atributos foram inicializados
    assert trader_manager.client == mock_client_instance
    assert trader_manager.bm == mock_socket_manager_instance

    # Verifica se os mocks foram chamados corretamente
    mock_async_client.assert_called_once()  # Confirma que AsyncClient.create foi chamado
    mock_socket_manager.assert_called_once_with(mock_client_instance)  # Confirma que BinanceSocketManager foi chamado com o cliente


# @pytest.mark.asyncio
# async def test_close_binance_client(trader_manager):
#     # Mock de `db`
#     trader_manager.db = MagicMock()
#     trader_manager.db.update_many = MagicMock()

#     # Mock do cliente Binance
#     mock_client = AsyncMock()
#     trader_manager.client = mock_client

#     # Mock das tarefas em segundo plano
#     mock_task = AsyncMock()
#     trader_manager.background_tasks = [mock_task]

#     await trader_manager.close_binance_client()

#     # Verifique se os métodos foram chamados corretamente
#     trader_manager.db.update_many.assert_called_once_with("active_traders", {}, {"active": False})
#     trader_manager.client.close_connection.assert_called_once()
#     for task in trader_manager.background_tasks:
#         task.cancel.assert_called_once()




def test_generate_trade_id(trader_manager):
    params = {"symbol": "BTCUSDT", "strategy": 1, "sl_percent": 0.02}
    trade_id = trader_manager._generate_trade_id(**params)
    assert isinstance(trade_id, str)
    assert len(trade_id) == 32  # MD5 hash tem 32 caracteres


@pytest.mark.asyncio
async def test_start_trading(trader_manager):
    # Mock de `db` e métodos dependentes
    trader_manager.db = MagicMock()
    trader_manager.db.query_single.return_value = None  # Indica que o trade não existe
    trader_manager.get_historical_data = MagicMock(return_value=MagicMock())  # Mocka dados históricos
    trader_manager.signal_manager = MagicMock()  # Mock do SignalManager
    trader_manager.bm = MagicMock()  # Mock do BinanceSocketManager
    trader_manager.db.add_one = MagicMock()  # Mock para adicionar o trade

    # Chama o método start_trading
    response = await trader_manager.start_trading(
        symbol="BTCUSDT",
        bar_length="1h",
        strategy_type=1,
        ema_s=10,
        emaper_s=20,
        emaper_l=50,
        emaper_force=1.5,
        sl_percent=0.02,
    )

    # Verifica o resultado esperado
    assert response["status"] == "success"
    trader_manager.db.add_one.assert_called_once()  # Verifica se o trade foi adicionado ao banco


@pytest.mark.asyncio
async def test_stop_trading(trader_manager):
    # Mock de `db`
    trader_manager.db = MagicMock()
    trader_manager.db.query_single.return_value = {"active": True}

    response = await trader_manager.stop_trading("trade_id_123")

    assert response["status"] == "success"
    trader_manager.db.update_one.assert_called_once_with(
        "active_traders", {"trade_id": "trade_id_123"}, {"active": False}
    )



@patch("binance.Client.get_historical_klines")
@patch("pandas.DataFrame")
def test_get_historical_data(mock_dataframe, mock_get_historical_klines, trader_manager):
    mock_get_historical_klines.return_value = [[1, 2, 3, 4, 5, 6]]
    mock_dataframe.return_value = MagicMock()

    df = trader_manager.get_historical_data("BTCUSDT", "1h")
    assert mock_get_historical_klines.called
    assert isinstance(df, MagicMock)


@patch("pandas.to_datetime")
def test_process_stream_message(mock_to_datetime, trader_manager):
    # Configura mock dos dados do candle
    mock_to_datetime.return_value = "2023-01-01 00:00:00"
    mock_msg = {
        "k": {
            "t": 1672444800000,
            "o": "1.0",
            "h": "2.0",
            "l": "0.5",
            "c": "1.5",
            "v": "100",
            "x": True,
        }
    }
    mock_symbol = "BTCUSDT"

    # Mock de update_candle_data
    trader_manager.update_candle_data = MagicMock()

    # Chama o método
    trader_manager.process_stream_message(mock_symbol, mock_msg)

    # Verifica a chamada do update_candle_data quando o candle estiver completo
    trader_manager.update_candle_data.assert_called_once_with(
        mock_symbol,
        [
            1.0,  # Open
            2.0,  # High
            0.5,  # Low
            1.5,  # Close
            100.0,  # Volume
            "2023-01-01 00:00:00",  # Start Time
            True,  # Complete
        ],
        "2023-01-01 00:00:00",
    )

def test_update_candle_data(trader_manager):
    # Mock dos dados
    mock_symbol = "BTCUSDT"
    mock_candle_data = [1.0, 2.0, 0.5, 1.5, 100.0, "2023-01-01 00:00:00", True]
    mock_start_time = "2023-01-01 00:00:00"

    # Mock de atributos e métodos dependentes
    trader_manager.candle_data = {mock_symbol: MagicMock()}
    trader_manager.monitor_trades_for_partial_close = MagicMock()
    trader_manager.active_trader_instances = {
        "trade_id_123": MagicMock(symbol=mock_symbol)
    }
    mock_trader_instance = trader_manager.active_trader_instances["trade_id_123"]

    # Chama o método
    trader_manager.update_candle_data(mock_symbol, mock_candle_data, mock_start_time)

    # Verifica se o DataFrame centralizado foi atualizado
    trader_manager.candle_data[mock_symbol].loc.__setitem__.assert_called_once_with(
        mock_start_time, mock_candle_data
    )

    # Verifica se monitor_trades_for_partial_close foi chamado
    trader_manager.monitor_trades_for_partial_close.assert_called_once_with(
        mock_symbol, mock_candle_data
    )

    # Verifica se a estratégia do trader foi atualizada
    mock_trader_instance.define_strategy.assert_called_once_with(mock_start_time)

def test_monitor_trades_for_partial_close(trader_manager):
    # Mock dos dados
    mock_symbol = "BTCUSDT"
    mock_candle_data = {"Close": 1.5}
    mock_trade = {"_id": "trade_id_123", "symbol": mock_symbol}

    # Mock de métodos dependentes
    trader_manager.db.query_partial_trades = MagicMock(return_value=[mock_trade])
    trader_manager.signal_manager.check_break_even_and_partial = MagicMock()
    trader_manager.trade_executor.monitor_tp_sl_for_remaining_position = MagicMock()

    # Chama o método
    trader_manager.monitor_trades_for_partial_close(mock_symbol, mock_candle_data)

    # Verifica as chamadas
    trader_manager.db.query_partial_trades.assert_called_once()
    trader_manager.signal_manager.check_break_even_and_partial.assert_called_once_with(
        "trade_id_123", 1.5
    )
    trader_manager.trade_executor.monitor_tp_sl_for_remaining_position.assert_called_once_with(
        "trade_id_123"
    )
