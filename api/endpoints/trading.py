from fastapi import APIRouter, HTTPException
from core.instances import trader_manager

router = APIRouter()


@router.post("/start/{symbol}")
async def start_trading(
    symbol: str,
    bar_length: str,
    units: float,
    historical_days: float,
    strategy_type: int,
    ema_s: int,
    ema_l: int,
    emaper_window: int,
    emaper_s: int, 
    emaper_force: float, 
    sl_percent: float,
    rsi_force: float, 
    rsi_window: int, 
    adx_force: float, 
    adx_window: int
):
    response = await trader_manager.start_trading(
        symbol,
        bar_length,
        units,
        historical_days,
        strategy_type,
        ema_s,
        ema_l,
        emaper_window,
        emaper_s, 
        emaper_force, 
        sl_percent,
        rsi_force, 
        rsi_window, 
        adx_force, 
        adx_window
    )
    if response["status"] == "error":
        raise HTTPException(status_code=400, detail=response["message"])
    return response


@router.post("/stop/{symbol}")
async def stop_trading(symbol: str):
    response = await trader_manager.stop_trading(symbol)
    if response["status"] == "error":
        raise HTTPException(status_code=404, detail=response["message"])
    return response


@router.get("/active")
async def get_active_traders():
    return trader_manager.get_active_traders()
