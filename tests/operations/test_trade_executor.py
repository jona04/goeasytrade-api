import pytest
from unittest.mock import MagicMock, patch
from operations.trade_executor import TradeExecutor
from binance.exceptions import BinanceAPIException


@pytest.fixture
def trade_executor():
    return TradeExecutor()


@patch("operations.trade_executor.TradeExecutor.calculate_stop_loss", return_value=98.0)
@patch("operations.trade_executor.TradeExecutor.calculate_take_profit", return_value=102.0)
@patch("operations.trade_executor.TradeExecutor.get_quantity", return_value=1)
@patch("operations.trade_executor.TradeExecutor.get_leverage", return_value=10)
@patch("operations.trade_executor.TradeExecutor.open_trade", return_value={"orderId": "123"})
@patch("operations.trade_executor.TradeExecutor.set_stop_loss", return_value={"orderId": "456"})
@patch("operations.trade_executor.TradeExecutor.set_take_profit", return_value={"orderId": "789"})
@patch("operations.trade_executor.Client.futures_account_trades", return_value=[{"price": "100"}])
def test_execute_trade(
    mock_futures_account_trades, 
    mock_set_tp, 
    mock_set_sl, 
    mock_open_trade,
    mock_get_leverage, 
    mock_get_quantity, 
    mock_calculate_tp, 
    mock_calculate_sl, 
    trade_executor
):
    # Mock do banco de dados
    trade_executor.db = MagicMock()

    # Parâmetros do trade
    trade_params = {"symbol": "BTCUSDT", "trade_id": "trade123", "sl_percent": 0.02}
    signal = {"SIGNAL_UP": 1}

    # Executa o método
    order = trade_executor.execute_trade(trade_params, signal)

    # Verificar que `open_trade` foi chamado
    mock_open_trade.assert_called_once_with(symbol="BTCUSDT", side="BUY", quantity=1, position_side="LONG")

    # Verificar que `calculate_stop_loss` e `calculate_take_profit` foram chamados
    mock_calculate_sl.assert_called_once_with(100, trade_params, "LONG")
    mock_calculate_tp.assert_called_once_with(100, trade_params, "LONG")

    # Verificar que `set_stop_loss` foi chamado
    mock_set_sl.assert_called_once_with("BTCUSDT", 1, "LONG", 98.0)

    # Verificar que `set_take_profit` foi chamado
    mock_set_tp.assert_called_once_with("BTCUSDT", 1, "LONG", 102.0)

    # Verificar que `update_trade_status` foi chamado com os valores esperados
    trade_executor.db.update_trade_status.assert_any_call(
        open_order_id="123",
        stop_loss_order_id="456"
    )
    trade_executor.db.update_trade_status.assert_any_call(
        open_order_id="123",
        take_profit_order_id="789"
    )




@patch("operations.trade_executor.Client.futures_create_order", return_value={"orderId": "123"})
def test_open_trade(mock_create_order, trade_executor):
    result = trade_executor.open_trade("BTCUSDT", "BUY", 1, "LONG")
    assert result == {"orderId": "123"}
    mock_create_order.assert_called_once_with(
        symbol="BTCUSDT", side="BUY", type="MARKET", quantity=1, positionSide="LONG"
    )


@patch("operations.trade_executor.Client.futures_get_open_orders", return_value=[{"orderId": "456"}])
@patch("operations.trade_executor.Client.futures_cancel_order")
def test_check_and_close_tp_sl_orders_sl_cancel(
    mock_cancel_order, mock_get_open_orders, trade_executor
):
    trade_executor.db = MagicMock()
    trade_executor.db.query_all.return_value = [
        {"_id": "123", "symbol": "BTCUSDT", "take_profit_order_id": "789", "stop_loss_order_id": "456"}
    ]

    trade_executor.check_and_close_tp_sl_orders()

    # Verificar que `futures_cancel_order` foi chamado para SL
    mock_cancel_order.assert_called_once_with(symbol="BTCUSDT", orderId="456")
    trade_executor.db.update_one.assert_called_once()


