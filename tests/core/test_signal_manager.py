import pytest
from unittest.mock import MagicMock, patch
from collections import defaultdict
from core.signal_manager import SignalManager
import pandas as pd

@pytest.fixture
def signal_manager():
    return SignalManager(total_tasks=5)


# Teste para `register_signal`
def test_register_signal(signal_manager):
    trade_id = "trade1"
    signal = {"SIGNAL_UP": 1}
    signal_manager.register_signal(trade_id, signal)
    assert signal_manager.signals[trade_id] == [signal]


# Teste para `register_task_completion`
@patch("core.signal_manager.SignalManager.process_signals")
def test_register_task_completion(mock_process_signals, signal_manager):
    signal_manager.completed_tasks_count = 4  # Total tasks - 1
    signal_manager.register_task_completion("2023-01-01T12:00:00")
    assert signal_manager.completed_tasks_count == 0
    mock_process_signals.assert_called_once()


@patch("core.signal_manager.SignalManager.process_signals")
def test_register_task_completion_not_ready(mock_process_signals, signal_manager):
    signal_manager.completed_tasks_count = 2  # Menor que total_tasks
    signal_manager.register_task_completion("2023-01-01T12:00:00")
    assert signal_manager.completed_tasks_count == 3
    mock_process_signals.assert_not_called()


@patch("core.signal_manager.SignalManager.process_signals")
def test_register_task_completion_already_processed(mock_process_signals, signal_manager):
    signal_manager.completed_tasks_count = 4  # Total tasks - 1
    signal_manager.last_processed_timestamp = "2023-01-01T12:00:00"
    signal_manager.register_task_completion("2023-01-01T12:00:00")
    assert signal_manager.completed_tasks_count == 5  # Apenas incrementa
    mock_process_signals.assert_not_called()

@patch("core.signal_manager.SignalManager.process_signals")
def test_register_task_completion_count_exceeds_total(mock_process_signals, signal_manager):
    signal_manager.completed_tasks_count = 6  # Maior que total_tasks (suposto erro lógico)
    signal_manager.register_task_completion("2023-01-01T12:00:00")
    assert signal_manager.completed_tasks_count == 7  # Continua incrementando
    mock_process_signals.assert_not_called()


# Teste para `add_priority_in_db`
def test_add_priority_in_db(signal_manager):
    signal_manager.db = MagicMock()
    signal_manager.add_priority_in_db()
    signal_manager.db.delete_many.assert_called_once_with("priority_criteria")
    signal_manager.db.add_many.assert_called_once()


# Teste para `get_trade_params`
def test_get_trade_params(signal_manager):
    signal_manager.db = MagicMock()
    signal_manager.db.query_single.return_value = {"trade_id": "trade1", "symbol": "BTCUSDT"}
    trade_params = signal_manager.get_trade_params("trade1")
    assert trade_params == {"trade_id": "trade1", "symbol": "BTCUSDT"}
    signal_manager.db.query_single.assert_called_once_with("active_traders", trade_id="trade1")


# Teste para `get_priority_table`
def test_get_priority_table(signal_manager):
    signal_manager.db = MagicMock()
    signal_manager.db.query_all.return_value = [
        {"emaper_s": 50, "emaper_l": 100, "emaper_force": 5, "sl_percent": -0.03}
    ]
    priority_table = signal_manager.get_priority_table()
    assert not priority_table.empty
    signal_manager.db.query_all.assert_called_once_with("priority_criteria")


# Teste para `select_top_signals`
@patch("core.signal_manager.SignalManager.get_priority_table")
def test_select_top_signals(mock_get_priority_table, signal_manager):
    mock_get_priority_table.return_value = pd.DataFrame([
        {"emaper_s": 50, "emaper_l": 100, "emaper_force": 5, "sl_percent": -0.03}
    ])
    signals = {"trade1": [{"SIGNAL_UP": 1}]}
    signal_manager.db = MagicMock()
    signal_manager.db.query_single.return_value = {
        "emaper_s": 50, "emaper_l": 100, "emaper_force": 5, "sl_percent": -0.03
    }
    top_signals = signal_manager.select_top_signals(signals)
    assert len(top_signals) == 1


