from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.instances import pair_trader_manager

router = APIRouter()

class PairTradingConfig(BaseModel):
    target_asset: str
    cluster_assets: list[str]
    entry_threshold: float
    exit_threshold: float
    window: int
    stop_loss: float
    trailing_stop_target: float
    trailing_stop_loss: float

@router.post("/start", summary="Inicia uma sessão de pair-trading")
async def start_pair_trading(config: PairTradingConfig):
    """
    Cria uma nova sessão de pair-trading e salva a configuração no banco.
    """
    try:
        result = await pair_trader_manager.start_pair_trading(
            config.target_asset,
            config.cluster_assets,
            config.entry_threshold,
            config.exit_threshold,
            config.window,
            config.stop_loss,
            config.trailing_stop_target,
            config.trailing_stop_loss
            
        )
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