@patch("operations.trade_executor.Client.futures_get_open_orders", return_value=[{"orderId": "789"}])
@patch("operations.trade_executor.Client.futures_cancel_order")
def test_check_and_close_tp_sl_orders_tp_cancel(
    mock_cancel_order, mock_get_open_orders, trade_executor
):
    trade_executor.db = MagicMock()
    trade_executor.db.query_all.return_value = [
        {"_id": "123", "symbol": "BTCUSDT", "take_profit_order_id": "789", "stop_loss_order_id": "456"}
    ]

    trade_executor.check_and_close_tp_sl_orders()

    # Verificar que `futures_cancel_order` foi chamado para TP
    mock_cancel_order.assert_called_once_with(symbol="BTCUSDT", orderId="789")
    trade_executor.db.update_one.assert_called_once()



# Teste do método `close_partial_position`
@patch("operations.trade_executor.Client.futures_create_order")
def test_close_partial_position(mock_create_order, trade_executor):
    mock_create_order.return_value = {"orderId": "partial1"}
    trade_executor.db = MagicMock()
    trade_executor.db.query_single.return_value = {
        "_id": "123", "symbol": "BTCUSDT", "positionSide": "LONG", "quantity": 1, "entry_price": 100
    }

    trade_executor.close_partial_position("123", 50)

    mock_create_order.assert_called_once_with(
        symbol="BTCUSDT", side="SELL", type="MARKET", quantity=0.5, positionSide="LONG"
    )
    trade_executor.db.update_partial_close.assert_called_once_with(
        "123", closed_percentage=50, remaining_quantity=0.5, break_even_price=100
    )


# Teste do método `adjust_stop_loss`
@patch("operations.trade_executor.TradeExecutor.set_stop_loss")
def test_adjust_stop_loss(mock_set_stop_loss, trade_executor):
    trade_executor.db = MagicMock()
    trade_executor.db.query_single.return_value = {
        "_id": "123", "symbol": "BTCUSDT", "positionSide": "LONG", "remaining_quantity": 0.5
    }

    mock_set_stop_loss.return_value = {"orderId": "new_sl"}
    trade_executor.adjust_stop_loss("123", 101)

    mock_set_stop_loss.assert_called_once_with("BTCUSDT", 0.5, "LONG", 101)
    trade_executor.db.update_trade_status.assert_called_once_with(
        open_order_id="123", stop_loss_order_id="new_sl"
    )


# Teste do método `monitor_tp_sl_for_remaining_position`
@patch("operations.trade_executor.Client.futures_mark_price")
@patch("operations.trade_executor.TradeExecutor.close_remaining_position")
def test_monitor_tp_sl_for_remaining_position(mock_close_remaining, mock_mark_price, trade_executor):
    trade_executor.db = MagicMock()
    trade_executor.db.query_single.return_value = {
        "_id": "123",
        "symbol": "BTCUSDT",
        "remaining_quantity": 0.5,
        "take_profit": 105,
        "stop_loss": 95,
        "activate": True,
    }
    mock_mark_price.return_value = {"markPrice": "105"}

    trade_executor.monitor_tp_sl_for_remaining_position("123")
    mock_close_remaining.assert_called_once_with("123", reason="TP")

# Teste para o método `activate_break_even`
@patch("operations.trade_executor.TradeExecutor.set_stop_loss")
@patch("operations.trade_executor.TradeExecutor.cancel_order")
def test_activate_break_even(mock_cancel_order, mock_set_stop_loss, trade_executor):
    trade_executor.db = MagicMock()
    trade_executor.db.query_single.return_value = {
        "_id": "123",
        "symbol": "BTCUSDT",
        "positionSide": "LONG",
        "quantity": 1,
        "entry_price": 100,
        "stop_loss_order_id": "sl123"
    }
    mock_set_stop_loss.return_value = {"orderId": "new_sl"}

    trade_executor.activate_break_even({"_id": "123", "symbol": "BTCUSDT", "positionSide": "LONG", "quantity": 1, "entry_price": 100, "stop_loss_order_id": "sl123"})

    # Verificar que a ordem de Stop Loss existente foi cancelada
    mock_cancel_order.assert_called_once_with("BTCUSDT", "sl123")

    # Verificar que um novo Stop Loss foi definido
    mock_set_stop_loss.assert_called_once_with("BTCUSDT", 1, "LONG", 100)

    # Verificar que o status do trade foi atualizado
    trade_executor.db.update_trade_status.assert_called_once_with(
        open_order_id="123",
        stop_loss_order_id="new_sl",
        break_even=True
    )