@patch("core.signal_manager.SignalManager.get_priority_table")
def test_select_top_signals_respects_priority_table(mock_get_priority_table, signal_manager):
    # Simula a tabela de prioridade (ordem já representa a prioridade)
    mock_get_priority_table.return_value = pd.DataFrame([
        {"emaper_s": 50, "emaper_l": 100, "emaper_force": 5, "sl_percent": -0.03},
        {"emaper_s": 50, "emaper_l": 100, "emaper_force": 4, "sl_percent": -0.02},
        {"emaper_s": 20, "emaper_l": 50, "emaper_force": 5, "sl_percent": -0.04},
        {"emaper_s": 10, "emaper_l": 50, "emaper_force": 2, "sl_percent": -0.03},
        {"emaper_s": 5, "emaper_l": 100, "emaper_force": 2, "sl_percent": -0.04},
    ])

    # Simula sinais associados a trades
    signals = {
        "trade1": [{"SIGNAL_UP": 1}],  # Prioridade 1
        "trade2": [{"SIGNAL_UP": 2}],  # Prioridade 2
        "trade3": [{"SIGNAL_UP": 3}],  # Prioridade 3
        "trade4": [{"SIGNAL_UP": 4}],  # Prioridade 4
        "trade5": [{"SIGNAL_UP": 5}],  # Prioridade 5
        "trade6": [{"SIGNAL_UP": 6}],  # Fora do top 5
    }

    # Mock para `get_trade_params`
    def mock_get_trade_params(trade_id):
        trade_id_to_params = {
            "trade1": {"emaper_s": 50, "emaper_l": 100, "emaper_force": 5, "sl_percent": -0.03},
            "trade2": {"emaper_s": 50, "emaper_l": 100, "emaper_force": 4, "sl_percent": -0.02},
            "trade3": {"emaper_s": 20, "emaper_l": 50, "emaper_force": 5, "sl_percent": -0.04},
            "trade4": {"emaper_s": 10, "emaper_l": 50, "emaper_force": 2, "sl_percent": -0.03},
            "trade5": {"emaper_s": 5, "emaper_l": 100, "emaper_force": 2, "sl_percent": -0.04},
            "trade6": {"emaper_s": 5, "emaper_l": 100, "emaper_force": 2, "sl_percent": -0.03},
        }
        return trade_id_to_params.get(trade_id, {})

    signal_manager.get_trade_params = MagicMock(side_effect=mock_get_trade_params)

    # Executa o método
    top_signals = signal_manager.select_top_signals(signals)

    # Valida se apenas os 5 sinais prioritários foram retornados
    assert len(top_signals) == 5

    # Verifica se os sinais estão em ordem de prioridade conforme a tabela
    expected_signals = [
        ({"emaper_s": 50, "emaper_l": 100, "emaper_force": 5, "sl_percent": -0.03}, {"SIGNAL_UP": 1}),
        ({"emaper_s": 50, "emaper_l": 100, "emaper_force": 4, "sl_percent": -0.02}, {"SIGNAL_UP": 2}),
        ({"emaper_s": 20, "emaper_l": 50, "emaper_force": 5, "sl_percent": -0.04}, {"SIGNAL_UP": 3}),
        ({"emaper_s": 10, "emaper_l": 50, "emaper_force": 2, "sl_percent": -0.03}, {"SIGNAL_UP": 4}),
        ({"emaper_s": 5, "emaper_l": 100, "emaper_force": 2, "sl_percent": -0.04}, {"SIGNAL_UP": 5}),
    ]
    assert top_signals == expected_signals

# Teste para `process_signals`
@patch("core.signal_manager.SignalManager.select_top_signals", return_value=[({}, {"SIGNAL_UP": 1})])
@patch("core.signal_manager.TradeExecutor.execute_trade")
def test_process_signals(mock_execute_trade, mock_select_top_signals, signal_manager):
    signal_manager.get_signals = MagicMock(return_value={"trade1": [{"SIGNAL_UP": 1}]})
    signal_manager.process_signals()
    mock_execute_trade.assert_called_once()


