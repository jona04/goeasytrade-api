from fastapi import APIRouter, Query
from typing import Optional
from operations.trade_executor import TradeExecutor
from pydantic import BaseModel, Field
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from models.create_trade import CreateTrade
from models.break_even_request import BreakEvenRequest
from models.close_partial_request import ClosePartialRequest
from models.adjust_stop_loss_request import AdjustStopLossRequest
from models.monitor_tp_sl_request import MonitorTpSlRequest
from models.close_remaining_request import CloseRemainingRequest

router = APIRouter()
trade_executor = TradeExecutor()

class TradeUpdate(BaseModel):
    updates: Dict[str, Any] = Field(
        ...,
        description="Campos a serem atualizados no trade.",
        example={
            "quantity": 100,
            "activate": True,
            "stop_loss": 1.4500
        }
    )

@router.get("/opened_trades")
def get_opened_trades(
    activate: Optional[bool] = Query(None, description="True para buscar opened_trades ativos, False para inativos."),
    partial_close_triggered: Optional[bool] = Query(None, description="True para opened_trades com parcial ativada, False para sem parcial.")
):
    """
    Retorna opened_trades com base nos parâmetros fornecidos.
    """
    try:
        opened_trades = trade_executor.get_opened_trades(
            activate=activate, 
            partial_close_triggered=partial_close_triggered
        )
        return {"opened_trades": opened_trades}
    except Exception as e:
        return {"error": str(e)}

@router.put("/opened_trades/{opened_trade_id}")
def edit_opened_trade(opened_trade_id: str, trade_update: TradeUpdate):
    """
    Atualiza um trade específico no banco de dados.
    :param opened_trade_id: ID do trade a ser editado.
    :param trade_update: Dados a serem atualizados.
    """
    try:
        result = trade_executor.edit_opened_trades(
            opened_trade_id=int(opened_trade_id), 
            updates=trade_update.updates
        )
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/opened_trades")
def create_trade(trade: CreateTrade):
    """
    Cria um novo trade na coleção `opened_trades`.
    """
    try:
        # Insere ou atualiza o trade na coleção `opened_trades`
        result = trade_executor.edit_trades(
            opened_trade_id=trade.open_order_id,
            updates={
                "trade_id": trade.trade_id,
                "entry_price": trade.entry_price,
                "symbol": trade.symbol,
                "position_side": trade.position_side,
                "quantity": trade.quantity,
                "stop_loss_order_id": trade.stop_loss_order_id,
                "take_profit_order_id": trade.take_profit_order_id,
                "activate": trade.activate,
                "close_type": trade.close_type,
                "take_profit": trade.take_profit,
                "stop_loss": trade.stop_loss,
                "break_even": trade.break_even,
                "timestamp": trade.timestamp,
            },
            upsert=True
        )

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])

        return {"status": "success", "message": f"Trade aberto {trade.open_order_id} criado com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check_break_even_and_partial")
def check_break_even_and_partial(request: BreakEvenRequest):
    """
    Endpoint para verificar se o lucro percentual atingiu o limiar para ativar o Break Even
    e, se necessário, realizar o encerramento parcial.
    """
    try:
        trade_executor.check_break_even_and_partial(
            opened_trade=request.opened_trade,
            current_price=request.current_price
        )
        return {
            "status": "success",
            "message": f"Verificação de Break Even concluída para o trade {request.opened_trade.get('_id', 'desconhecido')}."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao verificar Break Even: {str(e)}")
    
@router.post("/close_partial_position")
def close_partial_position(request: ClosePartialRequest):
    """
    Endpoint para fechar parcialmente uma posição aberta.
    """
    try:
        trade_executor.close_partial_position(
            opened_trade=request.opened_trade,
            percentage=request.percentage
        )
        return {
            "status": "success",
            "message": f"Parcial de {request.percentage}% encerrada para o trade {request.opened_trade.get('_id', 'desconhecido')}."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao fechar posição parcial: {str(e)}")
    

@router.post("/adjust_stop_loss")
def adjust_stop_loss(request: AdjustStopLossRequest):
    """
    Endpoint para ajustar o Stop Loss de uma posição aberta.
    """
    try:
        trade_executor.adjust_stop_loss(
            opened_trade=request.opened_trade,
            new_sl_price=request.new_sl_price
        )
        return {
            "status": "success",
            "message": f"Novo Stop Loss ajustado para {request.new_sl_price} no trade {request.opened_trade.get('_id', 'desconhecido')}."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ajustar Stop Loss: {str(e)}")


@router.post("/cancel_order")
def cancel_order(symbol: str = Query(..., description="Símbolo do ativo (ex: BTCUSDT)"),
                 order_id: int = Query(..., description="ID da ordem a ser cancelada")):
    """
    Endpoint para cancelar uma ordem específica.
    """
    try:
        trade_executor.cancel_order(symbol=symbol, order_id=order_id)
        return {
            "status": "success",
            "message": f"Ordem {order_id} cancelada com sucesso para o símbolo {symbol}."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao cancelar a ordem: {str(e)}")
    
    
@router.post("/monitor_tp_sl_for_remaining_position")
def monitor_tp_sl_for_remaining_position(request: MonitorTpSlRequest):
    """
    Endpoint para monitorar a posição restante de um trade para fechamento no TP ou no novo SL ajustado.
    """
    try:
        # Transforma os dados da requisição no formato esperado pelo método
        opened_trade = {
            "_id": request._id,
            "symbol": request.symbol,
            "remaining_quantity": request.remaining_quantity,
            "take_profit": request.take_profit,
            "stop_loss": request.stop_loss,
            "activate": request.activate,
        }

        # Chama o método de monitoramento
        trade_executor.monitor_tp_sl_for_remaining_position(opened_trade=opened_trade)

        return {
            "status": "success",
            "message": f"Monitoramento de TP/SL concluído para o trade aberto {request._id}."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao monitorar TP/SL: {str(e)}")

@router.post("/close_remaining_position")
def close_remaining_position(request: CloseRemainingRequest):
    """
    Endpoint para encerrar a posição restante de um trade.
    """
    try:
        # Transforma os dados da requisição no formato esperado pelo método
        opened_trade = {
            "_id": request._id,
            "symbol": request.symbol,
            "position_side": request.position_side,
            "remaining_quantity": request.remaining_quantity
        }

        # Chama o método de fechamento
        trade_executor.close_remaining_position(
            opened_trade=opened_trade,
            reason=request.reason
        )

        return {
            "status": "success",
            "message": f"Trade aberto {request._id} encerrado por {request.reason}."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao encerrar posição restante: {str(e)}")