# Teste para o método `close_remaining_position`
@patch("operations.trade_executor.Client.futures_create_order")
def test_close_remaining_position(mock_create_order, trade_executor):
    mock_create_order.return_value = {"orderId": "close1"}
    trade_executor.db = MagicMock()
    trade_executor.db.query_single.return_value = {
        "_id": "123",
        "symbol": "BTCUSDT",
        "positionSide": "LONG",
        "remaining_quantity": 0.5,
    }

    trade_executor.close_remaining_position("123", reason="TP")

    # Verificar que a ordem foi enviada para fechar a posição restante
    mock_create_order.assert_called_once_with(
        symbol="BTCUSDT", side="SELL", type="MARKET", quantity=0.5, positionSide="LONG"
    )

    # Verificar que o banco de dados foi atualizado para desativar o trade
    trade_executor.db.update_trade_status.assert_called_once_with(
        open_order_id="123",
        activate=False,
        close_type="TP",
        stop_loss_order_id=None,
        take_profit_order_id=None
    )


# Teste para o método `cancel_order`
@patch("operations.trade_executor.Client.futures_cancel_order")
def test_cancel_order(mock_cancel_order, trade_executor):
    trade_executor.cancel_order("BTCUSDT", "order123")

    # Verificar que a ordem foi cancelada corretamente
    mock_cancel_order.assert_called_once_with(symbol="BTCUSDT", orderId="order123")

# Teste para o método `calculate_take_profit`
def test_calculate_take_profit(trade_executor):
    # Cenário 1: Posição LONG
    entry_price = 100
    trade_params_long = {"sl_percent": 0.05}
    position_side_long = "LONG"

    tp_price_long = trade_executor.calculate_take_profit(entry_price, trade_params_long, position_side_long)

    # Verifica que o preço de Take Profit foi calculado corretamente para LONG
    assert tp_price_long == 105.0  # 100 + (100 * 0.05)

    # Cenário 2: Posição SHORT
    entry_price = 100
    trade_params_short = {"sl_percent": 0.05}
    position_side_short = "SHORT"

    tp_price_short = trade_executor.calculate_take_profit(entry_price, trade_params_short, position_side_short)

    # Verifica que o preço de Take Profit foi calculado corretamente para SHORT
    assert tp_price_short == 95.0  # 100 - (100 * 0.05)


# Teste para o método `calculate_stop_loss`
def test_calculate_stop_loss(trade_executor):
    # Cenário 1: Posição LONG
    entry_price = 100
    trade_params_long = {"sl_percent": 0.05}
    position_side_long = "LONG"

    sl_price_long = trade_executor.calculate_stop_loss(entry_price, trade_params_long, position_side_long)

    # Verifica que o preço de Stop Loss foi calculado corretamente para LONG
    assert sl_price_long == 95.0  # 100 - (100 * 0.05)

    # Cenário 2: Posição SHORT
    entry_price = 100
    trade_params_short = {"sl_percent": 0.05}
    position_side_short = "SHORT"

    sl_price_short = trade_executor.calculate_stop_loss(entry_price, trade_params_short, position_side_short)

    # Verifica que o preço de Stop Loss foi calculado corretamente para SHORT
    assert sl_price_short == 105.0  # 100 + (100 * 0.05)


def test_get_quantity(trade_executor):
    # Mock manual do atributo `db`
    trade_executor.db = MagicMock()
    trade_executor.db.query_single.return_value = {"quantity": 1}

    # Executa o método
    result = trade_executor.get_quantity("BTCUSDT")

    # Verifica o resultado
    assert result == 1
    trade_executor.db.query_single.assert_called_once_with("config_assets", symbol="BTCUSDT")

def test_get_leverage(trade_executor):
    # Mock manual do atributo `db`
    trade_executor.db = MagicMock()
    trade_executor.db.query_single.return_value = {"leverage": 10}

    # Executa o método
    result = trade_executor.get_leverage("BTCUSDT")

    # Verifica o resultado
    assert result == 10
    trade_executor.db.query_single.assert_called_once_with("config_assets", symbol="BTCUSDT")

def test_log_order(trade_executor):
    # Mock manual do atributo `db`
    trade_executor.db = MagicMock()

    # Ordem fictícia
    order = {"orderId": "123", "symbol": "BTCUSDT"}

    # Executa o método
    trade_executor.log_order(order)

    # Verifica se `add_one` foi chamado corretamente
    trade_executor.db.add_one.assert_called_once_with("orders", order)
