from fastapi import APIRouter, Query
from typing import Optional
from operations.trade_executor import TradeExecutor

router = APIRouter()
trade_executor = TradeExecutor()

@router.get("/trades")
def get_trades(
    activate: Optional[bool] = Query(None, description="True para buscar trades ativos, False para inativos."),
    partial_close_triggered: Optional[bool] = Query(None, description="True para trades com parcial ativada, False para sem parcial.")
):
    """
    Retorna trades com base nos parâmetros fornecidos.
    """
    try:
        trades = trade_executor.get_trades(activate=activate, partial_close_triggered=partial_close_triggered)
        return {"trades": trades}
    except Exception as e:
        return {"error": str(e)}