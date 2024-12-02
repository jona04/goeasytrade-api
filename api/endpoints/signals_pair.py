from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any
from core.signal_pair_manager import SignalPairManager
from datetime import datetime

router = APIRouter()
signal_manager = SignalPairManager()

class RegisterSignalRequest(BaseModel):
    pair_trader_id: str = Field(..., description="ID único do trade relacionado ao sinal.")
    signal: Dict[str, Any] = Field(
        ...,
        description="Dados do sinal que devem ser registrados, como preços e direção do mercado."
    )

@router.post("/register_signal")
def register_signal(request: RegisterSignalRequest):
    """
    Registra um novo sinal para o trade especificado.
    """
    try:
        signal_manager.register_signal(pair_trader_id=request.pair_trader_id, signal=request.signal)
        return {
            "status": "success",
            "message": f"Sinal registrado para o trade {request.pair_trader_id}."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