@patch("core.signal_manager.SignalManager.select_top_signals", return_value=[({}, {"SIGNAL_UP": 1})])
@patch("core.signal_manager.TradeExecutor.execute_trade")
@patch("core.signal_manager.DataDB.query_single", return_value={"use_top_signals": True})
def test_process_signals_use_top_signals_true(mock_query_single, mock_execute_trade, mock_select_top_signals, signal_manager):
    signal_manager.get_signals = MagicMock(return_value={"trade1": [{"SIGNAL_UP": 1}]})
    signal_manager.process_signals()

    # Verificar que `select_top_signals` foi chamado
    mock_select_top_signals.assert_called_once_with({"trade1": [{"SIGNAL_UP": 1}]}, top_n=10)

    # Verificar que `execute_trade` foi chamado para o sinal retornado
    mock_execute_trade.assert_called_once_with({}, {"SIGNAL_UP": 1})


@patch("core.signal_manager.TradeExecutor.execute_trade")
@patch("core.signal_manager.DataDB.query_single", return_value={"use_top_signals": False})
def test_process_signals_use_top_signals_false(mock_query_single, mock_execute_trade, signal_manager):
    signal_manager.get_signals = MagicMock(return_value={"trade1": [{"SIGNAL_UP": 1}, {"SIGNAL_UP": 2}]})
    signal_manager.get_trade_params = MagicMock(return_value={"param_key": "param_value"})

    signal_manager.process_signals()

    # Verificar que `select_top_signals` não foi chamado
    signal_manager.select_top_signals = MagicMock()
    signal_manager.select_top_signals.assert_not_called()

    # Verificar que `execute_trade` foi chamado para cada sinal
    mock_execute_trade.assert_any_call({"param_key": "param_value"}, {"SIGNAL_UP": 1})
    mock_execute_trade.assert_any_call({"param_key": "param_value"}, {"SIGNAL_UP": 2})
    assert mock_execute_trade.call_count == 2


@patch("core.signal_manager.TradeExecutor.execute_trade")
@patch("core.signal_manager.DataDB.query_single", return_value={"use_top_signals": True})
def test_process_signals_no_signals(mock_query_single, mock_execute_trade, signal_manager):
    signal_manager.get_signals = MagicMock(return_value={})  # Nenhum sinal registrado

    signal_manager.process_signals()

    # Verificar que `execute_trade` não foi chamado
    mock_execute_trade.assert_not_called()


@patch("core.signal_manager.TradeExecutor.execute_trade")
@patch("core.signal_manager.DataDB.query_single", return_value={})  # Não retorna "use_top_signals"
def test_process_signals_default_use_top_signals(mock_query_single, mock_execute_trade, signal_manager):
    signal_manager.get_signals = MagicMock(return_value={"trade1": [{"SIGNAL_UP": 1}]})
    signal_manager.get_trade_params = MagicMock(return_value={"param_key": "param_value"})

    signal_manager.process_signals()

    # Verificar que `execute_trade` foi chamado
    mock_execute_trade.assert_called_once_with({"param_key": "param_value"}, {"SIGNAL_UP": 1})


# Teste para `get_signals`
def test_get_signals(signal_manager):
    signal_manager.signals = defaultdict(list, {"trade1": [{"SIGNAL_UP": 1}]})
    signals = signal_manager.get_signals()
    assert signals == {"trade1": [{"SIGNAL_UP": 1}]}
    assert signal_manager.signals == {}


# Teste para `check_signals`
def test_check_signals(signal_manager):
    signal_manager.signals = defaultdict(list, {"trade1": [{"SIGNAL_UP": 1}]})
    signals = signal_manager.check_signals()
    assert signals == {"trade1": [{"SIGNAL_UP": 1}]}
    assert signal_manager.signals == {"trade1": [{"SIGNAL_UP": 1}]}


