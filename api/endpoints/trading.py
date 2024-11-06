from fastapi import APIRouter, HTTPException
from core.instances import trader_manager

router = APIRouter()

@router.post("/start/{symbol}")
async def start_trading(
    symbol: str, bar_length: str, ema_s: int, units: float, quote_units: float, historical_days: float
):
    response = await trader_manager.start_trading(symbol, bar_length, ema_s, units, quote_units, historical_days)
    if response["status"] == "error":
        raise HTTPException(status_code=400, detail=response["message"])
    return response

@router.post("/stop/{symbol}")
async def stop_trading(
    symbol: str
):
    response = await trader_manager.stop_trading(symbol)
    if response["status"] == "error":
        raise HTTPException(status_code=404, detail=response["message"])
    return response

@router.get("/active")
async def get_active_traders():
    return trader_manager.get_active_traders()
