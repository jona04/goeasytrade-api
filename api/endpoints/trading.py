from fastapi import APIRouter, HTTPException
from core.instances import trader_manager

router = APIRouter()

@router.post("/start/{symbol}")
async def start_trading(
    symbol: str,
    bar_length: str,
    strategy_type: int,
    ema_s: int,
    emaper_s: int,
    emaper_l: int,
    emaper_force: float,
    sl_percent: float,
):
    response = await trader_manager.start_trading(
        symbol,
        bar_length,
        strategy_type,
        ema_s,
        emaper_s,
        emaper_l,
        emaper_force,
        sl_percent,
    )
    if response["status"] == "error":
        raise HTTPException(status_code=400, detail=response["message"])
    return response


@router.post("/start/trade_id/{trade_id}")
async def start_trading_with_trade_id(trade_id: str):
    """Inicia um trading baseado em um trade_id existente no banco."""
    try:
        # Verifica se o trade_id existe no banco de dados
        existing_trade = trader_manager.db.query_single("active_traders", trade_id=trade_id)
        
        if not existing_trade:
            raise HTTPException(
                status_code=404,
                detail=f"Trade ID {trade_id} não encontrado no banco de dados."
            )

        # Verifica se o trade já está ativo
        if existing_trade["active"]:
            return {
                "status": "error",
                "message": f"Trading já está ativo para o trade_id {trade_id}."
            }

        # Reativa o trade utilizando os dados existentes no banco
        response = await trader_manager.start_trading(
            existing_trade["symbol"],
            existing_trade["bar_length"],
            existing_trade["strategy_type"],
            existing_trade["ema_s"],
            existing_trade["emaper_s"],
            existing_trade["emaper_l"],
            existing_trade["emaper_force"],
            existing_trade["sl_percent"],
        )

        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao iniciar o trading para o trade_id {trade_id}: {str(e)}"
        )


@router.post("/stop/trade_id/{trade_id}")
async def stop_trading(trade_id: str):
    response = await trader_manager.stop_trading(trade_id)
    if response["status"] == "error":
        raise HTTPException(status_code=404, detail=response["message"])
    return response


@router.get("/active")
async def get_active_traders():
    return trader_manager.get_active_traders()


@router.post("/priority/add")
async def add_priority():
    """Endpoint para adicionar critérios de prioridade no banco de dados."""
    try:
        trader_manager.signal_manager.add_priority_in_db()
        return {"status": "success", "message": "Prioridades adicionadas com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/priority/table")
async def get_priority_table():
    """Endpoint para obter a tabela de prioridades."""
    try:
        priority_table = trader_manager.signal_manager.get_priority_table()
        return priority_table.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trade/params/{trade_id}")
async def get_trade_params(trade_id: str):
    """Endpoint para obter os parâmetros de um trade específico."""
    try:
        trade_params = trader_manager.signal_manager.get_trade_params(trade_id)
        if not trade_params:
            raise HTTPException(status_code=404, detail="Trade ID não encontrado.")
        return trade_params
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signals/select")
async def select_top_signals(top_n: int = 10):
    """Endpoint para selecionar os top sinais baseados nas prioridades."""
    try:
        signals = trader_manager.signal_manager.check_signals()  # Recupera sinais
        top_signals = trader_manager.signal_manager.select_top_signals(signals, top_n)
        return {"status": "success", "top_signals": top_signals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/check")
async def check_signals():
    """Endpoint para verificar os sinais sem limpá-los."""
    try:
        signals = trader_manager.signal_manager.check_signals()
        return {"status": "success", "signals": signals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