@patch("operations.trade_executor.TradeExecutor.close_partial_position")
@patch("operations.trade_executor.TradeExecutor.adjust_stop_loss")
@patch("core.signal_manager.DataDB.query_single")
@patch("operations.trade_executor.TradeExecutor.calculate_profit_percent")
def test_check_break_even_and_partial_partial_close_triggered(
    mock_calculate_profit_percent,
    mock_query_single,
    mock_adjust_stop_loss,
    mock_close_partial_position,
    signal_manager,
):
    """
    Cenário 1: profit_percent >= breakeven_threshold and partial_close_triggered is False.
    """
    # Mock do banco de dados
    signal_manager.db = MagicMock()

    # Mock dos retornos
    signal_manager.db.query_single.side_effect = [
        {
            "_id": "123",
            "entry_price": 100,
            "positionSide": "LONG",
            "partial_close_triggered": False,
        },
        {"breakeven_profit_threshold": 0.03},  # Config do sistema
    ]
    mock_calculate_profit_percent.return_value = 0.05  # Lucro percentual acima do limiar

    # Executa o método
    signal_manager.check_break_even_and_partial("123", 105)

    # Verifica que `close_partial_position` foi chamado
    mock_close_partial_position.assert_called_once_with("123", 50)

    # Verifica que `adjust_stop_loss` foi chamado
    mock_adjust_stop_loss.assert_called_once_with("123", 100)


@patch("operations.trade_executor.TradeExecutor.close_partial_position")
@patch("operations.trade_executor.TradeExecutor.adjust_stop_loss")
@patch("core.signal_manager.DataDB.query_single")
@patch("operations.trade_executor.TradeExecutor.calculate_profit_percent")
def test_check_break_even_and_partial_already_triggered(
    mock_calculate_profit_percent,
    mock_query_single,
    mock_adjust_stop_loss,
    mock_close_partial_position,
    signal_manager,
):
    """
    Cenário 2: profit_percent >= breakeven_threshold but partial_close_triggered is True.
    """
    # Mock do banco de dados
    signal_manager.db = MagicMock()

    # Mock dos retornos
    signal_manager.db.query_single.side_effect = [
        {
            "_id": "123",
            "entry_price": 100,
            "positionSide": "LONG",
            "partial_close_triggered": True,
        },
        {"breakeven_profit_threshold": 0.03},  # Config do sistema
    ]
    mock_calculate_profit_percent.return_value = 0.05  # Lucro percentual acima do limiar

    # Executa o método
    signal_manager.check_break_even_and_partial("123", 105)

    # Verifica que `close_partial_position` não foi chamado
    mock_close_partial_position.assert_not_called()

    # Verifica que `adjust_stop_loss` não foi chamado
    mock_adjust_stop_loss.assert_not_called()


@patch("operations.trade_executor.TradeExecutor.close_partial_position")
@patch("operations.trade_executor.TradeExecutor.adjust_stop_loss")
@patch("core.signal_manager.DataDB.query_single")
@patch("operations.trade_executor.TradeExecutor.calculate_profit_percent")
def test_check_break_even_and_partial_below_threshold(
    mock_calculate_profit_percent,
    mock_query_single,
    mock_adjust_stop_loss,
    mock_close_partial_position,
    signal_manager,
):
    """
    Cenário 3: profit_percent < breakeven_threshold.
    """
    # Mock do banco de dados
    signal_manager.db = MagicMock()

    # Mock dos retornos
    signal_manager.db.query_single.side_effect = [
        {
            "_id": "123",
            "entry_price": 100,
            "positionSide": "LONG",
            "partial_close_triggered": False,
        },
        {"breakeven_profit_threshold": 0.03},  # Config do sistema
    ]
    mock_calculate_profit_percent.return_value = 0.02  # Lucro percentual abaixo do limiar

    # Executa o método
    signal_manager.check_break_even_and_partial("123", 101)

    # Verifica que `close_partial_position` não foi chamado
    mock_close_partial_position.assert_not_called()

    # Verifica que `adjust_stop_loss` não foi chamado
    mock_adjust_stop_loss.assert_not_called()
